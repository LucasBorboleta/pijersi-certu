# ENGINE-REDESIGN

## Introduction

In order to accelerate the Minimax algorithm, the alpha-beta optimization cuts is not enough. A rework of the representation of state that permits fast implementation of the rules, as well as fast implementation of state evaluation, is needed. 

## Concepts

Before moving to some precise and actual encoding aspects using Python (either field of bits or tuple) let us stay at the conceptual level.

### States

The game-state can be represented by :

- the board-state
- the credit
- the current player

The board-state can be represented by the Cartesian product of 45 hexagon-states.

The hexagon-state can be represented, by 7 bits of information, as follows:

- is_white (1 bit)
- is_empty (1 bit)
- is_stack (1 bit)
- bottom sort of cube : rock, paper, scissors, wise (2 bits)
- top sort of cube : rock, paper, scissors, wise (2 bits)

So a board-state can be represented by 45 x 7 bits = 315 bits.

### Actions

The possible actions from a board-state can be explored by hexagon occupied by the current player.

For a given hexagon occupied by a current player, the 4 action types can represented by:

- h1-h2 : move of a cube, in 6 directions, so representable by 3 bits
- h1=h2: move of a stack, in 6 directions, of 1 or 2 spaces, so representable by 4 bits
- h1-h2=h3 : move of a cube, chained by move of stack, so representable by 7 bits
- h1=h2-h4 : move of a stack, chained by a move of a cube, so representable by 7 bits

For each of the action-type, the following mappings or tables can be made:

- sub-state-mask : (h, t) --> (h1, ..., hn) where h is the starting hexagon, t is the translation, (h_1, ..., h_n) the list, maybe empty, of the hexagons to be considered.
  - Such "mask" is applied to the actual board-state s : it keeps the Cartesian product of the hexagon-states mentioned by the mask.
  - the starting hexagon h is always part of these (h1, ..., hn)
- legal-sub-states : (h, t) --> (s1, ... , sk) the list, maybe empty, of the k sub-states that are legals.
- new-sub-states : (h, t) --> (s'1, ..., s'k) the list, maybe empty, of the new k sub-states when the transition is legal.
- Each new-state can also encode in 1 bit is at least one capture occurred.

### Next steps

Start a prototype in Python for action-type h1-h2, then h1=h2. For hexagon-state, start with a tuple before considering a field of bits.

Then consider action types h1-h2=h3 and h1-h2=h3. If the size of the built tables are too large then the chaining of tables h1-h2 and h2=h3 can be considered.



