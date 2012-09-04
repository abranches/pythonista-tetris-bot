import copy
from PIL import Image, ImageStat

from log import LOG

SQUARE_SIDE = 12   # size in pixels of each square in blocks
EMPTY_SQUARE_COLOR = 0  # color of an empty square in a block (black in this case)

def paint_block_color(string, block, foreground=False):
    if hasattr(block, "color"):
        return "\033[%d%dm%s\033[0m" % (3 if foreground else 4, block.color, string)
    return string


def get_block_from_image(filename):
    im = Image.open(filename)

    squares = (im.size[0]/SQUARE_SIDE, im.size[1]/SQUARE_SIDE)

    matrix = BlockMatrix(m=squares[1], n=squares[0])
    for i in xrange(squares[1]):
        for j in xrange(squares[0]):
            square_im = im.crop( (j*SQUARE_SIDE,
                                  i * SQUARE_SIDE,
                                  (j+1)*SQUARE_SIDE-1,
                                  (i+1)*SQUARE_SIDE-1) )
            stats = ImageStat.Stat(square_im)
            matrix.set(i, j,
                    int(0 not in [x[0] for x in stats.extrema]))

    for b in BLOCKS:
        if b.matrix.data == matrix.data:
            return b()

    LOG.debug("no block matched for image %s" % filename)
    return None


class BlockMatrix:
    def __init__(self, data=[], m=0, n=0):
        if data:
            self.m = len(data)
            self.n = len(data[0])
            self.data = data
        else:
            self.n = n
            self.m = m
            self.data = []
            for i in xrange(self.m):
                self.data.append( [None,]*self.n )

    def get_x_y(self, x, y):
        return self.data[self.m-y-1][x]

    def set(self, i, j, value):
        self.data[i][j] = value

    def __getitem__(self, key):
        return self.data[key]

    def get_rotated(self, times=1):
        if times == 0:
            return self

        new_matrix = BlockMatrix(m=self.n, n=self.m)
        for i in xrange(self.m):
            for j in xrange(self.n):
                new_matrix.set(j, new_matrix.n-i-1, self.data[i][j])

        return new_matrix.get_rotated(times-1)

class Block:
    total_rotations = 0

    def __init__(self):
        self.matrix = copy.deepcopy(self.orig_matrix)
        self.height = self.matrix.m
        self.width = self.matrix.n
        self.rotation = 0

    def column_first_square(self, x):
        for y in xrange(self.height):
            if self.matrix.get_x_y(x,y) == 1:
                return y

    def __str__(self):
        c = ""
        if hasattr(self, "color"):
            c = ", color=%s" % paint_block_color(str(self.color), self, True)
        return "<%s, rotation=%d%s>"% (self.__class__, self.rotation, c)

    def rotate(self, times=1):
        self.matrix = self.matrix.get_rotated(times)
        self.height = self.matrix.m
        self.width = self.matrix.n
        self.rotation = (self.rotation+times) % self.total_rotations

    def get_rotated(self, times=1):
        new_block = copy.deepcopy(self)
        new_block.rotate(times)
        return new_block

    def _get_all_rotations(self):
        yield copy.deepcopy(self)
        for i in xrange(self.total_rotations-1):
            new_block = copy.deepcopy(self)
            new_block.rotate()
            yield new_block

    def get_solid_squares(self, x=None, y=None):
        squares = []
        if x is not None:
            for y in xrange(self.height):
                if self.matrix.get_x_y(x,y) == 1:
                    squares.append((x,y))
        elif y is not None:
            for x in xrange(self.width):
                if self.matrix.get_x_y(x,y) == 1:
                    squares.append((x,y))

        else:
            for y in xrange(self.height):
                for x in xrange(self.width):
                    if self.matrix.get_x_y(x,y) == 1:
                        squares.append((x,y))

        return squares


class BlockCube(Block):
    orig_matrix = BlockMatrix([[1, 1],
                               [1, 1]])
    color = 3
    total_rotations = 1

class BlockLeftEnv(Block):
    orig_matrix = BlockMatrix([[1, 1, 0],
                               [0, 1, 1],
                               [0, 0, 0]])
    color  = 1
    total_rotations = 2

class BlockRightEnv(Block):
    orig_matrix = BlockMatrix([[0, 1, 1],
                               [1, 1, 0],
                               [0, 0, 0]])
    color = 2
    total_rotations = 2

class BlockLeftL(Block):
    orig_matrix = BlockMatrix([[0, 0, 1],
                               [1, 1, 1],
                               [0, 0, 0]])
    color = 7
    total_rotations = 4

class BlockRightL(Block):
    orig_matrix = BlockMatrix([[1, 0, 0],
                               [1, 1, 1],
                               [0, 0, 0]])
    color = 4
    total_rotations = 4

class BlockSuper(Block):
    orig_matrix = BlockMatrix([[0, 1, 0],
                               [1, 1, 1],
                               [0, 0, 0]])
    color = 5
    total_rotations = 4

class BlockLine(Block):
    orig_matrix = BlockMatrix([[0, 0, 0, 0],
                               [0, 0, 0, 0],
                               [1, 1, 1, 1],
                               [0, 0, 0, 0],])
    color = 6
    total_rotations = 2

BLOCKS = (BlockCube, BlockLeftEnv, BlockRightEnv, BlockLeftL,
          BlockRightL, BlockSuper, BlockLine)
