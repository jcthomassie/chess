# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
import enum
import itertools
import time

###############################################################################
#  GLOBALS                                                                    #
###############################################################################

# BOARD PROPERTIES
N_RANKS = 8
N_FILES = 8
RANK_ZERO = "8"
FILE_ZERO = "A"

UNICODE_PIECES = False
UNICODE_PIECE_SYMBOLS = {
    "R": u"♖", "r": u"♜",
    "N": u"♘", "n": u"♞",
    "B": u"♗", "b": u"♝",
    "Q": u"♕", "q": u"♛",
    "K": u"♔", "k": u"♚",
    "P": u"♙", "p": u"♟",
}


class Color(enum.Enum):
    WHITE = -1
    BLACK = 1
    DRAW = 0

    @property
    def opponent(self):
        return Color(-self.value)

    @property
    def orientation(self):
        return self.value

###############################################################################
#  BOARD CORE                                                                 #
###############################################################################
class Square:
    """
    Board square representation. Allows flexible conversion between
    string and tuple representations
    """
    ROW_RANGE = range(N_RANKS)
    COL_RANGE = range(N_FILES)

    def __init__(self, row, col, rank=None, file=None):
        """
        Takes row and col coordinates as input.
        """
        # Check if in bounds
        if not row in self.ROW_RANGE:
            raise IndexError("Rank out of bounds!")
        if not col in self.COL_RANGE:
            raise IndexError("File out of bounds!")
        self.row = row
        self.col = col
        self._rank = rank
        self._file = file

    @property
    def file(self):
        """
        Only generate file string when asked first time.
        """
        if self._file is None:
            self._file = self.col_to_file(self.col)
        return self._file

    @property
    def rank(self):
        """
        Only generate rank string when asked first time.
        """
        if self._rank is None:
            self._rank = self.row_to_rank(self.row)
        return self._rank

    @classmethod
    def from_str(cls, pos_str):
        """
        Initializes a Square from a position string.
        A8 -> Square(0, 0)
        """
        if len(pos_str) != 2:
            raise ValueError("Square position string must be 2 characters!")
        pos_str = pos_str.upper()
        pos_tup = ( cls.rank_to_row(pos_str[1]), cls.file_to_col(pos_str[0]) )
        return cls(*pos_tup, rank=pos_str[1], file=pos_str[0])

    @classmethod
    def from_tup(cls, pos_tup):
        """
        Initializes a Square from a position tuple.
        """
        if ( len(pos_tup) != 2 or not isinstance(pos_tup[0], int)
                               or not isinstance(pos_tup[1], int) ):
                raise ValueError("Square position tuple must contain two integers!")
        return cls(*pos_tup)

    @staticmethod
    def file_to_col(file):
        """
        Convert file letter to a column integer
        ( 'A'->0, 'B'->1, ... )
        """
        if not isinstance(file, str):
            raise TypeError("File must be a string!")
        if not file.isalpha():
            raise ValueError("File must be an alphanumeric letter!")
        return ord(file.upper()) - ord(FILE_ZERO)

    @staticmethod
    def col_to_file(col):
        """
        Convert column integer to file letter
        ( 0->'A', 1->'B', ... )
        """
        if not isinstance(col, int):
            raise TypeError("Column must be an int!")
        return chr(ord(FILE_ZERO) + col)

    @staticmethod
    def rank_to_row(rank):
        """
        Convert rank string to row integer
        ( '8'->0, '1'->7, ... )
        """
        if not isinstance(rank, str):
            raise TypeError("Rank must be a string!")
        if not rank.isdigit():
            raise ValueError("Rank must be a digit string!")
        return ord(RANK_ZERO) - ord(rank)

    @staticmethod
    def row_to_rank(row):
        """
        Convert row integer to rank string
        ( 0->'8', 7->'1', ... )
        """
        if not isinstance(row, int):
            raise TypeError("Row must be an int!")
        return chr(ord(RANK_ZERO) - row)

    def __str__(self):
        """
        Return string representation of the square's position
        ( (0, 0)->'A8', (1, 1)->'B8', ... )
        """
        return f"{self.file}{self.rank}"

    def __iter__(self):
        yield self.row
        yield self.col

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return N_RANKS * self.row + self.col

    def __eq__(self, other):
        if isinstance(other, Square):
            return self.__hash__() == other.__hash__()
        elif isinstance(other, tuple):
            return self.row == other[0] and self.row == other[1]

    def __add__(self, other):
        if isinstance(other, Square):
            return (self.row + other.row, self.col + other.col)

    def __sub__(self, other):
        if isinstance(other, Square):
            return (self.row - other.row, self.col - other.col)


