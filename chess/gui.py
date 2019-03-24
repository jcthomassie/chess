import os
import itertools
import pygame

from chess import core

# COLORS
BLACK_RGB = (181, 136, 99) # brown
WHITE_RGB = (240, 217, 181) # tan
BG_RGB = (0, 0, 0) # black

TARGET_RGB = (132, 132, 132) # grey
CHECK_RGB = () # red
ARROW_RGB = () # green

# GEOMETRY
SQUARE_PIX = 80 # pixels
MARGIN_PIX = 10 # pixels

def square_center(row, col):
    x = MARGIN_PIX + (col + 1/2) * SQUARE_PIX
    y = MARGIN_PIX + (row + 1/2) * SQUARE_PIX
    return round(x), round(y)

class PieceIcon(pygame.sprite.Sprite):
    """
    Chess piece sprite.
    """
    def __init__(self, chess_piece):
        super(PieceIcon, self).__init__()
        im = self.get_image(chess_piece)
        self.image = pygame.transform.smoothscale(im, (SQUARE_PIX, SQUARE_PIX))
        self.rect = self.image.get_rect()

        self.piece_color = chess_piece.color
        self.piece_type = type(chess_piece)
        self.set_square(chess_piece.square)

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

    def set_square(self, square):
        self.square = square
        self.snap_to_square()

    def snap_to_square(self):
        self.rect.x = MARGIN_PIX + self.col * SQUARE_PIX
        self.rect.y = MARGIN_PIX + self.row * SQUARE_PIX

    def nearest_square(self):
        row = ( self.rect.centery - MARGIN_PIX ) // SQUARE_PIX
        col = ( self.rect.centerx - MARGIN_PIX ) // SQUARE_PIX
        return core.Square(row, col)

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

class Game:

    def __init__(self, board):
        # Connect board/game engine
        self.board = board
        # Create display
        board_width = SQUARE_PIX * len(self.board.board[0])
        board_height = SQUARE_PIX * len(self.board.board)
        dimensions = (board_width + 2 * MARGIN_PIX, board_height + 2 * MARGIN_PIX)
        self.screen = pygame.display.set_mode(dimensions)
        # Generate images
        self.board_icon = BoardIcon(board_width, board_height, SQUARE_PIX)
        self.piece_sprites = pygame.sprite.Group()
        for piece in self.board.piece_generator():
            self.piece_sprites.add( PieceIcon(piece) )
        self.sprite_lookup = { piece.square: piece for piece in self.piece_sprites }

        self.latched = None
        return

    def draw_target_dot(self, square):
        coord = square_center(square.row, square.col)
        radius = SQUARE_PIX // 8
        pygame.draw.circle(self.screen, TARGET_RGB, coord, radius, 0)

    def draw_move_arrow(self, from_square, to_square):
        pass

    def get_moveable_pieces(self):
        """
        Return a list of piece sprites that can be moved in the current game
        state.
        """
        moveable = [ ]
        for piece in self.piece_sprites:
            if piece.square in self.board.allowed_moves:
                moveable.append(piece)
        return moveable

    def show_moves(self, chess_piece):
        for target in self.board.allowed_moves[chess_piece.square]:
            self.draw_target_dot(target)
        return

    def start_move(self, event):
        """
        Mouse down event.
        """
        for piece in self.get_moveable_pieces():
            if isinstance(self.latched, PieceIcon):
                break
            elif piece.rect.collidepoint(event.pos) == True:
                self.latched = piece
        return

    def finish_move(self, event):
        """
        Mouse up event.
        """
        if isinstance(self.latched, PieceIcon):
            from_square = self.latched.square
            to_square = self.latched.nearest_square()
            self.attempt_move(from_square, to_square)
            self.latched.snap_to_square()
        self.latched = None
        return

    def move_sprites(self, move):
        """
        Update sprites using move info.
        """
        # Update sprites
        for piece in move.removals:
            sprite = self.sprite_lookup[piece.square]
            self.piece_sprites.remove(sprite)
            del self.sprite_lookup[piece.square]
        for piece in move.additions:
            sprite = PieceIcon(piece)
            self.piece_sprites.add( sprite )
            self.sprite_lookup[piece.square] = sprite

    def attempt_move(self, from_square, to_square):
        try:
            move = core.Move.from_squares(from_square, to_square, self.board)
            self.board.push_move(move)
            self.move_sprites(move)
        except core.InvalidMoveError as e:
            print("{}: {}".format(e.__class__.__name__, e))
        return

    def undo_move(self):
        if len(self.board.move_history) > 0:
            last_move = self.board.move_history[-1]
            self.move_sprites(last_move.inverse())
            self.board.undo_move()

    def loop(self):
        """
        Run the game loop
        """
        game_exit = False
        while not game_exit:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.start_move(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.finish_move(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u:
                        self.undo_move()
            # Update pieces
            if isinstance(self.latched, PieceIcon):
                self.latched.drag()

            # Draw board
            self.screen.fill(BG_RGB)
            self.screen.blit(self.board_icon, (MARGIN_PIX, MARGIN_PIX))
            self.piece_sprites.draw(self.screen)
            if isinstance(self.latched, PieceIcon):
                self.show_moves(self.latched)

            pygame.display.flip()
        return

    def __enter__(self):
        pygame.init()
        pygame.display.set_caption("Chess")
        return self

    def __exit__(self, *args):
        pygame.quit()