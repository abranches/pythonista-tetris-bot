import copy
#from PIL import Image, ImageStat

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

    # not used
    def get_rotated(self, times=1):
        if times == 0:
            return self

        if times > 0:
            new_matrix = BlockMatrix(m=self.n, n=self.m)
            for i in xrange(self.m):
                for j in xrange(self.n):
                    new_matrix.set(j, new_matrix.n-i-1, self.data[i][j])
        else:
            new_matrix = BlockMatrix(m=self.m, n=self.n)
            for j in xrange(self.n):
                for i in xrange(self.m):
                    new_matrix.set(new_matrix.m-j-1, i, self.data[i][j])


        # cmp(times, 0) -> get the sign of times
        return new_matrix.get_rotated(times + cmp(times,0)*(-1))

class Block:
    total_rotations = 0

    def __init__(self):
        self.matrix = self.matrixes[0]
        self.height = self.matrix.m
        self.width = self.matrix.n
        self.rotation = 0

        self.top_padding = 0
        self.bottom_padding = 0
        self.left_padding = 0
        self.right_padding = 0
        self._calc_paddings()

    def __deepcopy__(self, memo):
        # we reimplement deepcopy to make a shallow copy because
        # of the structure of this class.
        # self.matrixes is made to always point at the same static attributes
        # so only reference copies are needed
        return copy.copy(self)

    def __hash__(self):
        # to speed up this hash function I choosed to simply use the
        # matrix reference and not the matrix by itself
        # this is ok as long as someone somewhere in the code doesn't
        # mess up with the static elements of the class
        # (like assigning self.matrix to a copy of another matrix)
        return hash((id(self.matrix), self.rotation))
        #return hash((self.matrix, self.rotation))

    def __eq__(self, o):
        return o.__class__ == self.__class__ and \
                self.rotation == o.rotation

    def get_real_position(self, pos):
        return (pos[0] + self.left_padding, pos[1] + self.bottom_padding)

    def get_raw_position(self, pos):
        return (pos[0] - self.left_padding, pos[1] - self.bottom_padding)

    def column_first_square(self, x):
        for y in xrange(self.height):
            if self.matrix.get_x_y(x,y) == 1:
                return y

    def __str__(self):
        c = ""
        if hasattr(self, "color"):
            c = ", color=%s" % paint_block_color(str(self.color), self, True)
        return "<%s, rotation=%d%s>"% (self.__class__, self.rotation, c)

    def _calc_paddings(self):
        # TODO: this can also be written previously in the code instead
        # being computed each time this is called
        self.bottom_padding = 0
        for y in xrange(self.height):
            if self.get_solid_squares(y=y):
                self.bottom_padding = y
                break

        self.top_padding = 0
        for y in reversed(xrange(self.height)):
            if self.get_solid_squares(y=y):
                self.top_padding = self.height-y-1
                break

        self.left_padding = 0
        for x in xrange(self.width):
            if self.get_solid_squares(x=x):
                self.left_padding = x
                break

        self.right_padding = 0
        for x in reversed(xrange(self.width)):
            if self.get_solid_squares(x=x):
                self.right_padding = self.width-x-1
                break

    def rotate(self, times=1):
        # the % operation has no problems with negative `times`
        self.rotation = (self.rotation+times) % self.total_rotations

        # old way of rotating blocks:
        # compute the rotated matrix each time this is called
        #self.matrix = self.matrix.get_rotated(times)
        self.matrix = self.matrixes[self.rotation]
        self.height = self.matrix.m
        self.width = self.matrix.n
        self._calc_paddings()

    def get_rotated(self, times=1):
        new_block = copy.deepcopy(self)
        new_block.rotate(times)
        return new_block

    # no used
    def _get_all_rotations(self):
        yield copy.deepcopy(self)
        for i in xrange(self.total_rotations-1):
            new_block = copy.deepcopy(self)
            new_block.rotate()
            yield new_block


    # TODO: this doesn't need to be running all the time!!
    # save the results in a static way like what was done with the rotations
    def get_solid_squares(self, x=None, y=None):
        """
        Results are ordered by crescent order.
        If x-> squares come from bottom to top
        If y-> squares como from left to right
        """
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
    matrixes = [BlockMatrix(((1, 1),
                             (1, 1))),
               ]
    color = 3
    total_rotations = 1