class Board:

    fen_library = {
        "Standard" : "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"\
                     " w KQkq - 0 1",
        "Horde"    : "rnbqkbnr/pppppppp/8/1PP2PP1/PPPPPPPP/" \
                     "PPPPPPPP/PPPPPPPP/PPPPPPPP w KQkq - 0 1",
        "Pin"      : "R2rk2r/3pbp2/8/8/8/8/4Q3/R3K2R w KQkq - 0 1",
        "Mate"     : "8/8/1Kn5/3k4/4Q3/6N1/8/8 b KQkq - 0 1",
        "Castle"   : "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "PTest"    : "1r2qkb1/p5pp/4pp2/B2QQN1N/2R4/PP6/2P5/4K3 b KQkq - 0 1",
        "Custom"   : "rzbqkbgr/ppeppepp/8/8/8/8/PPEPPEPP/RZBQKBGR"\
                     " w KQkq - 0 1",
            }

    def __init__(self, fen="Standard", board=None):
        self._board_fmt_str = None
        self._square_list = None
        if fen is None:
            self.reset(board=board)
        else:
            self.load_fen(fen)

    def reset(self, board=None, to_move=Color.WHITE):
        """
        Initializes an empty board, clears game history, sets winner to None
        and to_move to WHITE. If board is specified, use that as the board.
        """
        # Construct board
        if board is None:
            self.board = [ [ None for _ in Square.COL_RANGE ]
                                  for _ in Square.ROW_RANGE
                                  ]
        else:
            self.board = board
        # Game trackers
        self.move_history = [ ]
        self.castle_states = {
            Color.WHITE : {"Q": True, "K": True},
            Color.BLACK : {"Q": True, "K": True},
        }
        self.rook_homes = {
            Color.WHITE: [
                Square(N_RANKS - 1, 0),
                Square(N_RANKS - 1, N_FILES - 1)
            ],
            Color.BLACK: [
                Square(0, 0),
                Square(0, N_FILES - 1)
            ],
        }
        self.en_passant_square = None

        self.to_move = to_move
        self.winner = None
        self.halfmoves = 0
        self.fullmoves = 1

        self._allowed_moves = dict( )
        self._last_move_recompute = None
        self._check = False
        self._last_check_recompute = None
        return

    def _set_coord(self, row, col, piece):
        self.board[row][col] = piece

    def _get_coord(self, row, col):
        return self.board[row][col]

    def _del_coord(self, row, col):
        self.board[row][col] = None

    def __setitem__(self, locus, piece):
        """
        Inserts a piece at the specified square position.
        board['A1'] = Rook(WHITE, 'A1')
        """
        if not (piece is None or isinstance(piece, Piece)):
            raise TypeError("Board can only contain Piece and NoneType objects!")

        if isinstance(locus, tuple) or isinstance(locus, Square):
            self._set_coord(*locus, piece)
        elif isinstance(locus, str):
            self._set_coord(*Square.from_str(locus), piece)
        else:
            raise TypeError("Invalid square locus for board!")

    def __getitem__(self, locus):
        """
        Gets the piece on the specified square position (None for empty square).
        board['A1'] -> Rook(White, A1)
        """
        if isinstance(locus, tuple) or isinstance(locus, Square):
            return self._get_coord(*locus)
        elif isinstance(locus, str):
            return self._get_coord(*Square.from_str(locus))
        else:
            raise TypeError("Invalid square locus for board!")

    def __delitem__(self, locus):
        """
        Removes any piece at the specified board position. Replaces the
        slot with None.
        """
        self[locus] = None

    def add_piece(self, piece, color, square):
        """
        Creates piece of color on square and adds it to the board.
        """
        self[square] = piece(square, color=color)
        return

    def square_generator(self, reverse=False):
        """
        Generator to iterate over all squares of the board. Starts at (0, 0)
        and iterates over rows then columns. If reverse, starts at (N, N) and
        works backwards.
        """
        if reverse:
            row_iter = range(N_RANKS - 1, -1, -1)
            col_iter = range(N_FILES - 1, -1, -1)
        else:
            row_iter = range(0, N_RANKS)
            col_iter = range(0, N_FILES)
        for row in row_iter:
            for col in col_iter:
                yield Square(row, col)

    def square_list(self, reverse=False):
        """
        Get a flat list of all squares on the board. Returns the reverse order
        if reverse is True. Stores the square_generator into a list one time to
        remove the need to repeatedly generate squares.
        """
        # Construct list if it does not yet exist
        if self._square_list is None:
            self._square_list = list(self.square_generator())
        # Return list in specified order
        if reverse:
            return reversed(self._square_list)
        else:
            return self._square_list

    def get_square(self, row, col):
        """
        Efficiently get the square at specified row, col.
        """
        square_index = N_RANKS * row + col
        return self.square_list()[square_index]

    def piece_generator(self, color=None):
        """
        Yields all pieces on the current board. If color is specified, only
        pieces of the specified color are yielded.
        """
        for row in self.board:
            for piece in row:
                if piece is None:
                    continue
                elif color is None or piece.color is color:
                    yield piece

    def coord_slice(self, row_0, col_0, row_1, col_1):
        """
        Generator that yields the squares on the board between from_square and
        to_square, inclusive. Only works for square/diagonal displacements.
        """
        d_row = row_1 - row_0
        d_col = col_1 - col_0
        # VERTICAL
        if d_col == 0:
            dr = (1, -1)[row_1 < row_0] # sign of row change
            for row in range(row_0, row_1 + dr, dr):
                yield row, col_0
        # HORIZONTAL
        elif d_row == 0:
            dc = (1, -1)[col_1 < col_0] # sign of col change
            for col in range(col_0, col_1 + dc, dc):
                yield row_0, col
        # DIAGONAL
        elif abs( d_row ) == abs( d_col ):
            dr = (1, -1)[d_row < 0] # sign of row change
            dc = (1, -1)[d_col < 0] # sign of col change
            r_to_c = dr * dc # 1 if same, -1 if opposite
            for r in range(0, d_row + dr, dr):
                row = row_0 + r
                col = col_0 + r * r_to_c
                yield row, col
        else:
            raise IndexError("Slices must be square or diagonal!")

    def square_slice(self, row_0, col_0, row_1, col_1):
        """
        Generator that yields the squares on the board between from_square and
        to_square, inclusive. Only works for square/diagonal displacements.
        """
        for row, col in self.coord_slice(row_0, col_0, row_1, col_1):
            yield self.get_square(row, col)

    def piece_slice(self, row_0, col_0, row_1, col_1):
        """
        Generator that yields pieces on the board from_square to_square,
        inclusive. Only works for square/diagonal displacements.
        """
        for row, col in self.coord_slice(row_0, col_0, row_1, col_1):
            yield self.board[row][col]

    def find_pieces(self, piece_type, color):
        """
        Yields pieces of the specified type and color from the board.
        """
        for piece in self.piece_generator(color=color):
            if isinstance(piece, piece_type):
                yield piece

    def obstruction(self, from_square, to_square):
        """
        Return True if there is a piece between the two squares.
        Return False if the path is clear.
        """
        return any(list(self.piece_slice(*from_square, *to_square))[1:-1])

    def has_attackers(self, square, color):
        """
        Return True if any pieces of color are eyeing the square.
        Return False otherwise
        """
        for piece in self.piece_generator(color=color):
            # Check if move is valid for piece
            d_row, d_col = square - piece.square
            if not piece.move_is_valid(d_row, d_col, capture=True):
                continue
            # Check for obstructions
            elif not piece.jumps and self.obstruction(piece.square, square):
                continue
            return True
        return False

    def verify_castle(self, king, rook):
        """
        Return True if the King and Rook can castle.
        Return False otherwise.
        """
        if self.obstruction(king.square, rook.square):
            return False
        # Make sure king doesn't cross through check (include current square)
        path = list(self.square_slice(*king.square, *rook.square))[:3]
        for square in path:
            if self.has_attackers(square, king.color.opponent):
                return False
        return True

    def valid_castles(self, king):
        """
        Yield valid castling moves for the input king.
        """
        # Check queen side
        for square, side, d_col in zip(self.rook_homes[king.color], ("Q", "K"), (-2, 2)):
            rook = self[square]
            if isinstance(rook, Rook):
                if self.castle_states[king.color][side]:
                    if self.verify_castle(king, rook):
                        yield self.get_square(king.row, king.col + d_col)

    def valid_targets_king(self, king):
        """
        Yield all valid target squares for a king. Gets list of
        normal king moves, removes moves that leave the king in check, and adds
        valid castling moves.
        """
        # Normal moves
        for square in self.valid_targets_piece(king):
            # Keep moves that do not result in check
            if not self.has_attackers(square, king.color.opponent):
                yield square
        # Castling moves
        for square in self.valid_castles(king):
            yield square

    def valid_targets_pawn(self, pawn):
        """
        Yield all valid target squares for a pawn. Gets list of
        normal pawn moves, adds captures.
        """
        # Normal moves
        for row, col in pawn.pseudovalid_coords_regular():
            target = self.board[row][col]
            if target is None:
                yield self.get_square(row, col)
            else:
                break
        # Captures and en passant
        for row, col in pawn.pseudovalid_coords_capture():
            target = self.board[row][col]
            square = self.get_square(row, col)
            if isinstance(target, Piece) and target.color != pawn.color:
                yield square
            elif square == self.en_passant_square:
                yield square

    def valid_targets_piece(self, piece):
        """
        Yield all valid target squares for the specified piece.
        Does not consider whether a move leaves player in check,
        does not consider castling, does not consider en passant.
        """
        for row, col in piece.pseudovalid_coords():
            # Check if out of bounds
            if not row in Square.ROW_RANGE or not col in Square.COL_RANGE:
                continue
            # Check for target validity
            target = self.board[row][col]
            if isinstance(target, Piece) and target.color is piece.color:
                continue
            # Check for obstructions
            square = self.get_square(row, col)
            if not piece.jumps:
                if self.obstruction(piece.square, square):
                    continue
            yield square

    def valid_moves_all(self):
        """
        Return a dictionary of all valid moves in the current board
        configuration. Keys are from square, values are lists of to squares.
        """
        move_lookup = dict( )
        king_square = self.find_king(color=self.to_move).square
        for piece in self.piece_generator(color=self.to_move):
            if isinstance(piece, Pawn):
                piece_targets = self.valid_targets_pawn(piece)
            elif isinstance(piece, King):
                piece_targets = self.valid_targets_king(piece)
            else:
                piece_targets = self.valid_targets_piece(piece)

            cleaned = list(self.remove_checks(piece.square, piece_targets, king_square, piece.color))
            if len(cleaned) > 0:
                move_lookup[piece.square] = cleaned
        return move_lookup

    def remove_checks(self, from_square, target_list, king_square, color):
        """
        Step through a target list for a piece. Yield any squares that do not
        leave the piece color's king in check.
        """
        for to_square in target_list:
            # Try the move on the test_board
            move = Move.from_squares(from_square, to_square, self, validate=False)
            self.push_move(move)
            # Keep the move if it does not cause check
            if from_square == king_square and not self.has_attackers(to_square, color.opponent):
                yield to_square
            elif not self.has_attackers(king_square, color.opponent):
                yield to_square
            # Reset for next test
            self.undo_move()

    @property
    def check(self):
        """
        Update the current check state.
        """
        if self._last_check_recompute != len(self.move_history):
            king = self.find_king(color=self.to_move)
            self._check = self.has_attackers(king.square, king.color.opponent)
            self._last_check_recompute = len(self.move_history)
        return self._check

    @property
    def allowed_moves(self):
        """
        Update the stored dictionary of allowed moves.
        """
        if self._last_move_recompute != len(self.move_history):
            self._allowed_moves = self.valid_moves_all()
            self._last_move_recompute = len(self.move_history)
        return self._allowed_moves

    def push_move(self, move):
        """
        Takes a move object. Applies the move to the current board.
        """
        # Apply removals
        for piece in move.removals:
            del self[piece.square]
        # Apply additions
        for piece in move.additions:
            self[piece.square] = piece
        # Update and store game state
        self.move_history.append(move)
        for side, state in move.castle_updates:
            self.castle_states[self.to_move][side] = state
        self.en_passant_square = move.en_passant_square
        self.to_move = self.to_move.opponent
        # TODO: update halfmoves and fullmoves
        return

    def undo_move(self):
        """
        Restore game state from one turn prior. Deletes the most recent move
        from move_history.
        """
        if len(self.move_history) == 0:
            raise InvalidMoveError("There are no moves to undo!")

        last_move = self.move_history.pop()
        # Revert additions
        for piece in last_move.additions:
            del self[piece.square]
        # Revert removals
        for piece in last_move.removals:
            self[piece.square] = piece

        self.to_move = self.to_move.opponent
        # Revert castle bans
        for side, state in last_move.castle_updates:
            self.castle_states[self.to_move][side] = not state
        # Get previous en passant
        if len(self.move_history) > 0:
            self.en_passant_square = self.move_history[-1].en_passant_square
        else:
            self.en_passant_square = None

        # TODO: update halfmoves and fullmoves
        return

    def process_move(self, move_str, validate=True):
        """
        Takes a move string as input. Trys to make the move, raises an error
        if the move fails.
        """
        t0 = time.time()
        # Parse and push the move
        self.push_move(Move.from_pgn(move_str, self, validate=validate))
        print("Move succeeded!")
        print(f"Now {sum(len(v) for v in self.allowed_moves.values())} valid moves")
        t1 = time.time()
        print(f"Move processed in {t1 - t0:.6f} sec")
        return

    def find_king(self, color=None):
        """
        Get the king for the current player. Raise error if player has no kings
        or more than one king.
        """
        if color is None:
            color = self.to_move
        # Get list of kings for current player
        king_list = list( self.find_pieces(King, color) )
        if len(king_list) == 0:
            raise InvalidBoardError(f"{color.name} has no king!")
        elif len(king_list) > 1:
            raise InvalidBoardError(f"{color.name} has more than one king!")
        return king_list[0]

    def checkmate(self):
        """
        Return True if current player is in checkmate.
        Return False otherwise.
        """
        if self.check and len(self.allowed_moves) == 0:
            return True
        return False

    def stalemate(self):
        """
        Return True if current player has no valid moves.
        Return False otherwise.
        """
        if len(self.allowed_moves) == 0:
            return True
        return False

    def game_over(self):
        """
        Return True if game is over...also set winner.
        Return False otherwise.
        """
        if self.checkmate():
            self.winner = self.to_move.opponent
            return True
        elif self.stalemate():
            self.winner = Color.DRAW
            return True
        else:
            return False

    def evaluate(self):
        """
        Returns the current material point spread.
        """
        score = 0
        for piece in self.piece_generator():
            # Add material for WHITE
            if piece.color is Color.WHITE:
                score += piece.value
            # Subtract material for BLACK
            else:
                score -= piece.value
        return score

    def play_turn(self):
        """
        Process the events of a turn.
        """
        actionable = False
        while not actionable:
            move_input = input(">>> ").strip()
            # DRAW: handle draw offer
            if move_input.upper() == "D":
                print("\n* * * Draw offered ( A - Accept ) * * * ")
                draw = input(">>> ").strip()
                if draw.strip().upper() == "A":
                    self.winner = Color.DRAW
                    actionable = True
            # LIST: print list of previous moves
            elif move_input.upper() == "L":
                print(self.pgn_str())
            # MOVES: print valid moves
            elif move_input[-1] == "?":
                # all valid moves
                if move_input == "?":
                    print(f"{sum((len(m) for m in self.allowed_moves.values()))} valid moves:\n")
                    for sq in self.allowed_moves.keys():
                        self.print_square_moves(sq)
                # valid moves for a piece
                elif move_input[1] == "?":
                    ptype = type(Piece.from_str(move_input[0]))
                    for piece in self.find_pieces(ptype, self.to_move):
                        self.print_square_moves(piece.square)
                # valid moves for a square
                else:
                    self.print_square_moves(Square.from_str(move_input[:-1]))
            else:
                actionable = True

        if move_input.upper() == "R":
            # Set winner to opponent
            self.winner = self.to_move.opponent
        elif move_input.upper() == "U":
            self.undo_move()
        else:
            self.process_move(move_input)
        return True

    def play_game(self):
        """
        Facilitate a game via commandline.
        """
        while self.winner is None:
            self.print_turn_header()

            # Game end conditions
            if self.game_over():
                break

            # Keep trying to move until a move succeeds
            while True:
                try:
                    self.play_turn()
                    break
                except (InvalidMoveError, IndexError) as e:
                    print(e)

        print("\n\n    * * * * * * * * * *")
        if self.winner is Color.DRAW:
            print("    *    GAME DRAWN   *")
        else:
            print(f"    *   {self.winner.name} WINS!   *")
        print("    * * * * * * * * * *\n")
        return

    def load_pgn(self, pgn_str):
        """
        Parses a PGN formatted string representation of a chess game into the
        current board.
        """
        if not isinstance(pgn_str, str):
            raise TypeError("Input must be a PGN string!")
        pgn_str = pgn_str.replace(",", " ")
        moves = pgn_str.split()
        for move in moves:
            self.process_move(move)
        return

    def load_fen(self, fen_str):
        """
        Parses a FEN formatted string representation of a chess board into
        current board.
        """
        if not isinstance(fen_str, str):
            raise TypeError("Input must be a FEN string or a name from the FEN library!")

        # If input is a name from the FEN library, get the FEN string
        fen_str = fen_str.strip()
        if fen_str in self.fen_library:
            fen_str = self.fen_library[fen_str]

        # Check FEN string
        fields = fen_str.split()
        if len(fields) != 6:
            raise ValueError("FEN str does not contain 6 space separated fields!")

        # Clear board
        self.reset()

        # Build board
        for r, row in enumerate(fields[0].split("/")):
            skips = 0
            for c, char in enumerate(row):
                # DIGITS -- skip that many spaces
                if char.isdigit():
                    skips += int(char) - 1
                # LETTER -- make a piece with it
                else:
                    col = c + skips
                    self[(r, col)] = Piece.from_str(char, row=r, col=col)

        # Determine whose move
        to_move = fields[1].lower()
        if to_move == "w":
            self.to_move = Color.WHITE
        elif to_move == "b":
            self.to_move = Color.BLACK
        else:
            raise ValueError("Unrecognized color symbol!")

        # TODO: parse castling state

        # TODO: parse en passant target square

        # Parse halfmoves
        try:
            self.halfmoves = int(fields[4])
        except ValueError:
            raise ValueError("Halfmove count is not an integer!")
        if self.halfmoves < 0:
            raise ValueError("Halfmove count must be non-negative!")
        # Parse fullmoves
        try:
            self.fullmoves = int(fields[5])
        except ValueError:
            raise ValueError("Fullmove count is not an integer!")
        if self.fullmoves < 1:
            raise ValueError("Fullmove count must be greater than 0!")
        return self

    @property
    def fen(self):
        """
        Constructs a FEN formatted string representation of the current board.
        """
        # Get board str
        row_strs = [ ]
        for row in self.board:
            row_str = ""
            skips = 0
            for piece in row:
                if piece is None:
                    skips += 1
                elif skips != 0:
                    row_str += str(skips)
                    skips = 0

                if skips == 0:
                    row_str += str(piece)
            else:
                # Handle empty rows
                if skips != 0:
                    row_str += str(skips)
            row_strs.append(row_str)
        board_str = "/".join(row_strs)

        # Get to move
        move_str = self.to_move.name[0].lower()

        # TODO: parse castling state
        castle_str = "KQkq"

        # TODO: parse en passant target square
        en_passant_str = "-"

        # Parse halfmoves
        half_move_str = str(self.halfmoves)

        # Parse fullmoves
        full_move_str = str(self.fullmoves)

        return " ".join([ board_str,
                          move_str,
                          castle_str,
                          en_passant_str,
                          half_move_str,
                          full_move_str, ])

    def print_turn_header(self):
        """
        Print a text representation of the current game state along with
        move hints.
        """
        space = "        "
        print("_________________________________________________________\n\n")
        print(self.filled_board_str(orient=self.to_move, notate=True, notate_prefix=space))
        print("\n" + space + f"     {self.to_move.name} to play!  (Spread: {self.evaluate():+d})")
        # Announce check
        if self.check:
            print("\n" + space + "  * * * King is in check! * * *")
        print("_________________________________________________________")
        print("Enter move: ( [R]esign | [D]raw | [U]ndo | [L]og | [?] )")
        return

    @property
    def board_fmt_str(self):
        """
        Creates multiline string for the board with empty format slots in all
        squares.
        """
        if self._board_fmt_str is None:
            edge_line =  "+" + "---+" * N_FILES + "\n"
            piece_line = "|" + "{}|" * N_FILES + "\n"
            self._board_fmt_str = edge_line
            for _ in Square.ROW_RANGE:
                self._board_fmt_str += piece_line + edge_line
        return self._board_fmt_str

    def filled_board_str(self, orient=Color.WHITE, notate=False, notate_prefix="", highlights=[]):
        """
        Populates the empty board format string with the pieces from the
        current board state. If reverse is True, shows perspective from top
        of board. If notate is True, square coordinates are added on the
        bottom edge and left edge. The notate_prefix string is added at the
        front of every line when notation is applied. Highlights is a list of
        squares to be wrapped with parentheses.
        """
        if orient is Color.BLACK:
            reverse = True
        else:
            reverse = False

        wrapped = ( (self[s], "({})") if s in highlights else (self[s], " {} ")
                        for s in self.square_list(reverse=reverse) )
        str_gen = ( wrap.format(" ") if p is None else wrap.format(p)
                        for p, wrap in wrapped )
        filled = self.board_fmt_str.format(*str_gen)

        if notate:
            if reverse:
                row_range = range(N_RANKS - 1, -1, -1)
                col_range = range(N_FILES - 1, -1, -1)
            else:
                row_range = range(0, N_RANKS)
                col_range = range(0, N_FILES)
            # Add rank numbers
            rank_fmt = " {} "
            rank_gen = ( Square.row_to_rank(r) for r in row_range )
            filled_rows = filled.strip().split("\n")
            filled = ""
            for i, row in enumerate(filled_rows):
                filled += notate_prefix
                if i % 2 == 1:
                    filled += rank_fmt.format(next(rank_gen))
                else:
                    filled += rank_fmt.format(" ")
                filled += row + "\n"
            # Add file letters
            file_gen = ( Square.col_to_file(c) for c in col_range )
            files = " " + " ".join(" {} ".format(l) for l in file_gen)
            filled += notate_prefix + rank_fmt.format(" ") + files
        return filled

    def print_square_moves(self, from_square):
        """
        Print all valid moves from the specified square.
        """
        piece = self[from_square]
        if piece is None:
            print(f"{from_square} is empty!")
        elif piece.square in self.allowed_moves:
            print(f"{piece!r}: {self.allowed_moves[from_square]}")
            print(self.moves_board_str(from_square) + "\n")
        else:
            print(f"No valid moves for {piece!r}!")
        return

    def moves_board_str(self, from_square, notate_prefix=""):
        """
        Return a mulitline string of the board showing the available moves
        for from_square.
        """
        # Get list of valid target squares
        targets = [ from_square ]
        if from_square in self.allowed_moves:
            targets.extend( self.allowed_moves[from_square] )
        # Get the board string
        return self.filled_board_str( orient=self.to_move,
                                      notate=True,
                                      highlights=targets,
                                      notate_prefix=notate_prefix )

    def pgn_str(self):
        """
        Return a string of all stored moves for the game in PGN format.
        """
        return " ".join([ m.pgn_str() for m in self.move_history ])

    def __str__(self):
        """
        Return a mulitline string of the current board.
        """
        return self.filled_board_str(orient=self.to_move, notate=True)

    def __repr__(self):
        return f"Board('{self.fen}')"

