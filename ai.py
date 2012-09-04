import time
import threading
import copy
from Queue import Queue, PriorityQueue

from log import LOG

class TetrisAI(object):
    def __init__(self, engine):
        self.engine = engine
        self._thread = threading.Thread(target=self._run_thread,
                                        name="AIThread")

    def play(self):
        self._thread.start()

    def _run_thread(self):
        while self.engine.running():
            algorithm = PossibleStatesBFSAlgorithm(self.engine.game_state)
            algorithm.go(self.engine)
            path = algorithm.optimal_path
            LOG.debug("PATH: %s" % path)
            LOG.debug("Best: %s" % algorithm.best_result)
            rotations = algorithm.best_result.game_state.drop_block.rotation
            LOG.debug("Rotations: %d" % rotations)

            for i in range(rotations):
                self.engine.rotate()

            for d in path:
                if d == Direction.DOWN:
                    self.engine.move_down()
                elif d == Direction.RIGHT:
                    self.engine.move_right()
                elif d == Direction.LEFT:
                    self.engine.move_left()
                time.sleep(0.03)
            LOG.debug("Done doing path")
            self.engine.move_down()
            #time.sleep(2)


class PossibleStatesBFSAlgorithm(object):
    def __init__(self, game_state):
        self.original_game_state = game_state

        self._results_queue = PriorityQueue()
        self.best_result = None
        self.optimal_path = []

    def go(self, e):
        for i in range(self.original_game_state.drop_block.total_rotations):
            game_state = copy.deepcopy(self.original_game_state)
            game_state.rotate_block(times=i)
            self._run_bfs(game_state)

        self.best_result = self._results_queue.queue[0]
        self.optimal_path = self.best_result.path


    def _run_bfs(self, game_state):
        queue = Queue()
        visited_nodes = {}

        start_node = game_state.drop_position
        queue.put((start_node, None))

        while not queue.empty():
            node, coming_direction = queue.get()

            if visited_nodes.has_key(node):
                continue

            visited_nodes[node] = coming_direction
            game_state.drop_position = node

            #e.set_game_state(game_state)
            #e.print_game()

            if game_state.drop_block_is_stuck():
                path = self._get_path(game_state.drop_position, visited_nodes)
                s = PossibleBlockState(copy.deepcopy(game_state), path)
                s.calc_stats()
                self._results_queue.put(s)
            else:
                # block is not stuck, so move_block_down() will return boolean
                # indicating either if the move is valid of not
                # it only returns an integer representing the nr of lines done
                # when it's called in a stuck position
                if game_state.move_block_down():
                    new_node = game_state.drop_position
                    queue.put((new_node, Direction.UP))
                    game_state.drop_position = node

            if game_state.move_block_left():
                new_node = game_state.drop_position
                queue.put((new_node, Direction.RIGHT))
                game_state.drop_position = node

            if game_state.move_block_right():
                new_node = game_state.drop_position
                queue.put((new_node, Direction.LEFT))
                game_state.drop_position = node

            #time.sleep(0.01)


    def _get_path(self, end_node, visited_nodes):
        path = []

        LOG.debug("Best position: %s" % (end_node,))
        direction = visited_nodes[end_node]

        node = end_node
        while direction:
            if direction == Direction.UP:
                path.insert(0, Direction.DOWN)
            elif direction == Direction.LEFT:
                path.insert(0, Direction.RIGHT)
            elif direction == Direction.RIGHT:
                path.insert(0, Direction.LEFT)

            node = (node[0]+direction[0], node[1]+direction[1])
            direction = visited_nodes[node]

        return path


class PossibleBlockState(object):
    def __init__(self, game_state, path):
        self.game_state = game_state
        self.path = path

        self.connected_sides = 0
        self.unconnected_sides = 0
        self.connected_ratio = 0

        self.height = 0

    def calc_stats(self):
        directions = (Direction.LEFT, Direction.RIGHT, Direction.UP,
                        Direction.DOWN)

        block_squares = self.game_state.drop_block.get_solid_squares()
        for x_block, y_block in block_squares:
            for x_dir, y_dir in directions:
                adjacent_x = self.game_state.drop_position[0]+x_block+x_dir
                adjacent_y = self.game_state.drop_position[1]+y_block+y_dir

                if not self.game_state.board.valid_position(adjacent_x,
                                                            adjacent_y, True) \
                   or self.game_state.board.block_at(adjacent_x, adjacent_y):
                    self.connected_sides += 1
                else:
                    self.unconnected_sides += 1

                if adjacent_y-1 > self.height:
                    self.height = adjacent_y-1

        self.connected_ratio = float(self.connected_sides) / (self.connected_sides +
                                                    self.unconnected_sides)

    def __str__(self):
        return "<Connected sides: %d, Height: %d>" % (self.connected_sides,
                                                      self.height)

    def __cmp__(self, o):
        if o.connected_sides == self.connected_sides:
            return self.height - o.height
        return o.connected_sides - self.connected_sides
        #return 100*o.connected_ratio - 100*self.connected_ratio
        #return o.connected_sides - self.connected_sides
        #return self.connected_sides - o.connected_sides
        #return self.height - o.height


class Direction(object):
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP = (0, 1)
    DOWN = (0, -1)
