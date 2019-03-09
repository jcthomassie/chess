# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 09:57:04 2019

@author: jthom
"""

class Board:
    
    def __init__(self, n_files=8, n_ranks=8):
        self.n_files = n_files
        self.n_ranks = n_ranks
        
    def check_file(self, file_int):
        """
        Raise error if file integer is out of bounds
        """
        if not file_int in range(1, self.n_files):
            raise ValueError("File coordinate '{}' is out of bounds!".format(file_int))
        pass
            
    def check_rank(self, rank_int):
        """
        Raise error if rank integer is out of bounds
        """
        if not rank_int in range(1, self.n_ranks):
            raise ValueError("Rank coordinate '{}' is out of bounds!".format(rank_int))
        pass
    
    @staticmethod
    def letter_to_int(file_letter):
        """
        Convert file letter to an integer (1-indexed)
        """
        file_int = ord(file_letter.upper()) - 64
        return file_int
    
    @staticmethod
    def int_to_letter(file_int):
        """
        Convert file integer coordinate to a letter (1->A, 2->B, ...)
        """
        file_letter = chr(64 + file_int)
        return file_letter

    @staticmethod
    def string_to_coord(string):
        """
        Convert string representation of position to integer tuple
        """
        if len(string) < 2:
            raise ValueError("Position string must be at least 2 characters")
        # Convert to integer coordinates
        file_int = Board.letter_to_int(string[0])
        rank_int = int(string[1:])
        return (file_int, rank_int)

    @staticmethod
    def coord_to_string(int_tuple):
        """
        Convert integer coordinate tuple into string representation
        """
        if len(int_tuple) != 2:
            raise ValueError("Coordinate iterable must be length 2!")
        # Convert to string representation
        file = Board.int_to_letter(int_tuple[0])
        rank = int_tuple[1]
        return "{}{:d}".format(file, rank)

class Piece:
    
    def __init__(self, board, coordinate):
        # Parse coordinate into file and rank
        if isinstance(coordinate, str):
            coordinate = board.string_to_coord(coordinate)
        self.file = coordinate[0]
        self.rank = coordinate[1]
        # Check if file and rank are in bounds
        board.check_file(self.file)
        board.check_rank(self.rank)
        
    @property
    def valid_squares(self):
        raise NotImplementedError()
        
    def move(self, coordinate):
        raise NotImplementedError()
        
    @property
    def pos_string(self):
        return "{}{}".format(self.file, self.rank)
    
    @property
    def pos_tuple(self):
        return (self.file, self.rank)
    
    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.coordinate)
        
if __name__ == "__main__":
    try:
        b = Board()
        res = input("Input coord(q to quit):")
        while res != "q":
            print(b.string_to_coord(res))
            res = input("Input coord(q to quit):")
    except Exception as e:
        print(e)
        input("Press <ENTER> to quit...")
        