class InvalidMoveError(Exception):
    pass

class InvalidBoardError(Exception):
    pass

###############################################################################
#  MOVES                                                                      #
###############################################################################
class Move:
    """
    Class for interpreting a move input. Encodes the move in a set of piece
    additions and removals.
    """
    def __init__(self, additions, removals, castle_updates=[], en_passant_square=None):
        # Board changes
        self.additions = additions # list of added pieces
        self.removals = removals # list of removed pieces
        self.castle_updates = castle_updates # list of K, Q
        self.en_passant_square = en_passant_square # en passant square
        return

    def inverse(self):
        """
        Return inverse of move.
        """
        castle_updates = [ (side, not state) for side, state in self.castle_updates ]
        return Move(self.removals, self.additions, castle_updates=castle_updates)

    @classmethod
    def from_squares(cls, from_square, to_square, board, promote_type=None, validate=True):
        """
        Takes a from_square, to_square and board object. Determines what
        actions are occuring as a result of the displacement. If promote_type
        is specified, the piece at from_square is dropped and a piece of
        the promote_type is added at the to_square.
        """
        # Check that move is valid
        if validate:
            if not from_square in board.allowed_moves.keys():
                raise InvalidMoveError(f"{from_square} cannot move!")
            if not to_square in board.allowed_moves[from_square]:
                raise InvalidMoveError(f"{board[from_square]!r} cannot move to {to_square}!")

        additions = [ ]
        removals = [ ]
        castle_updates = [ ]
        en_passant_square = None

        # Get pieces
        piece = board[from_square]
        target = board[to_square]

        # If promotion, remove piece and add new one
        if promote_type is not None:
            additions.append( promote_type(to_square, piece.color, has_moved=True) )
            removals.append(piece)
        # Otherwise just move the piece
        else:
            additions.append( type(piece)(to_square, piece.color, has_moved=True) )
            removals.append(piece)
        # Determine if capture
        if target is not None:
            removals.append(target)

        # Determine if en passant capture
        if to_square == board.en_passant_square:
            d_row = piece.color.orientation
            removals.append(board[to_square.row - d_row, to_square.col])

        # Determine if opens en passant square
        if isinstance(piece, Pawn):
            d_row = to_square.row - from_square.row
            if abs(d_row) == 2:
                en_passant_square = Square(from_square.row + d_row/2, from_square.col)

        # Determine if castle
        if isinstance(piece, King):
            d_col = to_square.col - from_square.col
            # King side castle
            if d_col == 2:
                rook = board[ board.rook_homes[piece.color][1] ]
                rook_to = Square( to_square.row, to_square.col - 1 )
                additions.append( Rook(rook_to, rook.color, has_moved=True) )
                removals.append( rook )
            # Queen side castle
            elif d_col == -2:
                rook = board[ board.rook_homes[piece.color][0] ]
                rook_to = Square( to_square.row, to_square.col + 1 )
                additions.append( Rook(rook_to, rook.color, has_moved=True) )
                removals.append( rook )
            # Any king move prevents future castles
            if board.castle_states[piece.color]["Q"]:
                castle_updates.append(("Q", False))
            if board.castle_states[piece.color]["K"]:
                castle_updates.append(("K", False))
        # Rook moves prevent future castles with that rook
        elif isinstance(piece, Rook):
            if from_square == board.rook_homes[piece.color][0]:
                if board.castle_states[piece.color]["Q"]:
                    castle_updates.append(("Q", False))
            elif from_square == board.rook_homes[piece.color][1]:
                if board.castle_states[piece.color]["K"]:
                    castle_updates.append(("K", False))

        return cls( additions,
                    removals,
                    castle_updates=castle_updates,
                    en_passant_square=en_passant_square )

    def pgn_str(self):
        """
        Returns PGN string representation of the move.
        """
        piece_0 = self.removals[0]
        piece_1 = self.additions[0]
        end = str(piece_1.square).lower()
        if type(piece_0) == Pawn:
            start = ""
            if len(self.removals) > 1:
                start += piece_0.file.lower()
            if type(piece_1) != Pawn:
                end += str(piece_1).upper()
        else:
            start = str(piece_0).upper()
            start += str(piece_0.square).lower()

        if len(self.removals) > 1:
            start += "x"
        return start + end

    @staticmethod
    def parse_pgn(pgn_str, board):
        """
        Parses a PGN formatted move string into a move.
        Examples: Kg3, axd4, Ndxe2, Rad1
        """
        pgn_str = pgn_str.rstrip("+")
        promote_type = None
        # Handle CASTLES
        if pgn_str.upper() in ( "O-O", "O-O-O" ):
            from_square = board.find_king().square
            if len(pgn_str) == 3:
                to_square = Square(from_square.row, from_square.col + 2)
            else:
                to_square = Square(from_square.row, from_square.col - 2)
            return from_square, to_square, promote_type

        # Handle PROMOTIONS
        if pgn_str[-1].isalpha():
            promote_type = type(Piece.from_str(pgn_str[-1]))
            pgn_str = pgn_str[:-1]
        else:
            promote_type = None

        # Handle piece type
        if pgn_str[0] == pgn_str[0].upper():
            ptype = type(Piece.from_str(pgn_str[0]))
            pgn_str = pgn_str[1:]
        else:
            ptype = Pawn

        # Get to square
        to_square = Square.from_str(pgn_str[-2:])
        pgn_str = pgn_str[:-2].rstrip("x")

        # Get list of possible pieces
        piece_list = [ p for p in board.find_pieces(ptype, board.to_move)
                          if p.square in board.allowed_moves
                              and to_square in board.allowed_moves[p.square] ]
        # Filter using PGN specs
        if len(piece_list) > 1:
            if len(pgn_str) == 1:
                file = pgn_str.upper()
                piece_list = [ p for p in piece_list if p.file == file ]
            else:
                sq = Square.from_str(pgn_str)
                piece_list = [ p for p in piece_list if p.square == sq ]

        # Ensure only one piece works
        if len(piece_list) == 0:
            raise InvalidMoveError(
                f"{board.to_move.name} has no {ptype.__name__}s that can move to {to_square}"
            )
        elif len(piece_list) > 1:
            raise InvalidMoveError(f"{len(piece_list)} pieces can move to {to_square}")

        piece = piece_list[0]
        return piece.square, to_square, promote_type

    @classmethod
    def from_pgn(cls, pgn_str, board, validate=True):
        from_square, to_square, promote_type = cls.parse_pgn(pgn_str, board)
        return cls.from_squares( from_square,
                                 to_square,
                                 board,
                                 promote_type=promote_type,
                                 validate=validate )

    @classmethod
    def from_square_str(cls, square_str, board):
        """
        Parses a string representation of a from square and to square.
        Example: c2c4
        """
        promote_type = None
        if len(square_str) == 5:
            promote_type = type(Piece.from_str(square_str[-1]))
        elif len(square_str) != 4:
            raise InvalidMoveError("Move string must be 4 characters (5 for pawn promotions)!")

        from_square = Square.from_str(square_str[:2])
        to_square = Square.from_str(square_str[2:4])

        return cls.from_squares(from_square, to_square, board, promote_type)

