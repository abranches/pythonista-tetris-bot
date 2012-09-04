from copy import deepcopy

from blocks import *
from log import LOG

class TetrisBoard:
    def __init__(self, height=20, width=10):
        self.height = height
        self.width = width
        self.board = []

        self._start_new_board()

    def copy(self):
        return deepcopy(self)

    def _start_new_board(self):
        self.board = []
        for i in xrange(self.height):
            self.board.append( [None,]*self.width )

    def block_at(self, x, y):
        return self.board[y][x]

    def clear_line(self, y_line):
        for y in range(y_line, self.height-1):
            self.board[y] = self.board[y+1]

    def column_height(self, x_column):
        # for now we must traverse the column all the way up because of
        # eventual holes in the board

        # TODO: the board should have a structure that holds the information
        # of the frontier/the top border of the blocks
        # with this structure this method would have O(1) or at least better
        # performance than now
        height = 0
        last_was_block = False
        for y in range(self.height):
            if self.board[y][x_column]:
                last_was_block = True
            else:
                if last_was_block:
                    height = y
                last_was_block = False
        return height

    def place_block(self, block, pos):
        """
        Updates the board by placing `block` at the position `pos`.
        """
        LOG.debug("Placing %s at %s" % (block, pos))
        x_pos, y_pos = pos
        for (x,y) in block.get_solid_squares():
            if self.board[y_pos+y][x_pos+x] != None:
                LOG.critical("Writing on a position of the board already filled, something wrong happend!")
            self.board[y_pos+y][x_pos+x] = block

    def valid_position(self, x, y, ignore_top=False):
        return x >= 0 and x < self.width and \
               y >= 0 and (ignore_top or y < self.height)# and \
               #self.block_at(x, y) is None
