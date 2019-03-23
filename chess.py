# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
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

# COLORS / RESULTS
WHITE = 0
BLACK = 1
DRAW = -1

# COLOR INFO
FLIP_COLOR = { WHITE: BLACK, BLACK: WHITE }
COLOR_ORIENTATION = { WHITE: -1, BLACK: 1 }
COLOR_NAME = { WHITE: "White", BLACK: "Black", DRAW: "Draw" }

###############################################################################
#  BOARD CORE                                                                 #
###############################################################################
class Square:
    """
    Board square representation. Allows flexible conversion between
    string and tuple representations
    """
    def __init__(self, row, col, rank=None, file=None):
        """
        Takes row and col coordinates as input.
        """
        # Check if in bounds
        if not row in range(0, N_RANKS):
            raise IndexError("Rank out of bounds!")
        if not col in range(0, N_FILES):
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
            raise ValueError("File must be a digit string!")
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
        return "{}{}".format(self.file, self.rank)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return N_RANKS * self.row + self.col

    def __eq__(self, other):
        if isinstance(other, Square):
            return self.__hash__() == other.__hash__()
        elif isinstance(other, tuple):
            return self.row == tuple[0] and self.row == tuple[1]

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
            }

    def __init__(self, fen="Standard", board=None):
        self._board_fmt_str = None
        self._square_list = None
        if fen is None:
            self.reset(board=board)
        else:
            self.load_fen(fen)

    def reset(self, board=None, to_move=WHITE):
        """
        Initializes an empty board, clears game history, sets winner to None
        and to_move to WHITE. If board is specified, use that as the board.
        """
        # Construct board
        if board is None:
            self.board = [ [ None for _ in range(N_FILES) ]
                                  for _ in range(N_RANKS)
                                  ]
        else:
            self.board = board
        # Game trackers
        self.move_history = [ ]
        self.castle_states = { "Q": True,
                               "K": True,
                               "q": True,
                               "k": True, }
        self.qr_home = { WHITE: Square(N_RANKS - 1, 0),
                         BLACK: Square(0, 0), }
        self.kr_home = { WHITE: Square(N_RANKS - 1, N_FILES - 1),
                         BLACK: Square(0, N_FILES - 1), }
        self.en_passant_square = None
        
        self.to_move = to_move
        self.winner = None
        self.halfmoves = 0
        self.fullmoves = 1

        self._allowed_moves = dict( )
        self._last_recompute = None
        return

    def __setitem__(self, locus, piece):
        """
        Inserts a piece at the specified square position.
        board['A1'] = Rook(WHITE, 'A1')
        """
        if not ( piece is None or isinstance(piece, Piece) ):
            raise TypeError("Board can only contain Piece and NoneType objects!")

        if isinstance(locus, tuple):
            self.board[locus[0]][locus[1]] = piece
        elif isinstance(locus, Square):
            self.board[locus.row][locus.col] = piece
        elif isinstance(locus, str):
            sq = Square.from_str(locus)
            self.board[sq.row][sq.col] = piece
        else:
            raise TypeError("Invalid square locus for board!")

    def __getitem__(self, locus):
        """
        Gets the piece on the specified square position (None for empty square).
        board['A1'] -> Rook(White, A1)
        """
        if isinstance(locus, tuple):
            piece = self.board[locus[0]][locus[1]]
        elif isinstance(locus, Square):
            piece = self.board[locus.row][locus.col]
        elif isinstance(locus, str):
            sq = Square.from_str(locus)
            piece = self.board[sq.row][sq.col]
        else:
            raise TypeError("Invalid square locus for board!")
        return piece

    def __delitem__(self, locus):
        """
        Removes any piece at the specified board position. Replaces the
        slot with None.
        """
        self[locus] = None
        return

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
                elif color is None or piece.color == color:
                    yield piece
    
    def square_slice(self, from_square, to_square):
        """
        Generator that yields the squares on the board between from_square and 
        to_square, inclusive. Only works for square/diagonal displacements.
        """
        d_row, d_col = to_square - from_square
        # VERTICAL
        if d_col == 0:
            dr = (1, -1)[to_square.row < from_square.row] # sign of row change
            for row in range(from_square.row, to_square.row + dr, dr):
                yield self.get_square(row, from_square.col)
        # HORIZONTAL
        elif d_row == 0:
            dc = (1, -1)[to_square.col < from_square.col] # sign of col change
            for col in range(from_square.col, to_square.col + dc, dc):
                yield self.get_square(from_square.row, col) 
        # DIAGONAL
        elif abs( d_row ) == abs( d_col ):
            dr = (1, -1)[d_row < 0] # sign of row change
            dc = (1, -1)[d_col < 0] # sign of col change
            r_to_c = dr * dc # 1 if same, -1 if opposite
            for r in range(0, d_row + dr, dr):
                row = from_square.row + r
                col = from_square.col + r * r_to_c
                yield self.get_square(row, col)
        else:
            raise IndexError("Slices must be square or diagonal!")

    def piece_slice(self, from_square, to_square):
        """
        Generator that yields pieces on the board from_square to_square,
        inclusive. Only works for square/diagonal displacements.
        """
        for square in self.square_slice(from_square, to_square):
            yield self.board[square.row][square.col]

    def find_pieces(self, piece_type, color):
        """
        Returns list of pieces of the specified type and color from the board.
        """
        found = [ ]
        for piece in self.piece_generator(color=color):
            if isinstance(piece, piece_type):
                found.append(piece)
        return found

    def obstruction(self, from_square, to_square):
        """
        Return True if there is a piece between the two squares.
        Return False if the path is clear.
        """
        pieces = list(self.piece_slice(from_square, to_square))[1:-1]
        if any(pieces):
            return True
        return False

    def get_attackers(self, square, color):
        """
        Check if any pieces of color are eyeing the square.
        Return list of pieces.
        """
        attackers = [ ]
        for piece in self.piece_generator(color=color):
            if self.valid_square_piece(piece, square, recaptures=True):
                attackers.append(piece)

        return attackers

    def get_pinners(self, square, color):
        """
        Check if any pieces of color are eyeing the square, but have one
        blocker.
        Return list of pieces.
        """
        pinners = [ ]
        for piece in self.piece_generator(color=color):
            threats = self.valid_targets_piece(piece, unpins_only=True)

            if square in threats:
                pinners.append(piece)
        return pinners

    def get_pinned(self, square, color):
        """
        Check if any pieces of color are pinned to the square. Returns
        list of pieces
        """
        pinned = [ ]
        for pinner in self.get_pinners(square, FLIP_COLOR[color]):
            path = list(self.piece_slice(pinner.square, square))[1:-1]
            piece = [p for p in path if p is not None][0]
            pinned.append(piece)
        return pinned

    def can_castle(self, king, rook):
        """
        Return True if the King and Rook can castle.
        Return False otherwise.
        """
        if king.has_moved or rook.has_moved:
            return False
        if king.row != rook.row:
            return False
        if self.obstruction(king.square, rook.square):
            return False

        # Make sure king doesn't cross through check (include current square)
        path = list(self.square_slice(king.square, rook.square))[:3]
        for square in path:
            if len(self.get_attackers(square, FLIP_COLOR[king.color])) > 0:
                return False
        return True

    def valid_castles(self, king=None):
        """
        Return a list of valid castling moves for the current player.
        """
        # Get king if king is not passed in
        if king is None:
            king = self.find_king()
        elif not isinstance(king, King):
            raise TypeError("valid_castles king must be a King or None!")
        # Build list of castle moves
        moves = [ ]
        for rook in self.find_pieces(Rook, king.color):
            if self.can_castle(king, rook):
                moves.append(list(self.square_slice(king.square, rook.square))[2])
        return moves

    def valid_targets_king(self, king):
        """
        Return a list of all valid target squares for a king. Gets list of
        normal king moves, removes moves that leave the king in check, and adds
        valid castling moves.
        """
        moves = [ ]
        # Normal moves
        for square in self.valid_targets_piece(king):
            # Keep moves that do not result in check
            if len(self.get_attackers(square, FLIP_COLOR[king.color])) == 0:
                moves.append(square)
        # Add castling moves
        moves.extend(self.valid_castles(king=king))
        return moves
    
    def valid_square_piece(self, piece, square, recaptures=False, unpins_only=False):
        """
        Return True if piece can move to square.
        Return False otherwise.
        If recaptures is True, includes squares that are occupied by a piece
        of the same color.
        """
        # Check for null move
        if square == piece.square:
            return False
        # Check for target validity
        target = self.board[square.row][square.col]
        if target is None:
            capture = False
        elif target.color != piece.color or recaptures:
            capture = True
        else:
            return False
        # Check if move is valid for piece
        d_row, d_col = square - piece.square
        if not piece.move_is_valid(d_row, d_col, capture=capture):
            return False
        # Only keep moves opened by an opponents move
        if unpins_only:
            if piece.jumps:
                return False
            path = list(self.piece_slice(piece.square, square))[1:-1]
            blockers = [ p for p in path if p is not None]
            # Piece must be blocked by exactly one piece of the opposite color
            if len(blockers) != 1 or blockers[0].color == piece.color:
                return False
        # Check for obstructions
        elif not piece.jumps:
            if self.obstruction(piece.square, square):
                return False
        return True

    def valid_targets_piece(self, piece, recaptures=False, unpins_only=False):
        """
        Return a list of all valid target squares for the specified piece.
        Does not consider whether a move leaves player in check,
        does not consider castling, does not consider en passant.
        """
        moves = [ ]
        for square in self.square_list():
            if self.valid_square_piece(piece, square, recaptures=recaptures, unpins_only=unpins_only):
                moves.append(square)
        return moves

    def valid_moves_all(self, remove_checks=True):
        """
        Return a dictionary of all valid moves in the current board
        configuration. Keys are from square, values are lists of to squares.
        """
        move_lookup = dict( )
        for piece in self.piece_generator(color=self.to_move):
            if isinstance(piece, King):
                piece_targets = self.valid_targets_king(piece)
            else:
                piece_targets = self.valid_targets_piece(piece)

            if len(piece_targets) > 0:
                move_lookup[piece.square] = piece_targets
        # Remove moves that leave king in check
        if remove_checks:
            move_lookup = self.remove_check_results(move_lookup)
        return move_lookup

    def remove_check_results(self, move_lookup):
        """
        Takes a move_lookup dict. Removes all moves that leave the king in
        check.
        """
        cleaned = dict( )
        color = self.to_move
        for from_square, targets in move_lookup.items():
            cleaned_targets = [ ]
            for to_square in targets:
                # Try the move on the test_board
                move = Move.from_squares(from_square, to_square, self)
                self.push_move(move)
                # Keep the move if it does not cause check
                if not self.check(color=color):
                    cleaned_targets.append(to_square)
                # Reset for next test
                self.undo_move()
            if len(cleaned_targets) > 0:
                cleaned[from_square] = cleaned_targets
        return cleaned

    @property
    def allowed_moves(self):
        """
        Update the stored dictionary of allowed moves. Call this every time the
        board position is changed!
        """
        # OPTIMIZE
        if self._last_recompute != len(self.move_history):
            self._allowed_moves = self.valid_moves_all()
            self._last_recompute = len(self.move_history)
        return self._allowed_moves

    def load_move(self, from_square, to_square, validate=True):
        """
        Takes from_square and to_square for move command. Attempts to process
        the move into a move dictionary. Returns the dictionary.
        """
        # Check that move is valid
        if validate:
            if not from_square in self.allowed_moves.keys():
                raise InvalidMoveError("{} cannot move!".format(from_square))
            if not to_square in self.allowed_moves[from_square]:
                raise InvalidMoveError("{!r} cannot move to {}!".format(self[from_square], to_square))

        return Move.from_squares(from_square, to_square, self)

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
        for key in move.castle_bans:
            self.castle_states[key] == False
        self.en_passant_square = move.en_passant_square
        self.to_move = FLIP_COLOR[self.to_move]
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
        # Revert castle bans
        for key in last_move.castle_bans:
            self.castle_states[key] == True
        # Get previous en passant
        if len(self.move_history) > 0:
            self.en_passant_square = self.move_history[-1].en_passant_square
        else:
            self.en_passant_square = None
        
        self.to_move = FLIP_COLOR[self.to_move]
        # TODO: update halfmoves and fullmoves
        return

    def process_move(self, move_str):
        """
        Takes a move string as input. Trys to make the move, raises an error
        if the move fails.
        """
        try:
            from_square = Square.from_str(move_str[:2])
            to_square = Square.from_str(move_str[2:].strip())
        except:
            raise InvalidMoveError("Could not parse move!")
        # Make move
        t0 = time.time()
        self.push_move(self.load_move(from_square, to_square))
        print("Move succeeded!")
        print("Now {} valid moves".format(sum(len(v) for v in self.allowed_moves.values())))
        t1 = time.time()
        print("Move processed in {:.6f} sec".format(t1-t0))
        return

    def find_king(self, color=None):
        """
        Get the king for the current player. Raise error if player has no kings
        or more than one king.
        """
        if color is None:
            color = self.to_move
        # Get list of kings for current player
        king_list = self.find_pieces(King, color)
        if len(king_list) == 0:
            raise InvalidBoardError("{} has no king!".format(COLOR_NAME[color]))
        elif len(king_list) > 1:
            raise InvalidBoardError("{} has more than one king!".format(COLOR_NAME[color]))
        return king_list[0]

    def check(self, color=None):
        """
        Return True if current player is in check.
        Return False otherwise.
        """
        if color is None:
            color = self.to_move
        king = self.find_king(color=color)
        if len(self.get_attackers(king.square, FLIP_COLOR[king.color])) > 0:
            return True
        return False

    def checkmate(self):
        """
        Return True if current player is in checkmate.
        Return False otherwise.
        """
        if self.check() and len(self.allowed_moves) == 0:
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

    def evaluate(self):
        """
        Returns the current material point spread.
        """
        score = 0
        for piece in self.piece_generator():
            # Add material for WHITE
            if piece.color == WHITE:
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
            move_input = input(">>> ").strip().upper()
            # DRAW: handle draw offer
            if move_input == "D":
                print("\n* * * Draw offered ( A - Accept ) * * * ")
                draw = input(">>> ").strip()
                if draw.strip().upper() == "A":
                    self.winner = DRAW
                    actionable = True
            # MOVES: print valid moves
            elif move_input[-1] == "?":
                # all valid moves
                if move_input == "?":
                    print("{} valid moves:\n".format(sum((len(m) for m in self.allowed_moves.values()))))
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

        if move_input == "R":
            # Set winner to opponent
            self.winner = FLIP_COLOR[self.to_move]
        elif move_input == "U":
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
            if self.checkmate():
                self.winner = FLIP_COLOR[self.to_move]
                break
            elif self.stalemate():
                self.winner = DRAW
                break

            # Keep trying to move until a move succeeds
            while True:
                try:
                    self.play_turn()
                    break
                except (InvalidMoveError, IndexError) as e:
                    print(e)

        print("\n\n    * * * * * * * * * *")
        if self.winner == DRAW:
            print("    *    GAME DRAWN   *")
        else:
            print("    *   {} WINS!   *".format(COLOR_NAME[self.winner]).upper())
        print("    * * * * * * * * * *\n")
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
            self.to_move = WHITE
        elif to_move == "b":
            self.to_move = BLACK
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
                else:
                    row_str += str(piece)
            else:
                # Handle empty rows
                if skips != 0:
                    row_str += str(skips)
            row_strs.append(row_str)
        board_str = "/".join(row_strs)

        # Get to move
        move_str = COLOR_NAME[self.to_move][0].lower()

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
        print("_________________________________________________________")
        print("\n")
        print(self.filled_board_str(orient=self.to_move, notate=True, notate_prefix=space))
        print()
        pstr = COLOR_NAME[self.to_move]
        e = self.evaluate()
        if e > 0:
            mstr = "+" + str(e)
        else:
            mstr = str(e)
        print(space + "     {} to play!  (Spread: {})".format(pstr, mstr))
        # Announce check
        if self.check():
            print("\n" + space + "  * * * King is in check! * * *")
        print("_________________________________________________________")
        print("Enter move: ( [R]esign | [D]raw | [U]ndo | [?] )")
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
            for r in range(0, N_RANKS):
                self._board_fmt_str += piece_line + edge_line
        return self._board_fmt_str

    def filled_board_str(self, orient=WHITE, notate=False, notate_prefix="", highlights=[]):
        """
        Populates the empty board format string with the pieces from the
        current board state. If reverse is True, shows perspective from top
        of board. If notate is True, square coordinates are added on the
        bottom edge and left edge. The notate_prefix string is added at the
        front of every line when notation is applied. Highlights is a list of
        squares to be wrapped with parentheses.
        """
        if orient == BLACK:
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
            print("{} is empty!".format(from_square))
        elif piece.square in self.allowed_moves:
            print("{!r}: {}".format(piece, self.allowed_moves[from_square]))
            print(self.moves_board_str(from_square) + "\n")
        else:
            print("No valid moves for {!r}!".format(piece))
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

    def __str__(self):
        """
        Return a mulitline string of the current board.
        """
        return self.filled_board_str(orient=self.to_move, notate=True)

    def __repr__(self):
        return "Board('{}')".format(self.fen)

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
    def __init__(self, additions, removals, castle_bans=[], en_passant_square=None):
        # Board changes
        self.additions = additions # list of added pieces
        self.removals = removals # list of removed pieces
        self.castle_bans = castle_bans # list of K, Q, k or q
        self.en_passant_square = en_passant_square # en passant square
        return
    
    @classmethod
    def from_squares(cls, from_square, to_square, board, promote_type=None):
        """
        Takes a from_square, to_square and board object. Determines what
        actions are occuring as a result of the displacement. If promote_type
        is specified, the piece at from_square is dropped and a piece of
        the promote_type is added at the to_square.
        
        NOTE: Does not check for validity!
        """
        additions = [ ]
        removals = [ ]
        castle_bans = [ ]
        en_passant_square = None
        
        # Get pieces
        piece = board.board[from_square.row][from_square.col]
        target = board.board[to_square.row][to_square.col]

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
            d_row = COLOR_ORIENTATION[piece.color]
            removals.append(board.board[to_square.row - d_row][to_square.col])
            
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
                rook = board[ board.kr_home[piece.color] ]
                rook_to = Square( to_square.row, to_square.col - 1 )
                additions.append( Rook(rook_to, rook.color, has_moved=True) )
                removals.append( rook )
            # Queen side castle
            elif d_col == -2:
                rook = board[ board.qr_home[piece.color] ]
                rook_to = Square( to_square.row, to_square.col + 1 )
                additions.append( Rook(rook_to, rook.color, has_moved=True) )
                removals.append( rook )
            # Any king move prevents future castles
            if piece.color == WHITE:
                castle_bans.extend(["K", "Q"])
            else:
                castle_bans.extend(["k", "q"])
        # Rook moves prevent future castles with that rook
        elif isinstance(piece, Rook):
            if from_square == board.qr_home[piece.color]:
                if piece.color == WHITE:
                    castle_bans.append("Q")
                else:
                    castle_bans.append("K")
            elif from_square == board.kr_home[piece.color]:
                if piece.color == WHITE:
                    castle_bans.append("q")
                else:
                    castle_bans.append("k")
        # Only keep castle bans that are currently allowed
        castle_bans = [ b for b in castle_bans if board.castle_states[b] ]
        
        return cls( additions, 
                    removals, 
                    castle_bans=castle_bans, 
                    en_passant_square=en_passant_square )

    @classmethod
    def from_PGN(cls, pgn_str, board):
        """
        Parses a PGN formatted move string into a move.
        Example: kg3
        """ 
        to_str = pgn_str[1:]
        to_square = Square.from_str(to_str)
        
        ptype = type(Piece.from_str(pgn_str[0]))
        piece_list = board.find_pieces(ptype, board.to_move)
        piece_list = [ p for p in piece_list if p.square in board.allowed_moves and to_square in board.allowed_moves[p.square] ]
        if len(piece_list) == 0:
            raise InvalidMoveError("{} has no {}'s that can move to {}".format(COLOR_NAME[board.to_move], ptype.__class__.__name__, to_str))
        elif len(piece_list) > 1:
            raise InvalidMoveError("{} pieces can move to {}")
        pass
    
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
    jumps = False # True for Knights
    value = None # Material point value
    
    def __init__(self, locus, color=WHITE, has_moved=False):
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

    @staticmethod
    def from_str(piece_char, row=0, col=0):
        """
        Takes a string with 1 letter identifying a piece.
        Returns that piece.
        """
        # Determine color
        piece_upper = piece_char.upper()
        if piece_upper == piece_char:
            color = WHITE
        else:
            color = BLACK
        # Determine piece type
        if piece_upper == "P":
            return Pawn((row, col), color=color)
        elif piece_upper == "N":
            return Knight((row, col), color=color)
        elif piece_upper == "B":
            return Bishop((row, col), color=color)
        elif piece_upper == "R":
            return Rook((row, col), color=color)
        elif piece_upper == "Q":
            return Queen((row, col), color=color)
        elif piece_upper == "K":
            return King((row, col), color=color)
        else:
            raise ValueError("Unrecognized piece string: {}".format(piece_char))

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

    def move_is_valid(self, d_row, d_col, capture=False):
        raise NotImplementedError()

    def letter(self):
        """
        Single character representation of piece.
        Uppercase for WHITE, lowercase for BLACK.
        """
        if self.color == BLACK:
            letter = self.__class__.__name__[0].lower()
        else:
            letter = self.__class__.__name__[0]
        return letter

    def u_str(self):
        """
        Unicode representation of piece
        """
        return UNICODE_PIECE_SYMBOLS[self.letter()]

    def __str__(self):
        if UNICODE_PIECES:
            return self.u_str()
        else:
            return self.letter()

    def __repr__(self):
        return "{}({}, {})".format( self.__class__.__name__,
                                    self.square,
                                    COLOR_NAME[self.color])


