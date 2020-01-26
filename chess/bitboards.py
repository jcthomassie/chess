# -*- coding: utf-8 -*-
import enum
import math

#####################################################################
# CORE FUNCTIONS / CONSTANTS
#####################################################################
MASK_EMPTY = 0
MASK_FULL = 0xFFFF_FFFF_FFFF_FFFF

MASK_LIGHT_SQUARES = 0x55AA_55AA_55AA_55AA
MASK_DARK_SQUARES = 0xAA55_AA55_AA55_AA55

def lsb(mask):
    """
    Get index of the least significant bit.
    """
    return Square((mask & -mask).bit_length() - 1)

def msb(mask):
    """
    Get index of the most significant bit.
    """
    return Square(mask.bit_length() - 1)

def scan_forward(mask):
    """
    Iterate through mask, yielding squares from LSB to MSB.
    """
    while mask:
        r = mask & -mask
        yield Square(r.bit_length() - 1)
        mask ^= r

def scan_reversed(mask):
    """
    Iterate through mask, yield squares from MSB to LSB.
    """
    while mask:
        r = mask.bit_length() - 1
        yield Square(r)
        mask ^= Square(r)

def popcount(mask):
    """
    Count the number of filled bits.
    """
    return bin(mask).count("1")


#####################################################################
# ENUMS (SQUARE, RANK, FILE)
#####################################################################
class MaskEnum(int, enum.Enum):
    """
    Special enum for classes that have associated bit masks.
    Integer value is set to the bit mask to allow bit operations.
    """
    def __new__(cls, value):
        mask = cls.mask_from_value(value)
        obj = int.__new__(cls, mask)
        obj._value_ = value
        return obj

    @staticmethod
    def mask_from_value(value):
        raise NotImplementedError()

    @property
    def bit_board(self):
        return BitBoard(self)


class Square(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 1 << value

    A1, B1, C1, D1, E1, F1, G1, H1, \
    A2, B2, C2, D2, E2, F2, G2, H2, \
    A3, B3, C3, D3, E3, F3, G3, H3, \
    A4, B4, C4, D4, E4, F4, G4, H4, \
    A5, B5, C5, D5, E5, F5, G5, H5, \
    A6, B6, C6, D6, E6, F6, G6, H6, \
    A7, B7, C7, D7, E7, F7, G7, H7, \
    A8, B8, C8, D8, E8, F8, G8, H8 = range(64)

    @property
    def rank(self):
        return Rank(self // 8)

    @property
    def file(self):
        return File(self % 8)

    @property
    def is_light(self):
        return bool(MASK_LIGHT_SQUARES & self)

    @property
    def is_dark(self):
        return bool(MASK_DARK_SQUARES & self)

    @classmethod
    def light(cls):
        """
        Yield light squares.
        """
        return scan_forward(MASK_LIGHT_SQUARES)

    @classmethod
    def dark(cls):
        """
        Yield dark squares.
        """
        return scan_forward(MASK_DARK_SQUARES)


class Rank(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 0xFF << (8 * value)

    _1, _2, _3, _4, _5, _6, _7, _8 = range(8)

    @property
    def squares(self):
        for file in File:
            yield Square(file.value + self.value * 8)


class File(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 0x0101_0101_0101_0101 << value

    A, B, C, D, E, F, G, H = range(8)

    @property
    def bit_board(self):
        return BitBoard(self)

    @property
    def squares(self):
        for rank in Rank:
            yield Square(self.value + rank.value * 8)


#####################################################################
# BIT BOARD
#####################################################################
class BitBoard:
    """
    Bit masks
    """
    def __init__(self, value=MASK_EMPTY):
        self.mask = MASK_FULL & int(value)

    # Bit operations
    def __and__(self, other):
        r = BitBoard(other)
        r.mask &= self.mask
        return r

    def __iand__(self, other):
        self.mask &= BitBoard(other).mask
        return self

    def __or__(self, other):
        r = BitBoard(other)
        r.mask |= self.mask
        return r

    def __ior__(self, other):
        self.mask |= BitBoard(other).mask
        return self

    def __xor__(self, other):
        r = BitBoard(other)
        r.mask ^= self.mask
        return r

    def __ixor__(self, other):
        self.mask ^= BitBoard(other).mask
        return self

    def __lshift__(self, shift):
        return BitBoard((self.mask << shift))

    def __ilshift__(self, shift):
        self.mask = (self.mask << shift) & MASK_FULL
        return self

    def __rshift__(self, shift):
        return BitBoard(self.mask >> shift)

    def __irshift__(self, shift):
        self.mask >>= shift
        return self

    def __invert__(self):
        return BitBoard(~self.mask)

    # Standard operators
    def __add__(self, other):
        r = BitBoard(other)
        r.mask |= self.mask
        return r

    def __iadd__(self, other):
        self.mask |= BitBoard(other).mask
        return self

    def __sub__(self, other):
        r = BitBoard(other)
        r.mask = self.mask & ~r.mask
        return r

    def __isub__(self, other):
        self.mask &= ~BitBoard(other).mask
        return self

    def __eq__(self, other):
        try:
            return self.mask == int(other)
        except (TypeError, ValueError):
            return NotImplemented

    # Set
    def __contains__(self, square):
        return bool(square & self.mask)

    def __iter__(self):
        return scan_forward(self.mask)

    def __reversed__(self):
        return scan_reversed(self.mask)

    def __len__(self):
        return popcount(self.mask)

    # MutableSet
    def add(self, square):
        """Adds a square to the set."""
        self.mask |= square

    def discard(self, square):
        """Discards a square from the set."""
        self.mask &= ~square

    def update(self, *others):
        for other in others:
            self |= other

    def intersection_update(self, *others):
        for other in others:
            self &= other

    def difference_update(self, other):
        self -= other

    def symmetric_difference_update(self, other):
        self ^= other

    def remove(self, square):
        """Removes a square from the set"""
        if self.mask & square:
            self.mask ^= square
        else:
            raise KeyError(square)

    def pop(self):
        """Removes MSB square from the set and returns it"""
        if not self.mask:
            raise KeyError("pop from empty BitBoard")

        square = msb(self.mask)
        self.mask &= (self.mask - 1)
        return square

    def clear(self):
        self.mask = MASK_EMPTY

    # frozenset
    def isdisjoint(self, other):
        """Test if the square sets are disjoint."""
        return not bool(self & other)

    def issubset(self, other):
        """Test if this square set is a subset of another."""
        return not bool(~self & other)

    def issuperset(self, other):
        """Test if this square set is a superset of another."""
        return not bool(self & ~BitBoard(other))

    def union(self, other):
        return self | other

    def intersection(self, other):
        return self & other

    def difference(self, other):
        return self - other

    def symmetric_difference(self, other):
        return self ^ other

    def copy(self):
        return BitBoard(self.mask)

    # Other types
    def __index__(self):
        return self.mask

    def __int__(self):
        return self.mask

    def __bool__(self):
        return bool(self.mask)

    def __str__(self):
        return "\n".join(
            " ".join(
                "+" if square in self else "."
                for square in rank.squares)
            for rank in reversed(Rank))

    def __repr__(self):
        return f"Board({self.mask:#021_x})"
