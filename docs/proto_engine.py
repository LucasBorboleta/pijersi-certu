# -*- coding: utf-8 -*-
"""
Prototyping a new design for the rules and AI engine intented to be fast
"""

import array
import copy
import enum
from dataclasses import dataclass
import os
import random
import sys
from typing import Callable
from typing import Iterable
from typing import NewType
from typing import Optional
from typing import Sequence
from typing import TypeVar


_package_home = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "pijersi_certu")
sys.path.append(_package_home)
import pijersi_rules as rules


@enum.unique
class Cube(enum.IntEnum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2
    WISE = 3
    assert ROCK < PAPER < SCISSORS < WISE


def beats(src: Cube, dst: Cube) -> bool:
    return (src, dst) in ((Cube.ROCK, Cube.SCISSORS), (Cube.SCISSORS, Cube.PAPER), (Cube.PAPER, Cube.ROCK) )


class Player(enum.IntEnum):
    WHITE = 0
    BLACK = 1
    assert WHITE < BLACK


@enum.unique
class Direction(enum.IntEnum):
    PHI_090 = 0
    PHI_150 = 1
    PHI_210 = 2
    PHI_270 = 3
    PHI_330 = 4
    PHI_030 = 5
    assert PHI_090 < PHI_150 < PHI_210 < PHI_270 < PHI_330 < PHI_030


HexIndex = NewType('HexIndex', int)
Sources = Iterable[HexIndex]
Path = Sequence[HexIndex]

HexCode = NewType('HexCode', int)
HEX_CODE_BASE = HexCode((2*2*2)*(2*2*2)*2)


class HexState:
    
    Self = TypeVar("Self", bound="HexState")

    __slots__ = ('is_empty', 'has_stack', 'player', 'bottom', 'top', '__code')
    
    def __init__(self, is_empty: bool=True, has_stack: bool=False, 
                player: Optional[Player]=None, bottom: Optional[Cube]=None, top: Optional[Cube]=None):
        
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
            
            assert 0 <= code < HEX_CODE_BASE
            self.__code = code
    
        return self.__code


    @staticmethod
    def decode(code: HexCode) -> Self:

        assert 0 <= code < HEX_CODE_BASE
    
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

    
PathState = Sequence[HexState]
BoardState = Sequence[HexState]


def iterate_hex_states() -> Iterable[HexState]:
    
    for is_empty in (True, False):
        
        if is_empty:
            has_stack = False
            player = None
            bottom = None
            top = None
            yield HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)

        else:
            for player in Player:
                for bottom in Cube:
                    for has_stack in (True, False):
                        if has_stack:
                            if bottom == Cube.WISE:
                                for top in Cube:
                                    yield HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)
                            else:
                                for top in (Cube.ROCK, Cube.PAPER, Cube.SCISSORS):
                                    yield HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)
                        else:
                            top = None
                            yield HexState(is_empty=is_empty, has_stack=has_stack, player=player, bottom=bottom, top=top)
  
def test_iterate_hex_states():
    
    print()
    print("-- test_iterate_hex_states --")
    
    hex_codes = set()
    
    for hex_state in iterate_hex_states():
        hex_code = hex_state.encode()
        print(f"hex_state = {hex_state} ; hex_code={hex_code}")
        assert hex_code not in hex_codes
        hex_codes.add(hex_code)
        
    print(f"len(hex_codes) = {len(hex_codes)} ; min(hex_codes) = {min(hex_codes)} ; max(hex_codes) = {max(hex_codes)}")
    assert len(hex_codes) <= HEX_CODE_BASE
    assert min(hex_codes) == 0
    assert max(hex_codes) <= HEX_CODE_BASE
    
        
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


def encode_path_state(path_state: PathState) -> int:
    code = 0
    shift = 1
    for hex_state in path_state:
        code += shift*hex_state.encode()
        shift *= HEX_CODE_BASE
    return code
 

def decode_path_state(code: int, path_length: int) -> PathState:
    path_state = list()
    
    assert code >= 0
    
    rest = code
    for hex_index in range(path_length):
        hex_code = rest % HEX_CODE_BASE
        rest = rest // HEX_CODE_BASE
        path_state.append(HexState.decode(hex_code))
        
    assert rest == 0
    
    return path_state


def generate_random_path_state(path_length: int) -> PathState:
    assert path_length >= 0
    path_state = [generate_random_hex_state() for _ in range(path_length)]
    return path_state
                               

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


