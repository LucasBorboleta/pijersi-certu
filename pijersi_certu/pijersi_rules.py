#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_rules.py implements the rules engine for the PIJERSI boardgame."""


__version__ = "2.0.0.rc3"

_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import array
from collections import Counter
from dataclasses import dataclass
import enum
import math
import os
import random
import re
from statistics import mean
import sys
import time
from typing import Iterable
from typing import Mapping
from typing import NewType
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import TypeVar

from concurrent.futures import ProcessPoolExecutor as PoolExecutor
from multiprocessing import freeze_support
import multiprocessing

OMEGA = 1_000.
OMEGA_2 = OMEGA**2

# The most compact storage
# >> Tests with all 32 signed bits or all 64 signed bits have not changed the profiling, neither the global time
ARRAY_TYPE_BOOL = 'B'
ARRAY_TYPE_COUNTER = 'B'
ARRAY_TYPE_STATE_1 = 'B'
ARRAY_TYPE_STATE_2 = 'H'
ARRAY_TYPE_STATE_3 = 'L'
ARRAY_TYPE_DISTANCE = 'f'


HexIndex = NewType('HexIndex', int)
Sources = Iterable[HexIndex]
Path = Sequence[HexIndex]

CaptureCode = NewType('CaptureCode', int)
HexCode = NewType('HexCode', int)
MoveCode = NewType('MoveCode', int)
PathCode = NewType('PathCode', int)

BoardCodes = Sequence[HexCode]
PathCodes = Sequence[HexCode]

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)


def log(msg: str=None):
    if msg is None:
        print("", file=sys.stderr, flush=True)
    else:
        for line in msg.split('\n'):
            print(f"{line}", file=sys.stderr, flush=True)


class Setup:
    SetupT = TypeVar("SetupT", bound="Setup.T")

    @enum.unique
    class T(enum.IntEnum):
        CLASSIC = 0
        FULL_RANDOM = 1
        HALF_RANDOM = 2
        GIVEN = 3
        assert CLASSIC < FULL_RANDOM < HALF_RANDOM < GIVEN


    __TABLE_SETUP_FROM_NAME = {
        'classic':T.CLASSIC,
        'full-random':T.FULL_RANDOM,
        'half-random':T.HALF_RANDOM,
        'given':T.GIVEN}

    __TABLE_SETUP_TO_NAME = {setup:name for (name, setup) in __TABLE_SETUP_FROM_NAME.items()}


    @staticmethod
    def from_name(name: str) -> SetupT:
        return Setup.__TABLE_SETUP_FROM_NAME[name]


    @staticmethod
    def to_name(setup: SetupT) -> str:
        return Setup.__TABLE_SETUP_TO_NAME[setup]


    @staticmethod
    def get_names() -> Sequence[str]:
        return [Setup.to_name(setup) for setup in Setup.T]


@enum.unique
class Reward(enum.IntEnum):
    WIN = 1
    DRAW = 0
    LOSS = -1

    assert LOSS < DRAW < WIN
    assert DRAW == 0
    assert LOSS + WIN == DRAW


class Player:
    PlayerT = TypeVar("PlayerT", bound="Player.T")

    @enum.unique
    class T(enum.IntEnum):
        WHITE = 0
        BLACK = 1
        assert WHITE < BLACK


    def __init__(self):
        assert False


    @staticmethod
    def to_name(player: PlayerT) -> str:
        return "white" if player == Player.T.WHITE else "black"


class Cube:
    CubeT = TypeVar("CubeT", bound="Cube.T")

    @enum.unique
    class T(enum.IntEnum):
        ROCK = 0
        PAPER = 1
        SCISSORS = 2
        WISE = 3
        assert ROCK < PAPER < SCISSORS < WISE


    __TABLE_CUBE_FROM_NAME = {
        'R':(Player.T.WHITE, T.ROCK),
        'P':(Player.T.WHITE, T.PAPER),
        'S':(Player.T.WHITE, T.SCISSORS),
        'W':(Player.T.WHITE, T.WISE),

        'r':(Player.T.BLACK, T.ROCK),
        'p':(Player.T.BLACK, T.PAPER),
        's':(Player.T.BLACK, T.SCISSORS),
        'w':(Player.T.BLACK, T.WISE)}

    __TABLE_CUBE_TO_NAME = {(player, cube):name for (name, (player, cube)) in __TABLE_CUBE_FROM_NAME.items()}


    @staticmethod
    def beats(src: CubeT, dst: CubeT) -> bool:
        assert src in Cube.T
        assert dst in Cube.T
        return (src, dst) in ((Cube.T.ROCK, Cube.T.SCISSORS),
                              (Cube.T.SCISSORS, Cube.T.PAPER),
                              (Cube.T.PAPER, Cube.T.ROCK))

    @staticmethod
    def from_name(name: str) -> CubeT:
        return Cube.__TABLE_CUBE_FROM_NAME[name]


    @staticmethod
    def to_name(player: Player.T, cube: CubeT) -> str:
        return Cube.__TABLE_CUBE_TO_NAME[(player, cube)]


    @staticmethod
    def get_names() -> Sequence[str]:
        return list(sorted(Cube.__TABLE_CUBE_FROM_NAME.keys()))


class Notation:


    @enum.unique
    class SimpleCase(enum.Enum):

        INVALID = 'invalid'

        MOVE_CUBE = 'xx-xx'
        MOVE_STACK = 'xx=xx'

        MOVE_CUBE_MOVE_STACK = 'xx-xx=xx'
        MOVE_STACK_MOVE_CUBE = 'xx=xx-xx'


    def __init__(self):
        assert False


    @staticmethod
    def simplify_notation(notation: str) -> str:
        return notation.strip().replace(' ', '').replace('!', '')


    @staticmethod
    def classify_notation(notation: str) -> Tuple[SimpleCase, int]:
        notation_simplified = Notation.simplify_notation(notation)
        notation_case = Notation.classify_simple_notation(notation_simplified)

        # guess number of capture
        capture = 0
        if re.match(r"^.*!.*$ ", notation):
            capture += 1
            if re.match(r"^.*![^!]+!.*$ ", notation):
                capture += 1

        return (notation_case, capture)


    @staticmethod
    def classify_simple_notation(notation: str) -> SimpleCase:
        if re.match(r'^[a-i][1-9]-[a-i][1-9]$', notation):
            # move cube
            return Notation.SimpleCase.MOVE_CUBE

        if re.match(r'^[a-i][1-9]=[a-i][1-9]$', notation):
            # move stack
            return Notation.SimpleCase.MOVE_STACK

        if re.match(r'^[a-i][1-9]-[a-i][1-9]=[a-i][1-9]$', notation):
            # move cube move stack
            return Notation.SimpleCase.MOVE_CUBE_MOVE_STACK

        if re.match(r'^[a-i][1-9]=[a-i][1-9]-[a-i][1-9]$', notation):
            # move stack move cube
            return Notation.SimpleCase.MOVE_STACK_MOVE_CUBE

        return Notation.SimpleCase.INVALID


    @staticmethod
    def validate_simple_notation(action_input: str, action_names: Sequence[str]) -> Tuple[bool, str]:

        def split_actions(action_names: Sequence[str]) -> Mapping[Notation.SimpleCase, Set[str]]:
            action_cases = {}

            for this_name in action_names:
                this_case = Notation.classify_simple_notation(this_name)
                if this_case not in action_cases:
                    action_cases[this_case] = set()
                action_cases[this_case].add(this_name)

            return action_cases


        action_input_simplified = Notation.simplify_notation(action_input)

        validated = action_input in action_names or action_input_simplified in action_names

        if validated:
            message = "validated action"

        else:
            action_cases = split_actions(action_names)
            action_input_case = Notation.classify_simple_notation(action_input_simplified)

            if action_input_case == Notation.SimpleCase.INVALID:
                message = "invalid action syntax !"

            elif action_input_case not in action_cases:
                message = f"{action_input_case.value} : impossible action !"

            else:
                message = "invalid action !"

            # guess hints from each case of action
            action_hints = []
            for this_case in action_cases:
                # find the longest match from the start
                upper_length = min(len(action_input_simplified), len(this_case.value))
                match_length = 0

                for this_name in action_cases[this_case]:
                    for end in range(match_length, upper_length + 1):
                        if action_input_simplified[:end] == this_name[:end]:
                            match_length = max(match_length, end)
                        else:
                            break

                action_hints.append(action_input_simplified[:match_length] + this_case.value[match_length:])

            if len(action_hints) == 1:
                message += " hint : " + action_hints[0]
            else:
                message += " hints : " + "  ".join(action_hints)

        return (validated, message)


class Hexagon:

    @enum.unique
    class Direction(enum.IntEnum):
        PHI_090 = 0
        PHI_150 = 1
        PHI_210 = 2
        PHI_270 = 3
        PHI_330 = 4
        PHI_030 = 5
        assert PHI_090 < PHI_150 < PHI_210 < PHI_270 < PHI_330 < PHI_030

    HexagonDirection = TypeVar("HexagonDirection", bound="Hexagon.Direction")

    # >> Optimizatoin of 'Hexagon.DIRECTION_ITERATOR = Hexagon.Direction' in expressions like 'for direction in Hexagon.DIRECTION_ITERATOR'
    DIRECTION_ITERATOR = range(len(Direction))

    Self = TypeVar("Self", bound="HexState")

    NULL = 127 # >> Should be be representable as a byte

    __slots__ = ('name', 'position_uv', 'index')

    __all_indices = []
    __all_sorted_hexagons = []
    __init_done = False
    __goal_indices = []
    __layout = []
    __name_to_hexagon = {}
    __next_fst_indices = []
    __next_snd_indices = []
    __position_uv_to_hexagon = {}
    __distance = {}
    __distance_to_goal = [[]]


    all = None # shortcut to Hexagon.get_all()


    def __init__(self, name: str, position_uv= Tuple[int, int]):

        assert name not in Hexagon.__name_to_hexagon
        assert len(position_uv) == 2
        assert position_uv not in Hexagon.__position_uv_to_hexagon
        assert len(name) == 2

        self.name = name
        self.position_uv = position_uv
        self.index = None

        Hexagon.__name_to_hexagon[self.name] = self
        Hexagon.__position_uv_to_hexagon[position_uv] = self


    def __str__(self):
        return f"Hexagon({self.name}, {self.position_uv}, {self.index}"


    @staticmethod
    def distance(position_uv_1: Tuple[int, int], position_uv_2: Tuple[int, int]) -> float:
        """reference: https://www.redblobgames.com/grids/hexagons/#distances"""
        (u1, v1) = position_uv_1
        (u2, v2) = position_uv_2
        distance = (math.fabs(u1 - u2) + math.fabs(v1 - v2)+ math.fabs(u1 + v1 - u2 - v2))/2
        return distance


    @staticmethod
    def get(name: str) ->Self:
        return Hexagon.__name_to_hexagon[name]


    @staticmethod
    def get_all() -> Sequence[Self]:
        return Hexagon.__all_sorted_hexagons


    @staticmethod
    def get_all_indices() -> Sequence[HexIndex]:
        return Hexagon.__all_indices


    @staticmethod
    def get_goal_indices(player: Player.T) -> Sequence[HexIndex]:
        return Hexagon.__goal_indices[player]


    @staticmethod
    def get_layout() -> Sequence[Sequence[str]]:
        return Hexagon.__layout


    @staticmethod
    def get_next_fst_index(hexagon_index: HexIndex, hexagon_dir: HexagonDirection) -> HexIndex:
        return Hexagon.__next_fst_indices[hexagon_index][hexagon_dir]


    @staticmethod
    def get_next_snd_index(hexagon_index: HexIndex, hexagon_dir: HexagonDirection) -> HexIndex:
        return Hexagon.__next_snd_indices[hexagon_index][hexagon_dir]


    @staticmethod
    def get_distance(hexagon_1_index: HexIndex, hexagon_2_index: HexIndex) -> float:
        return Hexagon.__distance[(hexagon_1_index, hexagon_2_index)]


    @staticmethod
    def get_distance_to_goal(hexagon_index: HexIndex, player: Player.T) -> float:
        return Hexagon.__distance_to_goal[player][hexagon_index]


    @staticmethod
    def init():
        if not  Hexagon.__init_done:
            Hexagon.__create_hexagons()
            Hexagon.__create_all_sorted_hexagons()
            Hexagon.__create_layout()
            Hexagon.__create_goal_hexagons()
            Hexagon.__create_delta_u_and_v()
            Hexagon.__create_next_hexagons()
            Hexagon.__create_distance()
            Hexagon.__create_distance_to_goal()
            Hexagon.__init_done = True


    @staticmethod
    def print_hexagons():
        for hexagon in Hexagon.__all_sorted_hexagons:
            log(hexagon)


    @staticmethod
    def __create_all_sorted_hexagons():
        for name in sorted(Hexagon.__name_to_hexagon.keys()):
            Hexagon.__all_sorted_hexagons.append(Hexagon.__name_to_hexagon[name])

        for (index, hexagon) in enumerate(Hexagon.__all_sorted_hexagons):
            hexagon.index = index

        for hexagon in Hexagon.__all_sorted_hexagons:
            Hexagon.__all_indices.append(hexagon.index)

        Hexagon.all = Hexagon.__all_sorted_hexagons


    @staticmethod
    def __create_delta_u_and_v():
        Hexagon.__delta_u = array.array('b', [+1, +1, +0, -1, -1, +0])
        Hexagon.__delta_v = array.array('b', [+0, -1, -1, +0, +1, +1])


    @staticmethod
    def __create_goal_hexagons():

        white_goal_hexagons = ["g1", "g2", "g3", "g4", "g5", "g6"]
        black_goal_hexagons = ["a1", "a2", "a3", "a4", "a5", "a6"]

        white_goal_indices = array.array('b', map(lambda x: Hexagon.get(x).index, white_goal_hexagons))
        black_goal_indices = array.array('b', map(lambda x: Hexagon.get(x).index, black_goal_hexagons))

        Hexagon.__goal_indices = [None for _ in Player.T]

        Hexagon.__goal_indices[Player.T.WHITE] = white_goal_indices
        Hexagon.__goal_indices[Player.T.BLACK] = black_goal_indices


    @staticmethod
    def __create_layout():

        Hexagon.__layout = []

        Hexagon.__layout.append( (1, ["g1", "g2", "g3", "g4", "g5", "g6"]))
        Hexagon.__layout.append( (0, ["f1", "f2", "f3", "f4", "f5", "f6", "f7"]))
        Hexagon.__layout.append( (1, ["e1", "e2", "e3", "e4", "e5", "e6"]))
        Hexagon.__layout.append( (0, ["d1", "d2", "d3", "d4", "d5", "d6", "d7"]))
        Hexagon.__layout.append( (1, ["c1", "c2", "c3", "c4", "c5", "c6"]))
        Hexagon.__layout.append( (0, ["b1", "b2", "b3", "b4", "b5", "b6", "b7"]))
        Hexagon.__layout.append( (1, ["a1", "a2", "a3", "a4", "a5", "a6"]))


    @staticmethod
    def __create_next_hexagons():

        Hexagon.__next_fst_indices = [None for _ in Hexagon.__all_sorted_hexagons]
        Hexagon.__next_snd_indices = [None for _ in Hexagon.__all_sorted_hexagons]

        for (hexagon_index, hexagon) in enumerate(Hexagon.__all_sorted_hexagons):
            (hexagon_u, hexagon_v) = hexagon.position_uv

            Hexagon.__next_fst_indices[hexagon_index] = array.array('b', [Hexagon.NULL for _ in Hexagon.Direction])
            Hexagon.__next_snd_indices[hexagon_index] = array.array('b', [Hexagon.NULL for _ in Hexagon.Direction])

            for hexagon_dir in Hexagon.Direction:
                hexagon_delta_u = Hexagon.__delta_u[hexagon_dir]
                hexagon_delta_v = Hexagon.__delta_v[hexagon_dir]

                hexagon_fst_u = hexagon_u + 1*hexagon_delta_u
                hexagon_fst_v = hexagon_v + 1*hexagon_delta_v

                hexagon_snd_u = hexagon_u + 2*hexagon_delta_u
                hexagon_snd_v = hexagon_v + 2*hexagon_delta_v

                if (hexagon_fst_u, hexagon_fst_v) in Hexagon.__position_uv_to_hexagon:
                    hexagon_fst = Hexagon.__position_uv_to_hexagon[(hexagon_fst_u, hexagon_fst_v)]
                    Hexagon.__next_fst_indices[hexagon_index][hexagon_dir] = hexagon_fst.index

                    if (hexagon_snd_u, hexagon_snd_v) in Hexagon.__position_uv_to_hexagon:
                        hexagon_snd = Hexagon.__position_uv_to_hexagon[(hexagon_snd_u, hexagon_snd_v)]
                        Hexagon.__next_snd_indices[hexagon_index][hexagon_dir] = hexagon_snd.index


    @staticmethod
    def __create_distance():
        for hexagon_1 in Hexagon.get_all():
            for hexagon_2 in Hexagon.get_all():
                distance = Hexagon.distance(hexagon_1.position_uv, hexagon_2.position_uv)
                Hexagon.__distance[(hexagon_1.index, hexagon_2.index)] = distance


    @staticmethod
    def __create_distance_to_goal():

        Hexagon.__distance_to_goal = [array.array('b', [0 for _ in Hexagon.get_all()]) for _ in Player.T]

        for player in Player.T:
            for hexagon_cube in Hexagon.get_all():
                for hexagon_goal_index in Hexagon.get_goal_indices(player):
                    distance = Hexagon.get_distance(hexagon_cube.index, hexagon_goal_index)
                    Hexagon.__distance_to_goal[player][hexagon_cube.index] = int(distance)


    @staticmethod
    def __create_hexagons():

        # Row "a"
        Hexagon('a1', (-1, -3))
        Hexagon('a2', (-0, -3))
        Hexagon('a3', (1, -3))
        Hexagon('a4', (2, -3))
        Hexagon('a5', (3, -3))
        Hexagon('a6', (4, -3))

        # Row "b"
        Hexagon('b1', (-2, -2))
        Hexagon('b2', (-1, -2))
        Hexagon('b3', (0, -2))
        Hexagon('b4', (1, -2))
        Hexagon('b5', (2, -2))
        Hexagon('b6', (3, -2))
        Hexagon('b7', (4, -2))

        # Row "c"
        Hexagon('c1', (-2, -1))
        Hexagon('c2', (-1, -1))
        Hexagon('c3', (0, -1))
        Hexagon('c4', (1, -1))
        Hexagon('c5', (2, -1))
        Hexagon('c6', (3, -1))

        # Row "d"
        Hexagon('d1', (-3, 0))
        Hexagon('d2', (-2, 0))
        Hexagon('d3', (-1, 0))
        Hexagon('d4', (0, 0))
        Hexagon('d5', (1, 0))
        Hexagon('d6', (2, 0))
        Hexagon('d7', (3, 0))

        # Row "e"
        Hexagon('e1', (-3, 1))
        Hexagon('e2', (-2, 1))
        Hexagon('e3', (-1, 1))
        Hexagon('e4', (0, 1))
        Hexagon('e5', (1, 1))
        Hexagon('e6', (2, 1))

        # Row "f"
        Hexagon('f1', (-4, 2))
        Hexagon('f2', (-3, 2))
        Hexagon('f3', (-2, 2))
        Hexagon('f4', (-1, 2))
        Hexagon('f5', (0, 2))
        Hexagon('f6', (1, 2))
        Hexagon('f7', (2, 2))

        # Row "g"
        Hexagon('g1', (-4, 3))
        Hexagon('g2', (-3, 3))
        Hexagon('g3', (-2, 3))
        Hexagon('g4', (-1, 3))
        Hexagon('g5', (0, 3))
        Hexagon('g6', (1, 3))


