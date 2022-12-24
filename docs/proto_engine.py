#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_rules.py implements the rules engine for the PIJERSI boardgame."""

__version__ = "1.1.0-rc3"

_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import array
import enum
from collections import Counter
from dataclasses import dataclass
import math
import os
import random
import sys
import time
import timeit
from types import SimpleNamespace
from typing import Iterable
from typing import NewType
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar

import cProfile
from pstats import SortKey


_package_home = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "pijersi_certu")
sys.path.append(_package_home)
import pijersi_rules as rules


_do_debug = False

OMEGA = 1_000.
OMEGA_2 = OMEGA**2

# The most compact storage
# >> Tests with all 32 signed bits or all 64 signed bits have not changed the profiling, neither the global time
ARRAY_TYPE_BOOL = 'B'
ARRAY_TYPE_COUNTER = 'B'
ARRAY_TYPE_STATE_1 = 'B'
ARRAY_TYPE_STATE_2 = 'H'
ARRAY_TYPE_STATE_3 = 'L'


HexIndex = NewType('HexIndex', int)
Sources = Iterable[HexIndex]
Path = Sequence[HexIndex]

CaptureCode = NewType('CaptureCode', int)
HexCode = NewType('HexCode', int)
MoveCode = NewType('MoveCode', int)
PathCode = NewType('PathCode', int)

BoardCodes = Sequence[HexCode]
PathCodes = Sequence[HexCode]


@enum.unique
class Reward(enum.IntEnum):
    WIN = 1
    DRAW = 0
    LOSS = -1

    assert LOSS < DRAW < WIN
    assert DRAW == 0
    assert LOSS + WIN == DRAW


@enum.unique
class Player(enum.IntEnum):
    WHITE = 0
    BLACK = 1
    assert WHITE < BLACK


def Player_name(player: Player) -> str:
    return "white" if player == Player.WHITE else "black"


@enum.unique
class Cube(enum.IntEnum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2
    WISE = 3
    assert ROCK < PAPER < SCISSORS < WISE


def Cube_beats(src: Cube, dst: Cube) -> bool:
    assert src in Cube
    assert dst in Cube
    return (src, dst) in ((Cube.ROCK, Cube.SCISSORS),
                          (Cube.SCISSORS, Cube.PAPER),
                          (Cube.PAPER, Cube.ROCK))

Cube_data = SimpleNamespace(TABLE_CUBE_FROM_NAME=None, TABLE_CUBE_TO_NAME=None)

Cube_data.TABLE_CUBE_FROM_NAME = {
    'R':(Player.WHITE, Cube.ROCK),
    'P':(Player.WHITE, Cube.PAPER),
    'S':(Player.WHITE, Cube.SCISSORS),
    'W':(Player.WHITE, Cube.WISE),

    'r':(Player.BLACK, Cube.ROCK),
    'p':(Player.BLACK, Cube.PAPER),
    's':(Player.BLACK, Cube.SCISSORS),
    'w':(Player.BLACK, Cube.WISE)}

Cube_data.TABLE_CUBE_TO_NAME = {(player, cube):name for (name, (player, cube)) in Cube_data.TABLE_CUBE_FROM_NAME.items()}


def Cube_from_name(name: str) -> Cube:
    return Cube_data.TABLE_CUBE_FROM_NAME[name]


def Cube_to_name(player: Player, cube: Cube) -> str:
    return Cube_data.TABLE_CUBE_TO_NAME[(player, cube)]


@enum.unique
class HexagonDirection(enum.IntEnum):
    PHI_090 = 0
    PHI_150 = 1
    PHI_210 = 2
    PHI_270 = 3
    PHI_330 = 4
    PHI_030 = 5
    assert PHI_090 < PHI_150 < PHI_210 < PHI_270 < PHI_330 < PHI_030

# >> Optimizatoin of 'HEXAGON_DIRECTION_ITERATOR = HexagonDirection' in expressions like 'for direction in HEXAGON_DIRECTION_ITERATOR'
HEXAGON_DIRECTION_ITERATOR = range(len(HexagonDirection))


def hex_distance(position_uv_1: Tuple[int, int], position_uv_2: Tuple[int, int]):
    """reference: https://www.redblobgames.com/grids/hexagons/#distances"""
    (u1, v1) = position_uv_1
    (u2, v2) = position_uv_2
    distance = (math.fabs(u1 - u2) + math.fabs(v1 - v2)+ math.fabs(u1 + v1 - u2 - v2))/2
    return distance


class Hexagon:

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
    __distance_to_goal = None


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
    def get(name: str) ->Self:
        return Hexagon.__name_to_hexagon[name]


    @staticmethod
    def get_all() -> Sequence[Self]:
        return Hexagon.__all_sorted_hexagons


    @staticmethod
    def get_all_indices() -> Sequence[HexIndex]:
        return Hexagon.__all_indices


    @staticmethod
    def get_goal_indices(player: Player) -> Sequence[HexIndex]:
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
    def get_distance_to_goal(hexagon_index: HexIndex, player: Player) -> float:
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
            print(hexagon)


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

        Hexagon.__goal_indices = [None for _ in Player]

        Hexagon.__goal_indices[Player.WHITE] = white_goal_indices
        Hexagon.__goal_indices[Player.BLACK] = black_goal_indices


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

            Hexagon.__next_fst_indices[hexagon_index] = array.array('b', [Hexagon.NULL for _ in HexagonDirection])
            Hexagon.__next_snd_indices[hexagon_index] = array.array('b', [Hexagon.NULL for _ in HexagonDirection])

            for hexagon_dir in HexagonDirection:
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
                distance = hex_distance(hexagon_1.position_uv, hexagon_2.position_uv)
                Hexagon.__distance[(hexagon_1.index, hexagon_2.index)] = distance


    @staticmethod
    def __create_distance_to_goal():

        Hexagon.__distance_to_goal = [array.array('b', [0 for _ in Hexagon.get_all()]) for _ in Player]

        for player in Player:
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
                 player: Optional[Player]=None,
                 bottom: Optional[Cube]=None,
                 top: Optional[Cube]=None):

        if is_empty:
            assert not has_stack
            assert player is None
            assert bottom is None
            assert top is None
        else:
            assert player is not None

            if has_stack:
                assert bottom is not None and top is not None
                if top == Cube.WISE:
                    assert bottom == Cube.WISE
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
    def make_single(player: Player, cube: Cube) -> Self:
        return HexState(player=player, bottom=cube, is_empty=False)


    @staticmethod
    def make_stack(player: Player, bottom: Cube, top: Cube) -> Self:
        return HexState(player=player, bottom=bottom, top=top, is_empty=False, has_stack=True)


    def __str__(self):
        return ( f"HexState(is_empty={self.is_empty}" +
                 f", has_stack={self.has_stack}" +
                 f", player={self.player.name if self.player is not None else None}" +
                 f", bottom={self.bottom.name if self.bottom is not None else None}" +
                 f", top={self.top.name if self.top is not None else None})" )


    def __repr__(self):
        return str(self)


    def __eq__(self, other):
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
            player = tuple(Player)[bit_player]

            bits_bottom = rest % 4
            rest = rest // 4
            bottom = tuple(Cube)[bits_bottom]

            if has_stack:
                bits_top = rest % 4
                rest = rest // 4
                top = tuple(Cube)[bits_top]

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
                for player in Player:
                    for bottom in Cube:
                        for has_stack in (True, False):
                            if has_stack:
                                if bottom == Cube.WISE:
                                    for top in Cube:
                                        yield HexState(is_empty=is_empty,
                                                       has_stack=has_stack,
                                                       player=player,
                                                       bottom=bottom,
                                                       top=top)
                                else:
                                    for top in (Cube.ROCK, Cube.PAPER, Cube.SCISSORS):
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
    next_board_codes: Optional[(BoardCodes)] = None
    path_vertices: Optional[Path] = None
    capture_code: Optional[CaptureCode] = None
    move_code: Optional[MoveCode] = None

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


    def __str__(self):

        hexagons = Hexagon.get_all()

        hex_names = [hexagons[hex_index].name for hex_index in self.path_vertices]
        move_names = PijersiAction.__TABLE_MOVE_CODE_TO_NAMES[self.move_code]
        capture_names = PijersiAction.__TABLE_CAPTURE_CODE_TO_NAMES[self.capture_code]

        action_name = hex_names[0]
        for (move_name, hex_name, capture_name) in zip(move_names, hex_names[1:], capture_names):
            action_name += move_name + hex_name + capture_name

        return action_name


