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
        global e
        e = self.engine
        while self.engine.running():
            #x = copy.deepcopy(self.engine.game_state)
            algorithm = PossibleStatesBFSAlgorithm(self.engine.game_state)
            algorithm.go()
            #e.set_game_state(x)

            path = algorithm.optimal_path

            for action in path:
                if isinstance(action, MakeMove):
                    d = action.direction
                    for i in range(action.times):
                        if d == Direction.DOWN:
                            self.engine.move_down()
                        elif d == Direction.RIGHT:
                            self.engine.move_right()
                        elif d == Direction.LEFT:
                            self.engine.move_left()
                        #time.sleep(0.1)
                elif isinstance(action, Rotate):
                    self.engine.rotate()
                #time.sleep(0.1)

            self.engine.move_down()
            #time.sleep(1)


class PossibleStatesBFSAlgorithm(object):
    def __init__(self, game_state):
        self.original_game_state = game_state

        self._results_queue = PriorityQueue()
        self.best_result = None
        self.optimal_path = []

    def go(self):
        game_state = copy.deepcopy(self.original_game_state)
        self._run_bfs(game_state)

        if self._results_queue.qsize() > 0:
            self.best_result = self._results_queue.queue[0]
            self.optimal_path = self.best_result.path
        #assert self._results_queue.qsize() > 0, "No results after BFS??"


    def _get_bfs_start_pos(self, game_state):
        """
        Get what is considered to be a good starting position
        for the BFS algorithm.

        This is needed to avoid the algorithm waste time processing all
        the nodes all the way down from the starting drop position to the base
        of the board.

        By checking where the highest column is we can set the starting position
        to the top of that column and tell the BFS to start from there.

        Because we are starting at the highest column, there isn't any trouble
        for the algorithm only testing LEFT, RIGHT and DOWN directions.

        Return:
            A tuple (start_pos, actions) where actions is a list of Action
            necessary to go from `game_state.drop_position` to `start_pos`.
        """
        start_pos = (0, 0)
        for x in range(game_state.board.width):
            column_height = game_state.board.column_height(x)
            if column_height > start_pos[1]:
                if game_state.board.block_fits(game_state.drop_block,
                                                (x, column_height)):
                    start_pos = (x, column_height)
                else:
                    start_pos = (start_pos[0], column_height)


        x_diff, y_diff = (start_pos[0] - game_state.drop_position[0],
                          start_pos[1] - game_state.drop_position[1])

        actions = []
        if x_diff != 0:
            if x_diff < 0:
                d = Direction.LEFT
            else:
                d = Direction.RIGHT
            actions.append(MakeMove(d, abs(x_diff)))

        if y_diff < 0 :
            actions.append(MakeMove(Direction.DOWN, abs(y_diff)))
        else:
            start_pos = game_state.drop_position
            actions = []

        return start_pos, actions


    def _run_bfs(self, game_state):
        start_time = time.time()
        total = 0
        queue = Queue()
        visited_nodes = {}

        start_drop_node = BoardNode(game_state.drop_block,
                                    game_state.drop_position)
        bfs_start_pos, actions = self._get_bfs_start_pos(game_state)

        node = BoardNode(game_state.drop_block, bfs_start_pos,
                        start_drop_node, actions)
        #node = BoardNode(block, game_state.drop_position)
        queue.put(node)

        while not queue.empty() and e.running():
            node = queue.get()

            if visited_nodes.has_key(node):
                continue

            visited_nodes[node] = True
            game_state.drop_position = node.drop_position

            # we need to have a copy of drop_block because it will be changed
            # with rotations
            game_state.drop_block = copy.copy(node.drop_block)



            LOG.debug("Current node: %s" % node)
            #e.set_game_state(game_state)
            #e.print_game()

            if game_state.rotate_block():
                new_node = BoardNode(game_state.drop_block,
                                    game_state.drop_position,
                                    node,
                                    [Rotate()])
                queue.put(new_node)
                # there's NO need to make a new copy of node.drop_block as
                # with the time of writing of this code the game_state.drop_block
                # isn't modified anywhere again in code.
                # if this changes, game_state.drop_block MUST be
                # assigned to a new copy of node.drop_block
                game_state.drop_block = node.drop_block

            if game_state.move_block_left():
                new_node = BoardNode(game_state.drop_block,
                                     game_state.drop_position,
                                     node,
                                     [MakeMove(Direction.LEFT)])
                queue.put(new_node)
                game_state.drop_position = node.drop_position

            if game_state.move_block_right():
                new_node = BoardNode(game_state.drop_block,
                                     game_state.drop_position,
                                     node,
                                     [MakeMove(Direction.RIGHT)])
                queue.put(new_node)
                game_state.drop_position = node.drop_position


            if game_state.drop_block_is_stuck():
                a = time.time()
                path = self._get_path(node)
                b = (time.time()-a)*1000
                total += b
                #LOG.debug("Time calcing path: %f" % b)
                s = PossibleBlockState(game_state, path)
                s.calc_stats()
                self._results_queue.put(s)
            else:
                # block is not stuck, so move_block_down() will return boolean
                # indicating either if the move is valid of not
                # it only returns an integer representing the nr of lines done
                # when it's called in a stuck position
                if game_state.move_block_down():
                    new_node = BoardNode(game_state.drop_block,
                                        game_state.drop_position,
                                        node,
                                        [MakeMove(Direction.DOWN)])
                    queue.put(new_node)
                    game_state.drop_position = node.drop_position

            #time.sleep(0.1)

        #LOG.debug("ALL TIME: %f" % ((time.time()-start_time)*1000))
        #LOG.debug("total paths time: %f" % total)

    def _get_path(self, end_node):
        #LOG.debug("End node: %s" % end_node)
        path = []

        node = end_node
        while node.previous_node:
            for a in node.previous_actions:
                path.insert(0, a)

            node = node.previous_node

        LOG.debug("PATH: %s" % path)
        LOG.debug("Start node: %s" % node)
        return path