def test_encode_and_decode_path_state():
    
    print()
    print("-- test_encode_and_decode_path_state --")
    
    path_state_count = 100
    path_length = 3
    
    for _ in range(path_state_count):
        path_state = generate_random_path_state(path_length)
        print()
        print(f"path_state = {path_state}")
    
        path_state_code = encode_path_state(path_state)
        print(f"path_state_code = {path_state_code}")
        
        path_decoded_state = decode_path_state(path_state_code, path_length)
        print(f"path_decoded_state = {path_decoded_state}")
        assert path_decoded_state == path_state

    
@dataclass
class GameState:
    board_state: BoardState
    is_terminal: bool
    credit: int
    turn: int
    current_player: Player
    
    
@dataclass
class Action:
    next_board_state: BoardState
    path_vertices: Path
    has_capture: bool

Actions = Sequence[Action]
  

def make_goal_scores(player: Player) -> Sequence[int]:
    table = array.array('B', [0 for _ in range(HEX_CODE_BASE)])
    
    for hex_state in iterate_hex_states():
        
        if hex_state.is_empty:
            count = 0
            
        elif hex_state.player == player:
            
            if hex_state.has_stack:
                count = 0
                count += 1 if hex_state.bottom != Cube.WISE else 0
                count += 1 if hex_state.top != Cube.WISE else 0
            
            else:
                count = 1 if hex_state.bottom != Cube.WISE else 0
            
        hex_code = hex_state.encode()
        table[hex_code] = count
    return table
  

TABLE_GOAL_INDICES_BY_PLAYER = [rules.Hexagon.get_goal_indices(player) for player in Player]
TABLE_GOAL_SCORES_BY_PLAYER = [make_goal_scores(player) for player in Player]


def player_is_arrived(board_state: BoardState, player: Player) -> bool:
 
    goal_indices = TABLE_GOAL_INDICES_BY_PLAYER[player]
    goal_scores = TABLE_GOAL_SCORES_BY_PLAYER[player]
   
    goal_score = sum([goal_scores[board_state[hex_index].encode()] for hex_index in goal_indices])
    is_arrived = (goal_score != 0)
    
    return is_arrived


def make_table_cube_count() -> Sequence[int]:
    table = array.array('B', [0 for _ in range(HEX_CODE_BASE)])
    
    for hex_state in iterate_hex_states():
        
        if hex_state.is_empty:
            count = 0
            
        elif hex_state.has_stack:
            count = 2
            
        else:
            count = 1
            
        hex_code = hex_state.encode()
        table[hex_code] = count
    return table


def make_table_fighter_count() -> Sequence[int]:
    table = array.array('B', [0 for _ in range(HEX_CODE_BASE)])
    
    for hex_state in iterate_hex_states():
        
        if hex_state.is_empty:
            count = 0
            
        elif hex_state.has_stack:
            count = 0
            count += 1 if hex_state.bottom != Cube.WISE else 0
            count += 1 if hex_state.top != Cube.WISE else 0
            
        else:
            count = 1 if hex_state.bottom != Cube.WISE else 0
            
        hex_code = hex_state.encode()
        table[hex_code] = count
    return table
    

TABLE_CUBE_COUNT = make_table_fighter_count()
TABLE_FIGHTER_COUNT = make_table_cube_count()

    
def print_table_cube_count():
    print()
    print("-- print_table_cube_count --")
    print(TABLE_CUBE_COUNT)
    
    
def print_table_fighter_count():
    print()
    print("-- print_table_fighter_count --")
    print(TABLE_FIGHTER_COUNT)


def get_distances_to_goal(board_state: BoardState) -> Sequence[Sequence[int]]:
    """White and black distances to goal"""

    distances_to_goal = [[] for _ in Player]

    for (hex_index, hex_state) in enumerate(board_state):
        fighter_count = TABLE_FIGHTER_COUNT[hex_state.encode()]
        if fighter_count != 0:
            distance = rules.Hexagon.get_distance_to_goal(hex_index, hex_state.player)
            distances_to_goal[hex_state.player].append(distance)

    return distances_to_goal


def get_fighter_counts(board_state: BoardState)-> Sequence[int]:
    counts = [0 for _ in Player]
    
    for hex_state in board_state:
        fighter_count = TABLE_FIGHTER_COUNT[hex_state.encode()]
        counts[hex_state.player] += fighter_count
    
    return counts


def get_cube_counts(board_state: BoardState)-> Sequence[int]:
    counts = [0 for _ in Player]
    
    for hex_state in board_state:
        fighter_count = TABLE_CUBE_COUNT[hex_state.encode()]
        counts[hex_state.player] += fighter_count
    
    return counts