PijersiActions = Sequence[PijersiAction]


class PijersiState:

    Self = TypeVar("Self", bound="PijersiState")

    __init_done = False
    __max_credit = 20
    __slots__ = ('__board_codes', '__player', '__credit', '__turn',
                 '__actions', '__actions_by_names', '__actions_by_simple_names', '__terminated')


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

    __TABLE_TRY_CUBE_PATH1_NEXT_CODE = None
    __TABLE_TRY_CUBE_PATH1_CAPTURE_CODE = None

    __TABLE_TRY_STACK_PATH1_NEXT_CODE = None
    __TABLE_TRY_STACK_PATH1_CAPTURE_CODE = None

    __TABLE_TRY_STACK_PATH2_NEXT_CODE = None
    __TABLE_TRY_STACK_PATH2_CAPTURE_CODE = None


    def __init__(self,
                 board_codes: Optional[BoardCodes]=None,
                 player: Player=Player.WHITE,
                 credit: Optional[int]=None,
                 turn: int=1):


        self.__board_codes = board_codes if board_codes is not None else PijersiState.__make_default_board_codes()
        self.__player = player
        self.__credit = credit if credit is not None else PijersiState.__max_credit
        self.__turn = turn
        self.__actions = None
        self.__actions_by_names = None
        self.__terminated = None

    @staticmethod
    def init():


        def create_table_has_cube() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:
                    count = 1
                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_has_stack() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty and hex_state.has_stack:
                    count = 1
                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_cube_count() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player]

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
            table = [array.array(ARRAY_TYPE_BOOL, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:

                    if hex_state.has_stack:
                        count = 0
                        count = max(count, 1 if hex_state.bottom != Cube.WISE else 0)
                        count = max(count, 1 if hex_state.top != Cube.WISE else 0)
                    else:
                        count = 1 if hex_state.bottom != Cube.WISE else 0

                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_fighter_count() -> Sequence[Sequence[int]]:
            table = [array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)]) for _ in Player]

            for hex_state in HexState.iterate_hex_states():

                if not hex_state.is_empty:

                    if hex_state.has_stack:
                        count = 0
                        count += 1 if hex_state.bottom != Cube.WISE else 0
                        count += 1 if hex_state.top != Cube.WISE else 0
                    else:
                        count = 1 if hex_state.bottom != Cube.WISE else 0

                    hex_code = hex_state.encode()
                    table[hex_state.player][hex_code] = count

            return table


        def create_table_cube_count_by_sort() ->Sequence[Sequence[Sequence[int]]] :
            table = [[array.array(ARRAY_TYPE_COUNTER, [0 for _ in range(HexState.CODE_BASE)])
                       for _ in Cube] for _ in Player]

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

            table = [[None for direction in HexagonDirection] for source in Hexagon.get_all_indices()]

            for source in Hexagon.get_all_indices():
                for direction in HexagonDirection:

                    path= None
                    next_fst_hex = Hexagon.get_next_fst_index(source, direction)
                    if next_fst_hex != Hexagon.NULL:
                        path = [source, next_fst_hex]

                    table[source][direction] = path

            return table


        def create_table_make_path2() -> Sequence[Optional[Sequence[int]]]:

            table = [[None for direction in HexagonDirection] for source in Hexagon.get_all_indices()]

            for source in Hexagon.get_all_indices():
                for direction in HexagonDirection:

                    path = None
                    next_fst_hex = Hexagon.get_next_fst_index(source, direction)
                    if next_fst_hex != Hexagon.NULL:
                        next_snd_hex = Hexagon.get_next_snd_index(source, direction)
                        if next_snd_hex != Hexagon.NULL:
                            path = [source, next_fst_hex, next_snd_hex]

                    table[source][direction] = path

            return table


        def create_table_goal_indices() -> Sequence[Sequence[int]]:
            return [Hexagon.get_goal_indices(player) for player in Player]


        def create_table_goal_distances() -> Sequence[Sequence[int]]:
            return [[Hexagon.get_distance_to_goal(hex_index, player)
                      for hex_index in Hexagon.get_all_indices()] for player in Player]


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
                                    if src_state.top != Cube.WISE or (src_state.top == Cube.WISE and dst_state.bottom == Cube.WISE):
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_stack(player=src_state.player, bottom=dst_state.bottom, top=src_state.top)

                                else:
                                    if src_state.bottom != Cube.WISE or (src_state.bottom == Cube.WISE and dst_state.bottom == Cube.WISE):
                                        next_src_state = HexState.make_empty()
                                        next_dst_state = HexState.make_stack(player=src_state.player, bottom=dst_state.bottom, top=src_state.bottom)

                        else:
                            # >> Capturing rules must be considered
                            if dst_state.has_stack:
                                # == Destination has a stack owned by the non-active player

                                if src_state.has_stack:
                                    if Cube_beats(src_state.top, dst_state.top):
                                        capture_code = 1
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)

                                else:
                                    if Cube_beats(src_state.bottom, dst_state.top):
                                        capture_code = 1
                                        next_src_state = HexState.make_empty()
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)

                            else:
                                # == Destination has a single cube owned by the non-active player

                                if src_state.has_stack:
                                    if Cube_beats(src_state.top, dst_state.bottom):
                                        capture_code = 1
                                        next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                        next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)
                                else:
                                    if Cube_beats(src_state.bottom, dst_state.bottom):
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
                                if Cube_beats(src_state.top, dst_state.top):
                                    capture_code = 1
                                    next_src_state = HexState.make_empty()
                                    next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)

                            else:
                                # == Destination has a single cube owned by the non-active player
                                if Cube_beats(src_state.top, dst_state.bottom):
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
            print()
            print("-- print_table_has_cube --")
            print(PijersiState.__TABLE_HAS_CUBE)


        def print_table_has_stack():
            print()
            print("-- print_table_has_stack --")
            print(PijersiState.__TABLE_HAS_STACK)


        def print_table_cube_count():
            print()
            print("-- print_table_cube_count --")
            print(PijersiState.__TABLE_CUBE_COUNT)


        def print_table_has_fighter():
            print()
            print("-- print_table_has_fighter --")
            print(PijersiState.__TABLE_HAS_FIGHTER)


        def print_table_fighter_count():
            print()
            print("-- print_table_fighter_count --")
            print(PijersiState.__TABLE_FIGHTER_COUNT)


        def print_table_cube_count_by_sort():
            print()
            print("-- print_table_cube_count_by_sort --")
            print(PijersiState.__TABLE_CUBE_COUNT_BY_SORT)


        def print_table_make_path1():
            print()
            print("-- print_table_make_path1 --")
            print(PijersiState.__TABLE_MAKE_PATH1)


        def print_table_make_path2():
            print()
            print("-- print_table_make_path2 --")
            print(PijersiState.__TABLE_MAKE_PATH2)


        def print_table_goal_indices():
            print()
            print("-- print_table_goal_indices --")
            print(PijersiState.__TABLE_GOAL_INDICES)


        def print_table_goal_distances():
            print()
            print("-- print_table_goal_distances --")
            print(PijersiState.__TABLE_GOAL_DISTANCES)


        def print_tables_try_cube_path1():
            print()
            print("-- print_tables_try_cube_path1 --")
            print(PijersiState.__TABLE_TRY_CUBE_PATH1_NEXT_CODE)
            print(PijersiState.__TABLE_TRY_CUBE_PATH1_CAPTURE_CODE)


        def print_tables_try_stack_path1():
            print()
            print("-- print_tables_try_stack_path1 --")
            print(PijersiState.__TABLE_TRY_STACK_PATH1_NEXT_CODE)
            print(PijersiState.__TABLE_TRY_STACK_PATH1_CAPTURE_CODE)


        def print_tables_try_stack_path2():
            print()
            print("-- print_tables_try_stack_path2 --")
            print(PijersiState.__TABLE_TRY_STACK_PATH2_NEXT_CODE)
            print(PijersiState.__TABLE_TRY_STACK_PATH2_CAPTURE_CODE)


        print_table_cube_count()
        print_table_has_cube()
        print_table_fighter_count()
        print_table_has_fighter()

        print_table_make_path1()
        print_table_make_path2()

        print_table_goal_indices()
        print_table_goal_distances()

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


    def get_current_player(self):
        return self.__player


    def get_other_player(self):
        return Player.BLACK if self.__player == Player.WHITE else Player.WHITE


    def get_turn(self):
        return self.__turn


    def is_terminal(self, use_cache: bool=True) -> bool:
        if not use_cache or self.__terminated is None:
            self.__terminated = (self.__player_is_arrived(Player.WHITE) or
                                    self.__player_is_arrived(Player.BLACK) or
                                    self.__credit == 0 or
                                    not self.__has_action())
        return self.__terminated


    def get_rewards(self) -> Optional[Tuple[Reward, Reward]]:

        rewards = [None for player in Player]

        if self.__player_is_arrived(Player.WHITE):
            rewards[Player.WHITE] = Reward.WIN
            rewards[Player.BLACK] = Reward.LOSS

        elif self.__player_is_arrived(Player.BLACK):
            rewards[Player.BLACK] = Reward.WIN
            rewards[Player.WHITE] = Reward.LOSS

        elif self.__credit == 0:
            rewards[Player.WHITE] = Reward.DRAW
            rewards[Player.BLACK] = Reward.DRAW

        elif self.__has_action():

            if self.__player == Player.WHITE:
                rewards[Player.BLACK] = Reward.WIN
                rewards[Player.WHITE] = Reward.LOSS

            elif self.__player == Player.BLACK:
                rewards[Player.WHITE] = Reward.WIN
                rewards[Player.BLACK] = Reward.LOSS

        else:
            rewards = None

        return rewards


    def get_actions(self, use_cache: bool=True) -> PijersiActions:

        if not use_cache or self.__actions is None:
            self.__actions = self.__find_all_actions()
        return self.__actions


    def get_action_names(self) -> PijersiActions:

        if self.__actions_by_names is None:
            self.__actions_by_names = {str(action):action for action in self.get_actions()}
        return self.__actions_by_names.keys()


    def get_action_simple_names(self) -> PijersiActions:

        if self.__actions_by_simple_names is None:
            self.__actions_by_simple_names = {str(action).replace('!', ''):action for action in self.get_actions()}
        return self.__actions_by_simple_names.keys()


    def take_action(self, action: PijersiAction) -> Self:

        return PijersiState(board_codes=action.next_board_codes,
                            player=self.get_other_player(),
                            credit=max(0, self.__credit - 1) if action.capture_code == 0 else self.__max_credit,
                            turn=self.__turn + 1)


    def take_action_by_name(self, action_name):
       _ = self.get_action_simple_names()
       action = self.__actions_by_simple_names[action_name.replace('!', '')]
       return self.take_action(action)


    def take_action_by_simple_name(self, action_name):
       return self.take_action_by_name(action_name)


    def get_fighter_counts(self)-> Sequence[int]:
        return [sum((PijersiState.__TABLE_FIGHTER_COUNT[player][hex_code] for hex_code in self.__board_codes)) for player in Player]


    def get_cube_counts(self)-> Sequence[int]:
        return [sum((PijersiState.__TABLE_CUBE_COUNT[player][hex_code] for hex_code in self.__board_codes)) for player in Player]


    def get_distances_to_goal(self) -> Sequence[Sequence[int]]:
        """White and black distances to goal"""

        distances_to_goal = list()

        for player in Player:
            has_fighter = PijersiState.__TABLE_HAS_FIGHTER[player]
            goal_distances = PijersiState.__TABLE_GOAL_DISTANCES[player]

            distances_to_goal.append([goal_distances[hex_index]
                                         for (hex_index, hex_code) in enumerate(self.__board_codes)
                                         if has_fighter[hex_code] != 0])
        return distances_to_goal


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
                    bottom_label = Cube_to_name(hex_state.player, hex_state.bottom)
                    row_text += "." + bottom_label

                elif hex_state.has_stack:
                    bottom_label = Cube_to_name(hex_state.player, hex_state.bottom)
                    top_label = Cube_to_name(hex_state.player, hex_state.top)
                    row_text += top_label + bottom_label

                row_text += shift
            show_text += row_text + "\n"

        return show_text


    def show(self):
        print()
        print(self.get_show_text())
        print()
        print(self.get_summary())


    def get_summary(self) -> str:

        counters = Counter()

        for player in Player:
            player_codes = [self.__board_codes[hex_index] for hex_index in PijersiState.__find_cube_sources(self.__board_codes, player)]

            for cube in Cube:
                player_cube_table = PijersiState.__TABLE_CUBE_COUNT_BY_SORT[player][cube]
                counters[Cube_to_name(player, cube)] = sum((player_cube_table[hex_code] for hex_code in player_codes))

        summary = (
            f"turn {self.__turn} / player {Player_name(self.__player)} / credit {self.__credit} / " +
             "alive " + " ".join([f"{cube_name}:{cube_count}" for (cube_name, cube_count) in sorted(counters.items())]))

        return summary


    @staticmethod
    def decode_path_code(code: PathCode, path_length: int) -> PathCodes:

        assert code >= 0
        assert path_length >= 0

        path_codes = list()

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
    def __make_empty_board_codes() -> BoardCodes :
        board_codes = bytearray([0 for _ in Hexagon.get_all()])
        return board_codes


    @staticmethod
    def __copy_board_codes(board_codes: BoardCodes) -> BoardCodes :
        return bytearray(board_codes)


    @staticmethod
    def __make_default_board_codes() -> BoardCodes :
        board_codes = PijersiState.__make_empty_board_codes()

        #-- Whites

        PijersiState.__set_stack_from_names(board_codes, 'b4', bottom_name='W', top_name='W')

        PijersiState.__set_cube_from_names(board_codes, 'a1', 'R')
        PijersiState.__set_cube_from_names(board_codes, 'a2', 'P')
        PijersiState.__set_cube_from_names(board_codes, 'a3', 'S')
        PijersiState.__set_cube_from_names(board_codes, 'a4', 'R')
        PijersiState.__set_cube_from_names(board_codes, 'a5', 'P')
        PijersiState.__set_cube_from_names(board_codes, 'a6', 'S')

        PijersiState.__set_cube_from_names(board_codes, 'b1', 'P')
        PijersiState.__set_cube_from_names(board_codes, 'b2', 'S')
        PijersiState.__set_cube_from_names(board_codes, 'b3', 'R')

        PijersiState.__set_cube_from_names(board_codes, 'b5', 'S')
        PijersiState.__set_cube_from_names(board_codes, 'b6', 'R')
        PijersiState.__set_cube_from_names(board_codes, 'b7', 'P')

        #-- Blacks

        PijersiState.__set_stack_from_names(board_codes, 'f4', bottom_name='w', top_name='w')

        PijersiState.__set_cube_from_names(board_codes, 'g6', 'r')
        PijersiState.__set_cube_from_names(board_codes, 'g5', 'p')
        PijersiState.__set_cube_from_names(board_codes, 'g4', 's')
        PijersiState.__set_cube_from_names(board_codes, 'g3', 'r')
        PijersiState.__set_cube_from_names(board_codes, 'g2', 'p')
        PijersiState.__set_cube_from_names(board_codes, 'g1', 's')

        PijersiState.__set_cube_from_names(board_codes, 'f7', 'p')
        PijersiState.__set_cube_from_names(board_codes, 'f6', 's')
        PijersiState.__set_cube_from_names(board_codes, 'f5', 'r')

        PijersiState.__set_cube_from_names(board_codes, 'f3', 's')
        PijersiState.__set_cube_from_names(board_codes, 'f2', 'r')
        PijersiState.__set_cube_from_names(board_codes, 'f1', 'p')

        return board_codes


    @staticmethod
    def __set_cube_from_names(board_codes: BoardCodes, hex_name: str, cube_name: str):
        hex_index = Hexagon.get(hex_name).index
        (player, cube) = Cube_from_name(cube_name)
        PijersiState.__set_cube(board_codes, hex_index, player, cube)


    @staticmethod
    def __set_stack_from_names(board_codes: BoardCodes, hex_name: str, bottom_name: Cube, top_name: Cube):
        hex_index = Hexagon.get(hex_name).index
        (player, bottom) = Cube_from_name(bottom_name)
        (top_player, top) = Cube_from_name(top_name)
        assert top_player == player
        PijersiState.__set_stack(board_codes, hex_index, player, bottom, top)


    @staticmethod
    def __set_cube(board_codes: BoardCodes, hex_index: HexIndex, player: Player, cube: Cube):
        hex_state = HexState.decode(board_codes[hex_index])

        assert hex_state.is_empty

        hex_state.is_empty = False
        hex_state.player = player
        hex_state.bottom = cube
        board_codes[hex_index] = hex_state.encode()


    @staticmethod
    def __set_stack(board_codes: BoardCodes, hex_index: HexIndex, player: Player, bottom: Cube, top: Cube):
        hex_state = HexState.decode(board_codes[hex_index])

        assert hex_state.is_empty

        hex_state.is_empty = False
        hex_state.has_stack = True
        hex_state.player = player
        hex_state.bottom = bottom
        hex_state.top = top
        board_codes[hex_index] = hex_state.encode()


    def __player_is_arrived(self, player: Player) -> bool:

        goal_indices = PijersiState.__TABLE_GOAL_INDICES[player]
        has_fighter = PijersiState.__TABLE_HAS_FIGHTER[player]

        return sum((has_fighter[self.__board_codes[hex_index]] for hex_index in goal_indices)) != 0


    def __has_action(self) -> bool:

        for cube_source in PijersiState.__find_cube_sources(self.__board_codes, self.__player):
            for cube_direction in HEXAGON_DIRECTION_ITERATOR:
                if PijersiState.__try_cube_path1_action(self.__board_codes, cube_source, cube_direction) is not None:
                    return True
        return False


    @staticmethod
    def __find_cube_sources(board_codes: BoardCodes, player: Player) -> Sources:
        table_code = PijersiState.__TABLE_HAS_CUBE[player]
        return (hex_index for (hex_index, hex_code) in enumerate(board_codes) if table_code[hex_code] != 0)


    def __find_all_actions(self) -> PijersiActions:

        actions = list()

        for cube_source_1 in PijersiState.__find_cube_sources(self.__board_codes, self.__player):

            for cube_direction_1 in HEXAGON_DIRECTION_ITERATOR:

                #-- all first moves using a cube
                action1 = PijersiState.__try_cube_path1_action(self.__board_codes, cube_source_1, cube_direction_1)
                if action1 is not None:
                    actions.append(action1)

                    board_codes_1 = action1.next_board_codes
                    stack_source_1 = action1.path_vertices[-1]
                    if PijersiState.__TABLE_HAS_STACK[self.__player][board_codes_1[stack_source_1]] != 0:
                        for stack_direction_1 in HEXAGON_DIRECTION_ITERATOR:
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
                            for cube_direction_2 in HEXAGON_DIRECTION_ITERATOR:
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
                                for cube_direction_2 in HEXAGON_DIRECTION_ITERATOR:
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
    def __encode_path3_codes(path_codes: PathCodes) -> PathCode:
        # >> optimization of 'encode_path_codes' for path3
        return path_codes[0] + path_codes[1]*HexState.CODE_BASE + path_codes[2]*HexState.CODE_BASE_2


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
        next_board_codes = PijersiState.__copy_board_codes(board_codes)

        next_board_codes[path[0]] = path_codes[0]
        next_board_codes[path[1]] = path_codes[1]
        return next_board_codes


    @staticmethod
    def __apply_path3_codes(board_codes: BoardCodes, path: Path, path_codes: PathCodes) -> BoardCodes:
        next_board_codes = PijersiState.__copy_board_codes(board_codes)
        next_board_codes[path[0]] = path_codes[0]
        next_board_codes[path[1]] = path_codes[1]
        next_board_codes[path[2]] = path_codes[2]
        return next_board_codes


    @staticmethod
    def __try_cube_path1_action(board_codes: BoardCodes, source: HexIndex, direction: HexagonDirection) -> Optional[PijersiAction]:

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
    def __try_stack_path1_action(board_codes: BoardCodes, source: HexIndex, direction: HexagonDirection) -> Optional[PijersiAction]:

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
    def __try_stack_path2_action(board_codes: BoardCodes, source: HexIndex, direction: HexagonDirection) -> Optional[PijersiAction]:

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

    __slots__ = ('__name')


    def __init__(self, name):
        self.__name = name


    def get_name(self) -> str:
        return self.__name


    def is_interactive(self) -> bool:
        return False


    def search(self, state: PijersiState) -> PijersiAction:
        actions = state.get_actions()
        action = actions[0]
        return action


