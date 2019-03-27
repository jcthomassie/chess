import os
import itertools
import pygame
from pygame import gfxdraw

from chess import core

# COLORS
BLACK_RGB = (181, 136, 99) # brown
WHITE_RGB = (240, 217, 181) # tan
BG_RGB = (0, 0, 0) # black

TARGET_RGB = (49, 175, 80) # pale green
CHECK_RGB = (255, 68, 68) # red
ARROW_RGB = (49, 175, 80) # green

# GEOMETRY
SQUARE_PIX = 81 # pixels
MARGIN_PIX = 10 # pixels

def square_center(row, col, flipped=False):
    if not flipped:
        x = MARGIN_PIX + (col + 1/2) * SQUARE_PIX
        y = MARGIN_PIX + (row + 1/2) * SQUARE_PIX
    else:
        x = MARGIN_PIX + ((core.N_FILES - 1 - col) + 1/2) * SQUARE_PIX
        y = MARGIN_PIX + ((core.N_RANKS - 1 - row) + 1/2) * SQUARE_PIX
    return round(x), round(y)

def square_corner(row, col, flipped=False):
    if not flipped:
        x = MARGIN_PIX + col * SQUARE_PIX
        y = MARGIN_PIX + row * SQUARE_PIX
    else:
        x = MARGIN_PIX + (core.N_FILES - 1 - col) * SQUARE_PIX
        y = MARGIN_PIX + (core.N_RANKS - 1 - row) * SQUARE_PIX
    return x, y

def pix_to_square(x, y, flipped=False):
    if not flipped:
        row = ( y - MARGIN_PIX ) // SQUARE_PIX
        col = ( x - MARGIN_PIX ) // SQUARE_PIX
    else:
        row = core.N_RANKS - 1 - ( y - MARGIN_PIX ) // SQUARE_PIX
        col = core.N_FILES - 1 - ( x - MARGIN_PIX ) // SQUARE_PIX
    # Restrict to board
    row = min( max(row, 0), core.N_RANKS - 1 )
    col = min( max(col, 0), core.N_FILES - 1 )
    return core.Square(row, col)

class PieceIcon(pygame.sprite.Sprite):
    """
    Chess piece sprite.
    """
    def __init__(self, chess_piece, flipped=False):
        super(PieceIcon, self).__init__()
        im = self.get_image(chess_piece)
        self.image = pygame.transform.smoothscale(im, (SQUARE_PIX, SQUARE_PIX))
        self.rect = self.image.get_rect()
        self.layer = 0

        self.piece_color = chess_piece.color
        self.piece_type = type(chess_piece)
        self.set_square(chess_piece.square, flipped=flipped)

    @staticmethod
    def get_image(chess_piece):
        piece_color = chess_piece.color_name.lower()
        piece_name = type(chess_piece).__name__.lower()
        image_dir = os.path.join(os.path.dirname(__file__), "icons")
        image_path = os.path.join(image_dir, "{}_{}.png".format( piece_name, piece_color ))
        return pygame.image.load(image_path)

    @property
    def row(self):
        return self.square.row

    @property
    def col(self):
        return self.square.col

    def set_square(self, square, flipped=False):
        self.square = square
        self.snap_to_square(flipped=flipped)

    def snap_to_square(self, flipped=False):
        self.rect.x, self.rect.y = square_corner(self.row, self.col, flipped=flipped)
        return

    def nearest_square(self, flipped=False):
        return pix_to_square(self.rect.centerx, self.rect.centery, flipped=flipped)

    def drag(self):
        pos = pygame.mouse.get_pos()
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]


class BoardIcon(pygame.Surface):
    def __init__(self, width, height, square_size):
        super(BoardIcon, self).__init__((width, height))

        colors = itertools.cycle((WHITE_RGB, BLACK_RGB))

        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                rect = (x, y, square_size, square_size)
                pygame.draw.rect(self, next(colors), rect)
            next(colors)


class Arrow:
    pass


