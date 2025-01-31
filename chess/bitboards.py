# -*- coding: utf-8 -*-
"""
Python chess library heavily inspired by https://github.com/niklasf/python-chess
"""
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
    return SQUARES[(mask & -mask).bit_length() - 1]

def msb(mask):
    """
    Get index of the most significant bit.
    """
    return SQUARES[mask.bit_length() - 1]

def scan_forward(mask):
    """
    Iterate through mask, yielding squares from LSB to MSB.
    """
    while mask:
        r = mask & -mask
        yield SQUARES[r.bit_length() - 1]
        mask ^= r

def scan_reversed(mask):
    """
    Iterate through mask, yield squares from MSB to LSB.
    """
    while mask:
        r = mask.bit_length() - 1
        yield SQUARES[r]
        mask ^= SQUARES[r]

def popcount(mask):
    """
    Count the number of filled bits.
    """
    return bin(mask).count("1")


#####################################################################
# ENUMS (Color, Square, Rank, File)
#####################################################################
class Color(int, enum.Enum):
    BLACK = False
    WHITE = True

    @property
    def opponent(self):
        return Color(not self.value)

    @property
    def orientation(self):
        return 1 if self.value else -1


class MaskEnum(int, enum.Enum):
    """
    Special Enum for classes that have associated bit masks.
    Integer value is set to the bit mask to allow bit operations.
    """
    def __new__(cls, value):
        mask = cls.mask_from_value(value)
        obj = int.__new__(cls, mask)
        obj._value_ = value
        return obj

    @staticmethod
    def mask_from_value(value):
        """
        Compute mask value from input enum index.
        """
        raise NotImplementedError()

    def __str__(self):
        """
        Print gives bit-board representation.
        """
        return str(SquareSet(self))


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

    @property
    def is_light(self):
        return bool(MASK_LIGHT_SQUARES & self)

    @property
    def is_dark(self):
        return bool(MASK_DARK_SQUARES & self)

    @property
    def _rank(self):
        return self.value >> 3

    @property
    def _file(self):
        return self.value & 7

    @property
    def rank(self):
        return Rank(self._rank)

    @property
    def file(self):
        return File(self._file)

    def distance(self, other):
        """
        Gets the distance (i.e., the number of king steps) between the squares.
        """
        return max(abs(self._file - other._file), abs(self._rank - other._rank))

    def mirror(self):
        """
        Mirrors the square vertically.
        """
        return SQUARES[self.value ^ 0x38]


