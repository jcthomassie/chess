# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 10:45:07 2019

@author: jctho_000
"""
import argparse
from chess import core, gui

if __name__ == "__main__":
    # Define commandline parameters
    parser = argparse.ArgumentParser(description="Pythonic chess commandline and GUI interface")
    parser.add_argument(
        "fen",
        nargs="?",
        default="Standard",
        help="Starting position FEN string"
    )
    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="run performance test"
    )
    parser.add_argument(
        "-c", "--command-line",
        action="store_true",
        help="play chess via commandline instead of the GUI"
    )

    # Parse arguments
    args = parser.parse_args()
    if args.test:
        core.test()
    else:
        board = core.Board(args.fen)
        if args.command_line:
            board.play_game()
        else:
            with gui.Game(board) as game:
                game.loop()