class HexState:

    Self = TypeVar("Self", bound="HexState")

    CODE_BASE = HexCode((2*2*2)*(2*2*2)*2)
    CODE_BASE_2 = CODE_BASE*CODE_BASE
    CODE_BASE_3 = CODE_BASE_2*CODE_BASE

    __slots__ = ('is_empty', 'has_stack', 'player', 'bottom', 'top', '__code')

    def __init__(self,
                 is_empty: bool=True,
                 has_stack: bool=False,
                 player: Optional[Player.T]=None,
                 bottom: Optional[Cube.T]=None,
                 top: Optional[Cube.T]=None):

        if is_empty:
            assert not has_stack
            assert player is None
            assert bottom is None
            assert top is None
        else:
            assert player is not None

            if has_stack:
                assert bottom is not None and top is not None
                if top == Cube.T.WISE:
                    assert bottom == Cube.T.WISE
            else:
                assert bottom is not None and top is None

        self.is_empty = is_empty
        self.has_stack = has_stack
        self.player = player
        self.bottom = bottom
        self.top = top
        self.__code = None


    @staticmethod
    def make_empty() -> Self:
        return HexState()


    @staticmethod
    def make_single(player: Player.T, cube: Cube.T) -> Self:
        return HexState(player=player, bottom=cube, is_empty=False)


    @staticmethod
    def make_stack(player: Player.T, bottom: Cube.T, top: Cube.T) -> Self:
        return HexState(player=player, bottom=bottom, top=top, is_empty=False, has_stack=True)


    def __str__(self: Self) -> str:
        return ( f"HexState(is_empty={self.is_empty}" +
                 f", has_stack={self.has_stack}" +
                 f", player={self.player.name if self.player is not None else None}" +
                 f", bottom={self.bottom.name if self.bottom is not None else None}" +
                 f", top={self.top.name if self.top is not None else None})" )


    def __repr__(self: Self) -> str:
        return str(self)


    def __eq__(self, other: Self) -> bool:
        return (self.is_empty == other.is_empty and
                self.has_stack == other.has_stack and
                self.player == other.player and
                self.bottom == other.bottom and
                self.top == other.top)


    def encode(self) -> HexCode:
        if self.__code is None:
            code = 0
            code +=   (0 if self.is_empty else 1)
            code += 2*(1 if self.has_stack else 0)
            code += 4*(self.player.value if self.player is not None else 0)
            code += 8*(self.bottom.value if self.bottom is not None else 0)
            code += 32*(self.top.value if self.top is not None else 0)

            assert 0 <= code < HexState.CODE_BASE

            if self.is_empty:
                assert code == 0

            self.__code = code

        return self.__code


    @staticmethod
    def decode(code: HexCode) -> Self:

        assert 0 <= code < HexState.CODE_BASE

        is_empty = True
        has_stack = False
        player = None
        bottom = None
        top = None

        rest = code

        bit_empty = rest % 2
        rest = rest // 2
        is_empty = bit_empty == 0

        if not is_empty:
            bit_stack = rest % 2
            rest = rest // 2
            has_stack = bit_stack != 0

            bit_player = rest % 2
            rest = rest // 2
            player = tuple(Player.T)[bit_player]

            bits_bottom = rest % 4
            rest = rest // 4
            bottom = tuple(Cube.T)[bits_bottom]

            if has_stack:
                bits_top = rest % 4
                rest = rest // 4
                top = tuple(Cube.T)[bits_top]

        assert rest == 0

        return HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)


    @staticmethod
    def iterate_hex_states() -> Iterable[Self]:

        for is_empty in (True, False):

            if is_empty:
                has_stack = False
                player = None
                bottom = None
                top = None
                yield HexState(is_empty=is_empty,
                               has_stack=has_stack,
                               player=player,
                               bottom=bottom,
                               top=top)

            else:
                for player in Player.T:
                    for bottom in Cube.T:
                        for has_stack in (True, False):
                            if has_stack:
                                if bottom == Cube.T.WISE:
                                    for top in Cube.T:
                                        yield HexState(is_empty=is_empty,
                                                       has_stack=has_stack,
                                                       player=player,
                                                       bottom=bottom,
                                                       top=top)
                                else:
                                    for top in (Cube.T.ROCK, Cube.T.PAPER, Cube.T.SCISSORS):
                                        yield HexState(is_empty=is_empty,
                                                       has_stack=has_stack,
                                                       player=player,
                                                       bottom=bottom,
                                                       top=top)
                            else:
                                top = None
                                yield HexState(is_empty=is_empty,
                                               has_stack=has_stack,
                                               player=player,
                                               bottom=bottom,
                                               top=top)


PathStates = Sequence[HexState]
BoardStates = Sequence[HexState]


@dataclass
class PijersiAction:
    Self = TypeVar("Self", bound="PijersiAction")
    PijersiState = TypeVar("PijersiState", bound="PijersiState")

    next_board_codes: Optional[(BoardCodes)] = None
    path_vertices: Optional[Path] = None
    capture_code: Optional[CaptureCode] = None
    move_code: Optional[MoveCode] = None
    value: Optional[float] = None
    next_state: Optional[PijersiState] = None

    __TABLE_MOVE_CODE_TO_NAMES = [None for _ in range(4)]
    __TABLE_MOVE_CODE_TO_NAMES[0] = ['-', '']
    __TABLE_MOVE_CODE_TO_NAMES[1] = ['=', '-']
    __TABLE_MOVE_CODE_TO_NAMES[2] = ['-', '=']
    __TABLE_MOVE_CODE_TO_NAMES[3] = ['=', '-']

    __TABLE_CAPTURE_CODE_TO_NAMES = [None for _ in range(4)]
    __TABLE_CAPTURE_CODE_TO_NAMES[0] = ['', '']
    __TABLE_CAPTURE_CODE_TO_NAMES[1] = ['!', '']
    __TABLE_CAPTURE_CODE_TO_NAMES[2] = ['', '!']
    __TABLE_CAPTURE_CODE_TO_NAMES[3] = ['!', '!']


    def __str__(self: Self) -> str:

        hexagons = Hexagon.get_all()

        hex_names = [hexagons[hex_index].name for hex_index in self.path_vertices]
        move_names = PijersiAction.__TABLE_MOVE_CODE_TO_NAMES[self.move_code]
        capture_names = PijersiAction.__TABLE_CAPTURE_CODE_TO_NAMES[self.capture_code]

        action_name = hex_names[0]
        for (move_name, hex_name, capture_name) in zip(move_names, hex_names[1:], capture_names):
            action_name += move_name + hex_name + capture_name

        return action_name


    def __hash__(self):
        return hash((*self.path_vertices, self.move_code))


    def __lt__(self, other):
        return self.value < other.value


    def __le__(self, other):
        return self.value <= other.value


    def __gt__(self, other):
        return self.value > other.value


    def __ge__(self, other):
        return self.value >= other.value


    def __eq__(self, other):
        return self.value == other.value and self.path_vertices == other.path_vertices


