# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""

import copy
from time import time

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
    def __init__(self, position):
        """
        Takes a tuple or string of length 2 as input.
        """
        # Parse square
        if isinstance(position, Square):
            pos_tup = ( position.row, position.col )
            pos_str = str(position)
        # Parse string
        elif isinstance(position, str):
            if len(position) != 2:
                raise ValueError("Square position string must be 2 characters!")
            pos_str = position.upper()
            pos_tup = ( self.rank_to_row(pos_str[1]), self.file_to_col(pos_str[0]) )
        # Parse (row, col) tuple
        elif isinstance(position, tuple):
            if ( len(position) != 2 or not isinstance(position[0], int)
                                 or not isinstance(position[1], int) ):
                raise ValueError("Square position tuple must contain two integers!")
            pos_tup = position
            pos_str = self.col_to_file(pos_tup[1]) + self.row_to_rank(pos_tup[0])
        else:
            raise TypeError("Square position must be a string or tuple!")
        # Check if in bounds
        if not pos_tup[0] in range(0, N_RANKS):
            raise IndexError("Rank out of bounds!")
        if not pos_tup[1] in range(0, N_FILES):
            raise IndexError("File out of bounds!")
        self.row = pos_tup[0]
        self.col = pos_tup[1]
        self.file = pos_str[0]
        self.rank = pos_str[1]
        return

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
        return int(str(self.row) + str(self.col))

    def __eq__(self, other):
        if isinstance(other, Square):
            return self.row == other.row and self.col == other.col
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
            }

    def __init__(self, fen="Standard"):
        self._board_fmt_str = None
        if fen is None:
            self.clear_board()
        else:
            self.load_fen(fen)

    def clear_board(self, to_move=WHITE):
        """
        Initializes an empty board, clears game history, sets winner to None
        and to_move to WHITE.
        """
        # Construct board
        self.board = [ [ None for _ in range(N_FILES) ]
                              for _ in range(N_RANKS)
                      ]
        # Game trackers
        self.game_history = [ ]
        self.to_move = to_move
        self.winner = None
        self.halfmoves = 0
        self.fullmoves = 1

        self._allowed_moves = dict( )
        self._last_recompute = 0
        return

    def __setitem__(self, position, piece):
        """
        Inserts a piece at the specified square position.
        board['A1'] = Rook(WHITE, 'A1')
        """
        sq = Square(position)
        if piece is None or isinstance(piece, Piece):
            self.board[sq.row][sq.col] = piece
        else:
            raise TypeError("Board can only contain Piece and NoneType objects!")

    def __getitem__(self, position):
        """
        Gets the piece on the specified square position (None for empty square).
        board['A1'] -> Rook(White, A1)
        """
        sq = Square(position)
        piece = self.board[sq.row][sq.col]
        return piece

    def __delitem__(self, position):
        """
        Removes any piece at the specified board position. Replaces the
        slot with None.
        """
        self[position] = None

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
                yield Square((row, col))

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

    def add_piece(self, piece, color, square):
        """
        Creates piece of color on square and adds it to the board.
        """
        self[square] = piece(square, color=color)
        return

    def square_slice(self, from_square, to_square):
        """
        Slices out a list representation of the squares on the board
        from_square to_square, inclusive. Only works for square/diagonal
        displacements
        """
        from_square = Square(from_square)
        to_square = Square(to_square)
        d_row, d_col = to_square - from_square
        squares = [ ]
        # DIAGONAL MOVE
        if abs(d_row) == abs(d_col):
            r_unit = (1, -1)[d_row < 0] # get sign of row change
            c_unit = (1, -1)[d_col < 0] # get sign of col change
            r_to_c = r_unit * c_unit # 1 if same, -1 if opposite
            for r in range(0, d_row + r_unit, r_unit):
                pos_tup = (from_square.row + r, from_square.col + r * r_to_c)
                squares.append(Square(pos_tup))
        # VERTICAL MOVE
        elif d_col == 0:
            r_unit = (1, -1)[d_row < 0] # get sign of row change
            for r in range(0, d_row + r_unit, r_unit):
                pos_tup = (from_square.row + r, from_square.col)
                squares.append(Square(pos_tup))
        # HORIZONTAL MOVE
        elif d_row == 0:
            c_unit = (1, -1)[d_col < 0] # get sign of col change
            for c in range(0, d_col + c_unit, c_unit):
                pos_tup = (from_square.row, from_square.col + c)
                squares.append(Square(pos_tup))
        else:
            raise IndexError("Slices must be square or diagonal!")

        return squares

    def piece_slice(self, from_square, to_square):
        """
        Slices out a list representation of the board from_square to_square,
        inclusive. Only works for square/diagonal displacements.
        """
        squares = self.square_slice(from_square, to_square)
        return [ self[s] for s in squares ]

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
        pieces = self.piece_slice(from_square, to_square)[1:-1]
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
            threats = self.valid_targets_piece(piece, recaptures=True)

            if square in threats:
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
            path = self.piece_slice(pinner.square, square)[1:-1]
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
        if self.obstruction(king.square, rook.square):
            return False

        # Make sure king doesn't cross through check (include current square)
        path = self.square_slice(king.square, rook.square)[:3]
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
                moves.append(self.square_slice(king.square, rook.square)[2])
        return moves

    def valid_en_passants(self):
        """
        Return a list of valid en passant moves for the current player.
        """
        # TODO
        moves = [ ]
        return moves

    def valid_promotes(self):
        """
        Return a list of valid pawn promotions for the current player.
        """
        # TODO
        moves = [ ]
        return moves

    def valid_targets_king(self, king):
        """
        Return a list of all valid target squares for a king. Gets list of normal king
        moves, removes moves that leave the king in check, and adds valid
        castling moves.
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

    def valid_targets_piece(self, piece, recaptures=False, unpins_only=False):
        """
        Return a list of all valid target squares for the specified piece.
        Does not consider whether a move leaves player in check,
        does not consider castling, does not consider en passant.
        """
        moves = [ ]
        for square in self.square_generator():
            if square == piece.square:
                continue
            target = self[square]
            if target is None:
                # EMPTY case
                capture = False
            elif target.color != piece.color:
                # CAPTURE case
                capture = True
            elif recaptures:
                # RECAPTURE case
                capture = True
            else:
                continue
            # Check if move is valid for piece
            d_row, d_col = square - piece.square
            if not piece.move_is_valid(d_row, d_col, capture=capture):
                continue

            # Only keep moves opened by an opponents move
            if unpins_only:
                if piece.jumps:
                    continue
                path = self.piece_slice(piece.square, square)[1:-1]
                blockers = [ p for p in path if p is not None]
                # Piece must be blocked by exactly one piece of the opposite color
                if len(blockers) != 1 or blockers[0].color == piece.color:
                    continue
            # Keep moves without obstructions
            elif not piece.jumps:
                if self.obstruction(piece.square, square):
                    continue

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
        test_board = copy.deepcopy(self)
        for from_square, targets in move_lookup.items():
            cleaned_targets = [ ]
            for to_square in targets:
                # Try the move on the test_board
                move = test_board.load_move(from_square, to_square, verify_move=False)
                test_board.push_move(move)
                # Keep the move if it does not cause check
                if not test_board.check(color=color):
                    cleaned_targets.append(to_square)
                # Reset for next test
                test_board.undo_move()
            if len(cleaned_targets) > 0:
                cleaned[from_square] = cleaned_targets
        return cleaned

    @property
    def allowed_moves(self):
        """
        Update the stored dictionary of allowed moves. Call this every time the
        board position is changed!
        """
        if self._last_recompute != len(self.game_history):
            self._allowed_moves = self.valid_moves_all()
            self._last_recompute = len(self.game_history)
        return self._allowed_moves

    def move_piece(self, from_square, to_square, capture=False, castle=False, en_passant=False):
        """
        Moves the piece on from_square to to_square.
        Does not check for board validity.
        """
        piece = self[from_square]
        piece.move(to_square, capture=capture, castle=castle, en_passant=en_passant)
        self[to_square] = piece
        del self[from_square]
        return

    def castle(self, king_from_square, king_to_square):
        """
        Process a castle move.
        Does not check for board validity.
        """
        # Get King and Rook positions
        king = self[king_from_square]
        rook = None
        for test_rook in self.find_pieces(Rook, king.color):
            move_direction = (1, -1)[(king_to_square.col - king_from_square.col < 0)]
            rook_direction = (1, -1)[(test_rook.col - king.col < 0)]
            if not test_rook.has_moved and move_direction == rook_direction:
                rook = test_rook
        if rook is None:
            raise InvalidMoveError("Could not process castle move!")
        rook_from_square = rook.square
        rook_to_square = self.square_slice(king_from_square, king_to_square)[1]
        # Move the pieces
        self.move_piece(king_from_square, king_to_square, castle=True)
        self.move_piece(rook_from_square, rook_to_square)
        return

    def en_passant(self, pawn, target):
        """
        Process an en passant capture.
        Does not check for board validity.
        """
        # TODO
        return

    def promote(self, pawn):
        """
        Process a pawn promotion.
        """
        # TODO
        return

    def load_move(self, from_square, to_square, verify_move=True):
        """
        Takes from_square and to_square for move command. Attempts to process
        the move into a move dictionary. Returns the dictionary.
        """
        # OPTIMIZE
        # Check that move is valid
        if verify_move:
            if not from_square in self.allowed_moves.keys():
                raise InvalidMoveError("{} cannot move!".format(from_square))
            if not to_square in self.allowed_moves[from_square]:
                raise InvalidMoveError("{!r} cannot move to {}!".format(self[from_square], to_square))

        # Get pieces
        piece = self[from_square]
        target = self[to_square]

        # Determine if capture
        if target is not None:
            capture = True
        else:
            capture = False

        # Determine if en passant or promote
        en_passant = False
        promote = False
        if isinstance(piece, Pawn):
            if to_square in self.valid_en_passants():
                en_passant = True
            if to_square in self.valid_promotes():
                promote = True

        # Determine if castle
        castle = False
        if isinstance(piece, King):
            if to_square in self.valid_castles():
                castle = True

        return dict( from_square=from_square,
                     to_square=to_square,
                     capture=capture,
                     castle=castle,
                     en_passant=en_passant,
                     promote=promote )

    def push_move(self, move_dict):
        """
        Takes a list of Square pairs for final displacements. Applies the move
        to the board.
        """
        # Push castle to board
        if move_dict["castle"]:
            self.castle(move_dict["from_square"], move_dict["to_square"])
        # Push en passant to board
        elif move_dict["en_passant"]:
            self.en_passant()
        # Push promotion to board
        elif move_dict["promote"]:
            self.promote()
        # Push normal move to board
        else:
            piece = self[move_dict["from_square"]]
            # Move the piece and update the board
            piece.move(move_dict["to_square"], capture=move_dict["capture"])
            self[move_dict["to_square"]] = piece
            del self[move_dict["from_square"]]
        # Update and store game state
        self.game_history.append(copy.deepcopy(self.board))
        self.to_move = FLIP_COLOR[self.to_move]

        # TODO: update halfmoves and fullmoves
        return

    def undo_move(self):
        """
        Restore game state from one turn prior. Deletes the most recent move
        from game_history.
        """
        if len(self.game_history) == 1:
            raise InvalidMoveError("There are no moves to undo!")
        # Deleted current board
        del self.game_history[-1]
        # Get last board state
        self.board = copy.deepcopy(self.game_history[-1])
        self.to_move = FLIP_COLOR[self.to_move]
        self.winner = None

        # TODO: update halfmoves and fullmoves
        return

    def process_move(self, move_str):
        """
        Takes a move string as input. Trys to make the move, raises an error
        if the move fails.
        """
        try:
            from_square = Square(move_str[:2])
            to_square = Square(move_str[2:].strip())
        except:
            raise InvalidMoveError("Could not parse move!")
        # Make move
        t0 = time()
        self.push_move(self.load_move(from_square, to_square))
        print("Move succeeded!")
        print("Now {} valid moves".format(sum(len(v) for v in self.allowed_moves.values())))
        t1 = time()
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
            if move_input == "D":
                print("\n* * * Draw offered ( A - Accept ) * * * ")
                draw = input(">>> ").strip()
                if draw.strip().upper() == "A":
                    self.winner = DRAW
                    actionable = True
            elif move_input[-1] == "?":
                if move_input == "?":
                    for sq in self.allowed_moves.keys():
                        self.print_square_moves(sq)
                elif move_input[1] == "?":
                    ptype = type(Piece.from_str(move_input[0]))
                    for piece in self.find_pieces(ptype, self.to_move):
                        self.print_square_moves(piece.square)
                else:
                    self.print_square_moves(move_input[:-1])
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
        self.clear_board()

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

        # Save copy of board to history
        self.game_history.append(copy.deepcopy(self.board))

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
        print(space + "     {} to play!  (Material: {})".format(COLOR_NAME[self.to_move], self.evaluate()))
        # Announce check
        if self.check():
            print("\n" + space + "  * * * King is in check! * * *")
        print("_________________________________________________________")
        print("Enter move: c2c4 ( [R]esign | [D]raw | [U]ndo | [?] )")
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
                        for s in self.square_generator(reverse=reverse) )
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
    
    def print_square_moves(self, pos_str):
        """
        Print all valid moves from the specified square.
        """
        sq = Square(pos_str)
        piece = self[sq]
        if piece is None:
            print("{} is empty!".format(sq))
        elif piece.square in self.allowed_moves:
            print("{!r}: {}".format(piece, self.allowed_moves[sq]))
            print(self.moves_board_str(sq) + "\n")
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
#  PIECES                                                                     #
###############################################################################
class Piece:
    """
    Base class for all chess pieces.
    """
    def __init__(self, locus, color=WHITE):
        # Core attributes
        self.color = color
        self.jumps = False # True for Knights
        self.value = None # Material point value
        self.has_moved = False
        # Handle init from Pawn promotion
        if isinstance(locus, Pawn):
            self.color = locus.color
            self.square = locus.square
            self.has_moved = True
        # Handle init from Square
        elif isinstance(locus, Square):
            self.square = locus
        # Handle init from coordinate string/tuple
        else:
            self.square = Square(locus)

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

    def move(self, new_square, **kwargs):
        """
        Takes a position tuple or string as input. Checks if the position
        constitutes a valid move from the current square. If it is valid,
        then it updates it's position.
        """
        # Parse coordinate into tuple
        if new_square == self.square:
            raise InvalidMoveError("{!r} is already on {}!".format(self, new_square))
        # Check move
        d_row, d_col = new_square - self.square
        if self.move_is_valid(d_row, d_col, **kwargs):
            self.square = new_square
            self.has_moved = True
        else:
            raise InvalidMoveError("{!r} cannot move to {}!".format(self, new_square))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 1

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 3

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 3
        self.jumps = True

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 5

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 9

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 5

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
def main():
    board = Board("Standard")
    board.play_game()

if __name__ == "__main__":
    main()