class Pawn(Piece):
    value = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def move_is_valid(self, d_row, d_col, capture=False, **kwargs):
        """
        Can move forward 2 if it has not yet moved. Otherwise can only move 1.
        If the move is a capture, it can move diagonally
        """
        fwd = COLOR_ORIENTATION[self.color]
        # If move is a capture, only allow forward diagonal moves by 1 space
        if capture:
            if abs(d_col) == ( fwd * d_row ) == 1:
                return True
            else:
                return False
        else:
            # Only allow forward moves by 1 (if has not moved, then allow 2)
            if d_col == 0 and ( fwd * d_row == 1 or (not self.has_moved and fwd * d_row == 2) ):
                return True
            else:
                return False


class Bishop(Piece):
    value = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Rank and file must change by same amount
        """
        if ( abs(d_col) == abs(d_row) ):
            return True
        else:
            return False


class Knight(Piece):
    value = 3
    jumps = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Rank or file must change by 2, the other must change by 1
        """
        if sorted([abs(d_col), abs(d_row)]) == [1, 2]:
            return True
        else:
            return False

    def __str__(self):
        if self.color == BLACK:
            letter = "n"
        else:
            letter = "N"
        return "{}".format(letter)


class Rook(Piece):
    value = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            if sorted([abs(d_col), abs(d_row)]) in ([1, 1], [0, 1]):
                return True
            else:
                return False

###############################################################################
#  MAIN                                                                       #
###############################################################################
def test():
    board = Board("Standard")
    t0 = time.time()
    moves = [ "c2c4", "e7e5",
              "b1c3", "g8f6",
              "d2d4", "e5d4",
              "d1d4", "d7d5",
              "c4d5", "d8d5",
              "c3d5", "e8d7",
              "d5b6",
              ]
    move_counts = []
    for move in moves:
        board.process_move(move)
        move_counts.append( sum(len(v) for v in board.allowed_moves.values()) )
    t1 = time.time()
    print("\nEvaluated {:d} moves in {:f} sec".format(len(moves), t1-t0))
    print("({:f} sec/position)".format((t1-t0)/len(moves)))
    correct_move_counts = [ 20, 22, 30, 26, 29, 33, 27, 44, 36, 45, 32, 47, 4 ]
    if move_counts != correct_move_counts:
        print("ERROR: Move counts do not match!!!")
    return

def main():
    board = Board("Standard")
    board.play_game()
    return

if __name__ == "__main__":
    if 0:
        test()
    else:
        main()