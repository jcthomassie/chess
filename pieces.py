# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""
WHITE = "White"
BLACK = "Black"
COLOR_ORIENTATION = dict(( (WHITE, 1), (BLACK, -1) ))

class Coord:
    """
    Board coordinate representation. Allows flexible conversion between
    string and tuple representations
    """
    def __init__(self, coord):
        """
        Takes a tuple or string of length 2 as input.
        """
        if isinstance(coord, Coord):
            return coord
        elif isinstance(coord, str):
            if len(coord) != 2:
                raise ValueError("Piece coordinate string must be 2 characters!")
            cstr = coord
            coord = ( self.rank_to_row(cstr[1]), self.file_to_col(cstr[0]) )
        elif isinstance(coord, tuple):
            if ( len(coord) != 2 or not isinstance(coord[0], int) 
                                 or not isinstance(coord[1], int) ):
                raise ValueError("Piece coordinate tuple must contain two integers!")
            cstr = self.col_to_file(coord[1]) + self.row_to_rank(coord[0])
        else:
            raise ValueError("Piece coordinate must be a string or tuple!")
        self.row = coord[0]
        self.col = coord[1]
        self.file = cstr[0]
        self.rank = cstr[1]
        
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
        Return string representation of coordinate
        ( (0, 0)->'A8', (1, 1)->'B8', ... )
        """
        return "{}{}".format(self.file, self.rank)
    
    def __repr__(self):
        return "Coord({:d}, {:d})".format(self.row, self.col)
    
    def __add__(self, other):
        if isinstance(other, Coord):
            return (self.row + other.row, self.col + other.col)
        
    def __sub__(self, other):
        if isinstance(other, Coord):
            return (self.row - other.row, self.col - other.col)


class Board:
    
    def __init__(self, n_ranks=8, n_files=8):
        
        self.board = [ [ None for _ in range(n_files)] for _ in range(n_ranks) ]
        
        self.add_piece(Rook,   "A8", BLACK)
        self.add_piece(Knight, "B8", BLACK)
        self.add_piece(Bishop, "C8", BLACK)
        self.add_piece(Queen,  "D8", BLACK)
        self.add_piece(King,   "E8", BLACK)
        self.add_piece(Bishop, "F8", BLACK)
        self.add_piece(Knight, "G8", BLACK)
        self.add_piece(Rook,   "H8", BLACK)
        for i in range(n_files):
            self.add_piece(Pawn, (1, i), BLACK)
            
        self.add_piece(Rook,   "A1", WHITE)
        self.add_piece(Knight, "B1", WHITE)
        self.add_piece(Bishop, "C1", WHITE)
        self.add_piece(Queen,  "D1", WHITE)
        self.add_piece(King,   "E1", WHITE)
        self.add_piece(Bishop, "F1", WHITE)
        self.add_piece(Knight, "G1", WHITE)
        self.add_piece(Rook,   "H1", WHITE)
        for i in range(n_files):
            self.add_piece(Pawn, (6, i), WHITE)
        
    def add_piece(self, piece, coord, color):
        self[coord] = piece(coord, color=color)
        
    def print_board(self):
        
        for row in self.board:
            print("\t".join([str(p) for p in row]))

    def can_castle(self, king, rook):
        """
        """
        if king.has_moved or rook.has_moved:
            return False
        # IF KING IN CHECK, RETURN FALSE
        # IF PIECES BETWEEN, RETURN FALSE
        return True
    
    def promote_pawn():
        pass
    
    def __getitem__(self, coordinate):
        c = Coord(coordinate)
        return self.board[c.row][c.col]
    
    def __setitem__(self, coordinate, value):
        c = Coord(coordinate)
        self.board[c.row][c.col] = value
        
    def __delitem__(self, coordinate):
        c = Coord(coordinate)
        self.board[c.row][c.col] = None


class InvalidMoveError(Exception):
    pass


class Piece:
    
    def __init__(self, coordinate, color=WHITE):
        # Parse coordinate into tuple
        self.position = Coord(coordinate)
        self.color = color
        self.has_moved = False
        
    @property
    def row(self):
        return self.position.row
    
    @property
    def col(self):
        return self.position.col
        
    @property
    def rank(self):
        return self.position.rank
    
    @property
    def file(self):
        return self.position.file
        
    def move(self, coordinate, **kwargs):
        """
        Takes a coordinate tuple or string as input. Checks if the coordinate 
        constitutes a valid move from the current coordinate. If it is valid, 
        then it updates it's position.
        """
        # Parse coordinate into tuple
        coordinate = Coord(coordinate)
        if coordinate == self.position:
            raise InvalidMoveError("{} is already on {}!".format(self, str(coordinate)))
        # Check move
        dx, dy = coordinate - self.position
        if self.move_is_valid(dx, dy, **kwargs):
            self.position = coordinate
            self.has_moved = True
        else:
            raise InvalidMoveError("{} cannot move to {}!".format(self, str(coordinate)))
        
    def move_is_valid(self, dx, dy, capture=False):
        raise NotImplementedError()
    
    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.color, str(self.position))
    
    def __str__(self):
        return "[{}{}]".format(self.color[0], self.__class__.__name__[0])


class Pawn(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def move_is_valid(self, dx, dy, capture=False, **kwargs):
        """
        Can move forward 2 if it has not yet moved. Otherwise can only move 1.
        If the move is a capture, it can move diagonally
        """
        fwd = COLOR_ORIENTATION[self.color] # fwd = 1 for white, fwd = -1 for black
        # If move is a capture, only allow forward diagonal moves by 1 space
        if capture:
            if abs(dx) == ( fwd * dy ) == 1:
                return True
            else:
                return False
        else:
            # Only allow forward moves by 1 (if has not moved, then allow 2)
            if ( dx == 0 and ( fwd * dy ) == 1 ) or ( not self.has_moved and fwd * dy == 2 ):
                return True
            else:
                return False


class Bishop(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @staticmethod
    def move_is_valid(dx, dy, **kwargs):
        """
        Rank and file must change by same amount
        """
        if ( abs(dx) == abs(dy) ):
            return True
        else:
            return False


class Knight(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @staticmethod
    def move_is_valid(dx, dy, **kwargs):
        """
        Rank or file must change by 2, the other must change by 1
        """
        if sorted([abs(dx), abs(dy)]) == [1, 2]:
            return True
        else:
            return False
        
    def __str__(self):
        return "[{}N]".format(self.color[0]) 


class Rook(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @staticmethod
    def move_is_valid(dx, dy, **kwargs):
        """
        Rank or file can change any amount, but one must not change
        """
        if ( dx != 0 ) ^ ( dy != 0 ): # exclusive or
            return True
        else:
            return False


class Queen(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @staticmethod
    def move_is_valid(dx, dy, **kwargs):
        """
        Can move like Rook or Bishop
        """
        if Bishop.move_is_valid(dx, dy) or Rook.move_is_valid(dx, dy):
            return True
        else:
            return False


class King(Piece):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def move_is_valid(dx, dy, **kwargs):
        """
        Can move 1 square any direction, or diagonally
        """
        if sorted([abs(dx), abs(dy)]) in ([1, 1], [0, 1]):
            return True
        else:
            return False

def main():
    b = Board()
    b.print_board()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    finally:
        input("Press <ENTER> to quit...")