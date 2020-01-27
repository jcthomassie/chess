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


class MaskEnum(enum.IntEnum):
    """
    Special IntEnum for classes that have associated bit masks.
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
        return SquareSet(self)


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

    def mirror(self, square):
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


class File(MaskEnum):
    @staticmethod
    def mask_from_value(value):
        return 0x0101_0101_0101_0101 << value

    A, B, C, D, E, F, G, H = range(8)

    @property
    def bit_board(self):
        return SquareSet(self)

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

    def symbol(self):
        """
        Single character representation of piece.
        Uppercase for WHITE, lowercase for BLACK.
        """
        if self.color is Color.BLACK:
            return self._symbol.lower()
        return self._symbol

    def unicode_symbol(self):
        """
        Unicode representation of piece
        """
        return self._unicode_symbol_lookup[self.symbol()]

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
    def __init__(self):
        self._pieces = {}
        self._occupied = {
            None: MASK_EMPTY, # ANY COLOR
            Color.WHITE: MASK_EMPTY,
            Color.BLACK: MASK_EMPTY,
        }
        self.clear_board()

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
        return SquareSet(self._occupied[None])

    @property
    def occupied_mask(self):
        """
        Return mask for all occupied squares.
        """
        return self._occupied[None]

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
        if not square & self._occupied[None]:
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
        if not square & self._occupied[None]:
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
                attacks = BB_DIAG_ATTACKS[square.value][BB_DIAG_MASKS[square.value] & self._occupied[None]]
            if self.is_piece(square, Rook) or self.is_piece(square, Queen):
                attacks |= (BB_RANK_ATTACKS[square.value][BB_RANK_MASKS[square.value] & self._occupied[None]] |
                            BB_FILE_ATTACKS[square.value][BB_FILE_MASKS[square.value] & self._occupied[None]])
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

        queens_and_rooks = self._pieces_mask(Queen) | self._pieces_mask(Rook)
        queens_and_bishops = self._pieces_mask(Queen) | self._pieces_mask(Bishop)

        attackers = (
            (BB_KING_ATTACKS[square.value] & self._pieces_mask(King)) |
            (BB_KNIGHT_ATTACKS[square.value] & self._pieces_mask(Knight)) |
            (BB_RANK_ATTACKS[square.value][rank_pieces] & queens_and_rooks) |
            (BB_FILE_ATTACKS[square.value][file_pieces] & queens_and_rooks) |
            (BB_DIAG_ATTACKS[square.value][diag_pieces] & queens_and_bishops) |
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
        return self._attackers_mask(color, square, self._occupied[None])

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
