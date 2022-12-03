# -*- coding: utf-8 -*-
"""
Prototyping a new design for the rules and AI engine intented to be fast
"""

import copy
import enum
from dataclasses import dataclass
import random
import sys
from typing import List
from typing import Optional


@enum.unique
class Cube(enum.IntEnum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2
    WISE = 3
    assert ROCK < PAPER < SCISSORS < WISE


class Player(enum.IntEnum):
    WHITE = 0
    BLACK = 1
    assert WHITE < BLACK


@enum.unique
class Translation1(enum.IntEnum):
    PHI_090 = 0
    PHI_150 = 1
    PHI_210 = 2
    PHI_270 = 3
    PHI_330 = 4
    PHI_030 = 5
    assert PHI_090 < PHI_150 < PHI_210 < PHI_270 < PHI_330 < PHI_030


@enum.unique
class Translation2(enum.Enum):
    PHI_090 = 0
    PHI_150 = 1
    PHI_210 = 2
    PHI_270 = 3
    PHI_330 = 4
    PHI_030 = 5
    assert PHI_090 < PHI_150 < PHI_210 < PHI_270 < PHI_330 < PHI_030


HexIndex = int
Sources = List[HexIndex]
Path = List[HexIndex]

HexCode = int
HEX_CODE_BASE = (2*2*2)*(2*2*2)*2


class HexState:
    
    __slots__ = ('is_empty', 'has_stack', 'player', 'bottom', 'top')
    
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

    
PathState = List[HexState]
BoardState = List[HexState]


def encode_hex_state(hex_state: HexState) -> HexCode:
    code = 0
    code +=   (0 if hex_state.is_empty else 1)
    code += 2*(1 if hex_state.has_stack else 0)
    code += 4*(hex_state.player.value if hex_state.player is not None else 0)
    code += 8*(hex_state.bottom.value if hex_state.bottom is not None else 0)
    code += 32*(hex_state.top.value if hex_state.top is not None else 0)
    
    assert 0 <= code < HEX_CODE_BASE

    return code


def decode_hex_state(code: HexCode) -> HexState:

    assert 0 <= code < (2*2*2)*(2*2*2)*2

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
        code += shift*encode_hex_state(hex_state)
        shift *= HEX_CODE_BASE
    return code
 

def decode_path_state(code: int, path_length: int) -> PathState:
    path_state = list()
    
    assert code >= 0
    
    rest = code
    for hex_index in range(path_length):
        hex_code = rest % HEX_CODE_BASE
        rest = rest // HEX_CODE_BASE
        path_state.append(decode_hex_state(hex_code))
        
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
    
        hex_state_code = encode_hex_state(hex_state)
        print(f"hex_state_code = {hex_state_code}")
        
        hex_decoded_state = decode_hex_state(hex_state_code)
        print(f"hex_decoded_state = {hex_decoded_state}")
        assert hex_decoded_state == hex_state
    
    hex_state_count = 100
    
    for _ in range(hex_state_count):
       
        hex_state = generate_random_hex_state(is_empty=False, has_stack=True, bottom=Cube.WISE)
        print()
        print(f"hex_state = {hex_state}")
    
        hex_state_code = encode_hex_state(hex_state)
        print(f"hex_state_code = {hex_state_code}")
        
        hex_decoded_state = decode_hex_state(hex_state_code)
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
    path_summary: Path
    has_capture: bool

Actions = List[Action]
   
    
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


def make_path1(source: HexIndex, translation1: Translation1) -> Path:
    path = list()
    path.append(source)
    return path


def make_path2(source: HexIndex, translation2: Translation2) -> Path:
    path = list()
    path.append(source)
    return path


def make_path_state(board_state: BoardState, path: Path) -> PathState:
    path_state = [board_state[hex_index] for hex_index in path]
    return path_state
       

def try_cube_path1(path_state: PathState) -> (PathState, bool):
    next_path_state = None
    has_capture = False
    return (next_path_state, has_capture)


def try_stack_path1(path_state: PathState) -> (PathState, bool):
    next_path_state = None
    has_capture = False
    return (next_path_state, has_capture)


def try_stack_path2(path_state: PathState) -> (PathState, bool):
    next_path_state = None
    has_capture = False
    return (next_path_state, has_capture)


def apply_path_state(board_state: BoardState, path: Path, path_state: PathState) -> BoardState:
    next_board_state = copy.deepcopy(board_state)
    for (hex_index, hex_state) in zip(path, path_state):
        next_board_state[hex_index] = hex_state
    return next_board_state

   
def find_actions(game_state: GameState) -> Actions:
    actions = list()
    actions += find_cube_first_actions(game_state)
    actions += find_stack_first_actions(game_state)
    return actions


def find_cube_first_actions(game_state: GameState) -> Actions:
    actions = list()
    if not game_state.is_terminal:
        board_state = game_state.board_state
        current_player = game_state.current_player
        
        for cube_source in find_cube_sources(board_state, current_player):
            for cube_translation1 in Translation1:
                cube_path = make_path1(cube_source, cube_translation1)
                if len(cube_path) != 0:
                    path_state = make_path_state(board_state, cube_path)
                    (next_path_state, has_capture) = try_cube_path1(path_state)
                    if len(next_path_state) != 0:
                        board_state1 = apply_path_state(board_state, cube_path, next_path_state)
                        cube_destination = cube_path[-1]
                        action1 = Action()
                        action1.next_board_state = board_state1
                        action1.path_summary = [cube_source, cube_destination]
                        action1.has_capture = has_capture                       
                        actions.append(action1)   
                        
                        for stack_source in find_stack_sources(board_state1, current_player):
                            for (stack_translation1, stack_translation2) in zip(Translation1, Translation2):
                                stack_path = make_path1(stack_source, stack_translation1)
                                if len(stack_path) != 0:
                                    path_state = make_path_state(board_state1, stack_path)
                                    (next_path_state, has_capture) = try_stack_path1(path_state)
                                    if len(next_path_state) != 0:
                                        board_state21 = apply_path_state(board_state1, stack_path, next_path_state)
                                        stack_destination = stack_path[-1]
                                        action21 = Action()
                                        action21.next_board_state = board_state21
                                        action21.path_summary = action1.path_summary + [stack_destination]
                                        action21.has_capture = action1.has_capture or has_capture                      
                                        actions.append(action21)  
                                        
                                        stack_path = make_path2(stack_source, stack_translation1)
                                        if len(stack_path) != 0:
                                            path_state = make_path_state(board_state1, stack_path)
                                            (next_path_state, has_capture) = try_stack_path2(path_state)
                                            if len(next_path_state) != 0:
                                                board_state22 = apply_path_state(board_state1, stack_path, next_path_state)
                                                stack_destination = stack_path[-1]
                                                action22 = Action()
                                                action22.next_board_state = board_state22
                                                action22.path_summary = action1.path_summary + [stack_destination]
                                                action22.has_capture = action1.has_capture or has_capture                      
                                                actions.append(action22)   
                        
    return actions
    

def find_stack_first_actions(game_state: GameState) -> Actions:
    actions = list()
    if not game_state.is_terminal:
        board_state = game_state.board_state
        current_player = game_state.current_player
        
        for stack_source in find_stack_sources(board_state, current_player):
            for (stack_translation1, stack_translation2) in zip(Translation1, Translation2):
                stack_path = make_path1(stack_source, stack_translation1)
                if len(stack_path) != 0:
                    path_state = make_path_state(board_state, stack_path)
                    (next_path_state, has_capture) = try_stack_path1(path_state)
                    if len(next_path_state) != 0:
                        board_state11 = apply_path_state(board_state, stack_path, next_path_state)
                        stack_destination = stack_path[-1]
                        action11 = Action()
                        action11.next_board_state = board_state11
                        action11.path_summary = [stack_source, stack_destination]
                        action11.has_capture = has_capture                      
                        actions.append(action11)  

                        for cube_source in find_cube_sources(board_state11, current_player):
                            for cube_translation1 in Translation1:
                                cube_path = make_path1(cube_source, cube_translation1)
                                if len(cube_path) != 0:
                                    path_state = make_path_state(board_state11, cube_path)
                                    (next_path_state, has_capture) = try_cube_path1(path_state)
                                    if len(next_path_state) != 0:
                                        board_state12 = apply_path_state(board_state11, cube_path, next_path_state)
                                        cube_destination = cube_path[-1]
                                        action12 = Action()
                                        action12.next_board_state = board_state12
                                        action12.path_summary = action11.path_summary + [cube_destination]
                                        action12.has_capture = action11.has_capture or has_capture                      
                                        actions.append(action12)   

                        stack_path = make_path1(stack_source, stack_translation2)
                        if len(stack_path) != 0:
                            path_state = make_path_state(board_state, stack_path)
                            (next_path_state, has_capture) = try_stack_path2(path_state)
                            if len(next_path_state) != 0:
                                board_state21 = apply_path_state(board_state, stack_path, next_path_state)
                                stack_destination = stack_path[-1]
                                action21 = Action()
                                action21.next_board_state = board_state21
                                action21.path_summary = [stack_source, stack_destination]
                                action21.has_capture = has_capture                      
                                actions.append(action21)  
        
                                for cube_source in find_cube_sources(board_state21, current_player):
                                    for cube_translation1 in Translation1:
                                        cube_path = make_path1(cube_source, cube_translation1)
                                        if len(cube_path) != 0:
                                            path_state = make_path_state(board_state21, cube_path)
                                            (next_path_state, has_capture) = try_cube_path1(path_state)
                                            if len(next_path_state) != 0:
                                                board_state22 = apply_path_state(board_state21, cube_path, next_path_state)
                                                cube_destination = cube_path[-1]
                                                action22 = Action()
                                                action22.next_board_state = board_state22
                                                action22.path_summary = action21.path_summary + [cube_destination]
                                                action22.has_capture = action21.has_capture or has_capture                      
                                                actions.append(action22)   

    return actions
       

def main():
    print()
    print("Hello")
    print(f"sys.version = {sys.version}")
    
    test_encode_and_decode_hex_state()
    test_encode_and_decode_path_state()
    
    print()
    print("Bye")
    
    if True:
        print()
        _ = input("main: done ; press enter to terminate")
   

if __name__ == "__main__":
    main()