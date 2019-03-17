# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
import traceback
import copy

WHITE = "White"
BLACK = "Black"
FLIP_COLOR = dict(( (WHITE, BLACK), (BLACK, WHITE) ))
COLOR_ORIENTATION = dict(( (WHITE, -1), (BLACK, 1) ))

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
        return ord(file.upper()) - ord("A")
    
    @staticmethod
    def col_to_file(col):
        """
        Convert column integer to file letter 
        ( 0->'A', 1->'B', ... )
        """
        return chr(ord("A") + col)
    
    @staticmethod
    def rank_to_row(rank):
        """
        Convert rank string to row integer 
        ( '8'->0, '1'->7, ... )
        """
        return ord("8") - ord(rank)
    
    @staticmethod
    def row_to_rank(row):
        """
        Convert row integer to rank string 
        ( 0->'8', 7->'1', ... )
        """
        return chr(ord("8") - row)
        
    def __str__(self):
        """
        Return string representation of the square's position
        ( (0, 0)->'A8', (1, 1)->'B8', ... )
        """
        return "{}{}".format(self.file, self.rank)
    
    def __repr__(self):
        return "Square({:d}, {:d})".format(self.row, self.col)
    
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
                yield self[(row, col)]
    
    def add_piece(self, piece, color, square):
        """
        Creates piece of color on square and adds it to the board.
        """
        self[square] = piece(square, color=color)
        return
    
    def get_slice(self, from_square, to_square):
        """
        Slices out a list representation of the board from_square to_square,
        inclusive. Only works for square/diagonal displacements.
        """
        from_square = Square(from_square)
        to_square = Square(to_square)
        d_row, d_col = to_square - from_square
        pieces = [ ]
        # DIAGONAL MOVE
        if abs(d_row) == abs(d_col):
            r_unit = (1, -1)[d_row < 0] # get sign of row change
            c_unit = (1, -1)[d_col < 0] # get sign of col change
            r_to_c = r_unit * c_unit # 1 if same, -1 if opposite
            for r in range(0, d_row + r_unit, r_unit):
                pos_tup = (from_square.row + r, from_square.col + r * r_to_c)
                pieces.append(self[pos_tup])
        # VERTICAL MOVE
        elif d_col == 0:
            r_unit = (1, -1)[d_row < 0] # get sign of row change
            for r in range(0, d_row + r_unit, r_unit):
                pos_tup = (from_square.row + r, from_square.col)
                pieces.append(self[pos_tup])
        # HORIZONTAL MOVE
        elif d_row == 0:
            c_unit = (1, -1)[d_col < 0] # get sign of col change
            for c in range(0, d_col + c_unit, c_unit):
                pos_tup = (from_square.row, from_square.col + c)
                pieces.append(self[pos_tup])
        else:
            raise ValueError("Slices must be square or diagonal!")
        
        return pieces

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

    def castle(self, king, rook):
        """
        Attempt to castle.
        """
        if king.has_moved or rook.has_moved:
            return False
        # IF KING IN CHECK, RETURN FALSE
        # IF PIECES BETWEEN, RETURN FALSE
        return True
    
    def promote_pawn():
        pass
    
    def get_attackers(self, target_square, color):
        """
        Check if any pieces of color are eyeing the square. 
        Return list of pieces.
        """
        target = Square(target_square)
        attackers = [ ]
        for piece in self.flattened():
            # Skip empty squares
            if piece is None:
                continue
            # Skip pieces of other color
            if piece.color != color:
                continue
            # Skip pieces that cannot capture the square
            d_row, d_col = target - piece.square
            if not piece.move_is_valid( d_row, d_col, capture=True ):
                continue
            # Skip obstructed pieces
            if not piece.jumps:
                if self.obstruction(piece.square, target):
                    continue
            
            attackers.append(piece)
        
        return attackers
    
    def check(self):
        """
        Return True if current player is in check.
        Return False otherwise.
        """
        # Find king for player to move
        king = None
        for piece in self.flattened():
            if isinstance(piece, King):
                if piece.color == self.to_move:
                    king = piece
        if king is None:
            raise Exception("Could not locate {} king!".format(self.to_move))
        # See if king is attacked
        if len(self.get_attackers(king.square, FLIP_COLOR[king.color])) > 0:
            return True
        return False
    
    def checkmate(self):
        """
        Return True if current player is in checkmate.
        Return False otherwise.
        """
        return False

    def stalemate(self):
        """
        Return True if current player cannot move.
        Return False otherwise.
        """
        return False
    
    def obstruction(self, from_square, to_square):
        """
        Return True if there is a piece between the two squares.
        Return False if the path is clear.
        """
        pieces = self.get_slice(from_square, to_square)[1:-1]
        if any(pieces):
            return True
        return False
    
    def evaluate(self):
        """
        Returns the current material point spread.
        """
        score = 0
        for piece in self.flattened():
            # Skip empty squares
            if piece is None:
                continue
            # Add material for WHITE
            if piece.color == WHITE:
                score += piece.value
            # Subtract material for BLACK
            else:
                score -= piece.value
        return score
    
    def move(self, from_square, to_square):
        """
        Attempts to move the piece on from_square to to_square.
        """
        # Get piece
        piece = self[from_square]
        if piece is None:
            raise InvalidMoveError("From square is empty!")
        elif piece.color != self.to_move:
            raise InvalidMoveError("Wrong color piece!")
        # Check path
        if not piece.jumps:
            if self.obstruction(from_square, to_square):
                raise InvalidMoveError("Path is blocked!")
        # Check target
        target = self[to_square]
        if target is None:
            capture = False
        else:
            capture = True
            if target.color == piece.color:
                raise InvalidMoveError("You cannot capture your own piece!")
        # Try to move the piece to the square
        piece.move(to_square, capture=capture)
        # Update the board
        self[to_square] = piece
        del self[from_square]
        return
    
    def undo_move(self):
        """
        Restore game state from one turn prior. Deletes the most recent move
        from m
        """
        if len(self.game_history) == 1:
            raise Exception("There are no moves to undo!")
        del self.game_history[-1]
        self.board = copy.deepcopy(self.game_history[-1])
        self.to_move = FLIP_COLOR[self.to_move]
        return
    
    def print_board(self):
        """
        Print a text representation of the current board position.
        """
        letters = "     A    B    C    D    E    F    G    H     "
        if self.to_move == WHITE:
            display = [ ( r, row[:] ) for r, row in enumerate(self.board[:]) ]
        else: # flip for black
            display = [ ( self.n_ranks - r - 1, row[::-1] ) for r, row in enumerate(self.board[::-1]) ]
            letters = letters[::-1]
        edge = "   +" + "----+" * self.n_files
        mid = " {} | " + "{} | " * self.n_files
        print("_________________________________________________________")
        print("\n")
        print(edge)
        for r, row in display:
            row = [ "  " if p is None else p for p in row ]
            print(mid.format(Square.row_to_rank(r), *row))
            print(edge)
        print(letters)
        print()
        print("\t{} to play!  (Spread: {})".format(self.to_move, self.evaluate()))
        # Announce check
        if self.check():
            print("\n\t* * * King is in check! * * *")
        print("_________________________________________________________")
        return

    def play_turn(self):
        """
        Process the events of a turn
        """
        print("Enter piece move coordinates")
        print("R - Resign")
        print("U - Undo last move")
        move_input = input(">>> ").strip().upper()
        if move_input == "R":
            # Set winner to opponent
            self.winner = FLIP_COLOR[self.to_move]
        elif move_input == "U":
            self.undo_move()
        else:
            from_pos, to_pos = move_input.split()
            from_square = Square(from_pos)
            to_square = Square(to_pos)
            # Attempt move
            self.move(from_square, to_square)
            # Switch player
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
            
            # See if checkmate
            if self.checkmate():
                self.winner = FLIP_COLOR[self.to_move]
            # See if stalemate
            if self.stalemate():
                self.winner = "DRAW"
                
            # Keep trying to move until a move succeeds
            while True:
                try:
                    self.play_turn()
                    break
                except (InvalidMoveError, IndexError) as e:
                    print(e)
        
        print("\n    * * * * * * * * *")
        print("    * {} WINS!!! *".format(self.winner).upper())
        print("    * * * * * * * * *\n")
        return

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
            raise InvalidMoveError("{} is already on {}!".format(repr(self), str(new_square)))
        # Check move
        d_row, d_col = new_square - self.square
        if self.move_is_valid(d_row, d_col, **kwargs):
            self.square = new_square
            self.has_moved = True
        else:
            raise InvalidMoveError("{} cannot move to {}!".format(repr(self), str(new_square)))
        
    def move_is_valid(self, d_row, d_col, capture=False):
        raise NotImplementedError()
    
    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, str(self.square), self.color)
    
    def __str__(self):
        return "{}{}".format(self.color[0], self.__class__.__name__[0])


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
        return "{}N".format(self.color[0])


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
    def move_is_valid(d_row, d_col, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if sorted([abs(d_col), abs(d_row)]) in ([1, 1], [0, 1]):
            return True
        else:
            return False

def main():
    board = Board.standard()
    board.play_game()

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()
        input("Press <ENTER> to exit...")