###############################################################################
#  PIECES                                                                     #
###############################################################################
class Piece:
    """
    Base class for all chess pieces.
    """
    # Class constants
    jumps = False # True for Knight-like pieces
    value = None # Material point value

    _CHAR_LOOKUP = {}

    def __init__(self, locus, color=Color.WHITE, has_moved=False):
        # Core attributes
        self.color = color
        self.has_moved = has_moved
        # Handle init from Square
        if isinstance(locus, Square):
            self.square = locus
        # Handle init from coordinate tuple
        elif isinstance(locus, tuple):
            self.square = Square.from_tup(locus)
        # Handle init from coordinate string
        elif isinstance(locus, str):
            self.square = Square.from_str(locus)
        # Handle init from Pawn promotion
        elif isinstance(locus, Pawn):
            self.color = locus.color
            self.square = locus.square

    def __init_subclass__(cls, **kwargs):
        """
        Register the class character in the _CHAR_LOOKUP.
        """
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_char"):
            cls._char = cls.__name__[0]
        if not isinstance(cls._char, str) or len(cls._char) != 1:
            raise AttributeError("_char must be a single digit string")
        # Make sure char is not already taken
        cls._char = cls._char.upper()
        if cls._char in Piece._CHAR_LOOKUP:
            raise AttributeError(f"_char for {cls.__name__} is already taken by {Piece._CHAR_LOOKUP[cls._char].__name__}")
        # Add to the lookup
        Piece._CHAR_LOOKUP[cls._char] = cls

    @classmethod
    def from_str(cls, piece_char, row=0, col=0):
        """
        Takes a string with 1 letter identifying a piece. Returns that piece.
        """
        # Determine color
        if piece_char.isupper():
            color = Color.WHITE
        else:
            color = Color.BLACK
        # Determine piece type
        try:
            return cls._CHAR_LOOKUP[piece_char.upper()]((row, col), color=color)
        except KeyError:
            raise ValueError(f"Unrecognized piece string: {piece_char!r}")

    @property
    def row(self):
        return self.square.row

    @property
    def col(self):
        return self.square.col

    @property
    def rank(self):
        return self.square.rank

    @property
    def file(self):
        return self.square.file

    def generate_row(self):
        for col in range(0, self.col):
            yield self.row, col
        for col in range(self.col + 1, N_FILES):
            yield self.row, col

    def generate_col(self):
        for row in range(0, self.row):
            yield row, self.col
        for row in range(self.row + 1, N_RANKS):
            yield row, self.col

    def generate_diag(self):
        for row in range(0, self.row):
            d_row = row - self.row
            yield row, self.col + d_row
            yield row, self.col - d_row
        for row in range(self.row + 1, N_RANKS):
            d_row = row - self.row
            yield row, self.col + d_row
            yield row, self.col - d_row

    def move_is_valid(self, d_row, d_col, capture=False):
        raise NotImplementedError()

    def letter(self):
        """
        Single character representation of piece.
        Uppercase for WHITE, lowercase for BLACK.
        """
        if self.color is Color.BLACK:
            return self._char.lower()
        else:
            return self._char

    def u_str(self):
        """
        Unicode representation of piece
        """
        return UNICODE_PIECE_SYMBOLS[self.letter()]

    @property
    def name(self):
        """
        Return full piece name.
        """
        return self.__class__.__name__

    def __str__(self):
        if UNICODE_PIECES:
            return self.u_str()
        else:
            return self.letter()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.square}, {self.color.name})"


