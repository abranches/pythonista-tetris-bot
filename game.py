#!/usr/bin/python
import sys
import time
import os
import traceback
# keyboard input
import tty
import termios

from log import LOG
from blocks import *

from board import TetrisBoard
from engine import TetrisEngine, GameState
from ai import TetrisAI

LEFT_KEY = '\x1b[D'
RIGHT_KEY = '\x1b[C'
UP_KEY = '\x1b[A'
DOWN_KEY = '\x1b[B'
DROP_KEY = ' '

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        #return sys.stdin.read(1)
        return os.read(fd, 4)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

class TetrisGame:
    def __init__(self):
        self.game_state = GameState(TetrisBoard())
        self.engine = TetrisEngine(self.game_state)
        self.ai = TetrisAI(self.engine)

    def run_main(self):
        self.engine.start()

        while not self.engine.running():
            pass

        self.ai.play()

        while self.engine.running():
            try:
                c = getch()
                if c == LEFT_KEY:
                    self.engine.move_left()
                if c == RIGHT_KEY:
                    self.engine.move_right()
                if c == DOWN_KEY:
                    LOG.debug("XXX: %s" % self.engine.move_down())
                if c == DROP_KEY:
                    LOG.debug("XXX: %s" % self.engine.drop_block())
                if c == UP_KEY:
                    self.engine.rotate()
            except KeyboardInterrupt:
                self.engine.stop()

if __name__ == "__main__":
    game = TetrisGame()
    try:
        game.run_main()
    except:
        LOG.debug("Main thread just crashed!!", exc_info=True)
        traceback.print_exc()
        game.engine.stop()