def find_cube_sources(board_state: BoardState, current_player: Player) -> Sources:
    sources = list()
    for (hex_index, hex_state) in enumerate(board_state):
         if not hex_state.is_empty and hex_state.player == current_player:
             sources.append(hex_index)
    return sources
     
    
def find_stack_sources(board_state: BoardState, current_player: Player) -> Sources:
    sources = list()
    for (hex_index, hex_state) in enumerate(board_state):
         if not hex_state.is_empty and hex_state.player == current_player and hex_state.has_stack :
             sources.append(hex_index)
    return sources


def make_path1(source: HexIndex, direction: Direction) -> Optional[Path]:
    path = None
    
    next_fst_hex = rules.Hexagon.get_next_fst_active_indices(source, direction)
    
    if next_fst_hex != rules.Null.HEXAGON:
        path = [source, next_fst_hex]
        
    return path


def make_path2(source: HexIndex, direction: Direction) -> Optional[Path]:
    path = None
    
    next_fst_hex = rules.Hexagon.get_next_fst_active_indices(source, direction)
    
    if next_fst_hex != rules.Null.HEXAGON:
        next_snd_hex = rules.Hexagon.get_next_snd_active_indices(source, direction)

        if next_snd_hex != rules.Null.HEXAGON:
            path = [source, next_fst_hex, next_snd_hex]
        
    return path


def make_path_state(board_state: BoardState, path: Path) -> PathState:
    path_state = [board_state[hex_index] for hex_index in path]
    return path_state


def make_tables_try_cube_path1() -> (Sequence[int], Sequence[int]):
    table_next_code = array.array('H', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    table_has_capture = array.array('B', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    
    for src_state in iterate_hex_states():
        for dst_state in iterate_hex_states():
            code = encode_path_state([src_state, dst_state])
            
            next_code = 0
            has_capture = 0
            
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
                            if beats(src_state.top, dst_state.top):
                                has_capture = 1
                                next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)

                        else:
                            if beats(src_state.bottom, dst_state.top):
                                has_capture = 1
                                next_src_state = HexState.make_empty()
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                    
                    else:
                        # == Destination has a single cube owned by the non-active player
                        
                        if src_state.has_stack:
                            if beats(src_state.top, dst_state.bottom):
                                has_capture = 1
                                next_src_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.top)
                        else:
                            if beats(src_state.bottom, dst_state.bottom):
                                has_capture = 1
                                next_src_state = HexState.make_empty()
                                next_dst_state = HexState.make_single(player=src_state.player, cube=src_state.bottom)
                
                if next_src_state is not None and next_dst_state is not None:
                    next_code = encode_path_state([next_src_state, next_dst_state])
                
            table_next_code[code] = next_code
            table_has_capture[code] = has_capture
        
    return (table_next_code, table_has_capture )


def make_tables_try_stack_path(table_next_code: Sequence[int] , 
                               table_has_capture: Sequence[int], 
                               next_mid_state=Optional[HexState]) -> None:
   
    for src_state in iterate_hex_states():
        for dst_state in iterate_hex_states():
            code = encode_path_state([src_state, dst_state])
            
            next_code = 0
            has_capture = 0
            
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
                        if beats(src_state.top, dst_state.top):
                            has_capture = 1
                            next_src_state = HexState.make_empty()
                            next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)
                    
                    else:
                        # == Destination has a single cube owned by the non-active player
                        if beats(src_state.top, dst_state.bottom):
                            has_capture = 1
                            next_src_state = HexState.make_empty()
                            next_dst_state = HexState.make_stack(player=src_state.player, bottom=src_state.bottom, top=src_state.top)
             
                if next_src_state is not None and next_dst_state is not None:
                    
                    if next_mid_state is None:
                        next_code = encode_path_state([next_src_state, next_dst_state])
                        
                    else:
                        next_code = encode_path_state([next_src_state, next_mid_state, next_dst_state])

            table_next_code[code] = next_code
            table_has_capture[code] = has_capture
        
    return (table_next_code, table_has_capture )


