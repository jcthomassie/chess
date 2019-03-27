# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 10:45:07 2019

@author: jctho_000
"""
import argparse
from chess import core, gui

def main():
    # Parse commandline args
    parser = argparse.ArgumentParser(description="Play a chess game.")

    parser.add_argument("fen", nargs="?", default="Standard",
                        help="Starting position FEN string")
    args = parser.parse_args()

    # Setup board and GUI
    board = core.Board(args.fen)
    with gui.Game(board) as game:
        game.loop()
    return

if __name__ == "__main__":
    main()