class Pawn(Piece):
    value = 1

    def pseudovalid_coords_regular(self):
        """
        Generate all squares that the piece could potentially move to (non-captures)
        """
        row = self.row + self.color.orientation
        if 0 <= row < N_RANKS:
            yield row, self.col
        if not self.has_moved:
            row += self.color.orientation
            if 0 <= row < N_RANKS:
                yield row, self.col

    def pseudovalid_coords_capture(self):
        """
        Generate all squares that the piece could potentially move to (captures only)
        """
        if self.col < N_FILES - 1:
            yield self.row + self.color.orientation, self.col + 1
        if self.col > 0:
            yield self.row + self.color.orientation, self.col - 1

    def move_is_valid(self, d_row, d_col, capture=False, **kwargs):
        """
        Can move forward 2 if it has not yet moved. Otherwise can only move 1.
        If the move is a capture, it can move diagonally
        """
        # If move is a capture, only allow forward diagonal moves by 1 space
        if capture:
            if abs(d_col) == ( self.color.orientation * d_row ) == 1:
                return True
            else:
                return False
        else:
            # Only allow forward moves by 1 (if has not moved, then allow 2)
            if d_col == 0 and ( self.color.orientation * d_row == 1 or (not self.has_moved and self.color.orientation * d_row == 2) ):
                return True
            else:
                return False