class BlockLeftEnv(Block):
    matrixes = [BlockMatrix(((1, 1, 0),
                             (0, 1, 1),
                             (0, 0, 0))),
                BlockMatrix(((0, 0, 1),
                             (0, 1, 1),
                             (0, 1, 0))),
                BlockMatrix(((0, 0, 0),
                             (1, 1, 0),
                             (0, 1, 1))),
                BlockMatrix(((0, 1, 0),
                             (1, 1, 0),
                             (1, 0, 0))),
                ]
    color  = 1
    total_rotations = 4

class BlockRightEnv(Block):
    matrixes = [BlockMatrix(((0, 1, 1),
                             (1, 1, 0),
                             (0, 0, 0))),
                BlockMatrix(((0, 1, 0),
                             (0, 1, 1),
                             (0, 0, 1))),
                BlockMatrix(((0, 0, 0),
                             (0, 1, 1),
                             (1, 1, 0))),
                BlockMatrix(((1, 0, 0),
                             (1, 1, 0),
                             (0, 1, 0))),
                ]
    color = 2
    total_rotations = 4

class BlockLeftL(Block):
    matrixes = [BlockMatrix(((0, 0, 1),
                             (1, 1, 1),
                             (0, 0, 0))),
                BlockMatrix(((0, 1, 0),
                             (0, 1, 0),
                             (0, 1, 1))),
                BlockMatrix(((0, 0, 0),
                             (1, 1, 1),
                             (1, 0, 0))),
                BlockMatrix(((1, 1, 0),
                             (0, 1, 0),
                             (0, 1, 0)))
                ]

    color = 7
    total_rotations = 4

class BlockRightL(Block):
    matrixes = [BlockMatrix(((1, 0, 0),
                             (1, 1, 1),
                             (0, 0, 0))),
                BlockMatrix(((0, 1, 1),
                             (0, 1, 0),
                             (0, 1, 0))),
                BlockMatrix(((0, 0, 0),
                             (1, 1, 1),
                             (0, 0, 1))),
                BlockMatrix(((0, 1, 0),
                             (0, 1, 0),
                             (1, 1, 0)))
                ]


    color = 4
    total_rotations = 4

class BlockSuper(Block):
    matrixes = [BlockMatrix(((0, 1, 0),
                             (1, 1, 1),
                             (0, 0, 0))),
                BlockMatrix(((0, 1, 0),
                             (0, 1, 1),
                             (0, 1, 0))),
                BlockMatrix(((0, 0, 0),
                             (1, 1, 1),
                             (0, 1, 0))),
                BlockMatrix(((0, 1, 0),
                             (1, 1, 0),
                             (0, 1, 0)))
                ]


    color = 5
    total_rotations = 4

class BlockLine(Block):
    matrixes = [BlockMatrix(((0, 0, 0, 0),
                             (0, 0, 0, 0),
                             (1, 1, 1, 1),
                             (0, 0, 0, 0))),
                BlockMatrix(((0, 1, 0, 0),
                             (0, 1, 0, 0),
                             (0, 1, 0, 0),
                             (0, 1, 0, 0))),
                BlockMatrix(((0, 0, 0, 0),
                             (1, 1, 1, 1),
                             (0, 0, 0, 0),
                             (0, 0, 0, 0))),
                BlockMatrix(((0, 0, 1, 0),
                             (0, 0, 1, 0),
                             (0, 0, 1, 0),
                             (0, 0, 1, 0)))
                ]


    color = 6
    total_rotations = 4

BLOCKS = (BlockCube, BlockLeftEnv, BlockRightEnv, BlockLeftL,
          BlockRightL, BlockSuper, BlockLine)
