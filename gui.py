import pygame
import itertools
import chess

# COLORS
BLACK = (181, 136, 99)
WHITE = (240, 217, 181)
BG = pygame.Color("black")

# GEOMETRY
SQUARE_SIZE = 80 # pixels
MARGIN = 60 # pixels
BOARD_WIDTH = SQUARE_SIZE * chess.N_FILES
BOARD_HEIGHT = SQUARE_SIZE * chess.N_RANKS

class Piece(pygame.sprite.Sprite):
    def __init__(self, chess_piece):
        super(Piece, self).__init__()

        piece_color = chess.COLOR_NAME[chess_piece.color].lower()
        piece_name = type(chess_piece).__name__.lower()
        image_path = "icons/{}_{}.png".format( piece_name, piece_color )

        x = MARGIN + chess_piece.col * SQUARE_SIZE
        y = MARGIN + chess_piece.row * SQUARE_SIZE
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.rect = (x, y, SQUARE_SIZE, SQUARE_SIZE)
        self.image = pygame.transform.smoothscale(pygame.image.load(image_path), (SQUARE_SIZE, SQUARE_SIZE))

    def place(self, x, y):
        self.rect.x = x
        self.rect.y = y

def draw_board():

    colors = itertools.cycle((WHITE, BLACK))
    background = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))

    for y in range(0, BOARD_HEIGHT, SQUARE_SIZE):
        for x in range(0, BOARD_WIDTH, SQUARE_SIZE):
            rect = (x, y, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(background, next(colors), rect)
        next(colors)
    return background

def main():
    pygame.init()

    try:
        dimensions = (BOARD_WIDTH + 2 * MARGIN, BOARD_HEIGHT + 2 * MARGIN)
        screen = pygame.display.set_mode(dimensions)
        background = draw_board()

        chess_game = chess.Board()
        piece_list = [ Piece(p) for p in chess_game.piece_generator() ]

        clock = pygame.time.Clock()

        game_exit = False
        while not game_exit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True

            screen.fill(BG)
            screen.blit(background, (MARGIN, MARGIN))

            for piece in piece_list:
                screen.blit(piece.image, piece.rect)

            pygame.display.flip()
            clock.tick(30)
    except Exception as e:
        print(e)

    pygame.quit()
    return

if __name__ == "__main__":
    main()