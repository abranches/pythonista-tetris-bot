import threading
import time
import random

from log import LOG
from blocks import BLOCKS, paint_block_color

DROPPING_TIMEOUT = 60

def updateGame(f):
    def func(engine):
        if not engine.running():
            LOG.error("Engine not running! Not executing action")
            return 0
        engine._update_game_lock.acquire()
        done_lines = f(engine)
        engine.print_game()
        engine._update_game_lock.release()
        return done_lines
    return func


class TetrisEngine(object):
    def __init__(self, game_state):
        self.game_state = game_state
        self._thread = threading.Thread(target=self._run_thread,
                                        name="engineThread")

        self._exiting = False
        self._running = False
        self._restart_timeout = False

        self._update_game_lock = threading.RLock()

    def start(self):
        self._thread.start()
        while not self.running():
            time.sleep(0.1)

    def _run_thread(self):
        LOG.debug("Started game engine thread")
        self._running = True

        try:
            self.game_state.start_new_drop()
            self.print_game()

            while not self._exiting:
                a = time.time()
                while time.time()-a < DROPPING_TIMEOUT \
                        and not self._exiting and not self._restart_timeout:
                    time.sleep(0.1)

                if not self._exiting and not self._restart_timeout:
                    self._drop_timeout_update()

                self._restart_timeout = False

            LOG.debug("Engine thread terminated")

        except Exception:
            LOG.debug("Engine thread just crashed!", exc_info=True)

        self._running = False

    def stop(self):
        LOG.debug("Stopping engine")
        self._exiting = True
        while self.running():
            time.sleep(0.1)

    def running(self):
        return self._running

    def print_game(self):
        print "\033[H\033[J"
        s = self.game_state.board_print()
        print s

    @updateGame
    def _drop_timeout_update(self):
        LOG.debug("ENGINE - drop timeout update")
        return self.move_down()

    @updateGame
    def move_down(self):
        LOG.debug("ENGINE - move down")
        self._restart_timeout = True
        if self.game_state.drop_block_is_stuck():
            done_lines = self.game_state.move_block_down()
            self.game_state.start_new_drop()
            return done_lines

        self.game_state.move_block_down()
        return 0

    @updateGame
    def drop_block(self):
        LOG.debug("ENGINE - drop block")
        LOG.debug("Dropping block: %s" % self.game_state)

        self._restart_timeout = True

        while not self.game_state.drop_block_is_stuck():
            LOG.debug("looping while not drop block is stuck")
            self.game_state.move_block_down()

        done_lines = self.game_state.move_block_down()
        self.game_state.start_new_drop()

        return done_lines

    @updateGame
    def move_left(self):
        LOG.debug("ENGINE - move left")
        return self.game_state.move_block_left()

    @updateGame
    def move_right(self):
        LOG.debug("ENGINE - move right")
        return self.game_state.move_block_right()

    @updateGame
    def rotate(self):
        LOG.debug("ENGINE - rotate")
        self.game_state.rotate_block()

    def set_game_state(self, state):
        self._update_game_lock.acquire()
        self.game_state = state
        self._update_game_lock.release()


