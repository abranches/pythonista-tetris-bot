import rpdb2

from log import LOG

class TetrisBoard:
    def __init__(self, height=20, width=10):
        self.height = height
        self.width = width
        self.board = []

        self._column_heights = [0] * self.width

        self._start_new_board()

    def _start_new_board(self):
        self.board = []
        for i in xrange(self.height):
            self.board.append( [None,]*self.width )

    def block_at(self, x, y, ignore_top=True):
        assert x >= 0 and x < self.width and y >= 0 and \
                (ignore_top or y < self.height), \
                "(%d, %d) coordinates go beyond the board size" % (x, y)

        if ignore_top and y >= self.height:
            return None

        return self.board[y][x]

    def block_fits(self, block, pos, ignore_top=True):
        solid_squares = block.get_solid_squares()
        blocks_outside_top = 0

        for x_block, y_block in solid_squares:
            x, y = pos[0]+x_block, pos[1]+y_block
            if not self.valid_position(x, y, ignore_top):
                return False

            if y >= self.height:
                if ignore_top:
                    blocks_outside_top += 1
                    continue
                else:
                    # this shouldn't be necessary as self.valid_position()
                    # will previously return False with this conditions
                    assert False, \
                        "don't think valid_position() is working very well!"

            if self.block_at(x, y):
                return False

        if blocks_outside_top == len(solid_squares):
            return False

        return True

    def clear_line(self, y_line):
        for y in range(y_line, self.height-1):
            self.board[y] = self.board[y+1]
        self.board[self.height-1] = [None,]*self.width

        for x in xrange(self.width):
            self._column_heights[x] -= 1

    def column_height(self, x_column):
        assert x_column >= 0 and x_column < self.width, "Hmmm %d" % x_column
        return self._column_heights[x_column]

    def place_block(self, block, pos, ignore_top=True):
        """
        Updates the board by placing `block` at the position `pos`.
        """
        LOG.debug("Placing %s at %s" % (block, pos))

        solid_squares = block.get_solid_squares()
        heighest_columns = [0] * self.width

        for (x,y) in solid_squares:
            final_x, final_y = pos[0]+x, pos[1]+y

            if ignore_top and final_y >= self.height:
                continue

            assert self.valid_position(final_x, final_y, ignore_top), \
                "Trying to place %s outside the board limits! (%s)" % (block, pos)

            if self.board[final_y][final_x] != None:
                LOG.critical("Writing on (%d,%d), a position of the" % (final_x, final_y) + \
                        "board already filled, something wrong happend!")

            self.board[final_y][final_x] = block

            if final_y >= heighest_columns[final_x]:
                heighest_columns[final_x] = final_y + 1

        for (x, _) in solid_squares:
            final_x = pos[0]+x

            if heighest_columns[final_x] > self._column_heights[final_x]:
                self._column_heights[final_x] = heighest_columns[final_x]

    def valid_position(self, x, y, ignore_top=True):
        return x >= 0 and x < self.width and \
               y >= 0 and (ignore_top or y < self.height)# and \
               #self.block_at(x, y) is None