class Bishop(Piece):
    value = 3

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        """
        return self.generate_diag()

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Rank and file must change by same amount
        """
        if abs(d_col) == abs(d_row) != 0:
            return True
        else:
            return False


class Knight(Piece):
    _char = "N"
    value = 3
    jumps = True

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        """
        for d_row, d_col in itertools.permutations([2, 1]):
            for s_row, s_col in itertools.product([1, -1], repeat=2):
                row = self.row + d_row*s_row
                if not 0 <= row < N_RANKS:
                    continue
                col = self.col + d_col*s_col
                if not 0 <= col < N_FILES:
                    continue
                yield row, col

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Rank or file must change by 2, the other must change by 1
        """
        if set(( abs(d_col), abs(d_row) )) == set(( 1, 2 )):
            return True
        else:
            return False


class Rook(Piece):
    value = 5

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        """
        for coord in self.generate_col():
            yield coord
        for coord in self.generate_row():
            yield coord

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Rank or file can change any amount, but one must not change
        """
        if ( d_col == 0 and d_row != 0 ) or ( d_row == 0 and d_col != 0 ):
            return True
        else:
            return False


class Queen(Piece):
    value = 9

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        """
        chained = itertools.chain( self.generate_col(),
                                   self.generate_row(),
                                   self.generate_diag() )
        for coord in chained:
            yield coord

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Can make any move that is valid for Rook or Bishop
        """
        if Bishop.move_is_valid(d_col, d_row) or Rook.move_is_valid(d_col, d_row):
            return True
        else:
            return False