class Game:

    def __init__(self, board):
        # Connect board/game engine
        self.board = board
        # Create display
        self.flipped = False
        board_width = SQUARE_PIX * len(self.board.board[0])
        board_height = SQUARE_PIX * len(self.board.board)
        dimensions = (board_width + 2 * MARGIN_PIX, board_height + 2 * MARGIN_PIX)
        self.screen = pygame.display.set_mode(dimensions)
        # Generate images
        self.board_icon = BoardIcon(board_width, board_height, SQUARE_PIX)
        self.sprites = pygame.sprite.LayeredUpdates()
        for piece in self.board.piece_generator():
            self.sprites.add( PieceIcon(piece), flipped=self.flipped )
        self.sprite_lookup = { piece.square: piece for piece in self.sprites.get_sprites_from_layer(0) }

        self.latched = None
        return

    def draw_square_highlight(self, square, color):
        corner = square_corner(square.row, square.col, flipped=self.flipped)
        rect = (*corner, SQUARE_PIX, SQUARE_PIX)
        pygame.draw.rect(self.screen, color, rect)

    def draw_corner_highlight(self, square):
        corner = square_corner(square.row, square.col, flipped=self.flipped)
        for dx, dy in itertools.product([-1, 1], repeat=2):
            p0 = [corner[0], corner[1]]
            if dx == 1:
                p0[0] += SQUARE_PIX - 1
            if dy == 1:
                p0[1] += SQUARE_PIX - 1
            p1 = [p0[0] - dx * 14, p0[1]]
            p2 = [p0[0], p0[1] - dy * 14]
            pygame.draw.polygon(self.screen, TARGET_RGB, [p0, p1, p2])
            pygame.draw.aaline(self.screen, TARGET_RGB, p1, p2)

    def draw_target_dot(self, square):
        coord = square_center(square.row, square.col, flipped=self.flipped)
        radius = 9
        gfxdraw.aacircle(self.screen, *coord, radius, TARGET_RGB)
        gfxdraw.filled_circle(self.screen, *coord, radius, TARGET_RGB)

    def draw_move_arrow(self, from_square, to_square):
        pass

    def get_moveable_pieces(self):
        """
        Return a list of piece sprites that can be moved in the current game
        state.
        """
        moveable = [ ]
        for piece in self.sprites.get_sprites_from_layer(0):
            if piece.square in self.board.allowed_moves:
                moveable.append(piece)
        return moveable

    def show_moves(self, chess_piece):
        if chess_piece.square in self.board.allowed_moves:
            for target in self.board.allowed_moves[chess_piece.square]:
                if self.board[target] is None:
                    self.draw_target_dot(target)
                else:
                    self.draw_corner_highlight(target)
        return

    def grab(self, event):
        """
        Mouse down event.
        """
        for piece in self.sprites.get_sprites_from_layer(0):
            if isinstance(self.latched, PieceIcon):
                break
            elif piece.piece_color != self.board.to_move:
                continue
            elif piece.rect.collidepoint(event.pos) == True:
                self.sprites.move_to_front(piece)
                self.latched = piece
        return

    def drop(self):
        if isinstance(self.latched, PieceIcon):
            self.latched.snap_to_square(flipped=self.flipped)
            self.latched = None

    def finish_move(self, event):
        """
        Mouse up event.
        """
        if isinstance(self.latched, PieceIcon):
            from_square = self.latched.square
            to_square = self.latched.nearest_square(flipped=self.flipped)
            self.attempt_move(from_square, to_square)
        self.drop()
        return

    def move_sprites(self, move):
        """
        Update sprites using move info.
        """
        # Update sprites
        for piece in move.removals:
            sprite = self.sprite_lookup[piece.square]
            self.sprites.remove(sprite)
            del self.sprite_lookup[piece.square]
        for piece in move.additions:
            sprite = PieceIcon(piece, flipped=self.flipped)
            self.sprites.add( sprite )
            self.sprite_lookup[piece.square] = sprite

    def attempt_move(self, from_square, to_square):
        try:
            move = core.Move.from_squares(from_square, to_square, self.board)
            self.board.push_move(move)
            if self.board.game_over():
                print("GAME OVER!")
            self.move_sprites(move)
            self.flip_board(color=self.board.to_move)
        except:
            pass
        return

    def undo_move(self):
        if len(self.board.move_history) > 0:
            last_move = self.board.move_history[-1]
            self.move_sprites(last_move.inverse())
            self.board.undo_move()

    def flip_board(self, color=None):
        if color == core.WHITE:
            self.flipped = False
        elif color == core.BLACK:
            self.flipped = True
        else:
            self.flipped = not self.flipped
        for piece in self.sprites:
            piece.snap_to_square(flipped=self.flipped)

    def loop(self):
        """
        Run the game loop
        """
        game_clock = pygame.time.Clock()
        game_exit = False
        while not game_exit:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.latched is None:
                        self.grab(event)
                    else:
                        self.drop()
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.finish_move(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:
                        self.undo_move()
                    if event.key == pygame.K_f:
                        self.flip_board()

            # Draw board
            self.screen.fill(BG_RGB)
            self.screen.blit(self.board_icon, (MARGIN_PIX, MARGIN_PIX))
            if self.board.check:
                self.draw_square_highlight(self.board.find_king().square, CHECK_RGB)
            if self.board.winner is not None:
                self.draw_square_highlight(self.board.find_king(self.board.winner).square, ARROW_RGB)

            # Update and draw pieces
            if isinstance(self.latched, PieceIcon):
                self.latched.drag()
                self.show_moves(self.latched)
            self.sprites.draw(self.screen)

            pygame.display.flip()
            game_clock.tick(60)
        return

    def __enter__(self):
        pygame.init()
        pygame.display.set_caption("Chess")
        return self

    def __exit__(self, *args):
        pygame.quit()