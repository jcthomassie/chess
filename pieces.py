# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
import traceback
import copy

from collections.abc import Iterable

###############################################################################
#  GLOBALS                                                                    #
###############################################################################

# BOARD PROPERTIES
N_RANKS = 8
N_FILES = 8
RANK_ZERO = "8"
FILE_ZERO = "A"
UNICODE_PIECES = False

# COLORS / RESULTS
WHITE = 0
BLACK = 1
DRAW = -1

# COLOR INFO
FLIP_COLOR = dict(( (WHITE, BLACK), (BLACK, WHITE) ))
COLOR_ORIENTATION = dict(( (WHITE, -1), (BLACK, 1) ))
COLOR_NAME = dict(((WHITE, "White"), (BLACK, "Black"), (DRAW, "Draw")))

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
            position = ( position.row, position.col )
        # Parse string
        if isinstance(position, str):
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
        return self.__str__()#"Square({})".format(str(self))

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

    def __init__(self, board=None, to_move=WHITE):
        self.game_history = [ ]
        self.reset_board(to_move=to_move)
        return

    def reset_board(self, to_move=WHITE):
        """
        Initializes an empty board, clears game history, sets winner to None
        and to_move to WHITE.
        """
        # Construct board
        self.board = [ [ None for _ in range(N_FILES) ]
                              for _ in range(N_RANKS)
                      ]
        # Game trackers
        self.game_history.clear()
        self.to_move = to_move
        self.winner = None
        # TODO: add halfmove/fullmove counts
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

    def square_generator(self):
        """
        Generator to iterate over all squares of the board
        """
        for row in range(0, N_RANKS):
            for col in range(0, N_FILES):
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
                if color is None or piece.color == color:
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
        Yeilds pieces of the specified type and color.
        """
        for p in self.piece_generator(color=color):
            if isinstance(p, piece_type):
                yield p

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
            threats = self.valid_moves_piece(piece, recaptures=True)

            if square in threats:
                attackers.append(piece)

        return attackers

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

    def valid_castles(self):
        """
        Return a list of valid castling moves for the current player.
        """
        moves = [ ]
        return moves

    def valid_en_passant(self):
        """
        Return a list of valid en passant moves for the current player.
        """
        moves = [ ]
        return moves

    def valid_moves_king(self, king):
        """
        Return a list of all valid moves for a king. Gets list of normal king
        moves, removes moves that leave the king in check, and adds valid
        castling moves.
        """
        moves = [ ]
        # Normal moves
        for square in self.valid_moves_piece(king):
            # Keep moves that do not result in check
            if len(self.get_attackers(square, FLIP_COLOR[king.color])) == 0:
                moves.append(square)
        # Add castling moves
        for rook in self.find_pieces(Rook, king.color):
            if self.can_castle(king, rook):
                moves.append(self.square_slice(king.square, rook.square)[2])
        return moves

    def valid_moves_piece(self, piece, recaptures=False):
        """
        Return a list of all valid moves for the specified piece.
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
            # Check path
            if not piece.jumps:
                if self.obstruction(piece.square, square):
                    continue

            moves.append(square)

        return moves

    def valid_moves_all(self):
        """
        Return a list of all valid moves in the current board configuration.
        """
        moves = [ ]
        for piece in self.piece_generator(color=self.to_move):
            if isinstance(piece, King):
                moves.append( (piece.square, self.valid_moves_king(piece)) )
            else:
                moves.append( (piece.square, self.valid_moves_piece(piece)) )
        # TODO: Remove moves that leave king in check
        # TODO: Add en passant moves
        return moves

    def move_piece(self, from_square, to_square, capture=False, castle=False, en_passant=False):
        """
        Moves the piece on from_square to to_square.
        """
        piece = self[from_square]
        piece.move(to_square, capture=capture, castle=castle, en_passant=en_passant)
        self[to_square] = piece
        del self[from_square]
        return

    def castle(self, king, rook):
        """
        Process a castle move.
        """
        if self.can_castle(king, rook):
            # Get King and Rook positions
            path = self.square_slice(king.square, rook.square)
            king_old = king.square
            rook_old = rook.square
            king_square = path[2]
            rook_square = path[1]
            # Move the pieces
            self.move_piece(king_old, king_square, castle=True)
            self.move_piece(rook_old, rook_square)
        else:
            raise InvalidMoveError("{!r} cannot castle with {!r}!".format(king, rook))

    def en_passant(self, pawn, target):
        """
        Process an en passant capture.
        """
        return

    def promote(self, pawn):
        """
        Process a pawn promotion.
        """
        return

    def parse_move(self, from_square, to_square):
        """
        Takes from_square and to_square for move command. Attempts to process
        the move into a move dictionary. Returns the dictionary.
        """
        displacements = [ (from_square, to_square) ]
        # Check that move is valid
        valid_moves = self.valid_moves_all()
        valid_move_str = "|".join([ "{}{}".format(s0, s1) for s0, s1_list in valid_moves for s1 in s1_list ])
        move_str = "{}{}".format(from_square, to_square)
        if not move_str in valid_move_str:
            raise InvalidMoveError("{} is not a valid move!".format(move_str))

        # Get move info
        #piece = self[from_square]

        # Determine if capture
        if self[to_square] is not None:
            capture = True
        else:
            capture = False

        # TODO: determine if en passant
        en_passant = False

        # TODO: determine if castle
        castle = False

        # TODO: determine if promote
        promote = False

        return dict( displacements=displacements,
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
            self.castle()
        # Push en passant to board
        elif move_dict["en_passant"]:
            self.en_passant()
        # Push promotion to board
        elif move_dict["promote"]:
            self.promote()
        # Push normal move to board
        else:
            from_square, to_square = move_dict["displacements"][0]
            piece = self[from_square]
            # Move the piece and update the board
            piece.move(to_square, capture=move_dict["capture"])
            self[to_square] = piece
            del self[from_square]
        # Update and store game state
        self.game_history.append(copy.deepcopy(self.board))
        self.to_move = FLIP_COLOR[self.to_move]
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
        return

    def move(self, move_str):
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
        move = self.parse_move(from_square, to_square)
        self.push_move(move)
        return

    def check(self):
        """
        Return True if current player is in check.
        Return False otherwise.
        """
        king = next(self.find_pieces(King, self.to_move))
        if len(self.get_attackers(king.square, FLIP_COLOR[king.color])) > 0:
            return True
        return False

    def checkmate(self):
        """
        Return True if current player is in checkmate.
        Return False otherwise.
        """
        # TODO: fix false positives
        king = next(self.find_pieces(King, self.to_move))
        if len(self.get_attackers(king.square, FLIP_COLOR[king.color])) > 0:
            if len(self.valid_moves_king(king)) == 0:
                return True
        return False

    def stalemate(self):
        """
        Return True if current player has no valid moves.
        Return False otherwise.
        """
        if not any(self.valid_moves_all()):
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
        move_input = input(">>> ").strip().upper()
        if move_input == "R":
            # Set winner to opponent
            self.winner = FLIP_COLOR[self.to_move]
        elif move_input == "U":
            self.undo_move()
        elif move_input == "D":
            print("\n* * * Draw offered ( A - Accept ) * * * ")
            draw = input(">>> ").strip()
            if draw.strip().upper() == "A":
                self.winner = DRAW
        else:
            self.move(move_input)
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
            if self.stalemate():
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

    def construct_fen(self):
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

        # TODO: parse castling state
        castle_str = "KQkq"

        # TODO: parse en passant target square
        en_passant_str = "-"

        # TODO: parse halfmove clock
        half_move_str = "0"

        # TODO: parse fullmove number
        full_move_str = "1"

        return " ".join([ board_str,
                          castle_str,
                          en_passant_str,
                          half_move_str,
                          full_move_str, ])

    @classmethod
    def parse_fen(cls, fen_str):
        """
        Parses a FEN formatted string representation of a chess board into
        a Board object.
        """
        # Check input
        fields = fen_str.strip().split()
        if len(fields) != 6:
            raise ValueError("FEN str does not contain 6 space separated fields!")

        # Create empty board
        board = cls()

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
                    board[(r, col)] = Piece.from_str(char, row=r, col=col)

        # Save copy of board to history
        board.game_history.append(copy.deepcopy(board.board))

        # Determine whose move
        to_move = fields[1].lower()
        if to_move == "w":
            board.to_move = WHITE
        elif to_move == "b":
            board.to_move = BLACK
        else:
            raise ValueError("Unrecognized color symbol!")

        # TODO: parse castling state

        # TODO: parse en passant target square

        # TODO: parse halfmove clock

        # TODO: parse fullmove number

        return board

    @classmethod
    def standard(cls):
        """
        Construct a standard chess board.
        """
        return cls.parse_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    @classmethod
    def horde(cls):
        """
        Construct a Horde configured chess board.
        """
        return cls.parse_fen("rnbqkbnr/pppppppp/8/1PP2PP1/PPPPPPPP/PPPPPPPP/PPPPPPPP/PPPPPPPP w KQkq - 0 1")

    @classmethod
    def test_mate(cls):
        """
        Construct a board with checkmate.
        """
        return cls.parse_fen("8/8/1Kn5/3k4/4Q3/6N1/8/8 b KQkq - 0 1")

    @classmethod
    def test_castle(cls):
        """
        Construct a board with immediate castle.
        """
        return cls.parse_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")

    def print_turn_header(self):
        """
        Print a text representation of the current board position.
        """
        print("_________________________________________________________")
        print("\n")
        print(self)
        print()
        print("       {} to play!  (Material: {})".format(COLOR_NAME[self.to_move], self.evaluate()))
        # Announce check
        if self.check():
            print("\n       * * * King is in check! * * *")
        print("_________________________________________________________")
        print("Enter move: c2c4 ( R - Resign | D - Draw | U - Undo )")
        return

    def __str__(self):
        """
        Return a mulitline string of the board.
        """
        letters =    "       A   B   C   D   E   F   G   H       "
        edge_line =  "     +" + "---+" * N_FILES
        piece_line = "   {} | " + "{} | " * N_FILES

        if self.to_move == WHITE:
            display = [ ( r, row[:] ) for r, row in enumerate(self.board[:]) ]
        else: # flip for black
            display = [ ( N_RANKS - r - 1, row[::-1] ) for r, row in enumerate(self.board[::-1]) ]
            letters = letters[::-1]

        board_str = edge_line + "\n"
        for r, row in display:
            row = [ " " if p is None else p for p in row ]
            board_str += piece_line.format(Square.row_to_rank(r), *row) + "\n"
            board_str += edge_line + "\n"
        board_str += letters
        return board_str

    def __repr__(self):
        return "Board({})".format(self.construct_fen())

class InvalidMoveError(Exception):
    pass

###############################################################################
#  PIECES                                                                     #
###############################################################################
UNICODE_PIECE_SYMBOLS = dict(( ("R", u"♖"), ("r", u"♜"),
                               ("N", u"♘"), ("n", u"♞"),
                               ("B", u"♗"), ("b", u"♝"),
                               ("Q", u"♕"), ("q", u"♛"),
                               ("K", u"♔"), ("k", u"♚"),
                               ("P", u"♙"), ("p", u"♟"),  ))

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

    def ustr(self):
        """
        Unicode representation of piece
        """
        return UNICODE_PIECE_SYMBOLS[self.letter()]

    def __str__(self):
        if UNICODE_PIECES:
            return self.ustr()
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
    board = Board.standard()
    board.play_game()

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()