class Rank(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 0xFF << (8 * value)

    _1, _2, _3, _4, _5, _6, _7, _8 = range(8)

    @property
    def squares(self):
        for file in FILES:
            yield SQUARES[file.value + self.value * 8]

    @property
    def name(self):
        return self._name_.strip("_")


class File(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 0x0101_0101_0101_0101 << value

    A, B, C, D, E, F, G, H = range(8)

    @property
    def squares(self):
        for rank in RANKS:
            yield SQUARES[self.value + rank.value * 8]

# Provide list for fast lookup by index
SQUARES = list(Square)
RANKS = list(Rank)
FILES = list(File)


#####################################################################
# ATTACK/MOVE GENERATION
#####################################################################
def _sliding_attacks(square, occupied, deltas):
    attacks = MASK_EMPTY

    for delta in deltas:
        i_sq = square.value

        while True:
            i_sq += delta
            if not (0 <= i_sq < 64) or Square.distance(SQUARES[i_sq], SQUARES[i_sq - delta]) > 2:
                break

            attacks |= SQUARES[i_sq]

            if occupied & SQUARES[i_sq]:
                break

    return attacks

def _step_attacks(square, deltas):
    return _sliding_attacks(square, MASK_FULL, deltas)

BB_PAWN_ATTACKS = [[_step_attacks(sq, deltas) for sq in SQUARES] for deltas in [[-7, -9], [7, 9]]]
BB_KNIGHT_ATTACKS = [_step_attacks(sq, [17, 15, 10, 6, -17, -15, -10, -6]) for sq in SQUARES]
BB_KING_ATTACKS = [_step_attacks(sq, [9, 8, 7, 1, -9, -8, -7, -1]) for sq in SQUARES]

def _edges(square):
    return (((Rank._1 | Rank._8) & ~square.rank) |
            ((File.A | File.H) & ~square.file))

def _carry_rippler(mask):
    # Carry-Rippler trick to iterate subsets of mask.
    subset = MASK_EMPTY
    while True:
        yield subset
        subset = (subset - mask) & mask
        if not subset:
            break

def _attack_table(deltas):
    mask_table = []
    attack_table = []

    for square in SQUARES:
        attacks = {}

        mask = _sliding_attacks(square, 0, deltas) & ~_edges(square)
        for subset in _carry_rippler(mask):
            attacks[subset] = _sliding_attacks(square, subset, deltas)

        attack_table.append(attacks)
        mask_table.append(mask)

    return mask_table, attack_table

BB_DIAG_MASKS, BB_DIAG_ATTACKS = _attack_table([-9, -7, 7, 9])
BB_FILE_MASKS, BB_FILE_ATTACKS = _attack_table([-8, 8])
BB_RANK_MASKS, BB_RANK_ATTACKS = _attack_table([-1, 1])

def _rays():
    rays = []
    between = []
    for a in SQUARES:
        rays_row = []
        between_row = []
        for b in SQUARES:
            if BB_DIAG_ATTACKS[a.value][0] & b:
                rays_row.append((BB_DIAG_ATTACKS[a.value][0] & BB_DIAG_ATTACKS[b.value][0]) | a | b)
                between_row.append(BB_DIAG_ATTACKS[a.value][BB_DIAG_MASKS[a.value] & b] & BB_DIAG_ATTACKS[b.value][BB_DIAG_MASKS[b.value] & a])
            elif BB_RANK_ATTACKS[a.value][0] & b:
                rays_row.append(BB_RANK_ATTACKS[a.value][0] | a)
                between_row.append(BB_RANK_ATTACKS[a.value][BB_RANK_MASKS[a.value] & b] & BB_RANK_ATTACKS[b.value][BB_RANK_MASKS[b.value] & a])
            elif BB_FILE_ATTACKS[a.value][0] & b:
                rays_row.append(BB_FILE_ATTACKS[a.value][0] | a)
                between_row.append(BB_FILE_ATTACKS[a.value][BB_FILE_MASKS[a.value] & b] & BB_FILE_ATTACKS[b.value][BB_FILE_MASKS[b.value] & a])
            else:
                rays_row.append(MASK_EMPTY)
                between_row.append(MASK_EMPTY)
        rays.append(rays_row)
        between.append(between_row)
    return rays, between

BB_RAYS, BB_BETWEEN = _rays()

#####################################################################
# SquareSet | Tool for bitboard manipulation and viewing
#####################################################################
class SquareSet:
    """
    Flexible bit board representation. Provides integer-like and set-like
    interfaces for manipulating squares in a bit board.

    >>> print(SquareSet(Square.C3, File.G))
    . . . . . . 1 .
    . . . . . . 1 .
    . . . . . . 1 .
    . . . . . . 1 .
    . . . . . . 1 .
    . . 1 . . . 1 .
    . . . . . . 1 .
    . . . . . . 1 .
    """
    def __init__(self, *args):
        self.mask = MASK_EMPTY
        for mask in args:
            self.mask |= int(mask)

    # Bit operations
    def __and__(self, other):
        r = SquareSet(other)
        r.mask &= self.mask
        return r

    def __iand__(self, other):
        self.mask &= SquareSet(other).mask
        return self

    def __or__(self, other):
        r = SquareSet(other)
        r.mask |= self.mask
        return r

    def __ior__(self, other):
        self.mask |= SquareSet(other).mask
        return self

    def __xor__(self, other):
        r = SquareSet(other)
        r.mask ^= self.mask
        return r

    def __ixor__(self, other):
        self.mask ^= SquareSet(other).mask
        return self

    def __lshift__(self, shift):
        return SquareSet((self.mask << shift))

    def __ilshift__(self, shift):
        self.mask = (self.mask << shift) & MASK_FULL
        return self

    def __rshift__(self, shift):
        return SquareSet(self.mask >> shift)

    def __irshift__(self, shift):
        self.mask >>= shift
        return self

    def __invert__(self):
        return SquareSet(~self.mask)

    # Standard operators
    def __add__(self, other):
        r = SquareSet(other)
        r.mask |= self.mask
        return r

    def __iadd__(self, other):
        self.mask |= SquareSet(other).mask
        return self

    def __sub__(self, other):
        r = SquareSet(other)
        r.mask = self.mask & ~r.mask
        return r

    def __isub__(self, other):
        self.mask &= ~SquareSet(other).mask
        return self

    def __eq__(self, other):
        try:
            return self.mask == int(other)
        except (TypeError, ValueError):
            return NotImplemented

    # Set
    def __contains__(self, other):
        return (other & self.mask) == other

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
            raise KeyError("pop from empty SquareSet")

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
        return not bool(self & ~SquareSet(other))

    def union(self, other):
        return self | other

    def intersection(self, other):
        return self & other

    def difference(self, other):
        return self - other

    def symmetric_difference(self, other):
        return self ^ other

    def copy(self):
        return SquareSet(self.mask)

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
                "1" if square in self else "."
                for square in rank.squares)
            for rank in reversed(Rank))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.mask:#021_x})"


