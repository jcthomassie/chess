import os
import itertools
import pygame

# COLORS
BLACK_RGB = (181, 136, 99)
WHITE_RGB = (240, 217, 181)
BG_RGB = (0, 0, 0)

# GEOMETRY
SQUARE_PIX = 80 # pixels
MARGIN_PIX = 10 # pixels

class PieceIcon(pygame.sprite.Sprite):
    """
    Chess piece sprite.
    """
    def __init__(self, chess_piece):
        super(PieceIcon, self).__init__()

        piece_color = chess_piece.color_name.lower()
        piece_name = type(chess_piece).__name__.lower()
        image_dir = os.path.join(os.path.dirname(__file__), "icons")
        image_path = os.path.join(image_dir, "{}_{}.png".format( piece_name, piece_color ))
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.transform.smoothscale(pygame.image.load(image_path), (SQUARE_PIX, SQUARE_PIX))
        self.rect = self.image.get_bounding_rect()

        self.set_square(chess_piece)

    def set_square(self, chess_piece):
        self.row = chess_piece.row
        self.col = chess_piece.col
        self.snap_to_square()

    def snap_to_square(self):
        self.rect.x = MARGIN_PIX + self.col * SQUARE_PIX
        self.rect.y = MARGIN_PIX + self.row * SQUARE_PIX

    def nearest_square(self):
        row = ( self.rect.x - MARGIN_PIX ) // SQUARE_PIX
        col = ( self.rect.y - MARGIN_PIX ) // SQUARE_PIX
        return row, col


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
        self.board = board

        # Create screen
        board_width = SQUARE_PIX * len(self.board.board[0])
        board_height = SQUARE_PIX * len(self.board.board)
        pygame.display.set_caption("Chess")
        dimensions = (board_width + 2 * MARGIN_PIX, board_height + 2 * MARGIN_PIX)
        self.screen = pygame.display.set_mode(dimensions)

        # Generate images
        self.board_icon = BoardIcon(board_width, board_height, SQUARE_PIX)
        self.piece_sprites = pygame.sprite.Group()
        for piece in self.board.piece_generator():
            self.piece_sprites.add( PieceIcon(piece) )
        return

    def loop(self):
        game_exit = False
        while not game_exit:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print("Mouse down")
                elif event.type == pygame.MOUSEBUTTONUP:
                    print("Mouse up")

            # Draw board and pieces
            self.screen.fill(BG_RGB)
            self.screen.blit(self.board_icon, (MARGIN_PIX, MARGIN_PIX))
            self.piece_sprites.draw(self.screen)

            pygame.display.flip()
        return

    def __enter__(self):
        pygame.init()
        return self

    def __exit__(self, *args):
        pygame.quit()