class PijersiState:

    Self = TypeVar("Self", bound="PijersiState")

    __init_done = False
    __max_credit = 20
    __slots__ = ('__board_codes', '__player', '__credit', '__turn', '__setup',
                 '__actions',
                 '__actions_by_names', '__actions_by_simple_names', '__actions_by_ugi_names',
                 '__is_terminal_cache', '__has_action_cache', '__player_is_arrived_cache')


    __TABLE_HAS_CUBE = None
    __TABLE_HAS_STACK = None

    __TABLE_CUBE_COUNT = None

    __TABLE_HAS_FIGHTER = None
    __TABLE_FIGHTER_COUNT = None

    __TABLE_CUBE_COUNT_BY_SORT = None

    __TABLE_MAKE_PATH1 = None
    __TABLE_MAKE_PATH2 = None

    __TABLE_GOAL_INDICES = None
    __TABLE_GOAL_DISTANCES = None

    __TABLE_CENTER_DISTANCES = None

    __TABLE_TRY_CUBE_PATH1_NEXT_CODE = None
    __TABLE_TRY_CUBE_PATH1_CAPTURE_CODE = None

    __TABLE_TRY_STACK_PATH1_NEXT_CODE = None
    __TABLE_TRY_STACK_PATH1_CAPTURE_CODE = None

    __TABLE_TRY_STACK_PATH2_NEXT_CODE = None
    __TABLE_TRY_STACK_PATH2_CAPTURE_CODE = None


    def __init__(self,
                 board_codes: Optional[BoardCodes]=None,
                 player: Player.T=Player.T.WHITE,
                 credit: Optional[int]=None,
                 turn: int=1,
                 setup=Setup.T.CLASSIC):

        self.__board_codes = board_codes if board_codes is not None else PijersiState.setup_board_codes(setup)
        self.__player = player
        self.__credit = credit if credit is not None else PijersiState.__max_credit
        self.__turn = turn
        self.__setup = setup
        self.__actions = None
        self.__actions_by_names = None
        self.__actions_by_simple_names = None
        self.__actions_by_ugi_names = None
        self.__is_terminal_cache = None
        self.__has_action_cache = None
        self.__player_is_arrived_cache = None


    @staticmethod
    def init():


        def create_table_has_cube() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:
                    count = 1
                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_has_stack() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty and hex_state.has_stack:
                    count = 1
                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_cube_count() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:

                    if hex_state.has_stack:
                        count = 2
                    else:
                        count = 1

                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_has_fighter() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:

                    if hex_state.has_stack:
                        count = 0
                        count = max(count, 1 if hex_state.bottom != Cube.T.WISE else 0)
                        count = max(count, 1 if hex_state.top != Cube.T.WISE else 0)
                    else:
                        count = 1 if hex_state.bottom != Cube.T.WISE else 0

                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_fighter_count() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:

                    if hex_state.has_stack:
                        count = 0
                        count += 1 if hex_state.bottom != Cube.T.WISE else 0
                        count += 1 if hex_state.top != Cube.T.WISE else 0
                    else:
                        count = 1 if hex_state.bottom != Cube.T.WISE else 0

                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_cube_count_by_sort() ->Sequence[Sequence[Sequence[int]]] :
            table = [[array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)])
                       for _ in Cube.T] for _ in Player.T]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:
                    hex_code = hex_state.encode()

                    if hex_state.has_stack:
                        table[hex_state.player][hex_state.bottom][hex_code] += 1
                        table[hex_state.player][hex_state.top][hex_code] += 1
                    else:
                        table[hex_state.player][hex_state.bottom][hex_code] += 1

            return table


        def create_table_make_path1() -> Sequence[Optional[Sequence[int]]]:

            table = [[None for direction in Hexagon.Direction] for source in Hexagon.get_all_indices()]

            for source in Hexagon.get_all_indices():
                for direction in Hexagon.Direction:

                    path= None
                    next_fst_hex = Hexagon.get_next_fst_index(source, direction)
                    if next_fst_hex != Hexagon.NULL:
                        path = [source, next_fst_hex]

                    table[source][direction] = path

            return table


        def create_table_make_path2() -> Sequence[Optional[Sequence[int]]]:

            table = [[None for direction in Hexagon.Direction] for source in Hexagon.get_all_indices()]

            for source in Hexagon.get_all_indices():
                for direction in Hexagon.Direction:

                    path = None
                    next_fst_hex = Hexagon.get_next_fst_index(source, direction)
                    if next_fst_hex != Hexagon.NULL:
                        next_snd_hex = Hexagon.get_next_snd_index(source, direction)
                        if next_snd_hex != Hexagon.NULL:
                            path = [source, next_fst_hex, next_snd_hex]

                    table[source][direction] = path

            return table


        def create_table_goal_indices() -> Sequence[Sequence[int]]:
            return [Hexagon.get_goal_indices(player) for player in Player.T]


        def create_table_goal_distances() -> Sequence[Sequence[float]]:
            return [[Hexagon.get_distance_to_goal(hex_index, player)
                      for hex_index in Hexagon.get_all_indices()] for player in Player.T]


        def create_table_center_distances() -> Sequence[float]:
            table = array.array(ARRAY_TYPE_DISTANCE, [0 for _ in Hexagon.get_all_indices()])

            center_names = ['d3', 'd4', 'd5']
            center_indices = [Hexagon.get(hex_name).index for hex_name in center_names]

            for hex_index in Hexagon.get_all_indices():
                distances = []
                for center_index in center_indices:
                    distances.append(Hexagon.get_distance(hex_index, center_index))
                table[hex_index] = min(distances)

            return table


        def create_tables_try_cube_path1() -> Tuple[Sequence[PathCode], Sequence[CaptureCode]]:
            table_next_code = array.array(ARRAY_TYPE_STATE_2, [0 for _ in range(HexState.CODE_BASE_2)])
            table_has_capture = array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE_2)])

            for src_state in HexState.iterate_hex_states():
                for dst_state in HexState.iterate_hex_states():
                    code = PijersiState.encode_path_states([src_state, dst_state])

                    next_code = 0
                    capture_code = 0

                    next_src_state = None
                    next_dst_state = None

                    if not src_state.is_empty:

                        if dst_state.is_empty:
                            #-- Just moves without stacking rules involved
                            if src_state.has_stack:
                                next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)

                            else:
                                next_src_state = HexState.make_empty()
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)

                        elif dst_state.player == src_state.player:
                            # >> Stacking rules must be considered
                            if not dst_state.has_stack:
                                # == Destination has a single cube owned by the active player
                                if src_state.has_stack:
                                    if src_state.top != Cube.T.WISE or (src_state.top == Cube.T.WISE and dst_state.bottom == Cube.T.WISE):
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_stack(player=src_state.player, bottom=dst_state.bottom, top=src_state.top)

                                else:
                                    if src_state.bottom != Cube.T.WISE or (src_state.bottom == Cube.T.WISE and dst_state.bottom == Cube.T.WISE):
                                        next_src_state = HexState.make_empty()
                                        next_dst_state = HexState.make_stack(player=src_state.player, bottom=dst_state.bottom, top=src_state.bottom)

                        else:
                            # >> Capturing rules must be considered
                            if dst_state.has_stack:
                                # == Destination has a stack owned by the non-active player

                                if src_state.has_stack:
                                    if Cube.beats(src_state.top, dst_state.top):
                                        capture_code = 1
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)

                                else:
                                    if Cube.beats(src_state.bottom, dst_state.top):
                                        capture_code = 1
                                        next_src_state = HexState.make_empty()
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)

                            else:
                                # == Destination has a single cube owned by the non-active player

                                if src_state.has_stack:
                                    if Cube.beats(src_state.top, dst_state.bottom):
                                        capture_code = 1
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)
                                else:
                                    if Cube.beats(src_state.bottom, dst_state.bottom):
                                        capture_code = 1
                                        next_src_state = HexState.make_empty()
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)

                        if next_src_state is not None and next_dst_state is not None:
                            next_code = PijersiState.encode_path_states([next_src_state, next_dst_state])

                    table_next_code[code] = next_code
                    table_has_capture[code] = capture_code

            return (table_next_code, table_has_capture)


        def create_tables_try_stack_path(table_next_code: Sequence[PathCode] ,
                                       table_has_capture: Sequence[CaptureCode],
                                       next_mid_state=Optional[HexState]) -> None:

            for src_state in HexState.iterate_hex_states():
                for dst_state in HexState.iterate_hex_states():
                    code = PijersiState.encode_path_states([src_state, dst_state])

                    next_code = 0
                    capture_code = 0

                    next_src_state = None
                    next_dst_state = None

                    if not src_state.is_empty and src_state.has_stack:

                        if dst_state.is_empty:
                            #-- Just moves without stacking rules involved
                            next_src_state = HexState.make_empty()
                            next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)

                        elif dst_state.player != src_state.player:
                            # >> Capturing rules must be considered

                            if dst_state.has_stack:
                                # == Destination has a stack owned by the non-active player
                                if Cube.beats(src_state.top, dst_state.top):
                                    capture_code = 1
                                    next_src_state = HexState.make_empty()
                                    next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)

                            else:
                                # == Destination has a single cube owned by the non-active player
                                if Cube.beats(src_state.top, dst_state.bottom):
                                    capture_code = 1
                                    next_src_state = HexState.make_empty()
                                    next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)

                        if next_src_state is not None and next_dst_state is not None:

                            if next_mid_state is None:
                                next_code = PijersiState.encode_path_states([next_src_state, next_dst_state])

                            else:
                                next_code = PijersiState.encode_path_states([next_src_state, next_mid_state, next_dst_state])

                    table_next_code[code] = next_code
                    table_has_capture[code] = capture_code

            return (table_next_code, table_has_capture )


        def create_tables_try_stack_path1() -> Tuple[Sequence[PathCode], Sequence[CaptureCode]]:
            table_next_code = array.array(ARRAY_TYPE_STATE_2, [0 for _ in range(HexState.CODE_BASE_2)])
            table_has_capture = array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE_2)])

            create_tables_try_stack_path(table_next_code, table_has_capture, next_mid_state=None)

            return (table_next_code, table_has_capture)


        def create_tables_try_stack_path2() -> Tuple[Sequence[PathCode], Sequence[CaptureCode]]:
            table_next_code = array.array(ARRAY_TYPE_STATE_3, [0 for _ in range(HexState.CODE_BASE_2)])
            table_has_capture = array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE_2)])

            create_tables_try_stack_path(table_next_code, table_has_capture, next_mid_state=HexState.make_empty())

            return (table_next_code, table_has_capture)


        if not PijersiState.__init_done:

            PijersiState.__TABLE_HAS_CUBE = create_table_has_cube()
            PijersiState.__TABLE_HAS_STACK = create_table_has_stack()

            PijersiState.__TABLE_CUBE_COUNT = create_table_cube_count()

            PijersiState.__TABLE_HAS_FIGHTER = create_table_has_fighter()

            PijersiState.__TABLE_FIGHTER_COUNT= create_table_fighter_count()

            PijersiState.__TABLE_CUBE_COUNT_BY_SORT = create_table_cube_count_by_sort()

            PijersiState.__TABLE_MAKE_PATH1 = create_table_make_path1()
            PijersiState.__TABLE_MAKE_PATH2 = create_table_make_path2()

            PijersiState.__TABLE_GOAL_INDICES = create_table_goal_indices()
            PijersiState.__TABLE_GOAL_DISTANCES = create_table_goal_distances()
            PijersiState.__TABLE_CENTER_DISTANCES = create_table_center_distances()

            ( PijersiState.__TABLE_TRY_CUBE_PATH1_NEXT_CODE,
              PijersiState.__TABLE_TRY_CUBE_PATH1_CAPTURE_CODE ) =  create_tables_try_cube_path1()

            ( PijersiState.__TABLE_TRY_STACK_PATH1_NEXT_CODE,
              PijersiState.__TABLE_TRY_STACK_PATH1_CAPTURE_CODE ) = create_tables_try_stack_path1()

            ( PijersiState.__TABLE_TRY_STACK_PATH2_NEXT_CODE,
              PijersiState.__TABLE_TRY_STACK_PATH2_CAPTURE_CODE ) = create_tables_try_stack_path2()

            PijersiState.__init_done = True


    @staticmethod
    def print_tables():


        def print_table_has_cube():
            log()
            log("-- print_table_has_cube --")
            log(f"{PijersiState.__TABLE_HAS_CUBE}")


        def print_table_has_stack():
            log()
            log("-- print_table_has_stack --")
            log(f"{PijersiState.__TABLE_HAS_STACK}")


        def print_table_cube_count():
            log()
            log("-- print_table_cube_count --")
            log("f{PijersiState.__TABLE_CUBE_COUNT}")


        def print_table_has_fighter():
            log()
            log("-- print_table_has_fighter --")
            log(f"{PijersiState.__TABLE_HAS_FIGHTER}")


        def print_table_fighter_count():
            log()
            log("-- print_table_fighter_count --")
            log(f"{PijersiState.__TABLE_FIGHTER_COUNT}")


        def print_table_cube_count_by_sort():
            log()
            log("-- print_table_cube_count_by_sort --")
            log(f"{PijersiState.__TABLE_CUBE_COUNT_BY_SORT}")


        def print_table_make_path1():
            log()
            log("-- print_table_make_path1 --")
            log(f"{PijersiState.__TABLE_MAKE_PATH1}")


        def print_table_make_path2():
            log()
            log("-- print_table_make_path2 --")
            log(f"{PijersiState.__TABLE_MAKE_PATH2}")


        def print_table_goal_indices():
            log()
            log("-- print_table_goal_indices --")
            log(f"{PijersiState.__TABLE_GOAL_INDICES}")


        def print_table_goal_distances():
            log()
            log("-- print_table_goal_distances --")
            log(f"{PijersiState.__TABLE_GOAL_DISTANCES}")


        def print_table_center_distances():
            log()
            log("-- print_table_center_distances --")
            log(f"{PijersiState.__TABLE_CENTER_DISTANCES}")


        def print_tables_try_cube_path1():
            log()
            log("-- print_tables_try_cube_path1 --")
            log(f"{PijersiState.__TABLE_TRY_CUBE_PATH1_NEXT_CODE}")
            log(f"{PijersiState.__TABLE_TRY_CUBE_PATH1_CAPTURE_CODE}")


        def print_tables_try_stack_path1():
            log()
            log("-- print_tables_try_stack_path1 --")
            log(f"{PijersiState.__TABLE_TRY_STACK_PATH1_NEXT_CODE}")
            log(f"{PijersiState.__TABLE_TRY_STACK_PATH1_CAPTURE_CODE}")


        def print_tables_try_stack_path2():
            log()
            log("-- print_tables_try_stack_path2 --")
            log(f"{PijersiState.__TABLE_TRY_STACK_PATH2_NEXT_CODE}")
            log(f"{PijersiState.__TABLE_TRY_STACK_PATH2_CAPTURE_CODE}")


        print_table_cube_count()
        print_table_cube_count_by_sort()
        print_table_has_cube()
        print_table_has_stack()
        print_table_fighter_count()
        print_table_has_fighter()

        print_table_make_path1()
        print_table_make_path2()

        print_table_goal_indices()
        print_table_goal_distances()
        print_table_center_distances()

        print_tables_try_cube_path1()
        print_tables_try_stack_path1()
        print_tables_try_stack_path2()


    @staticmethod
    def get_max_credit() -> int:
        return PijersiState.__max_credit


    @staticmethod
    def set_max_credit(max_credit: int):
        assert max_credit > 0
        PijersiState.__max_credit = max_credit


    def get_credit(self) -> int:
        return self.__credit


    def get_setup(self) -> Setup.T:
        return self.__setup


    def get_current_player(self) -> Player.T:
        return self.__player


    def get_other_player(self) -> Player.T:
        return Player.T.BLACK if self.__player == Player.T.WHITE else Player.T.WHITE


    def get_turn(self) -> int:
        return self.__turn


    def is_terminal(self, use_cache: bool=True) -> bool:
        if not use_cache or self.__is_terminal_cache is None:
            self.__is_terminal_cache = (self.__player_is_arrived(Player.T.WHITE, use_cache) or
                                        self.__player_is_arrived(Player.T.BLACK, use_cache) or
                                        self.__credit == 0 or
                                        not self.__has_action(use_cache))
        return self.__is_terminal_cache


    def get_rewards(self) -> Optional[Tuple[Reward, Reward]]:

        if self.__player_is_arrived(Player.T.WHITE):
            return (Reward.WIN, Reward.LOSS)

        elif self.__player_is_arrived(Player.T.BLACK):
            return (Reward.LOSS, Reward.WIN)

        elif self.__credit == 0:
            return (Reward.DRAW, Reward.DRAW)

        elif not self.__has_action():

            if self.__player == Player.T.WHITE:
                return (Reward.LOSS, Reward.WIN)

            elif self.__player == Player.T.BLACK:
                return (Reward.WIN, Reward.LOSS)

        else:
            return None


    def get_actions(self, use_cache: bool=True) -> Sequence[PijersiAction]:

        if not use_cache or self.__actions is None:
            self.__actions = self.__find_all_actions()

        return self.__actions


    def get_action_names(self) -> Sequence[str]:

        if self.__actions_by_names is None:
            self.__actions_by_names = {str(action):action for action in self.get_actions()}
        return self.__actions_by_names.keys()


    def get_action_simple_names(self) -> Sequence[str]:

        if self.__actions_by_simple_names is None:
            self.__actions_by_simple_names = {str(action).replace('!', ''):action for action in self.get_actions()}
        return list(self.__actions_by_simple_names.keys())


    def get_action_ugi_names(self) -> Sequence[str]:

        if self.__actions_by_ugi_names is None:
            self.__actions_by_ugi_names = {}

            for action in self.get_actions():
                action_ugi_name = self.to_ugi_name(action)
                self.__actions_by_ugi_names[action_ugi_name] = action

        return list(self.__actions_by_ugi_names.keys())


    def get_action_by_name(self, action_name: str) -> PijersiAction:
        _ = self.get_action_names()
        return self.__actions_by_names[action_name]


    def get_action_by_simple_name(self, action_name: str) -> PijersiAction:
        _ = self.get_action_simple_names()
        return self.__actions_by_simple_names[action_name]


    def get_action_by_ugi_name(self, action_name: str) -> PijersiAction:
        _ = self.get_action_ugi_names()
        return self.__actions_by_ugi_names[action_name]



    def to_ugi_name(self, action: PijersiAction) -> Optional[str]:
        action_name = str(action).replace('!', '')

        if len(action_name) == 5:

            if action_name[2] == '=':
                action_ugi_name = action_name[0:2] + action_name[3:5] + action_name[3:5]

            else:
                action_ugi_name = action_name[0:2] + action_name[3:5]

                source_hex_state = HexState.decode(self.__board_codes[action.path_vertices[0]])
                if source_hex_state.has_stack:
                    action_ugi_name = action_name[0:2] + action_ugi_name

        elif len(action_name) == 8:
                action_ugi_name = action_name[0:2] + action_name[3:5] + action_name[6:8]

        else:
            action_ugi_name = None

        return action_ugi_name


    def take_action(self, action: PijersiAction, use_cache: bool=False) -> Self:
        if not use_cache or action.next_state is None:
            action.next_state = None
            action.next_state = PijersiState(board_codes=action.next_board_codes,
                                 player=self.get_other_player(),
                                 credit=max(0, self.__credit - 1) if action.capture_code == 0 else self.__max_credit,
                                 turn=self.__turn + 1,
                                 setup=self.__setup)

        return action.next_state


    def take_action_by_name(self, action_name: str) -> Self:
        action = self.get_action_names()[action_name.replace('!', '')]
        return self.take_action(action)


    def take_action_by_simple_name(self, action_name: str) -> Self:
        return self.take_action_by_name(action_name)


    def take_action_by_ugi_name(self, action_name: str) -> Self:
        action = self.get_action_by_ugi_name(action_name)
        return self.take_action(action)


    def get_fighter_counts(self)-> Sequence[int]:
        return [sum((PijersiState.__TABLE_FIGHTER_COUNT[player][hex_code] for hex_code in self.__board_codes)) for player in Player.T]


    def get_cube_counts(self)-> Sequence[int]:
        return [sum((PijersiState.__TABLE_CUBE_COUNT[player][hex_code] for hex_code in self.__board_codes)) for player in Player.T]


    def get_distances_to_goal(self) -> Sequence[Sequence[int]]:
        """White and black distances to goal"""

        distances_to_goal = [[] for player in Player.T]

        for player in Player.T:
            fighter_count = PijersiState.__TABLE_FIGHTER_COUNT[player]
            goal_distances = PijersiState.__TABLE_GOAL_DISTANCES[player]

            for (hex_index, hex_code) in enumerate(self.__board_codes):
                for _ in range(fighter_count[hex_code]):
                    distances_to_goal[player].append(goal_distances[hex_index])

        return distances_to_goal


    def get_distances_to_center(self) -> Sequence[Sequence[int]]:
        """White and black distances to center"""

        distances_to_center = [[] for player in Player.T]

        center_distances = PijersiState.__TABLE_CENTER_DISTANCES

        for player in Player.T:
            cube_count = PijersiState.__TABLE_CUBE_COUNT[player]

            for (hex_index, hex_code) in enumerate(self.__board_codes):
                for _ in range(cube_count[hex_code]):
                    distances_to_center[player].append(center_distances[hex_index])

        return distances_to_center


    def get_show_text(self) -> str:

        show_text = ""

        shift = " " * len("a1KR")

        for (row_shift_count, row_hexagon_names) in Hexagon.get_layout():

            row_text = shift*row_shift_count

            for hexagon_name in row_hexagon_names:

                row_text += hexagon_name
                hexagon = Hexagon.get(hexagon_name)
                hexagon_index = hexagon.index

                hex_state = HexState.decode(self.__board_codes[hexagon_index])

                if hex_state.is_empty:
                    row_text += ".."

                elif not hex_state.has_stack:
                    bottom_label = Cube.to_name(hex_state.player, hex_state.bottom)
                    row_text += "." + bottom_label

                elif hex_state.has_stack:
                    bottom_label = Cube.to_name(hex_state.player, hex_state.bottom)
                    top_label = Cube.to_name(hex_state.player, hex_state.top)
                    row_text += top_label + bottom_label

                row_text += shift
            show_text += row_text + "\n"

        return show_text


    def get_hex_states(self) -> Sequence[HexState]:
        return [HexState.decode(code) for code in self.__board_codes]


    def get_hex_states_as_ugi_fen(self) -> str:

        hex_rows = [hex_row for (_, hex_row) in Hexagon.get_layout()]

        hex_states = self.get_hex_states()

        fen_lines = []
        for hex_row in hex_rows:
            fen_line = ""
            empty_space_count = 0
            for hex_name in hex_row:
                hex_state = hex_states[Hexagon.get(hex_name).index]

                if hex_state.is_empty:
                    # Hexagon is empty
                    empty_space_count += 1

                elif hex_state.has_stack:
                    # Hexagon with a stack

                    if empty_space_count != 0:
                        fen_line += str(empty_space_count)
                        empty_space_count = 0

                    fen_line += Cube.to_name(hex_state.player, hex_state.bottom)
                    fen_line += Cube.to_name(hex_state.player, hex_state.top)

                elif hex_state.bottom is not None:
                    # Hexagon with a single cube at bottom

                    if empty_space_count != 0:
                        fen_line += str(empty_space_count)
                        empty_space_count = 0

                    fen_line += Cube.to_name(hex_state.player, hex_state.bottom)
                    fen_line += '-'

            if empty_space_count != 0:
                fen_line += str(empty_space_count)
                empty_space_count = 0

            fen_lines.append(fen_line)

        fen = '/'.join(fen_lines)
        return fen


    def get_ugi_fen(self) -> Sequence[str]:
        fen = [self.get_hex_states_as_ugi_fen()]

        if not self.is_terminal():

            if self.get_current_player() == Player.T.WHITE:
                fen.append('w')
            else:
                fen.append('b')

            turn = self.get_turn()
            credit = self.get_credit()
            max_credit = self.get_max_credit()

            full_move = (turn  + 1) // 2
            half_move = max_credit - credit

            fen.append(str(half_move))
            fen.append(str(full_move))

        return fen


    def get_board_codes(self) -> BoardCodes:
        return self.__board_codes


    def show(self):
        log()
        log(self.get_show_text())
        log()
        log(self.get_summary())


    def get_summary(self) -> str:

        counters = Counter()

        for player in Player.T:
            player_codes = [self.__board_codes[hex_index] for hex_index in PijersiState.__find_cube_sources(self.__board_codes, player)]

            for cube in Cube.T:
                player_cube_table = PijersiState.__TABLE_CUBE_COUNT_BY_SORT[player][cube]
                counters[Cube.to_name(player, cube)] = sum((player_cube_table[hex_code] for hex_code in player_codes))

        summary = (
            f"Turn {self.__turn} / player {Player.to_name(self.__player)} / credit {self.__credit} / " +
             "alive " + " ".join([f"{cube_name}:{cube_count}" for (cube_name, cube_count) in sorted(counters.items())]))

        return summary


    @staticmethod
    def decode_path_code(code: PathCode, path_length: int) -> PathCodes:
        assert code >= 0
        assert path_length >= 0

        path_codes = []

        rest = code
        for _ in range(path_length):
            hex_code = rest % HexState.CODE_BASE
            rest = rest // HexState.CODE_BASE
            path_codes.append(hex_code)

        assert rest == 0

        return path_codes


    @staticmethod
    def encode_path_states(path_states: PathStates) -> PathCode:
        return PijersiState.encode_path_codes([hex_state.encode() for hex_state in path_states])


    @staticmethod
    def encode_path_codes(path_codes: PathCodes) -> PathCode:

        code = 0
        shift = 1
        code_base = HexState.CODE_BASE
        for hex_code in path_codes:
            code += shift*hex_code
            shift *= code_base

        return code


    @staticmethod
    def decode_path_codes(path_codes: PathCodes) -> PathStates:
        return [HexState.decode(code) for code in path_codes]


    @staticmethod
    def copy_board_codes(board_codes: BoardCodes) -> BoardCodes :
        return bytearray(board_codes)


    @staticmethod
    def empty_board_codes() -> BoardCodes :
        board_codes = bytearray([0 for _ in Hexagon.get_all()])
        return board_codes


    @staticmethod
    def setup_board_codes(setup: Setup.T) -> BoardCodes :

        if setup == Setup.T.CLASSIC:
            return PijersiState.setup_classic_board_codes()

        elif setup == Setup.T.FULL_RANDOM:
            return PijersiState.setup_full_random_board_codes()

        elif setup == Setup.T.HALF_RANDOM:
            return PijersiState.setup_half_random_board_codes()

        elif setup == Setup.T.GIVEN:
            return PijersiState.empty_board_codes()


    @staticmethod
    def setup_classic_board_codes() -> BoardCodes :
        board_codes = PijersiState.empty_board_codes()

        #-- Whites

        PijersiState.set_stack_from_names(board_codes, 'b4', bottom_name='W', top_name='W')

        PijersiState.set_cube_from_names(board_codes, 'a1', 'R')
        PijersiState.set_cube_from_names(board_codes, 'a2', 'P')
        PijersiState.set_cube_from_names(board_codes, 'a3', 'S')
        PijersiState.set_cube_from_names(board_codes, 'a4', 'R')
        PijersiState.set_cube_from_names(board_codes, 'a5', 'P')
        PijersiState.set_cube_from_names(board_codes, 'a6', 'S')

        PijersiState.set_cube_from_names(board_codes, 'b1', 'P')
        PijersiState.set_cube_from_names(board_codes, 'b2', 'S')
        PijersiState.set_cube_from_names(board_codes, 'b3', 'R')

        PijersiState.set_cube_from_names(board_codes, 'b5', 'S')
        PijersiState.set_cube_from_names(board_codes, 'b6', 'R')
        PijersiState.set_cube_from_names(board_codes, 'b7', 'P')

        #-- Blacks

        PijersiState.set_stack_from_names(board_codes, 'f4', bottom_name='w', top_name='w')

        PijersiState.set_cube_from_names(board_codes, 'g6', 'r')
        PijersiState.set_cube_from_names(board_codes, 'g5', 'p')
        PijersiState.set_cube_from_names(board_codes, 'g4', 's')
        PijersiState.set_cube_from_names(board_codes, 'g3', 'r')
        PijersiState.set_cube_from_names(board_codes, 'g2', 'p')
        PijersiState.set_cube_from_names(board_codes, 'g1', 's')

        PijersiState.set_cube_from_names(board_codes, 'f7', 'p')
        PijersiState.set_cube_from_names(board_codes, 'f6', 's')
        PijersiState.set_cube_from_names(board_codes, 'f5', 'r')

        PijersiState.set_cube_from_names(board_codes, 'f3', 's')
        PijersiState.set_cube_from_names(board_codes, 'f2', 'r')
        PijersiState.set_cube_from_names(board_codes, 'f1', 'p')

        return board_codes


    @staticmethod
    def setup_full_random_board_codes() -> BoardCodes :
        board_codes = PijersiState.empty_board_codes()

        #-- Whites

        white_stack_hex = 'b4'
        white_cube_hexs = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6',  'b1', 'b2', 'b3', 'b5', 'b6', 'b7']

        white_cubes = ['W', 'W',  'R', 'R' , 'R', 'R',  'P', 'P', 'P', 'P',  'S', 'S', 'S', 'S']
        random.shuffle(white_cubes)

        white_cube_1 = white_cubes.pop()
        white_cube_2 = white_cubes.pop()

        if white_cube_1 == 'W':
            PijersiState.set_stack_from_names(board_codes, white_stack_hex, bottom_name=white_cube_1, top_name=white_cube_2)
        else:
            PijersiState.set_stack_from_names(board_codes, white_stack_hex, bottom_name=white_cube_2, top_name=white_cube_1)

        for (white_cube_hex, white_cube) in zip(white_cube_hexs, white_cubes):
            PijersiState.set_cube_from_names(board_codes, white_cube_hex, white_cube)

        #-- Blacks

        black_stack_hex = 'f4'
        black_cube_hexs = ['g1', 'g2', 'g3', 'g4', 'g5', 'g6',  'f1', 'f2', 'f3', 'f5', 'f6', 'f7']

        black_cubes = ['w', 'w',  'r', 'r' , 'r', 'r',  'p', 'p', 'p', 'p',  's', 's', 's', 's']
        random.shuffle(black_cubes)

        black_cube_1 = black_cubes.pop()
        black_cube_2 = black_cubes.pop()

        if black_cube_1 == 'w':
            PijersiState.set_stack_from_names(board_codes, black_stack_hex, bottom_name=black_cube_1, top_name=black_cube_2)
        else:
            PijersiState.set_stack_from_names(board_codes, black_stack_hex, bottom_name=black_cube_2, top_name=black_cube_1)

        for (black_cube_hex, black_cube) in zip(black_cube_hexs, black_cubes):
            PijersiState.set_cube_from_names(board_codes, black_cube_hex, black_cube)

        return board_codes


    @staticmethod
    def setup_half_random_board_codes() -> BoardCodes :
        board_codes = PijersiState.empty_board_codes()

        #-- Whites

        white_stack_hex = 'b4'
        white_cube_hexs = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6',  'b1', 'b2', 'b3', 'b5', 'b6', 'b7']

        white_cubes = ['W', 'W',  'R', 'R' , 'R', 'R',  'P', 'P', 'P', 'P',  'S', 'S', 'S', 'S']
        random.shuffle(white_cubes)

        # >> black sorts version of white sorts
        # >> make it before "poping" white_cubes !
        black_cubes = list(map(str.lower, white_cubes))

        white_cube_1 = white_cubes.pop()
        white_cube_2 = white_cubes.pop()

        if white_cube_1 == 'W':
            PijersiState.set_stack_from_names(board_codes, white_stack_hex, bottom_name=white_cube_1, top_name=white_cube_2)
        else:
            PijersiState.set_stack_from_names(board_codes, white_stack_hex, bottom_name=white_cube_2, top_name=white_cube_1)

        for (white_cube_hex, white_cube) in zip(white_cube_hexs, white_cubes):
            PijersiState.set_cube_from_names(board_codes, white_cube_hex, white_cube)

        #-- Blacks

        # >> symmetrical hexagons of white_stack_hex and white_cube_hexs
        black_stack_hex = 'f4'
        black_cube_hexs = ['g6', 'g5', 'g4', 'g3', 'g2', 'g1',  'f7', 'f6', 'f5', 'f3', 'f2', 'f1']

        black_cube_1 = black_cubes.pop()
        black_cube_2 = black_cubes.pop()

        if black_cube_1 == 'w':
            PijersiState.set_stack_from_names(board_codes, black_stack_hex, bottom_name=black_cube_1, top_name=black_cube_2)
        else:
            PijersiState.set_stack_from_names(board_codes, black_stack_hex, bottom_name=black_cube_2, top_name=black_cube_1)

        for (black_cube_hex, black_cube) in zip(black_cube_hexs, black_cubes):
            PijersiState.set_cube_from_names(board_codes, black_cube_hex, black_cube)

        return board_codes


    @staticmethod
    def setup_from_ugi_fen(fen: str) -> BoardCodes :
        board_codes = PijersiState.empty_board_codes()

        fen_canonized = ""
        for fen_item in fen:
            if fen_item in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                fen_canonized += int(fen_item)*'--'
            else:
                fen_canonized += fen_item

        fen_lines = fen_canonized.split('/')

        hex_rows = [hex_row for (_, hex_row) in Hexagon.get_layout()]

        for (fen_line, hex_row)  in zip(fen_lines, hex_rows):

            hex_named_states = zip(fen_line[::2], fen_line[1::2])

            for ((bottom_name, top_name), hex_name) in zip(hex_named_states, hex_row):

                if bottom_name != '-' and top_name != '-':
                    PijersiState.set_stack_from_names(board_codes, hex_name, bottom_name=bottom_name, top_name=top_name)

                elif bottom_name != '-' and top_name == '-':
                    PijersiState.set_cube_from_names(board_codes, hex_name, bottom_name)

                else:
                    assert bottom_name == '-' and top_name == '-'

        return board_codes


    @staticmethod
    def set_cube_from_names(board_codes: BoardCodes, hex_name: str, cube_name: str):
        hex_index = Hexagon.get(hex_name).index
        (player, cube) = Cube.from_name(cube_name)
        PijersiState.set_cube(board_codes, hex_index, player, cube)


    @staticmethod
    def set_stack_from_names(board_codes: BoardCodes, hex_name: str, bottom_name: str, top_name: str):
        hex_index = Hexagon.get(hex_name).index
        (player, bottom) = Cube.from_name(bottom_name)
        (top_player, top) = Cube.from_name(top_name)
        assert top_player == player
        if top == Cube.T.WISE:
            assert bottom == Cube.T.WISE
        PijersiState.set_stack(board_codes, hex_index, player, bottom, top)


    @staticmethod
    def set_cube(board_codes: BoardCodes, hex_index: HexIndex, player: Player.T, cube: Cube.T):
        hex_state = HexState.decode(board_codes[hex_index])

        assert hex_state.is_empty

        hex_state.is_empty = False
        hex_state.player = player
        hex_state.bottom = cube
        board_codes[hex_index] = hex_state.encode()


    @staticmethod
    def set_stack(board_codes: BoardCodes, hex_index: HexIndex, player: Player.T, bottom: Cube.T, top: Cube.T):
        hex_state = HexState.decode(board_codes[hex_index])

        assert hex_state.is_empty

        hex_state.is_empty = False
        hex_state.has_stack = True
        hex_state.player = player
        hex_state.bottom = bottom
        hex_state.top = top
        board_codes[hex_index] = hex_state.encode()


    def __player_is_arrived(self, player: Player.T, use_cache: bool=True) -> bool:

        if not use_cache or self.__player_is_arrived_cache is None:
            self.__player_is_arrived_cache = [None for _ in Player.T]

            for cache_player in Player.T:

                goal_indices = PijersiState.__TABLE_GOAL_INDICES[cache_player]
                has_fighter = PijersiState.__TABLE_HAS_FIGHTER[cache_player]

                self.__player_is_arrived_cache[cache_player] = sum((has_fighter[self.__board_codes[hex_index]] for hex_index in goal_indices)) != 0

        return self.__player_is_arrived_cache[player]


    def __has_action(self, use_cache: bool=True) -> bool:

        if not use_cache or self.__has_action_cache is None:

            self.__has_action_cache = False

            for cube_source in PijersiState.__find_cube_sources(self.__board_codes, self.__player):
                for cube_direction in Hexagon.DIRECTION_ITERATOR:
                    if PijersiState.__try_cube_path1_action(self.__board_codes, cube_source, cube_direction) is not None:
                        self.__has_action_cache = True
                        break

        return self.__has_action_cache


    @staticmethod
    def __find_cube_sources(board_codes: BoardCodes, player: Player.T) -> Sources:
        table_code = PijersiState.__TABLE_HAS_CUBE[player]
        return (hex_index for (hex_index, hex_code) in enumerate(board_codes) if table_code[hex_code] != 0)


    def __find_all_actions(self) -> Sequence[PijersiAction]:

        actions = []

        for cube_source_1 in PijersiState.__find_cube_sources(self.__board_codes, self.__player):

            for cube_direction_1 in Hexagon.DIRECTION_ITERATOR:

                #-- all first moves using a cube
                action1 = PijersiState.__try_cube_path1_action(self.__board_codes, cube_source_1, cube_direction_1)
                if action1 is not None:
                    actions.append(action1)

                    board_codes_1 = action1.next_board_codes
                    stack_source_1 = action1.path_vertices[-1]
                    if PijersiState.__TABLE_HAS_STACK[self.__player][board_codes_1[stack_source_1]] != 0:
                        for stack_direction_1 in Hexagon.DIRECTION_ITERATOR:
                            action21 = PijersiState.__try_stack_path1_action(board_codes_1, stack_source_1, stack_direction_1)
                            if action21 is not None:
                                action21 = PijersiAction(next_board_codes=action21.next_board_codes,
                                                  path_vertices=action1.path_vertices + [action21.path_vertices[-1]],
                                                  capture_code=action1.capture_code + 2*action21.capture_code,
                                                  move_code=action1.move_code + 2*action21.move_code)
                                actions.append(action21)

                                action22 = PijersiState.__try_stack_path2_action(board_codes_1, stack_source_1, stack_direction_1)
                                if action22 is not None:
                                    action22 = PijersiAction(next_board_codes=action22.next_board_codes,
                                                      path_vertices=action1.path_vertices + [action22.path_vertices[-1]],
                                                      capture_code=action1.capture_code + 2*action22.capture_code,
                                                      move_code=action1.move_code + 2*action22.move_code)
                                    actions.append(action22)

                    #-- all first moves using a stack
                    stack_source_2 = cube_source_1
                    stack_direction_2 = cube_direction_1

                    if PijersiState.__TABLE_HAS_STACK[self.__player][self.__board_codes[stack_source_2]] != 0:
                        action11 = PijersiState.__try_stack_path1_action(self.__board_codes, stack_source_2, stack_direction_2)
                        if action11 is not None:
                            actions.append(action11)

                            board_codes_11 = action11.next_board_codes
                            cube_source_2 = action11.path_vertices[-1]
                            for cube_direction_2 in Hexagon.DIRECTION_ITERATOR:
                                action12 = PijersiState.__try_cube_path1_action(board_codes_11, cube_source_2, cube_direction_2)
                                if action12 is not None:
                                    action12 = PijersiAction(next_board_codes=action12.next_board_codes,
                                                     path_vertices=action11.path_vertices + [action12.path_vertices[-1]],
                                                     capture_code=action11.capture_code + 2*action12.capture_code,
                                                     move_code=action11.move_code + 2*action12.move_code)
                                    actions.append(action12)

                            action21 = PijersiState.__try_stack_path2_action(self.__board_codes, stack_source_2, stack_direction_2)
                            if action21 is not None:
                                actions.append(action21)

                                board_codes_21 = action21.next_board_codes
                                cube_source_2 = action21.path_vertices[-1]
                                for cube_direction_2 in Hexagon.DIRECTION_ITERATOR:
                                    action22 = PijersiState.__try_cube_path1_action(board_codes_21, cube_source_2, cube_direction_2)
                                    if action22 is not None:
                                        action22 = PijersiAction(next_board_codes=action22.next_board_codes,
                                                         path_vertices=action21.path_vertices + [action22.path_vertices[-1]],
                                                         capture_code=action21.capture_code + 2*action22.capture_code,
                                                         move_code=action21.move_code + 2*action22.move_code )
                                        actions.append(action22)

        return actions


    @staticmethod
    def __encode_path2_codes(path_codes: PathCodes) -> PathCode:
        # >> optimization of 'encode_path_codes' for path2
        return path_codes[0] + path_codes[1]*HexState.CODE_BASE


    @staticmethod
    def __decode_path2_code(code: PathCode) -> PathCodes:
        # >> optimization of 'decode_path_code' for path2
        return (code % HexState.CODE_BASE,
                (code // HexState.CODE_BASE) % HexState.CODE_BASE)


    @staticmethod
    def __decode_path3_code(code: PathCode) -> PathCodes:
        # >> optimization of 'decode_path_code' for path2
        return(code % HexState.CODE_BASE,
               (code // HexState.CODE_BASE) % HexState.CODE_BASE,
               (code // HexState.CODE_BASE_2) % HexState.CODE_BASE)


    @staticmethod
    def __try_path1(path_codes: PathCodes,
                  table_next_code: Sequence[HexCode],
                  table_has_capture: Sequence[bool]) -> Tuple[Optional[PathCodes], bool]:

        code = PijersiState.__encode_path2_codes(path_codes)
        next_code = table_next_code[code]

        if next_code != 0:
            next_path_codes = PijersiState.__decode_path2_code(next_code)
            capture_code = table_has_capture[code]

        else:
            next_path_codes = None
            capture_code = False

        return (next_path_codes, capture_code)


    @staticmethod
    def __try_path2(path_codes: PathCodes,
                  table_next_code: Sequence[HexCode],
                  table_has_capture: Sequence[bool]) -> Tuple[Optional[PathCodes], bool]:

        next_path_codes = None
        capture_code = False

        # >> Optimization: if the intermediate hexagon is not empty then the stack cannot cross it
        # >> Such optimization is reducing the size of the index domain of table_next_code and table_has_capture
        if path_codes[1] == 0:
            code = PijersiState.__encode_path2_codes([path_codes[0], path_codes[2]])
            next_code = table_next_code[code]

            if next_code != 0:
                # >> next_code is encoding a three hexagons path state
                next_path_codes = PijersiState.__decode_path3_code(next_code)
                capture_code = table_has_capture[code]

        return (next_path_codes, capture_code)


    @staticmethod
    def __try_cube_path1(path_codes: PathCodes) -> Tuple[Optional[PathCodes], bool]:
        return PijersiState.__try_path1(path_codes, PijersiState.__TABLE_TRY_CUBE_PATH1_NEXT_CODE, PijersiState.__TABLE_TRY_CUBE_PATH1_CAPTURE_CODE)


    @staticmethod
    def __try_stack_path1(path_codes: PathCodes) -> Tuple[Optional[PathCodes], bool]:
        return PijersiState.__try_path1(path_codes, PijersiState.__TABLE_TRY_STACK_PATH1_NEXT_CODE, PijersiState.__TABLE_TRY_STACK_PATH1_CAPTURE_CODE)


    @staticmethod
    def __try_stack_path2(path_codes: PathCodes) -> Tuple[PathCodes, bool]:
        return PijersiState.__try_path2(path_codes, PijersiState.__TABLE_TRY_STACK_PATH2_NEXT_CODE, PijersiState.__TABLE_TRY_STACK_PATH2_CAPTURE_CODE)


    @staticmethod
    def __apply_path2_codes(board_codes: BoardCodes, path: Path, path_codes: PathCodes) -> BoardCodes:
        next_board_codes = PijersiState.copy_board_codes(board_codes)

        next_board_codes[path[0]] = path_codes[0]
        next_board_codes[path[1]] = path_codes[1]
        return next_board_codes


    @staticmethod
    def __apply_path3_codes(board_codes: BoardCodes, path: Path, path_codes: PathCodes) -> BoardCodes:
        next_board_codes = PijersiState.copy_board_codes(board_codes)
        next_board_codes[path[0]] = path_codes[0]
        next_board_codes[path[1]] = path_codes[1]
        next_board_codes[path[2]] = path_codes[2]
        return next_board_codes


    @staticmethod
    def __try_cube_path1_action(board_codes: BoardCodes, source: HexIndex, direction: Hexagon.Direction) -> Optional[PijersiAction]:

        path = PijersiState.__TABLE_MAKE_PATH1[source][direction]
        if path is not None:
            path_codes = [board_codes[path[0]],  board_codes[path[1]]]
            (next_path_codes, capture_code) = PijersiState.__try_cube_path1(path_codes)
            if next_path_codes is not None:
                action = PijersiAction(next_board_codes=PijersiState.__apply_path2_codes(board_codes, path, next_path_codes),
                                path_vertices=[source, path[-1]],
                                capture_code=capture_code,
                                move_code=0)
            else:
                action = None
        else:
            action = None

        return action


    @staticmethod
    def __try_stack_path1_action(board_codes: BoardCodes, source: HexIndex, direction: Hexagon.Direction) -> Optional[PijersiAction]:

        path = PijersiState.__TABLE_MAKE_PATH1[source][direction]
        if path is not None:
            path_codes = [board_codes[path[0]],  board_codes[path[1]]]
            (next_path_codes, capture_code) = PijersiState.__try_stack_path1(path_codes)
            if next_path_codes is not None:
                action = PijersiAction(next_board_codes=PijersiState.__apply_path2_codes(board_codes, path, next_path_codes),
                                path_vertices=[source, path[-1]],
                                capture_code=capture_code,
                                move_code=1)
            else:
                action = None
        else:
            action = None

        return action

    @staticmethod
    def __try_stack_path2_action(board_codes: BoardCodes, source: HexIndex, direction: Hexagon.Direction) -> Optional[PijersiAction]:

        path = PijersiState.__TABLE_MAKE_PATH2[source][direction]
        if path is not None:
            path_codes= [board_codes[path[0]],  board_codes[path[1]], board_codes[path[2]]]
            (next_path_codes, capture_code) = PijersiState.__try_stack_path2(path_codes)
            if next_path_codes is not None:
                action = PijersiAction(next_board_codes=PijersiState.__apply_path3_codes(board_codes, path, next_path_codes),
                                path_vertices=[source, path[-1]],
                                capture_code=capture_code,
                                move_code=1)
            else:
                action = None
        else:
            action = None

        return action


class Searcher():

    __slots__ = ('__name', '__time_limit')


    def __init__(self, name):
        self.__name = name
        self.__time_limit = None


    def get_name(self) -> str:
        return self.__name


    def set_time_limit(self, time_limit: Optional[int]):
        if time_limit is not None:
            assert time_limit > 0
        self.__time_limit = time_limit


    def get_time_limit(self) -> Optional[int]:
        return self.__time_limit


    def is_interactive(self) -> bool:
        return False


    def search(self, state: PijersiState) -> PijersiAction:
        actions = state.get_actions()
        action = actions[0]
        return action


class RandomSearcher(Searcher):


    def search(self, state: PijersiState) -> PijersiAction:
        actions = state.get_actions()
        # >> sorting help for testing against other implementations if random generators are identical
        actions.sort(key=str)
        action = random.choice(actions)
        return action


class HumanSearcher(Searcher):

    __slots__ = ('__action_simple_name', '__use_command_line')


    def __init__(self, name: str):
        super().__init__(name)
        self.__action_simple_name = None
        self.__use_command_line = False


    def is_interactive(self) -> bool:
        return True


    def use_command_line(self, condition: bool):
        assert condition in (True, False)
        self.__use_command_line = condition


    def set_action_simple_name(self, action_name: str):
        assert not self.__use_command_line
        self.__action_simple_name = action_name


    def search(self, state: PijersiState) -> PijersiAction:

        if self.__use_command_line:
            return self.__search_using_command_line(state)

        action = state.get_action_by_simple_name(self.__action_simple_name)
        self.__action_simple_name = None
        return action


    def __search_using_command_line(self, state: PijersiState) -> PijersiAction:
        assert self.__use_command_line

        action_names = state.get_action_simple_names()

        action_validated = False
        while not action_validated:
            action_input = Notation.simplify_notation(input("HumanSearcher: action? "))
            (action_validated, validation_message) = Notation.validate_simple_notation(action_input, action_names)
            log(validation_message)

        action = state.get_action_by_simple_name(action_input)

        log(f"HumanSearcher: action {action} has been selected")

        return action


class MinimaxState:
    """Adaptater of PijersiState for MinixmaxSearcher"""

    Self = TypeVar("Self", bound="MinimaxState")

    __slots__ = ('__pijersi_state', '__maximizer_player')


    def __init__(self, pijersi_state: PijersiState, maximizer_player: Player.T):
        self.__pijersi_state = pijersi_state
        self.__maximizer_player = maximizer_player


    def get_pijersi_state(self) -> PijersiState:
        return self.__pijersi_state


    def get_current_maximizer_player(self) -> Player.T:
        return self.__maximizer_player


    def get_current_minimizer_player(self) -> Player.T:
        return Player.T.BLACK if self.__maximizer_player == Player.T.WHITE else Player.T.WHITE


    def is_terminal(self) -> bool:
        return self.__pijersi_state.is_terminal()


    def get_reward(self) -> int:
        """Returns the reward for this state: 0 for a draw,
        positive for a win by maximizer player or negative for a win by the minimizer player.
        Only needed for terminal states."""

        pijersi_rewards = self.__pijersi_state.get_rewards()

        if pijersi_rewards[self.__maximizer_player] == Reward.DRAW:
            minimax_reward = 0

        elif pijersi_rewards[self.__maximizer_player] == Reward.WIN:
            minimax_reward = 1

        else:
            minimax_reward = -1

        return minimax_reward


    def get_actions(self) -> Sequence[PijersiAction]:
        return self.__pijersi_state.get_actions()


    def take_action(self, action: PijersiAction, use_cache=False) -> Self:
        return MinimaxState(self.__pijersi_state.take_action(action, use_cache), self.__maximizer_player)


class StateEvaluator():
    """State evaluator for MinimaxSearcher"""

    __slots__ = ('__cube_weight', '__fighter_weight',
                 '__dg_min_weight', '__dg_ave_weight', '__dc_ave_weight', '__credit_weight',
                 '__debugging')


    def __init__(self, cube_weight: Optional[float]=None,
                  fighter_weight: Optional[float]=None,
                  dg_min_weight: Optional[float]=None,
                  dg_ave_weight: Optional[float]=None,
                  dc_ave_weight: Optional[float]=None,
                  credit_weight: Optional[float]=None):

        default_weights = {'fighter_weight':16,
                           'cube_weight':8,
                           'dg_min_weight':4,
                           'dc_ave_weight':2,
                           'dg_ave_weight':2,
                           'credit_weight':1}

        self.__debugging = False

        self.__dg_min_weight = dg_min_weight if dg_min_weight is not None else default_weights['dg_min_weight']
        self.__dg_ave_weight = dg_ave_weight if dg_ave_weight is not None else default_weights['dg_ave_weight']
        self.__cube_weight = cube_weight if cube_weight is not None else default_weights['cube_weight']
        self.__fighter_weight = fighter_weight if fighter_weight is not None else default_weights['fighter_weight']
        self.__dc_ave_weight = dc_ave_weight if dc_ave_weight is not None else default_weights['dc_ave_weight']
        self.__credit_weight = credit_weight if credit_weight is not None else default_weights['credit_weight']

        # normalize weights
        max_weight = max(math.fabs(self.__dg_min_weight),
                         math.fabs(self.__dg_ave_weight),
                         math.fabs(self.__cube_weight),
                         math.fabs(self.__fighter_weight),
                         math.fabs(self.__dc_ave_weight),
                         math.fabs(self.__credit_weight))

        scale_weight = 64/max_weight

        self.__dg_min_weight *= scale_weight
        self.__dg_ave_weight *= scale_weight
        self.__cube_weight *= scale_weight
        self.__fighter_weight *= scale_weight
        self.__dc_ave_weight *= scale_weight
        self.__credit_weight *= scale_weight


    def evaluate_state_value(self, state: MinimaxState, depth: int) -> float:
        # evaluate favorability for maximizer

        assert depth >= 0

        value = 0

        pijersi_state = state.get_pijersi_state()

        maximizer = state.get_current_maximizer_player()
        minimizer = state.get_current_minimizer_player()


        if pijersi_state.is_terminal():

            # >> amplify terminal value using the depth (rationale: winning faster is safer)

            maximizer_reward = pijersi_state.get_rewards()[maximizer]

            if maximizer_reward == Reward.WIN:
                value = OMEGA_2*(depth + 1)

            elif maximizer_reward == Reward.LOSS:
                value = (-OMEGA_2)*(depth + 1)

            elif maximizer_reward == Reward.DRAW:
                # >> no minus sign because the DRAW applies to both maximizer and minimizer
                value = OMEGA*(depth + 1)

        else:

            dg_min_norm = 8
            dg_ave_norm = dg_min_norm
            dc_ave_norm = 3
            cube_norm = 14
            fighter_norm = 12
            credit_norm = PijersiState.get_max_credit()

            # maximizer and minimizer distances to goal
            distances_to_goal = pijersi_state.get_distances_to_goal()

            if not distances_to_goal[maximizer]:
                distances_to_goal[maximizer] = [dg_min_norm]

            if not distances_to_goal[minimizer]:
                distances_to_goal[minimizer] = [dg_min_norm]

            maximizer_dg_min = min(distances_to_goal[maximizer])
            minimizer_dg_min = min(distances_to_goal[minimizer])

            maximizer_ave_dg = mean(distances_to_goal[maximizer])
            minimizer_ave_dg = mean(distances_to_goal[minimizer])

            dg_min_difference = (minimizer_dg_min - maximizer_dg_min)
            dg_ave_difference = (minimizer_ave_dg - maximizer_ave_dg)

            # maximizer and minimizer distances to center
            distances_to_center = pijersi_state.get_distances_to_center()

            if not distances_to_center[maximizer]:
                distances_to_center[maximizer] = [dc_ave_norm]

            if not distances_to_center[minimizer]:
                distances_to_center[minimizer] = [dc_ave_norm]

            maximizer_ave_dc = mean(distances_to_center[maximizer])
            minimizer_ave_dc = mean(distances_to_center[minimizer])

            dc_ave_difference = (minimizer_ave_dc - maximizer_ave_dc)


            # white and black with alive cubes
            cube_counts = pijersi_state.get_cube_counts()
            cube_difference = (cube_counts[maximizer] - cube_counts[minimizer])

            # white and black with alive fighters
            fighter_counts = pijersi_state.get_fighter_counts()
            fighter_difference = (fighter_counts[maximizer] - fighter_counts[minimizer])

            # credit acts symmetrically for white and black
            credit = pijersi_state.get_credit()

            # normalize each feature in the intervall [-1, +1]

            if self.__debugging:
                assert dg_min_difference <= dg_min_norm
                assert -dg_min_difference <= dg_min_norm

                assert dg_ave_difference <= dg_ave_norm
                assert -dg_ave_difference <= dg_ave_norm

                assert dc_ave_difference <= dc_ave_norm
                assert -dc_ave_difference <= dc_ave_norm

                assert cube_difference <= cube_norm
                assert -cube_difference <= cube_norm

                assert fighter_difference <= fighter_norm
                assert -fighter_difference <= fighter_norm

                assert credit <= credit_norm
                assert -credit <= credit_norm

            dg_min_difference = dg_min_difference/dg_min_norm
            dg_ave_difference = dg_ave_difference/dg_ave_norm
            dc_ave_difference = dc_ave_difference/dc_ave_norm
            cube_difference = cube_difference/cube_norm
            fighter_difference = fighter_difference/fighter_norm
            credit = credit/credit_norm

            # synthesis

            value += self.__dg_min_weight*dg_min_difference
            value += self.__dg_ave_weight*dg_ave_difference
            value += self.__dc_ave_weight*dc_ave_difference
            value += self.__cube_weight*cube_difference
            value += self.__fighter_weight*fighter_difference
            value += self.__credit_weight*credit

        return value


STATE_EVALUATOR_MM1 = StateEvaluator(fighter_weight=41.885392174432646,
                                     cube_weight=26.143263284220737,
                                     dg_min_weight=-5.88263321226207,
                                     dg_ave_weight=-44.32882404147753,
                                     dc_ave_weight=19.73724041099422,
                                     credit_weight=-18.583746217767935)

STATE_EVALUATOR_MM2 = StateEvaluator(fighter_weight=44.63728045969825,
                                     cube_weight=21.408271707785577,
                                     dg_min_weight=7.447181775997062,
                                     dg_ave_weight=14.154256204653036,
                                     dc_ave_weight=3.9277270467740597,
                                     credit_weight=-2.1733667445890497)

STATE_EVALUATOR_MM3 = StateEvaluator(fighter_weight=65.52573448992278,
                                     cube_weight=4.616227996911011,
                                     dg_min_weight=14.424683698727392,
                                     dg_ave_weight=19.619155464089044,
                                     dc_ave_weight=2.5543281621200737,
                                     credit_weight=-1.202172844784375)

STATE_EVALUATOR_MM4 = STATE_EVALUATOR_MM3


class MinimaxSearcher(Searcher):

    MinimaxSearcher = TypeVar("MinimaxSearcher", bound="MinimaxSearcher")

    __slots__ = ('__max_depth', '__state_evaluator',
                 '__searcher_parent', '__transposition_table_depth_0', '__transposition_table_depth_n', '__null_windowing_count',
                 '__debugging', '__counting', '__logging',
                 '__alpha_cuts', '__beta_cuts', '__evaluation_count', '__fun_evaluation_count')

    __LOW_ALPHA_BETA_CUT = 0.50
    __LOW_ACTION_COUNT = int(1/__LOW_ALPHA_BETA_CUT)

    __NULL_ALPHA_BETA_WINDOW = 0.001


    def __init__(self, name: str, max_depth: int=1, time_limit: Optional[int]=None,
                 state_evaluator: Optional[StateEvaluator]=None,
                 searcher_parent: Optional[MinimaxSearcher]=None):

        super().__init__(name)

        assert max_depth >= 1
        self.__max_depth = max_depth

        if time_limit is not None:
            assert time_limit > 0
            assert max_depth > 1
            self.set_time_limit(time_limit)

        if state_evaluator is not None:
            self.__state_evaluator = state_evaluator

        elif self.__max_depth == 1:
            self.__state_evaluator = STATE_EVALUATOR_MM1

        elif self.__max_depth == 2:
            self.__state_evaluator = STATE_EVALUATOR_MM2

        elif self.__max_depth == 3:
            self.__state_evaluator = STATE_EVALUATOR_MM3

        elif self.__max_depth == 4:
            self.__state_evaluator = STATE_EVALUATOR_MM4

        else:
            self.__state_evaluator = StateEvaluator()

        self.__searcher_parent = searcher_parent
        self.__transposition_table_depth_0 = {}
        self.__transposition_table_depth_n = {}
        self.__null_windowing_count = 0

        self.__logging = False
        self.__debugging = False
        self.__counting = False

        self.__alpha_cuts = []
        self.__beta_cuts = []
        self.__evaluation_count = 0
        self.__fun_evaluation_count = 0


    def search(self, state: PijersiState) -> PijersiAction:

        do_check = False

        initial_state = MinimaxState(state, state.get_current_player())

        self.__alpha_cuts = []
        self.__beta_cuts = []
        self.__evaluation_count = 0
        self.__fun_evaluation_count = 0
        self.__null_windowing_count = 0

        # >> The transpostion tables were valid just for the previous pijersi_state.
        # >> So it is better to reset them.
        self.__transposition_table_depth_0 = {}
        self.__transposition_table_depth_n = {}

        if self.get_time_limit() is None:
            (best_value, best_branch, valued_actions) = self.alphabeta_plus(state=initial_state, player=1)

            best_actions = [action for action in valued_actions if action.value == best_value]
            best_action = random.choice(best_actions)

            if self.__counting:

                if self.__alpha_cuts:
                    alpha_cut_mean = sum(self.__alpha_cuts)/len(self.__alpha_cuts)
                    self.__alpha_cuts.sort()
                    alpha_cut_q95 = self.__alpha_cuts[int(0.95*len(self.__alpha_cuts))]
                else:
                    alpha_cut_mean = 0
                    alpha_cut_q95 = 0

                if self.__beta_cuts:
                    beta_cut_mean = sum(self.__beta_cuts)/len(self.__beta_cuts)
                    self.__beta_cuts.sort()
                    beta_cut_q95 = self.__beta_cuts[int(0.95*len(self.__beta_cuts))]
                else:
                    beta_cut_mean = 0
                    beta_cut_q95 = 0

                log()
                log( f"{self.__evaluation_count} state evaluations" + " / " +
                       f"alpha_cut #{len(self.__alpha_cuts)} cuts / #ratio at cut: mean={100*alpha_cut_mean:.0f}% q95={100*alpha_cut_q95:.0f}%" + " / " +
                       f"beta_cut #{len(self.__beta_cuts)} cuts / #ratio at cut: mean={100*beta_cut_mean:.0f}% q95={100*beta_cut_q95:.0f}%")

                log(f"{self.__fun_evaluation_count} function calls to state evaluation")
                log(f"{len(self.__transposition_table_depth_0)} values in transposition table depth-0")
                log(f"{len(self.__transposition_table_depth_n)} values in transposition table depth-n")

            if do_check:
                self.check(initial_state, best_value, [best_action])

            valued_actions.sort(reverse=True)

            if self.__logging:
                log()
                log(f"select action {best_action} with value {best_value:.2f} amongst {len(best_actions)} best actions")
                log(f"best actions: {[str(action) for action in best_actions]}")
                log(f"best branch: {[str(action) for action in best_branch]}")
                log("first actions: ", [f"{action}:{action.value:.2f}" for action in valued_actions[:min(6, len(valued_actions))]])

            action = best_action

        else:
            #-- submit minimax from depth 1 to depth self.__max_depth
            search_count = self.__max_depth
            concurrent_executor = PoolExecutor(max_workers=search_count)
            search_futures = [None for search_index in range(search_count)]

            for search_index in range(search_count):
                search_futures[search_index] = concurrent_executor.submit(minimax_search_task, depth=search_index + 1, state=state)

            #-- watch end of minimax of highest depth after each sleeping of "wait_slice" seconds
            wait_slice_min = 0.01
            wait_count = math.ceil(max(wait_slice_min, self.get_time_limit())/wait_slice_min)

            wait_slice = self.get_time_limit()/wait_count
            for _ in range(wait_count):
                time.sleep(wait_slice)
                if search_futures[search_count - 1].done():
                    break

            #-- collect the answer of the highest depth minmax that is finished
            action = None
            action_search_index = None

            for search_index in range(search_count):
                if search_futures[search_index].done():
                    action = search_futures[search_index].result()
                    action_search_index = search_index

            #-- ensure an action can be returned; at least by minimax-1
            if action is None:
                log()
                log("no action found after time limit ; force new search by minimax-1")
                fallback_minimax_searcher = MinimaxSearcher("minimax-1", max_depth=1)
                action = fallback_minimax_searcher.search(state)
                action_search_index = 0

            assert action is not None

            if action_search_index != search_count - 1:
                log()
                log(f"time limit reached ; action returned by minimax at depth {action_search_index + 1}")

            search_futures = [None for search_index in range(search_count)]
            concurrent_executor.shutdown(wait=False, cancel_futures=True)
            concurrent_executor = None

        return action


    def check(self, initial_state: PijersiState, best_value: float, valued_actions: Sequence[PijersiAction]):

        (best_value_ref, valued_actions_ref) = self.minimax(state=initial_state, player=1)

        log()
        log(f"check: best_value_ref={best_value_ref:.2f}")
        log(f"check: best_value={best_value:.2f}")
        log()

        best_actions_ref = []
        for action_ref in valued_actions_ref:
            if action_ref.value == best_value_ref:
                best_actions_ref.append(action_ref)
                log(f"check: best (action_ref, action_value_ref)= ({action_ref}, {action_ref.value:.2f})")

        log()
        log(f"check: {len(best_actions_ref)} best_actions_ref with best value {best_value_ref:.2f}")

        best_actions = []
        for action in valued_actions:
            if action.value == best_value:
                best_actions.append(action)
                log(f"check: best (action, action_value)= ({action}, {action.value:.2f})")

        log()

        action_names_ref = set(map(str, valued_actions_ref))
        action_names = set(map(str, valued_actions))

        best_names_ref = set(best_actions_ref)
        best_names = set(best_actions)

        assert best_value == best_value_ref

        assert len(action_names) <= len(action_names_ref)
        assert len(action_names - action_names_ref) == 0

        assert len(best_names) <= len(best_names_ref)
        assert len(best_names - best_names_ref) == 0


    def evaluate_state_value(self, state: MinimaxState, depth: int) -> float:

        self.__evaluation_count += 1

        pijersi_state = state.get_pijersi_state()
        credit = pijersi_state.get_credit()
        board_codes = pijersi_state.get_board_codes()

        key = (depth, credit, *board_codes)

        try:
            value = self.__transposition_table_depth_0[key]
            if False and self.__debugging:
                player = state.get_current_maximizer_player()
                log(f"HE: succeeded transposition table depth-0 at depth {depth}/{self.__max_depth} for player {player}")

        except:
            if False and self.__debugging:
                log(f"HE: failed transposition table depth-0 at depth {depth}/{self.__max_depth} for player {player}")

            self.__fun_evaluation_count += 1

            value = self.__state_evaluator.evaluate_state_value(state, depth)
            self.__transposition_table_depth_0[key] = value

        return value


    def minimax(self, state: MinimaxState, player: int, depth: Optional[int]=None) -> Tuple[float, Sequence[PijersiAction]]:

        if depth is None:
            depth = self.__max_depth


        if depth == 0 or state.is_terminal():
            state_value = self.evaluate_state_value(state, depth)
            return (state_value, [])


        actions = state.get_actions()

        valued_actions = []
        make_valued_actions = (depth == self.__max_depth)

        if player == 1:

            best_child_value = -math.inf

            for action in actions:
                child_state = state.take_action(action)

                (child_value, _) = self.minimax(state=child_state, player=-player, depth=depth - 1)

                if make_valued_actions:
                    action.value = child_value
                    valued_actions.append(action)

                best_child_value = max(best_child_value, child_value)

        elif player == -1:

            best_child_value = math.inf

            for action in actions:
                child_state = state.take_action(action)

                (child_value, _) = self.minimax(state=child_state, player=-player, depth=depth - 1)

                if make_valued_actions:
                    action.value = child_value
                    valued_actions.append(action)

                best_child_value = min(best_child_value, child_value)

        else:
            assert player in (-1, 1)


        return (best_child_value, valued_actions)


    def alphabeta_plus(self, state, player, depth=None, alpha=None, beta=None) -> Tuple[float, Sequence[PijersiAction], Sequence[PijersiAction]]:
        """alphabeta with extra features:
            - compute the best branch ;
            - iterated minimax for optimization ;
            - memoization of board values.
        """

        def score_action_type(action):
            return 2*(action.capture_code//2 + action.capture_code%2) + action.move_code//2 + action.move_code%2


        if depth is None:
            depth = self.__max_depth


        if depth == 0 or state.is_terminal():
            state_value = self.evaluate_state_value(state, depth)
            return (state_value, [], [])


        # >> HG: avoid state evaluation
        state_key = (depth, state.get_pijersi_state().get_credit(), *state.get_pijersi_state().get_board_codes())
        try:
            state_value = self.__transposition_table_depth_n[state_key]
            if False and self.__debugging:
                player = state.get_current_maximizer_player()
                log(f"HG: succeeded transposition table depth-n at depth {depth}/{self.__max_depth} for player {player}")
            return (state_value, [], [])

        except:
            if False and self.__debugging:
                player = state.get_current_maximizer_player()
                log(f"HG: failed transposition table depth-n at depth {depth}/{self.__max_depth} for player {player}")


        if alpha is None:
            alpha = -math.inf

        if beta is None:
            beta = math.inf

        assert alpha <= beta

        actions = state.get_actions()

        valued_actions = []
        make_valued_actions = (depth == self.__max_depth)

        # Manage openings file

        make_opening_file = False

        if ( depth == self.__max_depth and depth >= 2 and
            state.get_pijersi_state().get_turn() == 1 and
            state.get_pijersi_state().get_setup() == Setup.T.CLASSIC ):
            opening_file_path = os.path.join(_package_home, f"openings-minimax-{depth}.txt")

            if not os.path.isfile(opening_file_path):
                make_opening_file = True

            else:
                if self.__debugging:
                    log()
                    log(f"reading openings file {opening_file_path} ...")

                with open(opening_file_path, 'r') as opening_stream:
                    opening_lines = opening_stream.readlines()

                for opening_line in opening_lines:
                    opening_data = opening_line.split()
                    assert len(opening_data) == 2

                    action_value = float(opening_data[1])

                    action_name = opening_data[0]
                    action = None
                    for action_candidate in actions:
                        if str(action_candidate) == action_name:
                            action = action_candidate
                            break
                    assert action is not None
                    action.value = action_value

                    valued_actions.append(action)

                if self.__debugging:
                    log(f"reading openings file {opening_file_path} done")

                return (action_value, [], valued_actions)

        # >> A few heuristics for generating efficient alpha-beta cuts

        # >> HF: keep actions making unique states
        unique_actions = []
        unique_action_keys = set()

        for action in actions:
            action_key = (*action.next_board_codes,)
            if action_key not in unique_action_keys:
                unique_action_keys.add(action_key)
                unique_actions.append(action)

        if self.__debugging:
            log(f"HF: keeping {len(unique_actions)} unique actions over {len(actions)} actions at {depth}/{self.__max_depth} for player {player}")

        actions = unique_actions
        unique_actions = None
        unique_action_keys = None


        # >> HA: sort actions according to the type of action
        actions.sort(key=score_action_type, reverse=True)

        # >> HB: compute Minimax at inferior depth for sorting actions
        if self.__max_depth >= 2 and depth == self.__max_depth:

            pre_depth = self.__max_depth - 1

            if self.__debugging:
                log(f"HB: iterative deepening at depth {pre_depth} ...")

            pre_minimax_searcher = MinimaxSearcher(f"minimax-pre-{pre_depth}", max_depth=pre_depth, searcher_parent=self)
            (_, _, _) = pre_minimax_searcher.alphabeta_plus(state=state, player=player)

            self.__evaluation_count += pre_minimax_searcher.__evaluation_count
            self.__fun_evaluation_count += pre_minimax_searcher.__fun_evaluation_count

            if self.__debugging:
                log(f"HB: iterative deepening at depth {pre_depth} done")

        if self.__max_depth >= 2:
            # >> HB: sort actions according to Minimax at inferior depth
            actions_with_value = [action for action in actions if action.value is not None]
            actions_without_value = [action for action in actions if action.value is None]

            if len(actions_with_value) != 0:
                if self.__debugging:
                    log(f"HB: sorting {len(actions_with_value)} actions with value at depth {depth}/{self.__max_depth} for player {player}")
                actions_with_value.sort(reverse=(player == 1))

        else:
            actions_with_value = actions
            actions_without_value = []

        do_null_window_search = self.__max_depth >= 3 and depth >= 2

        if player == 1:

            best_child_value = -math.inf
            best_child_branch = None
            best_action = None
            best_child_break = False

            action_count = 0

            first_action = True

            for action in actions_with_value:

                action_count += 1

                child_state = state.take_action(action, use_cache=True)

                if not do_null_window_search or first_action:
                    first_action = False
                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=alpha, beta=beta)

                else:
                    self.__null_windowing_count += 1

                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=alpha, beta=alpha + self.__NULL_ALPHA_BETA_WINDOW)

                    self.__null_windowing_count -= 1

                    if alpha < child_value < beta:
                        (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                         alpha=alpha, beta=beta)
                        if False and self.__debugging:
                            log(f"HD: null-window failed for action {action_count}/{len(actions)} at depth {depth}/{self.__max_depth} for player {player}")
                    else:
                        if False and self.__debugging:
                            log(f"HD: null-window succeeded for action {action_count}/{len(actions)} at depth {depth}/{self.__max_depth} for player {player}")

                # >> HB: store value just for sorting
                action.value = child_value

                # >> HG: store value to avoid re-evaluation
                if self.__null_windowing_count == 0:
                    child_key = (depth - 1, child_state.get_pijersi_state().get_credit(), *action.next_board_codes)
                    self.__transposition_table_depth_n[child_key] = child_value

                # >> free some memory once action is valued and will never be explored  by any searcher
                if self.__searcher_parent is None:
                    action.next_state = None

                if make_valued_actions:
                    valued_actions.append(action)

                if child_value > best_child_value:
                    best_action = action
                    best_child_branch = child_branch

                best_child_value = max(best_child_value, child_value)

                if best_child_value > beta:
                    if self.__counting:
                        self.__beta_cuts.append(action_count/len(actions))

                    if self.__debugging:
                        if action_count/len(actions) > self.__LOW_ALPHA_BETA_CUT:
                            log(f"beta-cut after action {action_count}/{len(actions)} > {100*self.__LOW_ALPHA_BETA_CUT:.0f}% at depth {depth}/{self.__max_depth} for player {player}")

                    best_child_break = True
                    break

                alpha = max(alpha, best_child_value)

            if not best_child_break and len(actions_without_value) != 0:

                if depth >= 2:
                    if self.__debugging:
                        log(f"HC: pre-evaluating and sorting {len(actions_without_value)} actions without value at depth {depth}/{self.__max_depth} for player {player}")

                    for action in actions_without_value:
                        child_state = state.take_action(action, use_cache=True)
                        action.value = STATE_EVALUATOR_MM2.evaluate_state_value(child_state, depth - 1)

                    self.__evaluation_count += len(actions_without_value)
                    self.__fun_evaluation_count += len(actions_without_value)

                    actions_without_value.sort(reverse=(player == 1))

                for action in actions_without_value:
                    action_count += 1

                    child_state = state.take_action(action, use_cache=True)

                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=alpha, beta=beta)

                    # >> HB: store value just for sorting
                    action.value = child_value

                    # >> HG: store value to avoid re-evaluation
                    if self.__null_windowing_count == 0:
                        child_key = (depth - 1, child_state.get_pijersi_state().get_credit(), *action.next_board_codes)
                        self.__transposition_table_depth_n[child_key] = child_value

                    # >> free some memory once action is valued and will never be explored  by any searcher
                    if self.__searcher_parent is None:
                        action.next_state = None

                    if make_valued_actions:
                        valued_actions.append(action)

                    if child_value > best_child_value:
                        best_action = action
                        best_child_branch = child_branch

                    best_child_value = max(best_child_value, child_value)

                    if best_child_value > beta:
                        if self.__counting:
                            self.__beta_cuts.append(action_count/len(actions))

                        if self.__debugging:
                            if action_count/len(actions) > self.__LOW_ALPHA_BETA_CUT:
                                log(f"beta-cut after action {action_count}/{len(actions)} > {100*self.__LOW_ALPHA_BETA_CUT:.0f}% at depth {depth}/{self.__max_depth} for player {player}")

                        best_child_break = True
                        break

                    alpha = max(alpha, best_child_value)

            if self.__debugging:
                if not best_child_break and action_count > self.__LOW_ACTION_COUNT:
                    log(f"no beta-cut on {len(actions)} actions at depth {depth}/{self.__max_depth} for player {player}")

        elif player == -1:

            best_child_value = math.inf
            best_child_branch = None
            best_action = None
            best_child_break = False

            action_count = 0

            first_action = True

            for action in actions_with_value:

                action_count += 1

                child_state = state.take_action(action, use_cache=True)

                if not do_null_window_search or first_action:
                    first_action = False
                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=alpha, beta=beta)

                else:
                    self.__null_windowing_count += 1

                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=beta - self.__NULL_ALPHA_BETA_WINDOW, beta=beta)
                    self.__null_windowing_count -= 1

                    if alpha < child_value < beta:
                        (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                         alpha=alpha, beta=beta)
                        if False and self.__debugging:
                            log(f"HD: null-window failed for action {action_count}/{len(actions)} at depth {depth}/{self.__max_depth} for player {player}")
                    else:
                        if False and self.__debugging:
                            log(f"HD: null-window succeeded for action {action_count}/{len(actions)} at depth {depth}/{self.__max_depth} for player {player}")

                # >> HB: store value just for sorting
                action.value = child_value

                # >> HG: store value to avoid re-evaluation
                if self.__null_windowing_count == 0:
                    child_key = (depth - 1, child_state.get_pijersi_state().get_credit(), *action.next_board_codes)
                    self.__transposition_table_depth_n[child_key] = child_value

                # >> free some memory once action is valued and will never be explored  by any searcher
                if self.__searcher_parent is None:
                    action.next_state = None

                if make_valued_actions:
                    valued_actions.append(action)

                if child_value < best_child_value:
                    best_action = action
                    best_child_branch = child_branch

                best_child_value = min(best_child_value, child_value)

                if best_child_value < alpha:
                    if self.__counting:
                        self.__alpha_cuts.append(action_count/len(actions))

                    if self.__debugging:
                        if action_count/len(actions) > self.__LOW_ALPHA_BETA_CUT:
                            log(f"alpha-cut after action {action_count}/{len(actions)} > {100*self.__LOW_ALPHA_BETA_CUT:.0f}% at depth {depth}/{self.__max_depth} for player {player}")

                    best_child_break = True
                    break

                beta = min(beta, best_child_value)

            if not best_child_break and len(actions_without_value) != 0:

                if depth >= 2:
                    if self.__debugging:
                        log(f"HC: pre-evaluating and sorting {len(actions_without_value)} actions without value at depth {depth}/{self.__max_depth} for player {player}")

                    for action in actions_without_value:
                        child_state = state.take_action(action, use_cache=True)
                        action.value = STATE_EVALUATOR_MM2.evaluate_state_value(child_state, depth - 1)

                    self.__evaluation_count += len(actions_without_value)
                    self.__fun_evaluation_count += len(actions_without_value)

                    actions_without_value.sort(reverse=(player == 1))

                for action in actions_without_value:
                    action_count += 1

                    child_state = state.take_action(action, use_cache=True)

                    (child_value, child_branch, _) = self.alphabeta_plus(state=child_state, player=-player, depth=depth - 1,
                                                                     alpha=alpha, beta=beta)

                    # >> HB: store value just for sorting
                    action.value = child_value

                    # >> HG: store value to avoid re-evaluation
                    if self.__null_windowing_count == 0:
                        child_key = (depth - 1, child_state.get_pijersi_state().get_credit(), *action.next_board_codes)
                        self.__transposition_table_depth_n[child_key] = child_value

                    # >> free some memory once action is valued and will never be explored  by any searcher
                    if self.__searcher_parent is None:
                        action.next_state = None

                    if make_valued_actions:
                        valued_actions.append(action)

                    if child_value < best_child_value:
                        best_action = action
                        best_child_branch = child_branch

                    best_child_value = min(best_child_value, child_value)

                    if best_child_value < alpha:
                        if self.__counting:
                            self.__alpha_cuts.append(action_count/len(actions))

                        if self.__debugging:
                            if action_count/len(actions) > self.__LOW_ALPHA_BETA_CUT:
                                log(f"alpha-cut after action {action_count}/{len(actions)} > {100*self.__LOW_ALPHA_BETA_CUT:.0f}% at depth {depth}/{self.__max_depth} for player {player}")

                        best_child_break = True
                        break

                    beta = min(beta, best_child_value)

            if self.__debugging:
                if not best_child_break and action_count > self.__LOW_ACTION_COUNT:
                    log(f"no alpha-cut on {len(actions)} actions at depth {depth}/{self.__max_depth} for player {player}")

        else:
            assert player in (-1, 1)

        # Manage openings file

        if make_opening_file:
            if self.__debugging:
                log()
                log(f"writing openings file {opening_file_path} ...")

            opening_lines = [str(action) + " " + str(best_child_value) + "\n" for action in valued_actions if action.value == best_child_value]
            with open(opening_file_path, 'w') as opening_stream:
                opening_stream.writelines(opening_lines)

            if self.__debugging:
                log(f"writing openings file {opening_file_path} done")

        return (best_child_value, [best_action] + best_child_branch, valued_actions)



def minimax_search_task(depth, state):
    """A static wrapper function used for multiprocessing"""
    minimax_searcher = MinimaxSearcher(f"minimax-{depth}", max_depth=depth)
    return minimax_searcher.search(state)


class SearcherCatalog:

    __slots__ = ('__catalog')


    def __init__(self):
        self.__catalog = {}


    def add(self, searcher: Searcher):
        searcher_name = searcher.get_name()
        assert searcher_name not in self.__catalog
        self.__catalog[searcher_name] = searcher


    def get_names(self) -> Sequence[str]:
        return list(sorted(self.__catalog.keys()))


    def get(self, name: str) -> Searcher:
        assert name in self.__catalog
        return self.__catalog[name]


class Game:

    __slots__ = ('__searcher', '__pijersi_state', '__pijersi_setup', '__pijersi_setup_board_codes',
                 '__enabled_log', '__log', '__turn', '__last_action',
                 '__turn_duration', '__turn_start', '__turn_end')


    def __init__(self, setup: Setup.T=Setup.T.CLASSIC, board_codes: Optional[BoardCodes]=None):
        self.__searcher = [None, None]
        self.__pijersi_state = None
        self.__pijersi_setup = setup
        self.__pijersi_setup_board_codes = board_codes

        self.__enabled_log = True
        self.__log = ""
        self.__turn = 0
        self.__last_action = None
        self.__turn_duration = {Player.T.WHITE:[], Player.T.BLACK:[]}
        self.__turn_start = None
        self.__turn_end = None


    def enable_log(self, condition: bool):
        self.__enabled_log = condition
        if not self.__enabled_log:
            self.__log = ""


    def set_white_searcher(self, searcher: Searcher):
        self.__searcher[Player.T.WHITE] = searcher


    def set_black_searcher(self, searcher: Searcher):
        self.__searcher[Player.T.BLACK] = searcher


    def start(self):

        assert self.__searcher[Player.T.WHITE] is not None
        assert self.__searcher[Player.T.BLACK] is not None

        self.__pijersi_state = PijersiState(setup=self.__pijersi_setup, board_codes=self.__pijersi_setup_board_codes)

        if self.__enabled_log:
            self.__pijersi_state.show()
            self.__log = "Game started"

        if self.__pijersi_state.is_terminal():

            rewards = self.__pijersi_state.get_rewards()

            if self.__enabled_log:
                log()
                log("-"*40)

                white_player = f"{Player.to_name(Player.T.WHITE)}-{self.__searcher[Player.T.WHITE].get_name()}"
                black_player = f"{Player.to_name(Player.T.BLACK)}-{self.__searcher[Player.T.BLACK].get_name()}"

                if rewards[Player.T.WHITE] == rewards[Player.T.BLACK]:
                    self.__log = f"Nobody wins ; the game is a draw between {white_player} and {black_player}"

                elif rewards[Player.T.WHITE] > rewards[Player.T.BLACK]:
                    self.__log = f"Player {white_player} wins against {black_player}"

                else:
                    self.__log = f"Player {black_player} wins against {white_player}"

                log(self.__log)


    def get_log(self) -> str:
        return self.__log


    def get_turn(self) -> int:
        return self.__turn


    def get_last_action(self) -> str:
        assert self.__last_action is not None
        return self.__last_action


    def get_summary(self) -> str:
        return self.__pijersi_state.get_summary()


    def get_state(self) -> PijersiState:
        return self.__pijersi_state


    def set_state(self, state: PijersiState):
        self.__pijersi_state = state


    def set_turn_start(self, turn_start: Optional[float]):
        self.__turn_start = turn_start


    def set_turn_end(self, turn_end: Optional[float]):
        self.__turn_end = turn_end


    def get_rewards(self) -> Optional[Tuple[Reward, Reward]]:
        return self.__pijersi_state.get_rewards()


    def has_next_turn(self) -> bool:
        return not self.__pijersi_state.is_terminal()


    def next_turn(self):

        self.__log = ""

        if self.has_next_turn():
            player = self.__pijersi_state.get_current_player()

            if self.__enabled_log:
                player_name = f"{Player.to_name(player)}-{self.__searcher[player].get_name()}"
                log()
                log(f"Player {player_name} is thinking ...")
                turn_start = time.time() if self.__turn_start is None else self.__turn_start

            action = self.__searcher[player].search(self.__pijersi_state)

            self.__last_action = str(action)
            self.__turn = self.__pijersi_state.get_turn()

            if self.__enabled_log:
                turn_end = time.time() if self.__turn_end is None else self.__turn_end
                turn_duration = turn_end - turn_start
                self.__turn_duration[player].append(turn_duration)
                log(f"Player {player_name} is done after %.1f seconds" % turn_duration)

                action_count = len(self.__pijersi_state.get_actions())
                self.__log = f"Turn {self.__turn} : after {turn_duration:.1f} seconds {player_name} selects {action} amongst {action_count} actions"
                log(self.__log)
                log("-"*40)

            self.__pijersi_state = self.__pijersi_state.take_action(action)

            if self.__enabled_log:
                self.__pijersi_state.show()

        if self.__pijersi_state.is_terminal():

            rewards = self.__pijersi_state.get_rewards()
            player = self.__pijersi_state.get_current_player()

            if self.__enabled_log:
                log()
                log("-"*40)

                white_time = sum(self.__turn_duration[Player.T.WHITE])
                black_time = sum(self.__turn_duration[Player.T.BLACK])

                white_player = f"{Player.to_name(Player.T.WHITE)}-{self.__searcher[Player.T.WHITE].get_name()}"
                black_player = f"{Player.to_name(Player.T.BLACK)}-{self.__searcher[Player.T.BLACK].get_name()}"

                if rewards[Player.T.WHITE] == rewards[Player.T.BLACK]:
                    self.__log = f"Nobody wins ; the game is a draw between {white_player} and {black_player} ; {white_time:.0f} versus {black_time:.0f} seconds"

                elif rewards[Player.T.WHITE] > rewards[Player.T.BLACK]:
                    self.__log = f"Player {white_player} wins against {black_player} ; {white_time:.0f} versus {black_time:.0f} seconds"

                else:
                    self.__log = f"Player {black_player} wins against {white_player} ; {black_time:.0f} versus {white_time:.0f} seconds"

                log(self.__log)


Hexagon.init()
PijersiState.init()


if __name__ == "__main__":
    # >> "freeze_support()" is needed with using pijersi_gui as a single executable made by PyInstaller
    # >> otherwise when starting another process by "PoolExecutor" a second GUI windows is created
    freeze_support()

    log()
    log("Hello")
    log()
    log(f"Python sys.version = {sys.version}")

    log()
    log("Bye")

    # >> clean any residual process
    if len(multiprocessing.active_children()) > 0:
        log()
        log(f"{len(multiprocessing.active_children())} child processes are still alive")
        log("Terminating child processes ...")
        for child_process in multiprocessing.active_children():
            try:
                child_process.terminate()
            except:
                pass
        log("Terminating child processes done")
