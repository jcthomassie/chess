# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 10:45:07 2019

@author: jctho_000
"""

from chess import core, gui

def main():
    board = core.Board("Standard")
    with gui.Game(board) as game:
        game.loop()
    return

if __name__ == "__main__":
    main()