class GameState(object):
    def __init__(self, board):
        self.board = board

        self.drop_block = None
        self.drop_position = ()

        self._game_over = False

        self.completed_lines = 0

    def copy(self):
        o = copy.copy(self)
        o.drop_block = copy.deepcopy(self.drop_block)
        o.drop_position = copy.deepcopy(self.drop_position)

    def start_new_drop(self, block=None):
        if not block:
           block = random.choice(BLOCKS)()
           #block = BLOCKS[6]()

        self.drop_block = block
        self.drop_position = (self.board.width/2-1,
                            self.board.height-block.height)

        LOG.debug("Starting new drop: %s" % self)

    def move_block_down(self):
        #LOG.debug("game_state: trying to move down %s at (%d,%d)" %
        #    (self.drop_block,self.drop_position[0], self.drop_position[1]))

        if self.drop_block_is_stuck():
            self.board.place_block(self.drop_block, self.drop_position)
            done_lines = self.clear_completed_lines()
            return done_lines
        else:
            x, y = (self.drop_position[0], self.drop_position[1]-1)
            return self._move_if_valid(x, y)

    def move_block_left(self):
        x, y = (self.drop_position[0]-1, self.drop_position[1])
        return self._move_if_valid(x, y)

    def move_block_right(self):
        x, y = (self.drop_position[0]+1, self.drop_position[1])
        return self._move_if_valid(x, y)

    def _move_if_valid(self, x, y):
        for xblock, yblock in self.drop_block.get_solid_squares():
            final_x, final_y = x+xblock, y+yblock
            if not self.board.valid_position(final_x, final_y, True) \
               or self.board.block_at(final_x, final_y):
                   return False

        self.drop_position = (x, y)
        return True

    def drop_block_is_stuck(self):
        xpos, ypos = self.drop_position
        drop_block = self.drop_block

        vertical_padding = 0
        for y in xrange(drop_block.height):
            if drop_block.get_solid_squares(y=y):
                vertical_padding = y
                break

        if ypos+vertical_padding == 0:
            return True

        for xblock in xrange(drop_block.width):
            yblock = drop_block.column_first_square(xblock)
            if yblock is None:
                # avoid empty columns
                continue

            down_block = self.board.block_at(xpos+xblock, ypos+yblock-1)
            if down_block:
                return True
        return False

    def rotate_block(self, times=1):
        if self._rotation_is_valid(times):
            self.drop_block.rotate(times)
            return True
        return False

    def _rotation_is_valid(self, times=1):
        x, y = self.drop_position
        rotated = self.drop_block.get_rotated(times)
        for xblock, yblock in rotated.get_solid_squares():
            final_x, final_y = x+xblock, y+yblock
            if not self.board.valid_position(final_x, final_y, True) \
               or self.board.block_at(final_x, final_y):
                return False
        return True

    def clear_completed_lines(self):
        lines_done = 0
        # we must start from the top so the clearing
        # doesn't affect this loop
        for y in reversed(range(self.board.height)):
            is_done = True
            for x in range(self.board.width):
                block = self.board.block_at(x, y)
                if not block:
                    is_done = False
                    break

            if is_done:
                LOG.debug("Clearing line %d" % y)
                self.board.clear_line(y)
                lines_done += 1

        self.completed_lines += lines_done

        return lines_done

    def game_is_over(self):
        return self._game_over

    def __str__(self):
        return "<Drop block: %s, position: %s>" % (self.drop_block,
                                                   repr(self.drop_position))

    def board_print(self):
        out = []

        drop_block_positions = map(lambda (x,y): (self.drop_position[0]+x,
                                                  self.drop_position[1]+y),
                                   self.drop_block.get_solid_squares())

        for y in reversed(xrange(self.board.height)):
            line_str = [" ",] * (self.board.width*3)
            for x in reversed(xrange(self.board.width)):
                if (x,y) in drop_block_positions:
                    block = self.drop_block
                else:
                    block = self.board.block_at(x, y)

                if block != None:
                    line_str[x*3] = "|"
                    line_str[x*3+1] = paint_block_color("_", block)
                    line_str[x*3+2] = "|"
                    if out:
                        # work on the top border of a block's square
                        # it can be either a placed block or the dropping block
                        if (x,y+1) in drop_block_positions:
                            up_block = self.drop_block
                        else:
                            up_block = self.board.block_at(x,y+1)
                        s = "_"
                        if up_block:
                            s = paint_block_color("_", up_block)
                        out[-1][x*3+1] = s

            out.append(line_str)

        # apply borders
        for i,line in enumerate(out):
            line.insert(0, "%2d|"%(self.board.height-i-1))
            line.append("|")

        out.insert(0, ["  +"]+["-",]*(self.board.width*3) + ["+"])
        out.append(["  +"]+["-",]*(self.board.width*3) + ["+"])

        l = "   " + "".join(map(lambda i: "|%d|"%i, xrange(self.board.width)))
        out.append(l)

        out_str = "\n".join(map("".join, out))

        out_str += "\nDone lines: %d" % self.completed_lines

        return out_str
