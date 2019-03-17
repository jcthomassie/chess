# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
import traceback
import copy

WHITE = 0
BLACK = 1

DRAW = -1

RANK_ZERO = "8"
FILE_ZERO = "A"

FLIP_COLOR = dict(( (WHITE, BLACK), (BLACK, WHITE) ))
COLOR_ORIENTATION = dict(( (WHITE, -1), (BLACK, 1) ))
COLOR_NAME = dict(((WHITE, "White"), (BLACK, "Black"), (DRAW, "Draw")))

class Square:
    """
    Board square representation. Allows flexible conversion between
    string and tuple representations
    """
    def __init__(self, position):
        """
        Takes a tuple or string of length 2 as input.
        """
        if isinstance(position, Square):
            position = ( position.row, position.col )
        if isinstance(position, str):
            if len(position) != 2:
                raise ValueError("Square position string must be 2 characters!")
            pos_str = position
            pos_tup = ( self.rank_to_row(pos_str[1]), self.file_to_col(pos_str[0]) )
        elif isinstance(position, tuple):
            if ( len(position) != 2 or not isinstance(position[0], int) 
                                 or not isinstance(position[1], int) ):
                raise ValueError("Square position tuple must contain two integers!")
            pos_tup = position
            pos_str = self.col_to_file(pos_tup[1]) + self.row_to_rank(pos_tup[0])
        else:
            raise TypeError("Square position must be a string or tuple!")
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
        return ord(file.upper()) - ord(FILE_ZERO)
    
    @staticmethod
    def col_to_file(col):
        """
        Convert column integer to file letter 
        ( 0->'A', 1->'B', ... )
        """
        return chr(ord(FILE_ZERO) + col)
    
    @staticmethod
    def rank_to_row(rank):
        """
        Convert rank string to row integer 
        ( '8'->0, '1'->7, ... )
        """
        return ord(RANK_ZERO) - ord(rank)
    
    @staticmethod
    def row_to_rank(row):
        """
        Convert row integer to rank string 
        ( 0->'8', 7->'1', ... )
        """
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
    
    def __init__(self, n_ranks=8, n_files=8):
        # Construct board
        self.n_ranks = n_ranks
        self.n_files = n_files
        self.board = [ [ None for _ in range(self.n_files) ] 
                              for _ in range(self.n_ranks) 
                      ]
        # Game trackers
        self.to_move = WHITE
        self.game_history = [ ]
        self.winner = None
        return
    
    def __setitem__(self, position, piece):
        """
        Inserts a piece at the specified square position.
        board['A1'] = Rook(WHITE, 'A1')
        """
        if not isinstance(piece, Piece):
            raise TypeError("Board can only contain Piece objects!")
        sq = Square(position)
        if not sq.row in range(0, self.n_ranks):
            raise IndexError("Rank out of bounds!")
        if not sq.col in range(0, self.n_files):
            raise IndexError("File out of bounds!")
        self.board[sq.row][sq.col] = piece
        return
    
    def __getitem__(self, position):
        """
        Gets the piece on the specified square position (None for empty square).
        board['A1'] -> Rook(White, A1)
        """
        sq = Square(position)
        if not sq.row in range(0, self.n_ranks):
            raise IndexError("Rank out of bounds!")
        if not sq.col in range(0, self.n_files):
            raise IndexError("File out of bounds!")
        piece = self.board[sq.row][sq.col]
        return piece
        
    def __delitem__(self, position):
        """
        Removes any piece at the specified board position. Replaces the
        slot with None.
        """
        sq = Square(position)
        if not sq.row in range(0, self.n_ranks):
            raise IndexError("Rank out of bounds!")
        if not sq.col in range(0, self.n_files):
            raise IndexError("File out of bounds!")
        self.board[sq.row][sq.col] = None
        return
    
    def flattened(self):
        """
        Generator to iterate over all squares of the board
        """
        for row in range(0, self.n_ranks):
            for col in range(0, self.n_files):
                yield Square((row, col))
                
    def piece_generator(self, color=None):
        """
        Yields all pieces on the current board. If color is specified, only
        pieces of the specified color are yielded.
        """
        for square in self.flattened():
            piece = self[square]
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
    
    def enpassant(self, pawn, target):
        pass
    
    def promote_pawn(self, pawn):
        pass
    
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
            king.move(king_square, castle=True)
            rook.move(rook_square)
            # Update the board
            self[king_square] = king
            self[rook_square] = rook
            del self[king_old]
            del self[rook_old]
        else:
            raise InvalidMoveError("{!r} cannot castle with {!r}!".format(king, rook))
    
    def valid_moves_king(self, king):
        """
        Return a list of all valid moves for a king.
        """
        moves = [ ]
        # Normal moves
        for square in self.valid_moves_piece(king):
            threats = self.get_attackers(square, FLIP_COLOR[king.color])
            if len(threats) == 0:
                moves.append(square)
        # Castling
        for rook in self.find_pieces(Rook, king.color):
            if self.can_castle(king, rook):
                moves.append(self.square_slice(king.square, rook.square)[2])
        return moves
    
    def valid_moves_piece(self, piece, recaptures=False):
        """
        Return a list of all valid moves for the specified piece.
        """
        moves = [ ]
        for square in self.flattened():
            target = self[square]
            if target is None: 
                # EMPTY case
                capture = False
                castle = False
            elif target.color != piece.color: 
                # CAPTURE case
                capture = True
                castle = False
            elif recaptures:
                # RECAP case
                capture = True
                castle = False
            else:
                continue
            # Check if move is valid for piece
            d_row, d_col = square - piece.square
            if not piece.move_is_valid(d_row, d_col, capture=capture, castle=castle):
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
        return moves
    
    def move(self, from_square, to_square):
        """
        Attempts to move the piece on from_square to to_square.
        """
        # TODO: make valid_moves_all only call once per turn
        # Check that move is valid
        valid_moves = self.valid_moves_all()
        valid_move_str = "|".join([ "{}{}".format(s0, s1) for s0, s1_list in valid_moves for s1 in s1_list ])
        move_str = "{}{}".format(from_square, to_square)
        if not move_str in valid_move_str:
            raise InvalidMoveError("{} is not a valid move!".format(move_str))
        
        # Get move info
        piece = self[from_square]
        if self[to_square] is not None:
            capture = True
        else:
            capture = False
            
        # TODO: Handle castling
        #self.castle(piece, target)
        
        # TODO: Handle enpassant
        
        # TODO: Handle pawn promotions
        
        # Move the piece and update the board
        piece.move(to_square, capture=capture)
        self[to_square] = piece
        del self[from_square]
        return
    
    def undo_move(self):
        """
        Restore game state from one turn prior. Deletes the most recent move
        from game_history.
        """
        if len(self.game_history) == 1:
            raise InvalidMoveError("There are no moves to undo!")
        self.board = copy.deepcopy(self.game_history[-2])
        del self.game_history[-2:]
        self.to_move = FLIP_COLOR[self.to_move]
        self.winner = None
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
            try:
                from_pos = move_input[:2]
                to_pos = move_input[2:].strip()
                from_square = Square(from_pos)
                to_square = Square(to_pos)
            except:
                raise InvalidMoveError("Could not parse move!")
            # Make move
            self.move(from_square, to_square)
            self.to_move = FLIP_COLOR[self.to_move]
            
        return True
    
    def play_game(self):
        """
        Facilitate a game via commandline.
        """
        while self.winner is None:
            # Print board, save copy
            self.print_board()
            self.game_history.append(copy.deepcopy(self.board))
            
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
    
    def print_board(self):
        """
        Print a text representation of the current board position.
        """
        letters = "       A   B   C   D   E   F   G   H       "
        if self.to_move == WHITE:
            display = [ ( r, row[:] ) for r, row in enumerate(self.board[:]) ]
        else: # flip for black
            display = [ ( self.n_ranks - r - 1, row[::-1] ) for r, row in enumerate(self.board[::-1]) ]
            letters = letters[::-1]
        edge = "     +" + "---+" * self.n_files
        mid = "   {} | " + "{} | " * self.n_files
        print("_________________________________________________________")
        print("\n")
        print(edge)
        for r, row in display:
            row = [ " " if p is None else p for p in row ]
            print(mid.format(Square.row_to_rank(r), *row))
            print(edge)
        print(letters)
        print()
        print("       {} to play!  (Material: {})".format(COLOR_NAME[self.to_move], self.evaluate()))
        # Announce check
        if self.check():
            print("\n       * * * King is in check! * * *")
        print("_________________________________________________________")
        print("Enter move: c2c4 ( R - Resign | D - Draw | U - Undo )")
        return
    
    @classmethod
    def standard(cls):
        """
        Construct a standard chess board.
        """
        s_board = cls(n_ranks=8, n_files=8)
        
        # Populate board
        s_board.add_piece(Rook,   BLACK, "A8")
        s_board.add_piece(Knight, BLACK, "B8")
        s_board.add_piece(Bishop, BLACK, "C8")
        s_board.add_piece(Queen,  BLACK, "D8")
        s_board.add_piece(King,   BLACK, "E8")
        s_board.add_piece(Bishop, BLACK, "F8")
        s_board.add_piece(Knight, BLACK, "G8")
        s_board.add_piece(Rook,   BLACK, "H8")
        for i in range(s_board.n_files):
            s_board.add_piece(Pawn, BLACK, (1, i))
        s_board.add_piece(Rook,   WHITE, "A1")
        s_board.add_piece(Knight, WHITE, "B1")
        s_board.add_piece(Bishop, WHITE, "C1")
        s_board.add_piece(Queen,  WHITE, "D1")
        s_board.add_piece(King,   WHITE, "E1")
        s_board.add_piece(Bishop, WHITE, "F1")
        s_board.add_piece(Knight, WHITE, "G1")
        s_board.add_piece(Rook,   WHITE, "H1")
        for i in range(s_board.n_files):
            s_board.add_piece(Pawn, WHITE, (6, i))
        
        return s_board
    
    @classmethod
    def horde(cls):
        """
        Construct a Horde configured chess board.
        """
        h_board = cls(n_ranks=8, n_files=8)
        
        # Populate board
        h_board.add_piece(Rook,   BLACK, "A8")
        h_board.add_piece(Knight, BLACK, "B8")
        h_board.add_piece(Bishop, BLACK, "C8")
        h_board.add_piece(Queen,  BLACK, "D8")
        h_board.add_piece(King,   BLACK, "E8")
        h_board.add_piece(Bishop, BLACK, "F8")
        h_board.add_piece(Knight, BLACK, "G8")
        h_board.add_piece(Rook,   BLACK, "H8")
        for i in range(h_board.n_files):
            h_board.add_piece(Pawn, BLACK, (1, i))
        h_board.add_piece(Pawn, WHITE, "B5")
        h_board.add_piece(Pawn, WHITE, "C5")
        h_board.add_piece(Pawn, WHITE, "F5")
        h_board.add_piece(Pawn, WHITE, "G5")
        for i in range(h_board.n_files):
            for j in range(4, 8):
                h_board.add_piece(Pawn, WHITE, (j, i))
        
        return h_board
    
    @classmethod
    def test_check(cls):
        """
        Constructs a board with check.
        """
        t_board = cls(n_ranks=8, n_files=8)
        
        # Populate board
        t_board.add_piece(King,  BLACK, "A8")
        t_board.add_piece(Queen, BLACK, "G8")
        t_board.add_piece(King,  WHITE, "B3")
        
        return t_board
    
    @classmethod
    def test_mate(cls):
        """
        Constructs a board with checkmate.
        """
        t_board = cls(n_ranks=8, n_files=8)
        t_board.to_move = BLACK
        
        # Populate board
        t_board.add_piece(King,   BLACK, "D4")
        t_board.add_piece(Knight, BLACK, "C3")
        t_board.add_piece(King,   WHITE, "B3")
        t_board.add_piece(Queen,  WHITE, "E5")
        t_board.add_piece(Knight, WHITE, "G6")
        
        return t_board
    
    @classmethod
    def test_castle(cls):
        """
        Constructs a board with immediate castle.
        """
        t_board = cls(n_ranks=8, n_files=8)
        
        # Populate board
        t_board.add_piece(King, WHITE, "E1")
        t_board.add_piece(Rook, WHITE, "A1")
        t_board.add_piece(Rook, WHITE, "H1")
        t_board.add_piece(King, BLACK, "E8")
        t_board.add_piece(Rook, BLACK, "A8")
        t_board.add_piece(Rook, BLACK, "H8")
        
        return t_board


class InvalidMoveError(Exception):
    pass


class Piece:
    
    def __init__(self, position, color=WHITE):
        if isinstance(position, Square):
            self.square = position
        else:
            self.square = Square(position)
        self.color = color
        self.jumps = False
        self.value = None
        self.has_moved = False
        
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
    
    def __repr__(self):
        return "{}({}, {})".format( self.__class__.__name__, 
                                    self.square, 
                                    COLOR_NAME[self.color])
    
    def __str__(self):
        if self.color == BLACK:
            letter = self.__class__.__name__[0].lower()
        else:
            letter = self.__class__.__name__[0]
        return "{}".format(letter)


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
        Can move like Rook or Bishop
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

def main():
    board = Board.test_mate()
    board.play_game()

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()