#####################################################################
# HIGHER LEVEL OBJECTS
#####################################################################
class Piece:
    """
    Base class for all chess pieces.
    """
    # Class constants
    value = 0 # Material point value
    attacks = []

    _symbol_lookup = {}
    _unicode_symbol_lookup = {
        "R": u"♖", "r": u"♜",
        "N": u"♘", "n": u"♞",
        "B": u"♗", "b": u"♝",
        "Q": u"♕", "q": u"♛",
        "K": u"♔", "k": u"♚",
        "P": u"♙", "p": u"♟",
    }

    def __init__(self, color=Color.WHITE):
        self.color = Color(color)

    def __init_subclass__(cls, **kwargs):
        """
        Register the class character in the _symbol_lookup.
        """
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_symbol"):
            cls._symbol = cls.__name__[0]
        if not isinstance(cls._symbol, str) or len(cls._symbol) != 1:
            raise AttributeError("_symbol must be a single digit string")
        # Make sure char is not already taken
        cls._symbol = cls._symbol.upper()
        if cls._symbol in Piece._symbol_lookup:
            raise AttributeError(f"_symbol for {cls.__name__} is already taken by {Piece._symbol_lookup[cls._symbol].__name__}")
        # Add to the lookup
        Piece._symbol_lookup[cls._symbol] = cls

    @classmethod
    def from_symbol(cls, symbol):
        """
        Returns the appropriate piece for the input symbol.
        """
        try:
            return cls._symbol_lookup[symbol.upper()](Color(symbol.isupper()))
        except KeyError:
            raise ValueError(f"Unrecognized piece string: {symbol!r}")

    @property
    def name(self):
        """
        Return full piece name.
        """
        return self.__class__.__name__

    def symbol(self, invert_color=False):
        """
        Single character representation of piece.
        Uppercase for WHITE, lowercase for BLACK.
        """
        if self.color ^ invert_color:
            return self._symbol
        return self._symbol.lower()

    def unicode_symbol(self, invert_color=False):
        """
        Unicode representation of piece
        """
        return self._unicode_symbol_lookup[self.symbol(invert_color=invert_color)]

    def __str__(self):
        return self.symbol()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.color.name})"

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.color == other.color and isinstance(other, self.__class__)
        else:
            return NotImplemented