def make_tables_try_stack_path1() -> (Sequence[int], Sequence[int]):
    table_next_code = array.array('H', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    table_has_capture = array.array('B', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    
    make_tables_try_stack_path(table_next_code, table_has_capture, next_mid_state=None)

    return (table_next_code, table_has_capture)


def make_tables_try_stack_path2() -> (Sequence[int], Sequence[int]):
    table_next_code = array.array('L', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    table_has_capture = array.array('B', [0 for _ in range(HEX_CODE_BASE*HEX_CODE_BASE)])
    
    make_tables_try_stack_path(table_next_code, table_has_capture, next_mid_state=HexState.make_empty())

    return (table_next_code, table_has_capture)


( TABLE_TRY_CUBE_PATH1_NEXT_CODE, 
  TABLE_TRY_CUBE_PATH1_HAS_CAPTURE ) =  make_tables_try_cube_path1()
 
( TABLE_TRY_STACK_PATH1_NEXT_CODE, 
  TABLE_TRY_STACK_PATH1_HAS_CAPTURE ) = make_tables_try_stack_path1()
 
( TABLE_TRY_STACK_PATH2_NEXT_CODE,
  TABLE_TRY_STACK_PATH2_HAS_CAPTURE ) = make_tables_try_stack_path2()
 
    
def print_tables_try_cube_path1():
    print()
    print("-- print_tables_try_cube_path1 --")
    print(TABLE_TRY_CUBE_PATH1_NEXT_CODE)
    print(TABLE_TRY_CUBE_PATH1_HAS_CAPTURE)
 
    
def print_tables_try_stack_path1():
    print()
    print("-- print_tables_try_stack_path1 --")
    print(TABLE_TRY_STACK_PATH1_NEXT_CODE)
    print(TABLE_TRY_STACK_PATH1_HAS_CAPTURE)
 
    
def print_tables_try_stack_path2():
    print()
    print("-- print_tables_try_stack_path2 --")
    print(TABLE_TRY_STACK_PATH2_NEXT_CODE)
    print(TABLE_TRY_STACK_PATH2_HAS_CAPTURE)


def try_path1(path_state: PathState, 
              table_next_code: Sequence[HexCode], 
              table_has_capture: Sequence[bool]) -> (Optional[PathState], bool):

    assert len(path_state) == 2
    
    next_path_state = None
    has_capture = False
    
    code = encode_path_state(path_state)
    next_code = table_next_code[code]
    
    if next_code != 0:
        next_path_state = decode_path_state(next_code, len(path_state))
        has_capture = (table_has_capture[code] != 0)
    
    return (next_path_state, has_capture)


def try_path2(path_state: PathState, 
              table_next_code: Sequence[HexCode], 
              table_has_capture: Sequence[bool]) -> (Optional[PathState], bool):

    assert len(path_state) == 3
    
    next_path_state = None
    has_capture = False
    
    # >> Optimization: if the intermediate hexagon is not empty then the stack cannot cross it
    # >> Such optimization is reducing the size of the index domain of table_next_code and table_has_capture
    code1 = path_state[1].encode()
    if code1 != 0:
        compressed_path_state = [path_state[0], path_state[2]]
        code = encode_path_state(compressed_path_state)
        next_code = table_next_code[code]
    
        if next_code != 0:
            # >> next_code is encoding a three hexagons path state
            next_path_state = decode_path_state(next_code, len(path_state))
            has_capture = (table_has_capture[code] != 0)
    
    return (next_path_state, has_capture)


def try_cube_path1(path_state: PathState) -> (Optional[PathState], bool):
    return try_path1(path_state, TABLE_TRY_CUBE_PATH1_NEXT_CODE, TABLE_TRY_CUBE_PATH1_HAS_CAPTURE)


def try_stack_path1(path_state: PathState) -> (Optional[PathState], bool):
    return try_path1(path_state, TABLE_TRY_STACK_PATH1_NEXT_CODE, TABLE_TRY_STACK_PATH1_HAS_CAPTURE)


def try_stack_path2(path_state: PathState) -> (PathState, bool):
    return try_path2(path_state, TABLE_TRY_STACK_PATH2_NEXT_CODE, TABLE_TRY_STACK_PATH2_HAS_CAPTURE)


def apply_path_state(board_state: BoardState, path: Path, path_state: PathState) -> BoardState:
    next_board_state = copy.deepcopy(board_state)
    for (hex_index, hex_state) in zip(path, path_state):
        next_board_state[hex_index] = hex_state
    return next_board_state


def has_action(game_state: GameState) -> bool:
    actions = find_cube_first_actions(game_state, find_one=False)
    return len(actions) != 0

   
def find_actions(game_state: GameState) -> Actions:
    actions = list()
    actions += find_cube_first_actions(game_state)
    actions += find_stack_first_actions(game_state)
    return actions
    

def try_cube_path1_action(board_state: BoardState, source: HexIndex, direction: Direction) -> Optional[Action]:
    return try_path_action(board_state, source, direction, make_path1, try_cube_path1)                    
    

def try_stack_path1_action(board_state: BoardState, source: HexIndex, direction: Direction) -> Optional[Action]:
    return try_path_action(board_state, source, direction, make_path1, try_stack_path1)                    
    

def try_stack_path2_action(board_state: BoardState, source: HexIndex, direction: Direction) -> Optional[Action]:
    return try_path_action(board_state, source, direction, make_path2, try_stack_path2)                    


def try_path_action(board_state: BoardState, source: HexIndex, direction: Direction,
                    make_path: Callable, try_path: Callable) -> Optional[Action]:
    action = None
    path = make_path(source, direction)
    if path is not None:
        path_state = make_path_state(board_state, path)
        (next_path_state, has_capture) = try_path(path_state)
        if next_path_state is not None:
            action = Action()
            action.next_board_state = apply_path_state(board_state, path, next_path_state)
            action.path_vertices = [source, path[-1]]
            action.has_capture = has_capture  
    return action                    


def find_cube_first_actions(game_state: GameState, find_one=False) -> Actions:
    actions = list()
    found_one = False
    
    if not game_state.is_terminal:
        board_state = game_state.board_state
        current_player = game_state.current_player
        
        for cube_source in find_cube_sources(board_state, current_player):

            if find_one and found_one:
                break
            
            for cube_direction in Direction:
                action1 = try_cube_path1_action(board_state, cube_source, cube_direction)
                if action1 is not None:
                    actions.append(action1) 
                    
                    if find_one:
                        found_one = True
                        break
                    
                    board_state1 = action1.next_board_state    
                    for stack_source in find_stack_sources(board_state1, current_player):
                        for stack_direction in Direction:
                            action21 = try_stack_path1_action(board_state1, stack_source, stack_direction)
                            if action21 is not None:
                                action21.path_vertices = action1.path_vertices + [action21.path_vertices[-1]]
                                action21.has_capture = action1.has_capture or action21.has_capture                      
                                actions.append(action21)  

                                action22 = try_stack_path2_action(board_state1, stack_source, stack_direction)
                                if action22 is not None:
                                    action22.path_vertices = action1.path_vertices + [action22.path_vertices[-1]]
                                    action22.has_capture = action1.has_capture or action22.has_capture                      
                                    actions.append(action22)  
                        
    return actions


def find_stack_first_actions(game_state: GameState) -> Actions:
    actions = list()
    if not game_state.is_terminal:
        board_state = game_state.board_state
        current_player = game_state.current_player
        
        for stack_source in find_stack_sources(board_state, current_player):
            for stack_direction in Direction:
                
                action11 = try_stack_path1_action(board_state, stack_source, stack_direction)
                if action11 is not None:
                    actions.append(action11)   
                    
                    board_state11 = action11.next_board_state    
                    for cube_source in find_cube_sources(board_state11, current_player):
                        for cube_direction in Direction:
                            action12 = try_cube_path1_action(board_state11, cube_source, cube_direction)
                            if action12 is not None:
                               action12.path_vertices = action11.path_vertices + [action12.path_vertices[-1]]
                               action12.has_capture = action11.has_capture or action12.has_capture                      
                               actions.append(action12)  
                
                    action21 = try_stack_path2_action(board_state, stack_source, stack_direction)
                    if action21 is not None:
                        actions.append(action21)   
                        
                        board_state21 = action21.next_board_state    
                        for cube_source in find_cube_sources(board_state21, current_player):
                            for cube_direction in Direction:
                                action22 = try_cube_path1_action(board_state21, cube_source, cube_direction)
                                if action22 is not None:
                                   action22.path_vertices = action21.path_vertices + [action22.path_vertices[-1]]
                                   action22.has_capture = action21.has_capture or action22.has_capture                      
                                   actions.append(action22)  

    return actions
       

def main():
    print()
    print("Hello")
    print(f"sys.version = {sys.version}")
    
    test_encode_and_decode_hex_state()
    test_encode_and_decode_path_state()
    test_iterate_hex_states()
    
    print_table_cube_count()
    print_table_fighter_count()
    
    print_tables_try_cube_path1()
    print_tables_try_stack_path1()
    print_tables_try_stack_path2()
    
    print()
    print("Bye")
    
    if True:
        print()
        _ = input("main: done ; press enter to terminate")
   

if __name__ == "__main__":
    main()