class King(Piece):
    value = 5

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        (Excludes castles)
        """
        for d_row, d_col in itertools.product([1, 0, -1], [1, 0, -1]):
            yield self.row + d_row, self.col + d_col

    @staticmethod
    def move_is_valid(d_row, d_col, castle=False, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if castle:
            if abs(d_row) == 0 and abs(d_col) == 2:
                return True
            else:
                return False

        else:
            if set(( abs(d_col), abs(d_row) )).issubset( set(( 0, 1 )) ):
                return True
            else:
                return False

class Centaur(Piece):
    value = 5
    jumps = True

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        (Excludes castles)
        """
        # KING
        for d_row, d_col in itertools.product([1, 0, -1], [1, 0, -1]):
            yield self.row + d_row, self.col + d_col
        # KNIGHT
        for d_row, d_col in itertools.permutations([2, 1]):
            for s_row, s_col in itertools.product([1, -1], repeat=2):
                row = self.row + d_row*s_row
                if not 0 <= row < N_RANKS:
                    continue
                col = self.col + d_col*s_col
                if not 0 <= col < N_FILES:
                    continue
                yield row, col

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if set(( abs(d_col), abs(d_row) )).issubset( set(( 0, 1 )) ) or \
           set(( abs(d_col), abs(d_row) )) == set(( 1, 2 )):
            return True
        else:
            return False