class BoardNode(object):
    def __init__(self, drop_block, drop_position,
                previous_node=None, previous_actions=[]):
        self.drop_block = drop_block
        self.drop_position = drop_position

        self.previous_node = previous_node
        self.previous_actions = previous_actions

    def __str__(self):
        real_pos = self.drop_block.get_real_position(self.drop_position)
        return "<BoardNode: %s, at %s(real). Previous actions: [%s]>" % \
           (self.drop_block, real_pos, ", ".join(map(str, self.previous_actions)))

    def __eq__(self, o):
        real_pos = self.drop_block.get_real_position(self.drop_position)
        o_real_pos = o.drop_block.get_real_position(self.drop_position)

        # the Block class defines it's own __eq__() function
        return self.drop_block == o.drop_block and \
                real_pos == o_real_pos

    def __hash__(self):
        real_pos = self.drop_block.get_real_position(self.drop_position)
        return hash((hash(self.drop_block),
                    hash(real_pos)))


class PossibleBlockState(object):
    def __init__(self, game_state, path):
        self.game_state = game_state
        self.path = path

        self.unconnected_sides = 0
        self.connected_sides = 0
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
                        adjacent_y):
                    self.connected_sides += 1
                    pass
                elif self.game_state.board.block_at(adjacent_x, adjacent_y):
                    self.connected_sides += 1
                else:
                    self.unconnected_sides += 1

                if adjacent_y-1 > self.height:
                    self.height = adjacent_y-1

        self.connected_ratio = float(self.connected_sides) / self.unconnected_sides

    def __str__(self):
        return "<Connected sides: %d, Height: %d>" % (self.connected_sides,
                                                      self.height)

    def __cmp__(self, o):
        # -----
        if o.connected_sides == self.connected_sides:
            return self.height - o.height
        return o.connected_sides - self.connected_sides
        # -----

        a = 0.60
        x = a * self.connected_sides + \
            (1-a) * self.height
        x = x * 100
        y = a * o.connected_sides + \
            (1-a) * o.height
        y = y * 100
        return y-x


        #return 100*o.connected_ratio - 100*self.connected_ratio
        #return o.connected_sides - self.connected_sides
        #return self.connected_sides - o.connected_sides
        #return self.height - o.height


class Action(object):
    attributes = []
    def __str__(self):
        a = ["%s=%s" % (k, getattr(self, k)) for k in self.attributes]
        return "<%s, %s>" % (self.__class__.__name__, ", ".join(a))

class MakeMove(Action):
    attributes = ["direction", "times"]
    def __init__(self, direction, times=1):
        self.direction = direction
        self.times = times

    def __eq__(self, o):
        return self.direction == o.direction and self.times == o.times

class Rotate(Action):
    attributes = ["times"]
    def __init__(self, times=1):
        self.times = times

    def __eq__(self, o):
        return self.times == o.times

class Direction(object):
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP = (0, 1)
    DOWN = (0, -1)