class Pawn(Piece):
    value = 1

class Bishop(Piece):
    value = 3

class Knight(Piece):
    _symbol = "N"
    value = 3

class Rook(Piece):
    value = 5

class Queen(Piece):
    value = 9

class King(Piece):
    value = 5


class BaseBoard:
    """
    A board representing the position of chess pieces. See
    :class:`~chess.Board` for a full board with move generation.
    The board is initialized with the standard chess starting position, unless
    otherwise specified in the optional *board_fen* argument. If *board_fen*
    is ``None``, an empty board is created.
    """
    def __init__(self, fen=None):
        self._pieces = {}
        self._occupied = {
            None: MASK_EMPTY, # ANY COLOR
            Color.WHITE: MASK_EMPTY,
            Color.BLACK: MASK_EMPTY,
        }
        self.clear_board()

        if fen is not None:
            self.set_board_fen(fen)

    def clear_board(self):
        """
        Clears the board of all pieces.
        """
        self._pieces.clear()
        self._promoted = MASK_EMPTY
        for piece_color in self._occupied:
            self._occupied[piece_color] = MASK_EMPTY

    @classmethod
    def standard(cls):
        """
        Returns a new board filled with pieces in the standard starting configuration.
        """
        new = cls()
        new._pieces[Pawn] = Rank._2 | Rank._7
        new._pieces[Knight] = Square.B1 | Square.G1 | Square.B8 | Square.G8
        new._pieces[Bishop] = Square.C1 | Square.F1 | Square.C8 | Square.F8
        new._pieces[Rook] = Square.A1 | Square.H1 | Square.A8 | Square.H8
        new._pieces[Queen] = Square.D1 | Square.D8
        new._pieces[King] = Square.E1 | Square.E8

        new._promoted = MASK_EMPTY

        new._occupied[Color.WHITE] = Rank._1 | Rank._2
        new._occupied[Color.BLACK] = Rank._7 | Rank._8
        new._occupied[None] = new._occupied[Color.WHITE] | new._occupied[Color.BLACK]
        return new

    @property
    def white_squares(self):
        """
        Return SquareSet of locations occupied by white pieces.
        """
        return SquareSet(self._occupied[Color.WHITE])

    @property
    def black_squares(self):
        """
        Return SquareSet of locations occupied by black pieces.
        """
        return SquareSet(self._occupied[Color.BLACK])

    @property
    def all_squares(self):
        """
        Return SquareSet of locations occupied by any pieces.
        """
        return SquareSet(self.occupied)

    @property
    def occupied(self):
        """
        Return mask for all occupied squares.
        """
        return self._occupied[None]

    @property
    def sliding_attackers(self):
        """
        Return mask for all sliding attackers (rank and file attacks).
        """
        return self._pieces_mask(Queen) | self._pieces_mask(Rook)

    @property
    def diagonal_attackers(self):
        """
        Return mask for all diagonal attackers.
        """
        return self._pieces_mask(Queen) | self._pieces_mask(Bishop)

    def clear_mask(self, mask):
        """
        Clear board at all regions covered by the input mask.

        Parameters
        ----------
            mask (int)
        """
        not_mask = ~mask
        for piece_type in self._pieces:
            self._pieces[piece_type] &= not_mask
        for piece_color in self._occupied:
            self._occupied[piece_color] &= not_mask
        self._promoted &= not_mask

    def _pieces_mask(self, piece_type):
        return self._pieces.get(piece_type, MASK_EMPTY)

    def pieces_mask(self, piece_type, color=None):
        """
        Gets mask for pieces of the specified type and color.

        Parameters
        ----------
            piece_type (PieceType):
            color (Color):
        """
        return self._pieces_mask(piece_type) & self._occupied[color]

    def pieces(self, piece_type, color=None):
        """
        Gets squares occupied by pieces of the given type and color.

        Parameters
        ----------
            piece_type (PieceType):
            color (Color):
        """
        return SquareSet(self.pieces_mask(piece_type, color=color))

    def piece_type_at(self, square):
        """
        Get piece type at the specified square. Returns None if the
        square is empty.

        Parameters
        ----------
            square (Square)
        """
        if not square & self.occupied:
            return None  # Early return
        for piece_type, piece_mask in self._pieces.items():
            if square & piece_mask:
                return piece_type
        raise ValueError("Invalid board state")

    def is_piece(self, square, piece_type):
        """
        Check if the given square is the input piece type.
        """
        return bool(square & self._pieces_mask(piece_type))

    def is_color(self, square, color):
        """
        Check if the given square is the input color.
        """
        return bool(square & self._occupied[color])

    def piece_at(self, square):
        """
        Get the piece at the specified square.

        Parameters
        ----------
            square (Square)
        """
        piece_type = self.piece_type_at(square)
        if piece_type:
            piece_color = Color(bool(self._occupied[Color.WHITE] & square))
            return piece_type(piece_color)
        else:
            return None

    def color_at(self, square):
        """
        Gets the color of the piece at the given square.

        Parameters
        ----------
            square (Square)
        """
        if self._occupied[Color.WHITE] & square:
            return Color.WHITE
        elif self._occupied[Color.BLACK] & square:
            return Color.BLACK
        return None

    def pop_piece_at(self, square):
        """
        Remove and return the piece at the given square.

        Parameters
        ----------
            square (Square)
        """
        if not square & self.occupied:
            return None  # Early return
        for piece_type, piece_mask in self._pieces.items():
            if square & piece_mask:
                # Create piece
                piece_color = Color(bool(self._occupied[Color.WHITE] & square))
                piece = piece_type(piece_color)
                # Clear piece square
                self.clear_mask(square)
                return piece

    def set_piece_at(self, square, piece, promoted=False):
        """
        Sets a piece at the given square. Existing pieces at square are cleared.

        Parameters
        ----------
            square (Square)
            piece (Piece)
            promoted (bool)
        """
        # Remove old piece
        self.clear_mask(square)
        # Place new piece
        if isinstance(piece, Piece):
            # XOR faster than OR; equivalent since square has been cleared
            self._pieces[piece.__class__] = self._pieces_mask(piece.__class__) ^ square
            self._occupied[None] ^= square
            self._occupied[piece.color] ^= square
            if promoted:
                self._promoted ^= square

    def king(self, color):
        """
        Finds the king square of the given color. Returns ``None`` if there
        is no king of that color.
        In variants with king promotions, only non-promoted kings are
        considered.

        Parameters
        ----------
            color (Color)
        """
        king_mask = self.pieces_mask(King, color=color) & ~self._promoted
        if king_mask:
            return msb(king_mask)
        return None

    def attacks_mask(self, square):
        """
        Get mask for all outbound attacks from the given square.

        Parameters
        ----------
            square (Square)
        """
        if self.is_piece(square, Pawn):
            color = self.color_at(square)
            return BB_PAWN_ATTACKS[color][square.value]
        elif self.is_piece(square, Knight):
            return BB_KNIGHT_ATTACKS[square.value]
        elif self.is_piece(square, King):
            return BB_KING_ATTACKS[square.value]
        else:
            attacks = 0
            if self.is_piece(square, Bishop) or self.is_piece(square, Queen):
                attacks = BB_DIAG_ATTACKS[square.value][BB_DIAG_MASKS[square.value] & self.occupied]
            if self.is_piece(square, Rook) or self.is_piece(square, Queen):
                attacks |= (BB_RANK_ATTACKS[square.value][BB_RANK_MASKS[square.value] & self.occupied] |
                            BB_FILE_ATTACKS[square.value][BB_FILE_MASKS[square.value] & self.occupied])
            return attacks

    def attacks(self, square):
        """
        Gets the set of attacked squares from the given square.
        There will be no attacks if the square is empty. Pinned pieces are
        still attacking other squares.

        Parameters
        ----------
            square (Square)
        """
        return SquareSet(self.attacks_mask(square))

    def _attackers_mask(self, color, square, occupied):
        rank_pieces = BB_RANK_MASKS[square.value] & occupied
        file_pieces = BB_FILE_MASKS[square.value] & occupied
        diag_pieces = BB_DIAG_MASKS[square.value] & occupied

        attackers = (
            (BB_KING_ATTACKS[square.value] & self._pieces_mask(King)) |
            (BB_KNIGHT_ATTACKS[square.value] & self._pieces_mask(Knight)) |
            (BB_RANK_ATTACKS[square.value][rank_pieces] & self.sliding_attackers) |
            (BB_FILE_ATTACKS[square.value][file_pieces] & self.sliding_attackers) |
            (BB_DIAG_ATTACKS[square.value][diag_pieces] & self.diagonal_attackers) |
            (BB_PAWN_ATTACKS[not color][square.value] & self._pieces_mask(Pawn)))

        return attackers & self._occupied[color]

    def attackers_mask(self, color, square):
        """
        Get mask for all inbound attacks on the given square
        by the given color. Pinned pieces are included.

        Parameters
        ----------
            color (Color)
            square (Square)
        """
        return self._attackers_mask(color, square, self.occupied)

    def is_attacked_by(self, color, square):
        """
        Checks if the given side attacks the given square.
        Pinned pieces still count as attackers. Pawns that can be captured
        en passant are **not** considered attacked.

        Parameters
        ----------
            color (Color)
            square (Square)
        """
        return bool(self.attackers_mask(color, square))

    def attackers(self, color, square):
        """
        Get square set for all inbound attacks on the given square
        by the given color.

        Parameters
        ----------
            color (Color)
            square (Square)
        """
        return SquareSet(self.attackers_mask(color, square))

    def pin_mask(self, color, square):
        """
        Get pin mask from the given square to the king of the given color.
        If there is no pin, then a mask of the entire board is returned.

        Parameters
        ----------
            color (Color)
            square (Square)
        """
        king = self.king(color)
        if king is None:
            return MASK_FULL

        for attacks, sliders in [(BB_FILE_ATTACKS, self.sliding_attackers),
                                 (BB_RANK_ATTACKS, self.sliding_attackers),
                                 (BB_DIAG_ATTACKS, self.diagonal_attackers)]:
            rays = attacks[king.value][0]
            if rays & square:
                sniper_mask = rays & sliders & self._occupied[not color]
                for sniper in scan_reversed(sniper_mask):
                    if BB_BETWEEN[sniper.value][king.value] & (self.occupied | square) == square:
                        return BB_RAYS[king.value][sniper.value]

                break

        return MASK_FULL

    def pin(self, color, square):
        """
        Get square set for pins from the given square to the king of the given color.
        If there is no pin, then a mask of the entire board is returned.

        Parameters
        ----------
            color (Color)
            square (Square)
        """
        return SquareSet(self.pin_mask(color, square))

    def is_pinned(self, color, square):
        """
        Detects if the given square is pinned to the king of the given color.
        """
        return self.pin_mask(color, square) != MASK_FULL

    def board_fen(self, *, promoted=False):
        """
        Gets the board FEN string.
        """
        builder = []
        empty = 0

        for square in SQUARES:
            square = square.mirror()
            piece = self.piece_at(square)

            if not piece:
                empty += 1
            else:
                if empty:
                    builder.append(str(empty))
                    empty = 0
                builder.append(piece.symbol())
                if promoted and square & self.promoted:
                    builder.append("~")

            if square & File.H:
                if empty:
                    builder.append(str(empty))
                    empty = 0

                if square is not Square.H1:
                    builder.append("/")

        return "".join(builder)

    def set_board_fen(self, fen):
        """
        Parses a FEN and sets the board to match it.
        """
        # Compability with set_fen().
        fen = fen.strip()
        if " " in fen:
            raise ValueError(f"expected position part of fen, got multiple parts: {fen!r}")

        # Ensure the FEN is valid.
        rows = fen.split("/")
        if len(rows) != 8:
            raise ValueError(f"expected 8 rows in position part of fen: {fen!r}")

        # Validate each row.
        for row in rows:
            field_sum = 0
            previous_was_digit = False
            previous_was_piece = False

            for c in row:
                if c in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                    if previous_was_digit:
                        raise ValueError(f"two subsequent digits in position part of fen: {fen!r}")
                    field_sum += int(c)
                    previous_was_digit = True
                    previous_was_piece = False
                elif c == "~":
                    if not previous_was_piece:
                        raise ValueError(f"'~' not after piece in position part of fen: {fen!r}")
                    previous_was_digit = False
                    previous_was_piece = False
                elif c.upper() in Piece._symbol_lookup:
                    field_sum += 1
                    previous_was_digit = False
                    previous_was_piece = True
                else:
                    raise ValueError(f"invalid character in position part of fen: {fen!r}")

            if field_sum != 8:
                raise ValueError(f"expected 8 columns per row in position part of fen: {fen!r}")

        # Clear the board.
        self.clear_board()

        # Put pieces on the board.
        square_index = 0
        for c in fen:
            if c in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                square_index += int(c)
            elif c.upper() in Piece._symbol_lookup:
                piece = Piece.from_symbol(c)
                self.set_piece_at(SQUARES[square_index].mirror(), piece)
                square_index += 1
            elif c == "~":
                self._promoted |= SQUARES[square_index - 1].mirror()

    def copy(self):
        """
        Returns a copy of the board.
        """
        board = self.__class__()
        board._pieces = self._pieces.copy()
        board._occupied = self._occupied.copy()
        board._promoted = self._promoted
        return board

    def __copy__(self):
        return self.copy()

    def __iter__(self):
        """
        Yield all pieces on the board. None is yielded for empty squares.
        """
        for square in SQUARES:
            yield self.piece_at(square)

    def __contains__(self, other):
        """
        If other is a Piece, return True if the piece is on the board.
        If other is a Square, return True if the square is filled.
        If other is an int (mask), return True if all masked squares are filled.
        """
        if isinstance(other, Piece): # piece is on the board
            return bool(self.pieces_mask(other.__class__, other.color))
        elif isinstance(other, Square): # square is filled
            return self.piece_type_at(other) is not None
        try:
            return all(self.piece_type_at(square) is not None for square in SquareSet(other))
        except (TypeError, ValueError):
            return NotImplemented

    def __getitem__(self, mask):
        """
        Yield pieces occupying squares within the input mask.
        """
        for square in SquareSet(mask):
            yield self.piece_at(square)

    def __delitem__(self, mask):
        """
        Clear pieces occupying squares within the input mask.
        """
        self.clear_mask(mask)

    def __setitem__(self, mask, piece):
        """
        Set pieces occupying squares within the input mask.
        """
        for square in SquareSet(mask):
            self.set_piece_at(square, piece)

    def __eq__(self, board):
        """
        Return True if all masks other than promotions are equivalent.
        """
        if isinstance(board, BaseBoard):
            return all(
                self._occupied == board._occupied,
                self._pieces == board._pieces,
            )
        else:
            return NotImplemented

    def __repr__(self):
        return f"{self.__class__.__name__}({self.board_fen()!r})"

    def __str__(self):
        """
        Symbolic representation of the entire board.
        """
        builder = []

        for square in SQUARES:
            square = square.mirror()
            piece = self.piece_at(square)

            if piece:
                builder.append(piece.symbol())
            else:
                builder.append(".")

            if square & File.H:
                if square is not Square.H1:
                    builder.append("\n")
            else:
                builder.append(" ")

        return "".join(builder)

    def unicode(self, *, invert_color=False, borders=False):
        """
        Returns a string representation of the board with Unicode pieces.
        Useful for pretty-printing to a terminal.

        Parameters
        ----------
            invert_color (bool): invert color of the Unicode pieces
            borders (bool): show borders and a coordinate margin
        """
        separator = "  " + "+--" * 8 + "+\n"
        builder = []
        for rank in RANKS[::-1]:
            if borders:
                builder.append(separator)
                builder.append(rank.name)

            for file in FILES:
                square = msb(file & rank)

                if borders:
                    builder.append(" |")
                elif file.value > 0:
                    builder.append(" ")

                piece = self.piece_at(square)
                if piece:
                    builder.append(piece.unicode_symbol(invert_color=invert_color))
                elif borders:
                    builder.append(" ")
                else:
                    builder.append(u"·")

            if borders:
                builder.append(" |")

            if borders or rank.value > 0:
                builder.append("\n")

        if borders:
            builder.append(separator)
            builder.append("   a  b  c  d  e  f  g  h")

        return "".join(builder)