class Zebra(Piece):
    value = 3
    jumps = True

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        (Excludes castles)
        """
        for d_row, d_col in itertools.permutations([2, 3]):
            for s_row, s_col in itertools.product([1, -1], repeat=2):
                row = self.row + d_row*s_row
                if not 0 <= row < N_RANKS:
                    continue
                col = self.col + d_col*s_col
                if not 0 <= col < N_FILES:
                    continue
                yield row, col

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if set(( abs(d_col), abs(d_row) )) == set(( 2, 3 )):
            return True
        else:
            return False

class Giraffe(Piece):
    value = 2
    jumps = True

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to.
        (Excludes castles)
        """
        for d_row, d_col in itertools.permutations([4, 1]):
            for s_row, s_col in itertools.product([1, -1], repeat=2):
                row = self.row + d_row*s_row
                if not 0 <= row < N_RANKS:
                    continue
                col = self.col + d_col*s_col
                if not 0 <= col < N_FILES:
                    continue
                yield row, col

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if set(( abs(d_col), abs(d_row) )) == set(( 4, 1 )):
            return True
        else:
            return False

class Elephant(Piece):
    value = 2

    def pseudovalid_coords(self):
        """
        Generate all squares that the piece could potentially move to (non-captures)
        """
        yield self.row + self.color.orientation, self.col
        yield self.row + 1, self.col + 1
        yield self.row + 1, self.col - 1
        yield self.row - 1, self.col + 1
        yield self.row - 1, self.col - 1

    def move_is_valid(self, d_row, d_col, capture=False, **kwargs):
        """
        Can move forward 2 if it has not yet moved. Otherwise can only move 1.
        If the move is a capture, it can move diagonally
        """
        # Allow forward moves by 1
        if d_col == 0 and ( self.color.orientation * d_row == 1  ):
            return True
        # Diagonal moves
        elif abs(d_col) == abs(d_row) == 1:
            return True
        else:
            return False

###############################################################################
#  MAIN                                                                       #
###############################################################################
def test():
    game = """
    e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3 Nb8 d4 Nbd7 c4
    c6 cxb5 axb5 Nc3 Bb7 Bg5 b4 Nb1 h6 Bh4 c5 dxe5 Nxe4 Bxe7 Qxe7 exd6 Qf6 Nbd2
    Nxd6 Nc4 Nxc4 Bxc4 Nb6 Ne5 Rae8 Bxf7+ Rxf7 Nxf7 Rxe1+ Qxe1 Kxf7 Qe3 Qg5
    Qxg5 hxg5 b3 Ke6 a3 Kd6 axb4 cxb4 Ra5 Nd5 f3 Bc8 Kf2 Bf5 Ra7 g6 Ra6+ Kc5
    Ke1 Nf4 g3 Nxh3 Kd2 Kb5 Rd6 Kc5 Ra6 Nf2 g4 Bd3 Re6
    """
    board = Board("Standard")
    t0 = time.time()
    board.load_pgn(game)
    t1 = time.time()

    move_count = len(board.move_history)
    print(f"\nEvaluated {move_count:d} moves in {t1 - t0:f} sec")
    print(f"({(t1 - t0) / move_count:f} sec/position)")
    print(f"({move_count / (t1 - t0):f} position/sec)")

def main():
    board = Board("Standard")
    board.play_game()
