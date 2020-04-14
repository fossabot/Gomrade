from sgfmill import sgf, ascii_boards, boards

from gomrade.state_utils import project_stones_state

"""
What can happen:

# Casual game:

1. Color plays normally:
- One extra stone for color and the same num of the other color

2. Color plays and kills:
- One extra stone for color and at least one less of the other color

3. Undo to some move of a player
- Check previous states and if it was, generate

5. Undo to some move of AI
- Check previous states and if it was, wait

5. Undo to other move of a player
- Check previous states and whether they differ with just one stone of player color

6. Undo to other move of which is a kill
- Pff

# Introductions:

1. Game state is introduced without sgf

2. Game state is loaded from sgf

3. Game state is strongly changed but some history is preserved


# Errors:

1. Random stone is switched to opposite
- Just accept, fill with pass

2. Stone or stones disappear

3. A few stones are introduced



1. Easy-peasy
2. Need to check if it was a kill or a mistake. How verify the kill?
- maybe checking the liberties will be necessary?
3. 


"""


class GameTracker:
    def __init__(self):
        self.game = None
        self.board_size = None
        self.komi = None
        self.state_history = []

    def many_stones_added(self):
        pass

    def load_game(self, path):
        with open(path, 'r') as f:
            game_str = f.read()
        self.game = sgf.Sgf_game.from_string(game_str)

    def save_game(self, path):
        with open(path, 'w') as f:
            f.write(self.to_string())

    def wrong_color_added(self):
        pass

    def seems_like_undo(self):
        pass

    def seems_like_reset(self):
        pass

    def translate_stones_state(self):
        pass

    def update_sgf(self):
        pass

    def to_string(self):
        return self.game.serialise().decode("utf-8")

    def create_empty(self, size, komi):
        self.game = sgf.Sgf_game(size=size, encoding="UTF-8")
        self.board_size = size
        self.komi = komi
        root_node = self.game.get_root()
        root_node.set("KM", komi)

    def vanilla_parse(self, stones_state):
        """Temporary method """
        # tmp = ''
        self.create_empty(self.board_size, self.komi)

        for row in range(self.board_size):
            for col in range(self.board_size):
                c = stones_state[row*self.board_size + col]
                if c == '.':
                    continue
                # tmp = 'w' if tmp == 'b' else 'b'
                node = self.game.extend_main_sequence()
                node.set_move(c.lower(), (row, col))

    def replay_position(self, stones_state):

        stones_state = project_stones_state(stones_state, flip=True, rotate=False)
        self.state_history.append(stones_state)

        self.vanilla_parse(stones_state)
        # node = self.game.extend_main_sequence()
        # node.set_move('b', (2, 3))


if __name__ == '__main__':
    root = '/Users/dasm/projects/Gomrade/'
    # in_path = root + 'data/Xie_Yimin-Fujisawa_Rina.sgf', out_path = root + 'data/out.txt'

    gt = GameTracker()
    gt.create_empty(size=19, komi=6.5)

    stones_state = list('....................' * 19)
    stones_state[16] = 'b'
    stones_state[240] = 'w'

    gt.replay_position(''.join(stones_state))