class Move:
    """
    Represents a move from a square to a square and possibly the promotion
    piece type. Drops and null moves are supported.

    Parameters
    ----------
        from_square (Square)
        to_square (Square)
        promotion (Piece, None)
        drop (Piece, None)
    """
    __slots__ = ["from_square", "to_square", "promotion", "drop"]

    def __init__(self, from_square, to_square, promotion=None, drop=None):
        self.from_square = from_square
        self.to_square = to_square
        self.promotion = promotion
        self.drop = drop

    def uci(self):
        """
        Gets the UCI string for the move.
        For example, a move from a7 to a8 would be ``a7a8`` or ``a7a8q``
        (if the latter is a promotion to a queen).
        The UCI representation of a null move is ``0000``.
        """
        if self.drop is not None:
            return self.drop.symbol().upper() + "@" + self.to_square.name
        elif self.promotion is not None:
            return (self.from_square.name + self.to_square.name + self.promotion.symbol()).lower()
        elif self.from_square is not None and self.to_square is not None:
            return (self.from_square.name + self.to_square.name).lower()
        else:
            return "0000"

    def __bool__(self):
        return any(
            attr_ is not None for attr_ in
            (self.from_square, self.to_square, self.promotion, self.drop)
        )

    def __eq__(self, other):
        if isinstance(other, Move):
            return (
                self.from_square == other.from_square and
                self.to_square == other.to_square and
                self.promotion == other.promotion and
                self.drop == other.drop)
        else:
            return NotImplemented

    def __repr__(self):
        return f"Move.from_uci({self.uci()!r})"

    def __str__(self):
        return self.uci()

    @classmethod
    def from_uci(cls, uci):
        """
        Parses an UCI string.
        :raises: :exc:`ValueError` if the UCI string is invalid.
        """
        if uci == "0000":
            return cls.null()
        elif len(uci) == 4 and "@" == uci[1]:
            drop = Piece.from_symbol(uci[0])
            square = Square[uci[2:].upper()]
            return cls(square, square, drop=drop)
        elif 4 <= len(uci) <= 5:
            from_square = Square[uci[0:2].upper()]
            to_square = Square[uci[2:4].upper()]
            promotion = Piece.from_symbol(uci[4]) if len(uci) == 5 else None
            if from_square == to_square:
                raise ValueError(f"invalid uci (use 0000 for null moves): {uci!r}")
            return cls(from_square, to_square, promotion=promotion)
        else:
            raise ValueError(f"expected uci string to be of length 4 or 5: {uci!r}")

    @classmethod
    def null(cls):
        """
        Gets a null move.
        A null move just passes the turn to the other side (and possibly
        forfeits en passant capturing). Null moves evaluate to ``False`` in
        boolean contexts.
        """
        return cls(0, 0)
