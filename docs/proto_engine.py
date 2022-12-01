# -*- coding: utf-8 -*-
"""
Prototyping a new design for the rules and AI engine
"""
import copy
import enum
from dataclasses import dataclass


@enum.unique
class Cube(enum.Enum):
    PAPER = enum.auto()
    ROCK = enum.auto()
    SCISSORS = enum.auto()
    WISE = enum.auto()


class Player(enum.Enum):
    WHITE = enum.Enum
    BLACK = enum.auto()


@enum.unique
class Translation1(enum.Enum):
    PHI_090_RHO_1 = enum.Enum
    PHI_150_RHO_1 = enum.Enum
    PHI_210_RHO_1 = enum.Enum
    PHI_270_RHO_1 = enum.Enum
    PHI_330_RHO_1 = enum.Enum
    PHI_030_RHO_1 = enum.Enum


@enum.unique
class Translation2(enum.Enum):
    PHI_090_RHO_2 = enum.Enum
    PHI_150_RHO_2 = enum.Enum
    PHI_210_RHO_2 = enum.Enum
    PHI_270_RHO_2 = enum.Enum
    PHI_330_RHO_2 = enum.Enum
    PHI_030_RHO_2 = enum.Enum


@dataclass
class HexState:
    is_empty: bool
    player: Player
    is_stack: bool
    bottom: Cube
    top: Cube
 

HexIndex = int
Path = list[HexIndex]
PathState = list[HexState]
BoardState = list[HexState]
  
    
@dataclass
class GameState:
    board_state: BoardState
    terminal: bool
    credit: int
    turn: int
    current_player: Player
    
    
@dataclass
class Action:
    path_summary: Path
    new_board_state: BoardState
    has_capture: bool
     
    
def find_cube_sources(board_state: BoardState, current_player: Player) -> list[HexIndex]:
    sources = list()
    for (hex_index, hex_state) in enumerate(board_state):
         if not hex_state.empty and hex_state.player == current_player:
             sources.append(hex_index)
    return sources


def make_path1(source: HexIndex, translation: Translation1) -> Path:
    path = list()
    path.append(source)
    return path


def make_path2(source: HexIndex, translation: Translation2) -> Path:
    path = list()
    path.append(source)
    return path


def make_path_state(board_state: BoardState, path: Path) -> PathState:
    path_state = [board_state[hex_index] for hex_index in path]
    return path_state


def try_cube_path(path_state: PathState) -> (PathState, bool):
    new_path_state = None
    has_capture = False
    return (new_path_state, has_capture)


def apply_path_state(board_state: BoardState, path: Path, path_state: PathState) -> BoardState:
    new_board_state = copy.deepcopy(board_state)
    for (hex_index, hex_state) in zip(path, path_state):
        new_board_state[hex_index] = hex_state
    return new_board_state

    
def find_actions(game_state: GameState) -> list[Action]:
    actions = list()
    if not game_state.terminal:
        board_state = game_state.board_state
        current_player = game_state.current_player
        
        for source in find_cube_sources(board_state, current_player):
            for translation in Translation1:
                path = make_path1(source, translation)
                if len(path) != 0:
                    path_state = make_path_state(board_state, path)
                    (new_path_state, has_capture) = try_cube_path(path_state)
                    if len(new_path_state) != 0:
                        action = Action()
                        action.path_summary = [source, path[-1]]
                        action.new_board_state = apply_path_state(board_state, path, new_path_state)
                        action.has_capture = has_capture                       
                        actions.append(action)        
    return actions
    
        