class RandomSearcher(Searcher):


    def __init__(self, name):
        super().__init__(name)


    def search(self, state: PijersiState) -> PijersiAction:
        actions = state.get_actions()
        # >> sorting help for testing against other implementations if random generations are identical
        actions.sort(key=str)
        action = random.choice(actions)
        return action


class Game:

    __slots__ = ('__searcher', '__pijersi_state', '__enabled_log', '__log', '__turn', '__last_action', '__turn_duration')


    def __init__(self):
        self.__searcher = [None, None]
        self.__pijersi_state = None

        self.__enabled_log = True
        self.__log = ""
        self.__turn = None
        self.__last_action = None
        self.__turn_duration = {Player.WHITE:[], Player.BLACK:[]}


    def enable_log(self, condition: bool):
        self.__enabled_log = condition
        if not self.__enabled_log:
            self.__log = ""


    def set_white_searcher(self, searcher: Searcher):
        self.__searcher[Player.WHITE] = searcher


    def set_black_searcher(self, searcher: Searcher):
        self.__searcher[Player.BLACK] = searcher


    def start(self):

        assert self.__searcher[Player.WHITE] is not None
        assert self.__searcher[Player.BLACK] is not None

        self.__pijersi_state = PijersiState()

        if self.__enabled_log:
            self.__pijersi_state.show()
            self.__log = "Game started"


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


    def get_rewards(self) -> Optional[Tuple[Reward, Reward]]:
        return self.__pijersi_state.get_rewards()


    def has_next_turn(self) -> bool:
        return not self.__pijersi_state.is_terminal()


    def next_turn(self):

        self.__log = ""

        if self.has_next_turn():
            player = self.__pijersi_state.get_current_player()

            if self.__enabled_log:
                player_name = f"{Player_name(player)}-{self.__searcher[player].get_name()}"
                print()
                print(f"{player_name} is thinking ...")
                turn_start = time.time()

            action = self.__searcher[player].search(self.__pijersi_state)

            self.__last_action = str(action)
            self.__turn = self.__pijersi_state.get_turn()

            if self.__enabled_log:
                turn_end = time.time()
                turn_duration = turn_end - turn_start
                self.__turn_duration[player].append(turn_duration)
                print(f"{player_name} is done after %.1f seconds" % turn_duration)

                action_count = len(self.__pijersi_state.get_actions())
                self.__log = f"turn {self.__turn} : after {turn_duration:.1f} seconds {player_name} selects {action} amongst {action_count} actions"
                print(self.__log)
                print("-"*40)

            self.__pijersi_state = self.__pijersi_state.take_action(action)

            if self.__enabled_log:
                self.__pijersi_state.show()

        if self.__pijersi_state.is_terminal():

            rewards = self.__pijersi_state.get_rewards()
            player = self.__pijersi_state.get_current_player()

            if self.__enabled_log:
                print()
                print("-"*40)

                white_time = sum(self.__turn_duration[Player.WHITE])
                black_time = sum(self.__turn_duration[Player.BLACK])

                white_player = f"{Player_name(Player.WHITE)}-{self.__searcher[Player.WHITE].get_name()}"
                black_player = f"{Player_name(Player.BLACK)}-{self.__searcher[Player.BLACK].get_name()}"

                if rewards[Player.WHITE] == rewards[Player.BLACK]:
                    self.__log = f"nobody wins ; the game is a draw between {white_player} and {black_player} ; {white_time:.0f} versus {black_time:.0f} seconds"

                elif rewards[Player.WHITE] > rewards[Player.BLACK]:
                    self.__log = f"{white_player} wins against {black_player} ; {white_time:.0f} versus {black_time:.0f} seconds"

                else:
                    self.__log = f"{black_player} wins against {white_player} ; {black_time:.0f} versus {white_time:.0f} seconds"

                print(self.__log)


def test():


    def generate_random_hex_state(is_empty: Optional[bool]=None,
                                  has_stack: Optional[bool]=None,
                                  player: Optional[Player]=None,
                                  bottom: Optional[Cube]=None,
                                  top: Optional[Cube]=None) -> HexState:

        is_empty = random.choice((True, False)) if is_empty is None else is_empty
        if not is_empty:
            player = random.choice(tuple(Player)) if player is None else player
            bottom = random.choice(tuple(Cube)) if bottom is None else bottom
            has_stack = random.choice((True, False)) if has_stack is None else has_stack
            if has_stack:
                if bottom == Cube.WISE:
                    top = random.choice(tuple(Cube)) if top is None else top
                else:
                    top = random.choice((Cube.ROCK, Cube.PAPER, Cube.SCISSORS)) if top is None else top

        else:
            has_stack = False
            player = None
            bottom = None
            top = None

        return HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)


    def generate_random_path_state(path_length: int) -> PathStates:
        assert path_length >= 0
        path_state = [generate_random_hex_state() for _ in range(path_length)]
        return path_state


    def test_iterate_hex_states() -> None:

        print()
        print("-- test_iterate_hex_states --")

        hex_codes = set()

        for hex_state in HexState.iterate_hex_states():
            hex_code = hex_state.encode()
            print(f"hex_state = {hex_state} ; hex_code={hex_code}")
            assert hex_code not in hex_codes
            hex_codes.add(hex_code)

        print(f"len(hex_codes) = {len(hex_codes)} ; min(hex_codes) = {min(hex_codes)} ; max(hex_codes) = {max(hex_codes)}")
        assert len(hex_codes) <= HexState.CODE_BASE
        assert min(hex_codes) == 0
        assert max(hex_codes) <= HexState.CODE_BASE


    def test_encode_and_decode_hex_state():

        print()
        print("-- test_encode_and_decode_hex_state --")

        hex_state_count = 100

        for _ in range(hex_state_count):

            hex_state = generate_random_hex_state()
            print()
            print(f"hex_state = {hex_state}")

            hex_state_code = hex_state.encode()
            print(f"hex_state_code = {hex_state_code}")

            hex_decoded_state = HexState.decode(hex_state_code)
            print(f"hex_decoded_state = {hex_decoded_state}")
            assert hex_decoded_state == hex_state

        hex_state_count = 100

        for _ in range(hex_state_count):

            hex_state = generate_random_hex_state(is_empty=False, has_stack=True, bottom=Cube.WISE)
            print()
            print(f"hex_state = {hex_state}")

            hex_state_code = hex_state.encode()
            print(f"hex_state_code = {hex_state_code}")

            hex_decoded_state = HexState.decode(hex_state_code)
            print(f"hex_decoded_state = {hex_decoded_state}")
            assert hex_decoded_state == hex_state


    def test_encode_and_decode_path_states() -> None:

        print()
        print("-- test_encode_and_decode_path_states --")

        path_state_count = 100
        path_length = 3

        for _ in range(path_state_count):
            path_state = generate_random_path_state(path_length)
            print()
            print(f"path_state = {path_state}")

            path_code = PijersiState.encode_path_states(path_state)
            print(f"path_code = {path_code}")

            path_codes = PijersiState.decode_path_code(path_code, path_length)
            print(f"path_codes = {path_codes}")

            path_decoded_state = PijersiState.decode_path_codes(path_codes)
            print(f"path_decoded_state = {path_decoded_state}")
            assert path_decoded_state == path_state


    def test_first_get_actions():

        print()
        print("-- test_first_get_actions --")

        new_state = PijersiState()

        new_action_names = new_state.get_action_names()
        new_action_name_set = set(new_action_names)

        old_state = rules.PijersiState()
        old_action_names = old_state.get_action_names()
        old_action_name_set = set(old_action_names)

        print(f"len(new_action_name_set) = {len(new_action_name_set)} ; len(old_action_name_set) = {len(old_action_name_set)}")
        assert len(new_action_name_set) == len(old_action_name_set)
        assert new_action_name_set == old_action_name_set


    def test_first_get_summary():

        print()
        print("-- test_first_get_summary --")

        new_state = PijersiState()
        summary = new_state.get_summary()
        print()
        print(f"summary = {summary}")
        assert summary == "turn 1 / player white / credit 20 / alive P:4 R:4 S:4 W:2 p:4 r:4 s:4 w:2"


    def test_first_get_show_text():

        print()
        print("-- test_first_get_show_text --")

        new_state = PijersiState()
        new_show_text = new_state.get_show_text()

        old_state = rules.PijersiState()
        old_show_text = old_state.get_show_text()

        print()
        print(f"new_show_text = \n {new_show_text}")

        print()
        print(f"old_show_text = \n {old_show_text}")
        assert new_show_text == old_show_text


    def benchmark_first_get_actions():

        print()
        print("-- benchmark_first_get_actions --")

        new_state = PijersiState()
        new_actions = new_state.get_actions()
        new_actions_id = id(new_actions)

        old_state = rules.PijersiState()
        old_actions = old_state.get_actions()
        old_actions_id = id(old_actions)

        assert len(new_actions) == len(old_actions)
        assert new_actions_id != old_actions_id


        def do_new():
            new_actions = new_state.get_actions(use_cache=False)
            assert id(new_actions) != new_actions_id


        def do_old():
            old_actions = old_state.get_actions(use_cache=False)
            assert id(old_actions) != old_actions_id


        time_new = timeit.timeit(do_new, number=100)
        time_old = timeit.timeit(do_old, number=100)
        print("do_new() => ", time_new)
        print("do_old() => ", time_old,
              ', (time_new/time_old - 1)*100 =', (time_new/time_old -1)*100,
              ', time_old/time_new = ', time_old/time_new)


    def benchmark_first_is_terminal():

        print()
        print("-- benchmark_first_is_terminal --")

        new_state = PijersiState()
        old_state = rules.PijersiState()


        def do_new():
            assert not new_state.is_terminal(use_cache=False)


        def do_old():
            assert not old_state.is_terminal(use_cache=False)


        time_new = timeit.timeit(do_new, number=1_000)
        time_old = timeit.timeit(do_old, number=1_000)
        print("do_new() => ", time_new)
        print("do_old() => ", time_old,
              ', (time_new/time_old - 1)*100 =', (time_new/time_old -1)*100,
              ', time_old/time_new = ', time_old/time_new)


    def profile_first_get_actions():

        print()
        print("-- profile_first_get_actions --")

        test_profiling_1_data['pijersi_state'] = PijersiState()

        cProfile.run('test_profiling_1_get_actions()', sort=SortKey.TIME)


    def profile_first_is_terminal():

        print()
        print("-- profile_first_is_terminal --")

        test_profiling_1_data['pijersi_state'] = PijersiState()

        cProfile.run('test_profiling_2_is_terminal()', sort=SortKey.TIME)


    def test_game_between_random_players():

        print()
        print("-- test_game_between_random_players --")

        game_count = 10
        game_enabled_log = False

        for game_index in range(game_count):

            test_seed = random.randint(1, 1_000)
            test_max_credit = random.randint(10, 100)

            #-- Run new games

            default_max_credit = PijersiState.get_max_credit()
            PijersiState.set_max_credit(test_max_credit)

            random.seed(a=test_seed)
            new_show_texts = []
            new_action_sets = []
            new_summaries = []
            new_game = Game()
            new_game.enable_log(game_enabled_log)

            new_game.set_white_searcher(RandomSearcher("random"))
            new_game.set_black_searcher(RandomSearcher("random"))

            new_game.start()
            new_show_texts.append(new_game.get_state().get_show_text())
            new_action_sets.append(set(new_game.get_state().get_action_names()))
            new_summaries.append(new_game.get_state().get_summary())

            while new_game.has_next_turn():
                new_game.next_turn()
                new_show_texts.append(new_game.get_state().get_show_text())
                new_action_sets.append(set(new_game.get_state().get_action_names()))
                new_summaries.append(new_game.get_state().get_summary())

            new_rewards = new_game.get_state().get_rewards()

            PijersiState.set_max_credit(default_max_credit)

            #-- Run old games

            default_max_credit = rules.PijersiState.get_max_credit()
            rules.PijersiState.set_max_credit(test_max_credit)

            random.seed(a=test_seed)
            old_show_texts = []
            old_action_sets = []
            old_summaries = []
            old_game = rules.Game()
            old_game.enable_log(game_enabled_log)

            old_game.set_white_searcher(RandomSearcher("random"))
            old_game.set_black_searcher(RandomSearcher("random"))

            old_game.start()
            old_show_texts.append(old_game.get_state().get_show_text())
            old_action_sets.append(set(old_game.get_state().get_action_names()))
            old_summaries.append(old_game.get_state().get_summary())

            while old_game.has_next_turn():
                old_game.next_turn()
                old_show_texts.append(old_game.get_state().get_show_text())
                old_action_sets.append(set(old_game.get_state().get_action_names()))
                old_summaries.append(old_game.get_state().get_summary())

            old_rewards = old_game.get_state().get_rewards()

            rules.PijersiState.set_max_credit(default_max_credit)

            #-- Compare new games to old games

            print()

            print(f"len(new_show_texts) = {len(new_show_texts)} / len(old_show_texts) = {len(old_show_texts)}")
            assert len(new_show_texts) == len(old_show_texts)
            for (new_show_text, old_show_text) in zip(new_show_texts, old_show_texts):
                assert new_show_text == old_show_text

            print(f"len(new_action_sets) = {len(new_action_sets)} / len(old_action_sets) = {len(old_action_sets)}")
            assert len(new_action_sets) == len(old_action_sets)
            for (new_action_set, old_action_set) in zip(new_action_sets, old_action_sets):
                assert new_action_set == old_action_set

            print(f"len(new_summaries) = {len(new_summaries)} / len(old_summaries) = {len(old_summaries)}")
            assert len(new_summaries) == len(old_summaries)
            for (new_summary, old_summary) in zip(new_summaries, old_summaries):
                assert new_summary == old_summary

            print(f"new_rewards = {new_rewards} / old_rewards = {old_rewards}")
            assert new_rewards == old_rewards

            print(f"game {game_index} from {list(range(game_count))} OK")


    def benchmark_game_between_random_players():

        print()
        print("-- benchmark_game_between_random_players --")

        test_seed = random.randint(1, 1_000)
        test_max_credit_limits = (20, 1_000)
        game_count = 20
        game_enabled_log = False

        def do_new():
            random.seed(a=test_seed)

            for game_index in range(game_count):

                test_max_credit = random.randint(test_max_credit_limits[0], test_max_credit_limits[1])

                default_max_credit = PijersiState.get_max_credit()
                PijersiState.set_max_credit(test_max_credit)

                new_game = Game()
                new_game.enable_log(game_enabled_log)

                new_game.set_white_searcher(RandomSearcher("random"))
                new_game.set_black_searcher(RandomSearcher("random"))

                new_game.start()

                while new_game.has_next_turn():
                    new_game.next_turn()

                PijersiState.set_max_credit(default_max_credit)


        def do_old():
            random.seed(a=test_seed)

            for game_index in range(game_count):

                test_max_credit = random.randint(test_max_credit_limits[0], test_max_credit_limits[1])

                default_max_credit = rules.PijersiState.get_max_credit()
                rules.PijersiState.set_max_credit(test_max_credit)

                old_game = rules.Game()
                old_game.enable_log(game_enabled_log)

                old_game.set_white_searcher(RandomSearcher("random"))
                old_game.set_black_searcher(RandomSearcher("random"))

                old_game.start()

                while old_game.has_next_turn():
                    old_game.next_turn()

                rules.PijersiState.set_max_credit(default_max_credit)


        time_new = timeit.timeit(do_new, number=1)
        time_old = timeit.timeit(do_old, number=1)
        print("do_new() => ", time_new)
        print("do_old() => ", time_old,
              ', (time_new/time_old - 1)*100 =', (time_new/time_old -1)*100,
              ', time_old/time_new = ', time_old/time_new)


    if False:
        test_encode_and_decode_hex_state()
        test_encode_and_decode_path_states()
        test_iterate_hex_states()
        PijersiState.print_tables()

    if False:
        test_first_get_actions()

    if False:
        test_first_get_summary()

    if False:
        test_first_get_show_text()

    if True:
        benchmark_first_get_actions()

    if True:
        benchmark_first_is_terminal()

    if False:
        profile_first_is_terminal()

    if False:
        profile_first_get_actions()

    if False:
        test_game_between_random_players()

    if True:
        benchmark_game_between_random_players()


test_profiling_1_data = dict()


def test_profiling_1_get_actions():
    #>> Defined at the uper scope of the module because of "cProfile.run"

    pijersi_state = test_profiling_1_data['pijersi_state']

    for _ in range(100):
        actions = pijersi_state.get_actions(use_cache=False)
        assert actions is not None


def test_profiling_2_is_terminal():
    #>> Defined at the uper scope of the module because of "cProfile.run"

    pijersi_state = test_profiling_1_data['pijersi_state']

    for _ in range(100_000):
        assert not pijersi_state.is_terminal(use_cache=False)


def main():
    Hexagon.init()
    PijersiState.init()
    test()


if __name__ == "__main__":
    print()
    print("Hello")
    print(f"sys.version = {sys.version}")

    main()

    print()
    print("Bye")

    if True:
        print()
        _ = input("main: done ; press enter to terminate")
