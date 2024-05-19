#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_gui.py implements a GUI for the PIJERSI boardgame."""

_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.
CMALO is the name of the native internal Python AI-engine of PIJERSI-CERTU.

Copyright (C) 2022 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

_COPYRIGHT_AND_LICENSE_NATSEL = """
NATURAL-SELECTION (alias "natsel") implements an AI UGI-server for the PIJERSI boardgame (see also https://github.com/eclypse-prime/pijersi-rs).

Copyright (C) 2024 eclypse-prime (https://github.com/eclypse-prime).
"""


import copy
import enum
import sys
import glob
import math
import os
import re
import shutil
import time
from tkinter import font
from tkinter import ttk
import tkinter as tk

from concurrent.futures import ProcessPoolExecutor as PoolExecutor
from multiprocessing import freeze_support
import multiprocessing

from PIL import Image
from PIL import ImageGrab
from PIL import ImageTk

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules

from pijersi_ugi import UgiClient
from pijersi_ugi import UgiSearcher


def rgb_color_as_hexadecimal(rgb_triplet):
    (red, green, blue) = rgb_triplet
    assert 0 <= red <= 255
    assert 0 <= green <= 255
    assert 0 <= red <= 255
    return '#%02x%02x%02x' % (red, green, blue)


class AppConfig:
    # File path containing the icon to be displayed in the title bar of Pijersi GUI
    ICON_FILE = os.path.join(_package_home, 'pictures', 'pijersi.ico')

    # Directory path of a working directory for pictures
    TMP_PICTURE_DIR = os.path.join(_package_home, 'tmp-pictures')

    # Directory path of a working directory for animated pictures
    TMP_ANIMATION_DIR = os.path.join(TMP_PICTURE_DIR, 'animation')


class TinyVector:
    """Lightweight algebra on 2D vectors, inspired by numpy ndarray."""

    __slots__ = ("__x", "__y")

    def __init__(self, xy_pair=None):
        if xy_pair is None:
            self.__x = 0.
            self.__y = 0.

        else:
            self.__x = float(xy_pair[0])
            self.__y = float(xy_pair[1])

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str((self.__x, self.__y))

    def __getitem__(self, key):
        if key == 0:
            return self.__x

        elif key == 1:
            return self.__y

        else:
            raise IndexError()

    def __neg__(self):
        return TinyVector((-self.__x, -self.__y))

    def __pos__(self):
        return TinyVector((self.__x, self.__y))

    def __add__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x + other.__x, self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x + other, self.__y + other))

        else:
            raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((self.__x - other.__x, self.__y - other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((self.__x - other, self.__y - other))

        else:
            raise NotImplementedError()

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x*other, self.__y*other))

        else:
            raise NotImplementedError()

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return TinyVector((self.__x/other, self.__y/other))

        else:
            raise NotImplementedError()

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return self.__div__(other)

    def __rsub__(self, other):
        if isinstance(other, TinyVector):
            return TinyVector((-self.__x + other.__x, -self.__y + other.__y))

        elif isinstance(other, (int, float)):
            return TinyVector((-self.__x + other, -self.__y + other))

        else:
            raise NotImplementedError()

    @staticmethod
    def inner(that, other):
        if isinstance(that, TinyVector) and isinstance(other, TinyVector):
            return (that.__x*other.__x + that.__y*other.__y)

        else:
            raise NotImplementedError()

    @staticmethod
    def norm(that):
        if isinstance(that, TinyVector):
            return math.sqrt(that.__x*that.__x + that.__y*that.__y)

        else:
            raise NotImplementedError()


class CanvasConfig:

    def __init__(self):
        # Canvas x-y dimensions in hexagon width units
        # >> This complex formula is related to the construction of the background picture for the board
        self.NX = 8
        self.NY = (4 + 5/2)*2/math.sqrt(3)

        # Canvas x-y dimensions in pixels
        self.RATIO = self.NX/self.NY
        self.HEIGHT = 640
        self.WIDTH = self.HEIGHT*self.RATIO

        # Canvas background
        self.USE_BACKGROUND_PHOTO = True
        self.BACKGROUND_PHOTO_PATH = os.path.join(_package_home, 'pictures', 'pijersi-board.png')

        # Hexagon geometrical data
        self.HEXA_VERTEX_COUNT = 6
        self.HEXA_SIDE_ANGLE = 2*math.pi/self.HEXA_VERTEX_COUNT
        self.HEXA_WIDTH = self.WIDTH/self.NX
        self.HEXA_SIDE = self.HEXA_WIDTH*math.tan(self.HEXA_SIDE_ANGLE/2)
        self.HEXA_DELTA_Y = math.sqrt(self.HEXA_SIDE**2 - (self.HEXA_WIDTH/2)**2)
        self.HEXA_COS_SIDE_ANGLE = math.cos(self.HEXA_SIDE_ANGLE)
        self.HEXA_SIN_SIDE_ANGLE = math.sin(self.HEXA_SIDE_ANGLE)

        # Cube (square) geometrical data
        self.CUBE_VERTEX_COUNT = 4
        self.CUBE_SIDE_ANGLE = math.pi/2

        # Font used for text in the canvas
        self.FONT_FAMILY = 'Calibri'
        self.FONT_LABEL_SIZE = int(0.30*self.HEXA_SIDE)  # size for 'e5', 'f5' ...
        self.FONT_FACE_SIZE = int(0.50*self.HEXA_SIDE)  # size for 'K', 'F' ...
        self.FONT_LEGEND_SIZE = int(0.60*self.HEXA_SIDE)  # size for 'a1-a2!=a3!' ...
        self.FONT_LEGEND_COLOR = rgb_color_as_hexadecimal((166, 109, 60))

        # Geometrical line widths
        self.CUBE_LINE_WIDTH = 2
        self.HEXA_LINE_WIDTH = 1

        # Origin of the orthonormal x-y frame and the oblic u-v frame
        self.ORIGIN = TinyVector((self.WIDTH/2, self.HEIGHT/2))

        # Unit vectors of the orthonormal x-y frame
        self.UNIT_X = TinyVector((1, 0))
        self.UNIT_Y = TinyVector((0, -1))

        # Unit vectors of the oblic u-v frame
        self.UNIT_U = self.UNIT_X
        self.UNIT_V = self.HEXA_COS_SIDE_ANGLE*self.UNIT_X + self.HEXA_SIN_SIDE_ANGLE*self.UNIT_Y

    def update(self, height):
        self.HEIGHT = height
        self.WIDTH = self.HEIGHT*self.RATIO

        # Hexagon geometrical data
        self.HEXA_WIDTH = self.WIDTH/self.NX
        self.HEXA_SIDE = self.HEXA_WIDTH*math.tan(self.HEXA_SIDE_ANGLE/2)
        self.HEXA_DELTA_Y = math.sqrt(self.HEXA_SIDE**2 - (self.HEXA_WIDTH/2)**2)

        # Font used for text in the canvas
        self.FONT_LABEL_SIZE = int(0.30*self.HEXA_SIDE)  # size for 'e5', 'f5' ...
        self.FONT_FACE_SIZE = int(0.50*self.HEXA_SIDE)  # size for 'K', 'F' ...
        self.FONT_LEGEND_SIZE = int(0.60*self.HEXA_SIDE)  # size for 'a1-a2!=a3!' ...

        # Origin of the orthonormal x-y frame and the oblic u-v frame
        self.ORIGIN = TinyVector((self.WIDTH/2, self.HEIGHT/2))


class CubeConfig:
    # File path containing the icon to be displayed in the title bar of Pijersi GUI

    __cube_file_name = {}

    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.WISE) ] = 'wise-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.ROCK) ] = 'rock-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.PAPER)] = 'paper-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.SCISSORS)] = 'scissors-black.png'

    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.WISE)] = 'wise-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.ROCK)] = 'rock-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.PAPER)] = 'paper-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.SCISSORS)] = 'scissors-white.png'

    CUBE_FILE_PATH = {}

    for (file_key, file_name) in __cube_file_name.items():
        CUBE_FILE_PATH[file_key] = os.path.join(_package_home, 'pictures', file_name)


class CubeLocation(enum.Enum):
    BOTTOM = enum.auto()
    MIDDLE = enum.auto()
    TOP = enum.auto()


@enum.unique
class CubeColor(enum.Enum):
    BLACK = 'black'
    WHITE = 'white'


@enum.unique
class HexagonColor(enum.Enum):
    BORDER = rgb_color_as_hexadecimal((191, 89, 52))
    DARK = rgb_color_as_hexadecimal((166, 109, 60))
    LIGHT = rgb_color_as_hexadecimal((242, 202, 128))

    # Lucas-theme-2
    HIGHLIGHT_SOURCE_SELECTION = rgb_color_as_hexadecimal((217, 199, 193))
    HIGHLIGHT_DESTINATION_SELECTION = rgb_color_as_hexadecimal((140, 102, 94))
    HIGHLIGHT_CUBE_SELECTION = rgb_color_as_hexadecimal((6, 159, 191))
    HIGHLIGHT_STACK_SELECTION = rgb_color_as_hexadecimal((0, 95, 115))


class HexagonLineColor(enum.Enum):
    NORMAL = 'black'
    HIGHLIGHT = 'white'
    HIGHLIGHT_PLAYED_BY_WHITE = 'white'
    HIGHLIGHT_PLAYED_BY_BLACK = 'black'


class GraphicalHexagon:

    __all_sorted_hexagons = []
    __init_done = False
    __name_to_hexagon = {}

    all = None

    def __init__(self, hexagon, color):

        assert hexagon.name not in GraphicalHexagon.__name_to_hexagon
        assert color in HexagonColor

        self.name = hexagon.name
        self.position_uv = hexagon.position_uv
        self.index = hexagon.index
        self.color = color

        self.highlighted_as_played_by_white = False
        self.highlighted_as_played_by_black = False
        self.highlighted_as_selectable = False
        self.highlighted_as_cube = False
        self.highlighted_as_stack = False
        self.highlighted_as_destination = False

        GraphicalHexagon.__name_to_hexagon[self.name] = self

        (u, v) = self.position_uv

        self.center = CANVAS_CONFIG.ORIGIN + CANVAS_CONFIG.HEXA_WIDTH * (u*CANVAS_CONFIG.UNIT_U + v*CANVAS_CONFIG.UNIT_V)

        self.vertex_data = list()

        for vertex_index in range(CANVAS_CONFIG.HEXA_VERTEX_COUNT):
            vertex_angle = (1/2 + vertex_index)*CANVAS_CONFIG.HEXA_SIDE_ANGLE

            hexagon_vertex = self.center
            hexagon_vertex = hexagon_vertex + CANVAS_CONFIG.HEXA_SIDE * math.cos(vertex_angle)*CANVAS_CONFIG.UNIT_X
            hexagon_vertex = hexagon_vertex + CANVAS_CONFIG.HEXA_SIDE * math.sin(vertex_angle)*CANVAS_CONFIG.UNIT_Y

            self.vertex_data.append(hexagon_vertex[0])
            self.vertex_data.append(hexagon_vertex[1])

    def contains_point(self, point):
        """ Is the point inside the current hexagon ?"""

        # >> This implementation relies of the following properties:
        # >> - All hexagons of the Pijersi board are regular hexagons: all the 6 sides are of equal lengths.
        # >> - All hexagons have the same sizes.
        # >> - All hexagons can be translated to the central hexagon and does match it.
        # >> - The x-axis is orthogonal to an hexagon side.

        SAFE_RELATIVE_INSIDE_WIDTH = 0.99

        is_inside = True

        (hexagon_x, hexagon_y) = (self.center[0], self.center[1])
        (point_x, point_y) = point

        # Compute the standardized point : translated and scaled regarding the actual hexagon
        x = (point_x - hexagon_x)/(CANVAS_CONFIG.HEXA_WIDTH/2)
        y = (point_y - hexagon_y)/(CANVAS_CONFIG.HEXA_WIDTH/2)

        if is_inside:
            is_inside = math.fabs(x) < SAFE_RELATIVE_INSIDE_WIDTH

        if is_inside:
            # first rotation by CANVAS_CONFIG.HEXA_SIDE_ANGLE
            (x, y) = (CANVAS_CONFIG.HEXA_COS_SIDE_ANGLE*x - CANVAS_CONFIG.HEXA_SIN_SIDE_ANGLE*y,
                      CANVAS_CONFIG.HEXA_SIN_SIDE_ANGLE*x + CANVAS_CONFIG.HEXA_COS_SIDE_ANGLE*y)

            is_inside = math.fabs(x) < SAFE_RELATIVE_INSIDE_WIDTH

        if is_inside:
            # second rotation by CANVAS_CONFIG.HEXA_SIDE_ANGLE
            (x, y) = (CANVAS_CONFIG.HEXA_COS_SIDE_ANGLE*x - CANVAS_CONFIG.HEXA_SIN_SIDE_ANGLE*y,
                      CANVAS_CONFIG.HEXA_SIN_SIDE_ANGLE*x + CANVAS_CONFIG.HEXA_COS_SIDE_ANGLE*y)

            is_inside = math.fabs(x) < SAFE_RELATIVE_INSIDE_WIDTH

        return is_inside

    def __str__(self):
        return f"GraphicalHexagon({self.name}, {self.position_uv}, {self.index}, {self.color})"

    @staticmethod
    def get(name):
        return GraphicalHexagon.__name_to_hexagon[name]

    @staticmethod
    def init():
        if not GraphicalHexagon.__init_done:
            GraphicalHexagon.__create_hexagons()
            GraphicalHexagon.__create_all_sorted_hexagons()
            GraphicalHexagon.__init_done = True

    @staticmethod
    def reset():
        GraphicalHexagon.__all_sorted_hexagons = []
        GraphicalHexagon.__init_done = False
        GraphicalHexagon.__name_to_hexagon = {}

    @staticmethod
    def reset_highlights():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_selectable = False
            hexagon.highlighted_as_cube = False
            hexagon.highlighted_as_stack = False
            hexagon.highlighted_as_destination = False
            hexagon.highlighted_as_played_by_white = False
            hexagon.highlighted_as_played_by_black = False

    @staticmethod
    def reset_highlights_as_selectable():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_selectable = False

    @staticmethod
    def reset_highlights_as_cube_or_stack():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_cube = False
            hexagon.highlighted_as_stack = False

    @staticmethod
    def reset_highlights_as_destination():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_destination = False

    @staticmethod
    def reset_highlights_as_played():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_played_by_white = False
            hexagon.highlighted_as_played_by_black = False

    @staticmethod
    def show_all():
        for hexagon in GraphicalHexagon.__all_sorted_hexagons:
            print(hexagon)

    @staticmethod
    def __create_all_sorted_hexagons():
        for name in sorted(GraphicalHexagon.__name_to_hexagon.keys()):
            GraphicalHexagon.__all_sorted_hexagons.append(GraphicalHexagon.__name_to_hexagon[name])

        GraphicalHexagon.all = GraphicalHexagon.__all_sorted_hexagons

    @staticmethod
    def __create_hexagons():

        outer_ring = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6']
        outer_ring += ['g1', 'g2', 'g3', 'g4', 'g5', 'g6']
        outer_ring += ['b1', 'c1', 'd1', 'e1', 'f1']
        outer_ring += ['b7', 'c6', 'd7', 'e6', 'f7']

        inner_ring = ['e3', 'e4']
        inner_ring += ['d3', 'd5']
        inner_ring += ['c3', 'c4']

        for hexagon in rules.Hexagon.all:

            if hexagon.name in outer_ring:
                color = HexagonColor.DARK

            elif hexagon.name in inner_ring:
                color = HexagonColor.DARK
            else:
                color = HexagonColor.LIGHT

            GraphicalHexagon(hexagon, color)


@enum.unique
class CMCState(enum.Enum):
    """States of the CMC process (Canevas Mouse Control)"""

    SELECTING_1 = enum.auto()

    SELECTING_2 = enum.auto()

    SELECTING_3 = enum.auto()


def search_task(searcher, pijersi_state):
    action = searcher.search(pijersi_state)
    action_simple_name = str(action).replace("!", "")
    return action_simple_name


class GameGui(ttk.Frame):

    def __init__(self):

        self.__face_drawers = dict()
        self.__face_drawers[rules.Cube.T.PAPER] = self.__draw_paper_face
        self.__face_drawers[rules.Cube.T.ROCK] = self.__draw_rock_face
        self.__face_drawers[rules.Cube.T.SCISSORS] = self.__draw_scissors_face
        self.__face_drawers[rules.Cube.T.WISE] = self.__draw_wise_face

        self.__cube_photos = None

        self.__cube_faces_options = ("faces=letters", "faces=drawings", "faces=pictures")
        self.__cube_faces = self.__cube_faces_options[2]

        self.__background_tk_photo = None
        self.__use_background_photo = CANVAS_CONFIG.USE_BACKGROUND_PHOTO

        self.__legend = ""

        self.__game_timer_delay = 500
        self.__game_timer_id = None

        self.__action_animation_duration = 500

        self.__picture_gif_duration = 750

        self.__edit_actions = False
        self.__saved_actions_text = ""

        self.__turn_states = list()
        self.__turn_actions = list()

        self.__game = None

        self.__game_setup_board_codes_classic = rules.PijersiState.setup_board_codes(rules.Setup.T.CLASSIC)
        self.__game_setup = rules.Setup.T.CLASSIC
        self.__game_setup_board_codes = self.__game_setup_board_codes_classic

        self.__game_played = False
        self.__game_terminated = False
        self.__pijersi_state = rules.PijersiState()
        self.__searcher = [None, None]
        self.__searcher_max_time = None
        self.__searcher_start_time = None

        self.__action_input = None
        self.__action_validated = False

        self.__turn_states.append(self.__pijersi_state)
        self.__turn_actions.append("")

        # For concurrent execution
        self.__concurrent_executor = None
        self.__frontend_searchers = [None for player in rules.Player.T]
        self.__backend_searchers = [None for player in rules.Player.T]
        self.__backend_futures = [None for player in rules.Player.T]

        # Reset the Canevas Mouse Control (CMC) variables and the graphical hexagon highlights
        self.__cmc_reset()

        # Create GUI clients and the searher catalog
        self.__ugi_clients = make_ugi_clients()
        self.__searcher_catalog = make_searcher_catalog(self.__ugi_clients)

        # Create widgets

        self.__root = tk.Tk()

        try:
            self.__root.title(f"pijersi-certu-v{rules.__version__} for playing the pijersi boardgame and testing AI agents" +
                              " ; the rules of the game can be found at https://github.com/LucasBorboleta/pijersi")
            self.__root.iconbitmap(AppConfig.ICON_FILE)
        except:
            pass

        self.__create_widgets()

        # Update widgets

        self.__draw_state()
        self.__write_setup()

        self.__command_update_players()

        self.__variable_log.set(f"pijersi-certu version {rules.__version__} is ready !")
        self.__variable_summary.set("(c) 2022 Lucas Borboleta ; pijersi software license : GNU GPL ; pijersi rules license : CC-BY-NC-SA")

        if False:
            # Prepare the resizable feature
            self.__root.resizable(width=True, height=True)
            self.__finalize_timer_delay = 1
            self.__root.after(self.__finalize_timer_delay, self.__finalize_widgets)

        else:
            # Disable the resizable feature
            self.__root.resizable(width=False, height=False)

        # Wait events
        self.__root.mainloop()

    def __create_widgets(self):

        searcher_catalog_names = self.__searcher_catalog.get_names()
        searcher_catalog_names_width = max(map(len, searcher_catalog_names)) + 2

        setup_names = rules.Setup.get_names()
        setup_names_width = max(map(len, setup_names))

        self.__style = ttk.Style()
        # >> builtin theme_names()  are ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        # >> default and nice theme is 'vista'
        # >> but 'vista' does not support to change style for TProgressbar
        # >> so 'clam' is used instead, as a second nice choice
        self.__style.theme_use('clam')

        self.__style.configure("White.Horizontal.TProgressbar", background='white')
        self.__style.configure("Black.Horizontal.TProgressbar", background='black')

        self.__style.map("TCombobox", fieldbackground=[('disabled', 'lightgrey'), ('active', 'white')])
        self.__style.map("TSpinbox", fieldbackground=[('disabled', 'lightgrey'), ('active', 'white')])

        # Frames

        self.__frame_left = ttk.Frame(self.__root)
        self.__frame_left.grid(row=0, column=0, sticky='nw')

        self.__frame_right = ttk.Frame(self.__root, padding=15)
        self.__frame_right.grid(row=0, column=1, sticky='nw')

        self.__frame_commands_and_players = ttk.Frame(self.__frame_right)
        self.__frame_commands_and_players.grid(row=0, column=0, sticky='nw')

        self.__frame_actions = ttk.Frame(self.__frame_right)
        self.__frame_actions.grid(row=1, column=0, sticky='nw')

        self.__frame_board = ttk.Frame(self.__frame_left)
        self.__frame_board.pack(fill=tk.BOTH)

        self.__frame_commands = ttk.Frame(self.__frame_commands_and_players)
        self.__frame_commands.grid(row=0, column=0)

        self.__frame_players = ttk.Frame(self.__frame_commands_and_players)
        self.__frame_players.grid(row=0, column=1, sticky='e')

        self.__frame_commands_and_players.columnconfigure(1, pad=60)
        self.__frame_commands_and_players.columnconfigure(0, pad=20)

        self.__frame_human_actions = ttk.Frame(self.__frame_actions, padding=10)
        self.__frame_text_actions = ttk.Frame(self.__frame_actions, padding=10)

        # In __frame_commands

        self.__button_quit = ttk.Button(self.__frame_commands,
                                        text='Quit',
                                        command=self.__command_quit)

        self.__button_new_stop = ttk.Button(self.__frame_commands,
                                              text='New',
                                              command=self.__command_new_stop)

        self.__button_resume = ttk.Button(self.__frame_commands,
                                              text='Resume',
                                              command=self.__command_resume)

        self.__variable_easy_mode = tk.BooleanVar()
        self.__variable_easy_mode.set(True)
        self.__button_easy_mode = ttk.Checkbutton(self.__frame_commands,
                                                  text='Easy mode',
                                                  variable=self.__variable_easy_mode,
                                                  command=self.__command_update_easy_mode)

        self.__button_new_stop.grid(row=0, column=0)
        self.__button_quit.grid(row=0, column=1)

        #self.__button_easy_mode.grid(row=1, column=0)
        self.__button_easy_mode.pack_forget()
        self.__button_resume.grid(row=1, column=1)

        self.__frame_commands.rowconfigure(0, pad=5)
        self.__frame_commands.rowconfigure(1, pad=5)
        self.__frame_commands.columnconfigure(0, pad=5)
        self.__frame_commands.columnconfigure(1, pad=5)

        # In __frame_players

        self.__label_white_player = ttk.Label(self.__frame_players, text='White :')

        self.__variable_white_player = tk.StringVar()
        self.__combobox_white_player = ttk.Combobox(self.__frame_players,
                                                    width=searcher_catalog_names_width,
                                                    textvariable=self.__variable_white_player,
                                                    values=searcher_catalog_names)
        self.__combobox_white_player.config(state="readonly")
        self.__variable_white_player.set(searcher_catalog_names[0])

        self.__label_black_player = ttk.Label(self.__frame_players, text='Black :')

        self.__variable_black_player = tk.StringVar()
        self.__combobox_black_player = ttk.Combobox(self.__frame_players,
                                                    width=searcher_catalog_names_width,
                                                    textvariable=self.__variable_black_player,
                                                    values=searcher_catalog_names)
        self.__combobox_black_player.config(state="readonly")
        self.__variable_black_player.set(searcher_catalog_names[searcher_catalog_names.index("human")])

        self.__progressbar = ttk.Progressbar(self.__frame_players,
                                             orient=tk.HORIZONTAL,
                                             length=300,
                                             maximum=100,
                                             mode='determinate')
        self.__progressbar.configure(style="White.Horizontal.TProgressbar")

        self.__label_white_player.grid(row=0, column=0)
        self.__combobox_white_player.grid(row=0, column=1)

        self.__label_black_player.grid(row=0, column=2)
        self.__combobox_black_player.grid(row=0, column=3)

        self.__progressbar.grid(row=1, columnspan=4)

        self.__frame_players.rowconfigure(0, pad=5)
        self.__frame_players.rowconfigure(1, pad=5)
        self.__frame_players.columnconfigure(0, pad=5)
        self.__frame_players.columnconfigure(1, pad=5)
        self.__frame_players.columnconfigure(2, pad=5)
        self.__frame_players.columnconfigure(3, pad=5)

        self.__variable_white_player.trace_add('write', self.__command_update_players)
        self.__variable_black_player.trace_add('write', self.__command_update_players)

        # In __frame_board

        self.__canvas = tk.Canvas(self.__frame_board,
                                  height=CANVAS_CONFIG.HEIGHT,
                                  width=CANVAS_CONFIG.WIDTH)
        self.__canvas.pack(side=tk.TOP)

        self.__canvas.bind('<Motion>', self.__cmc_update_mouse_over)
        self.__canvas.bind('<Button-1>', self.__cmc_update_mouse_click)

       # In __frame_actions

        self.__variable_log = tk.StringVar()
        self.__label_log = ttk.Label(self.__frame_actions,
                                     textvariable=self.__variable_log,
                                     width=95,
                                     padding=5,
                                     foreground='brown',
                                     borderwidth=2, relief="groove")

        self.__variable_summary = tk.StringVar()
        self.__label_summary = ttk.Label(self.__frame_actions,
                                         textvariable=self.__variable_summary,
                                         width=95,
                                         padding=5,
                                         foreground='black',
                                         borderwidth=2, relief="groove")

       # In __frame_human_actions

        self.__label_setup = ttk.Label(self.__frame_human_actions, text='Setup :')

        self.__variable_setup = tk.StringVar()
        self.__combobox_setup = ttk.Combobox(self.__frame_human_actions,
                                                    width=setup_names_width,
                                                    textvariable=self.__variable_setup,
                                                    values=setup_names)
        self.__combobox_setup.bind('<<ComboboxSelected>>', self.__command_setup)
        self.__combobox_setup.config(state="readonly")
        self.__variable_setup.set(rules.Setup.to_name(self.__game_setup))

        self.__variable_action = tk.StringVar()

        self.__button_edit_actions = ttk.Button(self.__frame_human_actions,
                                                text='Edit',
                                                width=max(len('Edit'), len('Validate')),
                                                command=self.__command_edit_actions)
        self.__button_edit_actions.config(state="enabled")

        self.__button_reset_actions = ttk.Button(self.__frame_human_actions,
                                                text='Undo',
                                                command=self.__command_reset_actions)
        self.__button_reset_actions.config(state="enabled")

        self.__label_turn = ttk.Label(self.__frame_human_actions, text='Turn :')

        self.__variable_turn = tk.StringVar()
        self.__variable_turn.set(len(self.__turn_states) - 1)
        self.__spinbox_turn = ttk.Spinbox(self.__frame_human_actions,
                                          values=list(range(len(self.__turn_states))),
                                          wrap=True,
                                          command=self.__command_update_turn,
                                          textvariable=self.__variable_turn,
                                          width=5)
        self.__spinbox_turn.bind('<Return>', self.__command_update_turn)

        self.__button_make_pictures = ttk.Button(self.__frame_human_actions,
                                                 text='Make pictures',
                                                 command=self.__command_make_pictures)
        self.__button_make_pictures.config(state="enabled")

       # In __frame_text_actions

        self.__text_actions = tk.Text(self.__frame_text_actions,
                                      width=60,
                                      borderwidth=2, relief="groove",
                                      background='lightgrey')

        self.__scrollbar_actions = ttk.Scrollbar(self.__frame_text_actions, orient='vertical')

        self.__text_actions.config(yscrollcommand=self.__scrollbar_actions.set)
        self.__scrollbar_actions.config(command=self.__text_actions.yview)

        self.__label_log.grid(row=0, column=0)
        self.__label_summary.grid(row=1, column=0)
        self.__frame_human_actions.grid(row=2, column=0)
        self.__frame_text_actions.grid(row=3, column=0)

        self.__frame_actions.rowconfigure(0, pad=20)

        self.__label_setup.grid(row=0, column=0)
        self.__combobox_setup.grid(row=0, column=1)
        self.__button_edit_actions.grid(row=0, column=2)
        self.__button_reset_actions.grid(row=0, column=3)
        self.__label_turn.grid(row=0, column=4)
        self.__spinbox_turn.grid(row=0, column=5)
        self.__button_make_pictures.grid(row=0, column=6)

        self.__frame_human_actions.rowconfigure(0, pad=5)
        self.__frame_human_actions.columnconfigure(0, pad=5)
        self.__frame_human_actions.columnconfigure(1, pad=5)
        self.__frame_human_actions.columnconfigure(2, pad=5)
        self.__frame_human_actions.columnconfigure(3, pad=5)
        self.__frame_human_actions.columnconfigure(4, pad=5)
        self.__frame_human_actions.columnconfigure(5, pad=5)
        self.__frame_human_actions.columnconfigure(6, pad=10)

        self.__scrollbar_actions.pack(side=tk.LEFT, fill=tk.Y)
        self.__text_actions.pack(side=tk.LEFT)

        self.__text_actions.config(state="disabled")
        self.__button_resume.config(state="disabled")
        self.__button_reset_actions.config(state="disabled")

    def __create_cube_photos(self):
        if self.__cube_photos is None:

            cube_photo_width = int(CANVAS_CONFIG.HEXA_SIDE*math.cos(math.pi/4))

            self.__cube_photos = {}

            for (key, file) in CubeConfig.CUBE_FILE_PATH.items():
                cube_photo = Image.open(file)
                cube_photo = cube_photo.resize((cube_photo_width, cube_photo_width))
                cube_tk_photo = ImageTk.PhotoImage(cube_photo)
                self.__cube_photos[key] = cube_tk_photo

    def __command_quit(self, *_):

        if self.__concurrent_executor is not None:
            self.__backend_futures = [None for player in rules.Player.T]
            self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
            self.__concurrent_executor = None

        self.__root.destroy()

    def __finalize_widgets(self, *_):

        self.__initial_root_width = self.__root.winfo_width()
        self.__initial_root_height = self.__root.winfo_height()

        self.__initial_canvas_width = self.__canvas.winfo_width()
        self.__initial_canvas_height = self.__canvas.winfo_height()

        if ( math.fabs(self.__initial_canvas_width/CANVAS_CONFIG.WIDTH - 1) > 0.01  or
              math.fabs(self.__initial_canvas_height/CANVAS_CONFIG.HEIGHT - 1) > 0.01):

            self.__finalize_timer_delay = 100
            self.__root.after(self.__finalize_timer_delay, self.__finalize_widgets)

        print()
        print(f"DEBUG: __initial_root_width = {self.__initial_root_width}")
        print(f"DEBUG: __initial_root_height = {self.__initial_root_height}")

        print()
        print(f"DEBUG: __initial_canvas_width = {self.__initial_canvas_width}")
        print(f"DEBUG: __initial_canvas_height = {self.__initial_canvas_height}")

        self.__root.minsize(width=self.__initial_root_width, height=self.__initial_root_height)

        # react if widget has changed size or position
        self.__root.bind("<Configure>", self.__resize_widgets)


    def __resize_widgets(self, *_):

        current_root_width = self.__root.winfo_width()
        current_root_height = self.__root.winfo_height()

        if ( math.fabs(current_root_width/self.__initial_root_width - 1) > 0.01 or
             math.fabs(current_root_height/self.__initial_root_height - 1) > 0.01):

            scale_factor = min(current_root_width/self.__initial_root_width, current_root_height/self.__initial_root_height)

            if scale_factor > 1.01:

                print()
                print(f"DEBUG: current_root_width = {current_root_width}")
                print(f"DEBUG: current_root_height = {current_root_height}")
                print(f"DEBUG: scale_factor = {scale_factor}")

                new_canevas_width = scale_factor*self.__initial_canvas_width
                new_canevas_height = scale_factor*self.__initial_canvas_height

                self.__canvas.config(width=new_canevas_width, height=new_canevas_height)
                CANVAS_CONFIG.update(height=new_canevas_width)

                self.__background_tk_photo = None
                self.__cube_photos = None

                GraphicalHexagon.reset()
                GraphicalHexagon.init()

                self.__draw_state()

    def __command_update_players(self, *_):
        self.__searcher[rules.Player.T.WHITE] = self.__searcher_catalog.get(self.__variable_white_player.get())
        self.__searcher[rules.Player.T.BLACK] = self.__searcher_catalog.get(self.__variable_black_player.get())

    def __command_protect_action(self, *_):
        self.__variable_turn.set(len(self.__turn_states) - 1)
        self.__command_update_turn()

    def __command_update_turn(self, *_):

        try:
            turn_index = int(self.__variable_turn.get())
        except:
            turn_index = 0

        turn_index = max(0, min( len(self.__turn_states) - 1, turn_index))

        self.__pijersi_state = self.__turn_states[turn_index]

        if turn_index > 0:
            self.__legend = str(turn_index) + " " + self.__turn_actions[turn_index]

            if self.__game_terminated and turn_index == (len(self.__turn_states) - 1):
                self.__legend += " " + self.__make_legend_score(self.__pijersi_state)

        else:
            self.__legend = ""

        self.__variable_turn.set(turn_index)

        if turn_index != len(self.__turn_states) - 1 or not self.__game_terminated:
            self.__button_resume.config(state="enabled")
        else:
            self.__button_resume.config(state="disabled")

        self.__cmc_reset()
        self.__cmc_hightlight_played_hexagons()
        self.__draw_state()

    def __command_update_easy_mode(self):
        """
        If user changes easy mode checkbox during a game, redo the right drawing
        """

        self.__draw_state()

    def __command_confirm_action(self):

        self.__variable_turn.set(len(self.__turn_states) - 1)
        self.__command_update_turn()

        self.__action_input = self.__variable_action.get()
        self.__action_input = self.__action_input.replace("!", "")

        (self.__action_validated, message) = rules.Notation.validate_simple_notation(self.__action_input,
                                                                                     self.__pijersi_state.get_action_simple_names())

        if self.__action_validated:
            self.__variable_log.set(message)
            self.__variable_action.set("")
        else:
            self.__variable_log.set(message)

        self.__cmc_reset()


    def __command_setup(self, event):

        self.__game_setup = rules.Setup.from_name(self.__variable_setup.get())

        if self.__game_setup != rules.Setup.T.GIVEN:
            self.__game_setup_board_codes = rules.PijersiState.setup_board_codes(self.__game_setup)

        self.__pijersi_state = rules.PijersiState(setup=self.__game_setup,
                                                  board_codes=self.__game_setup_board_codes)

        self.__legend = ""

        self.__turn_states = list()
        self.__turn_states.append(self.__pijersi_state)
        self.__turn_actions = list()
        self.__turn_actions.append("")
        self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
        self.__variable_turn.set(len(self.__turn_states) - 1)

        self.__variable_log.set(f"Ready with '{self.__variable_setup.get()}' setup for a 'New' game")
        self.__variable_summary.set("")

        self.__text_actions.config(state="normal")
        self.__text_actions.delete('1.0', tk.END)
        self.__text_actions.config(state="disabled")
        self.__write_setup()

        self.__cmc_reset()
        self.__draw_state()

        self.__button_resume.config(state="disabled")


    def __command_edit_actions(self):

        if not self.__edit_actions:

            self.__edit_actions = True
            self.__saved_actions_text = self.__text_actions.get('1.0', tk.END)

            self.__button_edit_actions.configure(text="Validate")

            # update widgets status

            self.__button_reset_actions.config(state="enabled")

            self.__text_actions.config(state="normal", background='white')

            self.__button_new_stop.config(state="disabled")
            self.__combobox_white_player.config(state="disabled")
            self.__combobox_black_player.config(state="disabled")
            self.__combobox_setup.config(state="disabled")

            self.__spinbox_turn.config(state="disabled")
            self.__button_make_pictures.config(state="disabled")

            self.__button_resume.config(state="disabled")

            return

        elif self.__edit_actions:

            # try to validate edited actions

            actions_text = self.__text_actions.get('1.0', tk.END)

            self.__text_actions.config(state="normal")
            self.__text_actions.delete('1.0', tk.END)
            self.__text_actions.config(state="disabled")

            validated_edited_actions = True
            text_items = actions_text.split()

            # extract setup and actions items
            actions_items = []
            setup_items = []
            for text_item in text_items:
                if re.match(r".*:.*", text_item):
                    if len(actions_items) != 0:
                        validated_edited_actions = False
                        self.__variable_log.set("Error: setup cannot be after action")
                    setup_items.append(text_item)
                else:
                    actions_items.append(text_item)

            # interpret setup
            if len(setup_items) == 0:
                self.__game_setup_board_codes = self.__game_setup_board_codes_classic
                self.__game_setup = rules.Setup.T.CLASSIC

            else:
                board_codes = self.__read_setup(setup_items)

                if board_codes is not None:
                    self.__game_setup_board_codes = board_codes
                    self.__game_setup = rules.Setup.T.GIVEN

                    if self.__game_setup_board_codes == self.__game_setup_board_codes_classic:
                        self.__game_setup = rules.Setup.T.CLASSIC

                else:
                    validated_edited_actions = False
                    # >> left unchanged self.__game_setup and self.__game_setup_board_codes

            # check length of action items
            if validated_edited_actions and not len(actions_items) % 2 == 0:
                validated_edited_actions = False
                self.__variable_log.set("Error: not an even count of words")

            # check action indices
            if validated_edited_actions:
                action_count = int(len(actions_items)/2)
                for action_index in range(action_count):
                    even_action_item = actions_items[2*action_index]
                    if even_action_item != str(action_index + 1):
                        validated_edited_actions = False
                        self.__variable_log.set("Error: bad index '%s'" % even_action_item)

            # extract actions
            if validated_edited_actions:
                edited_actions = list()
                for action_index in range(action_count):
                    action = actions_items[2*action_index + 1]
                    action = action.replace("!", "")
                    edited_actions.append(action)

            # interpret actions
            if validated_edited_actions:

                self.__variable_setup.set(rules.Setup.to_name(self.__game_setup))
                self.__game = rules.Game(setup=self.__game_setup, board_codes=self.__game_setup_board_codes)

                white_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.WHITE].get_name())
                black_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.BLACK].get_name())

                self.__game.set_white_searcher(white_replayer)
                self.__game.set_black_searcher(black_replayer)

                self.__game.start()
                self.__game_setup_board_codes = self.__game.get_state().get_board_codes()
                self.__write_setup()

                self.__turn_states = list()
                self.__turn_states.append(self.__game.get_state())
                self.__turn_actions = list()
                self.__turn_actions.append("")
                self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                self.__variable_turn.set(len(self.__turn_states) - 1)

                for (action_index, action) in enumerate(edited_actions):

                    if not self.__game.has_next_turn():
                        validated_edited_actions = False
                        self.__variable_log.set("Error: too much actions")
                        break

                    self.__pijersi_state = self.__game.get_state()

                    (action_validated, message) = rules.Notation.validate_simple_notation(action,
                                                                                          self.__pijersi_state.get_action_simple_names())
                    if not action_validated:
                        validated_edited_actions = False
                        self.__variable_log.set("Error at turn %d: %s" % (action_index + 1, message))
                        break

                    player = self.__pijersi_state.get_current_player()

                    if player == rules.Player.T.WHITE:
                        white_replayer.set_action_simple_name(action)
                    else:
                        black_replayer.set_action_simple_name(action)

                    self.__game.next_turn()

                    self.__turn_states.append(self.__game.get_state())
                    self.__turn_actions.append(self.__game.get_last_action())

                    self.__variable_summary.set(self.__game.get_summary())
                    self.__variable_log.set(self.__game.get_log())

                    self.__text_actions.config(state="normal")

                    turn = self.__game.get_turn()
                    notation = str(turn).rjust(4) + " " + self.__game.get_last_action().ljust(16)
                    if turn % 2 == 0:
                        notation = ' '*2 + notation + "\n"

                    self.__text_actions.insert(tk.END, notation)
                    self.__text_actions.see(tk.END)
                    self.__text_actions.config(state="disabled")

                self.__game_terminated = not self.__game.has_next_turn()

                self.__pijersi_state = self.__game.get_state()

                self.__variable_summary.set(self.__game.get_summary())

                if self.__game.get_turn() > 0:
                    self.__legend = str(self.__game.get_turn()) + " " + self.__game.get_last_action()

                    if self.__game_terminated:
                        self.__legend += " " + self.__make_legend_score(self.__pijersi_state)

                else:
                    if self.__game_terminated:
                        self.__legend = " " + self.__make_legend_score(self.__pijersi_state)
                    else:
                        self.__legend = ""

                if validated_edited_actions:
                    self.__variable_log.set("Ready to 'Resume' or to start a 'New' game")

                self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                self.__variable_turn.set(len(self.__turn_states) - 1)

                self.__cmc_reset()
                self.__cmc_hightlight_played_hexagons()
                self.__draw_state()

            if not validated_edited_actions:

                self.__text_actions.config(state="normal")
                self.__text_actions.delete('1.0', tk.END)
                self.__text_actions.config(state="disabled")

                self.__text_actions.config(state="normal")
                self.__text_actions.insert(tk.END, actions_text)
                self.__text_actions.see(tk.END)

            if validated_edited_actions:

                self.__edit_actions = False
                self.__saved_actions_text = ""

                # update widgets status

                self.__button_reset_actions.config(state="disabled")

                self.__button_edit_actions.configure(text='Edit')

                self.__text_actions.config(state="disabled", background='lightgrey')

                self.__button_new_stop.config(state="enabled")
                self.__combobox_white_player.config(state="readonly")
                self.__combobox_black_player.config(state="readonly")
                self.__combobox_setup.config(state="readonly")

                self.__spinbox_turn.config(state="enabled")
                self.__button_make_pictures.config(state="enabled")

                if not self.__game_terminated:
                    self.__button_resume.config(state="enabled")
                else:
                    self.__button_resume.config(state="disabled")

            return


    def __command_reset_actions(self):
        self.__text_actions.delete('1.0', tk.END)
        self.__text_actions.insert(tk.END, self.__saved_actions_text)
        self.__variable_log.set("")


    def __command_make_pictures(self):

        # Disable widgets

        self.__button_quit.config(state="disabled")
        self.__button_new_stop.config(state="disabled")
        self.__combobox_white_player.config(state="disabled")
        self.__combobox_black_player.config(state="disabled")
        self.__combobox_setup.config(state="disabled")

        self.__button_easy_mode.config(state="disabled")
        self.__button_resume.config(state="disabled")

        self.__button_edit_actions.config(state="disabled")
        self.__spinbox_turn.config(state="disabled")
        self.__button_make_pictures.config(state="disabled")

        self.__text_actions.config(state="disabled")

        # Take pictures

        self.__variable_log.set("Making pictures ...")
        self.__label_log.update()

        if os.path.isdir(AppConfig.TMP_PICTURE_DIR):
            shutil.rmtree(AppConfig.TMP_PICTURE_DIR)
        os.mkdir(AppConfig.TMP_PICTURE_DIR)

        if os.path.isdir(AppConfig.TMP_ANIMATION_DIR):
            shutil.rmtree(AppConfig.TMP_ANIMATION_DIR)
        os.mkdir(AppConfig.TMP_ANIMATION_DIR)

        animation_index = 0

        for turn_index in range(len(self.__turn_states)):

            self.__variable_log.set(f"Making picture {turn_index} ...")
            self.__label_log.update()

            self.__pijersi_state = self.__turn_states[turn_index]

            if turn_index > 0:
                self.__legend = str(turn_index) + " " + self.__turn_actions[turn_index]

                if self.__game_terminated and turn_index == (len(self.__turn_states) - 1):
                    self.__legend += " " + self.__make_legend_score(self.__pijersi_state)

            else:
                self.__legend = ""

            self.__variable_turn.set(turn_index)

            # cinemetic: begin

            if turn_index != 0:
                pijersi_saved_state = self.__pijersi_state
                self.__pijersi_state = self.__turn_states[turn_index - 1]

                action_simple_name = self.__turn_actions[turn_index].replace("!", "")
                player = rules.Player.T.WHITE if turn_index % 2 == 1 else rules.Player.T.BLACK

                if len(action_simple_name) == 5:
                    src_hex_name = action_simple_name[0:2]
                    dst_hex_name = action_simple_name[3:5]

                    src_hex = GraphicalHexagon.get(src_hex_name)
                    dst_hex = GraphicalHexagon.get(dst_hex_name)

                    if action_simple_name[2] == '-':
                        src_hex.highlighted_as_cube = True
                    else:
                        src_hex.highlighted_as_stack = True

                    if player == rules.Player.T.WHITE:
                        src_hex.highlighted_as_played_by_white = True
                    else:
                        src_hex.highlighted_as_played_by_black = True

                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                    dst_hex.highlighted_as_destination = True
                    if player == rules.Player.T.WHITE:
                        dst_hex.highlighted_as_played_by_white = True
                    else:
                        dst_hex.highlighted_as_played_by_black = True

                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                elif len(action_simple_name) == 8:
                    intermediate_move = action_simple_name[0:5]

                    src_hex_name = action_simple_name[0:2]
                    int_hex_name = action_simple_name[3:5]
                    dst_hex_name = action_simple_name[6:8]

                    src_hex = GraphicalHexagon.get(src_hex_name)
                    int_hex = GraphicalHexagon.get(int_hex_name)
                    dst_hex = GraphicalHexagon.get(dst_hex_name)

                    if action_simple_name[2] == '-':
                        src_hex.highlighted_as_cube = True
                    else:
                        src_hex.highlighted_as_stack = True

                    if player == rules.Player.T.WHITE:
                        src_hex.highlighted_as_played_by_white = True
                    else:
                        src_hex.highlighted_as_played_by_black = True
                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                    int_hex.highlighted_as_destination = True
                    if player == rules.Player.T.WHITE:
                        int_hex.highlighted_as_played_by_white = True
                    else:
                        int_hex.highlighted_as_played_by_black = True
                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                    intermediate_action = self.__pijersi_state.get_action_by_simple_name(intermediate_move)
                    self.__pijersi_state = self.__pijersi_state.take_action(intermediate_action)
                    src_hex.highlighted_as_cube = False
                    src_hex.highlighted_as_stack = False
                    src_hex.highlighted_as_played_by_white = False
                    src_hex.highlighted_as_played_by_black = False

                    int_hex.highlighted_as_destination = False

                    if action_simple_name[5] == '-':
                        int_hex.highlighted_as_cube = True
                    else:
                        int_hex.highlighted_as_stack = True

                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                    dst_hex.highlighted_as_destination = True
                    if player == rules.Player.T.WHITE:
                        dst_hex.highlighted_as_played_by_white = True
                    else:
                        dst_hex.highlighted_as_played_by_black = True
                    self.__draw_state()
                    self.__canvas.update()
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                self.__pijersi_state = pijersi_saved_state
                pijersi_saved_state = None

            # cinematic: end

            self.__cmc_reset()
            self.__cmc_hightlight_played_hexagons()
            self.__draw_state()

            self.__canvas.update()

            picture_png_file = os.path.join(AppConfig.TMP_PICTURE_DIR, "state-%3.3d" % turn_index) + '.png'
            self.__take_picture(picture_png_file)

            if turn_index != 0:
                animation_index += 1
            animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
            self.__take_picture(animation_png_file)

            # simulate thinking and let the reader thinking too
            if animation_index != 0:
                saved_legend = self.__legend
                for pause_index in range(4):
                    self.__legend =  (pause_index + 1 ) *'.' + " " + saved_legend + " " + (pause_index + 1 ) *'.'
                    self.__draw_state()
                    self.__canvas.update()

                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_picture(animation_png_file)

                self.__legend = saved_legend
                self.__draw_state()
                self.__canvas.update()

        self.__variable_log.set("Making animated pictures ...")
        self.__label_log.update()
        self.__make_animated_pictures()

        self.__variable_log.set("Pictures are ready ; see the terminal window")
        print()
        print("pictures are available in directory '%s'" % AppConfig.TMP_PICTURE_DIR)

        # Enable widgets

        self.__button_quit.config(state="enabled")
        self.__button_new_stop.config(state="enabled")
        self.__combobox_white_player.config(state="readonly")
        self.__combobox_black_player.config(state="readonly")
        self.__combobox_setup.config(state="readonly")

        self.__button_easy_mode.config(state="enabled")
        self.__button_resume.config(state="enabled")

        self.__button_edit_actions.config(state="enabled")
        self.__spinbox_turn.config(state="enabled")
        self.__button_make_pictures.config(state="enabled")

        self.__text_actions.config(state="disabled")

    def __command_new_stop(self):

        if self.__game_timer_id is not None:
            self.__canvas.after_cancel(self.__game_timer_id)
            self.__game_timer_id = None

        if not self.__game_played:

            self.__game_played = True
            self.__game_terminated = False

            self.__concurrent_executor = PoolExecutor(max_workers=1)
            self.__backend_futures = [None for player in rules.Player.T]

            self.__game_setup = rules.Setup.from_name(self.__variable_setup.get())

            if  self.__game_setup == rules.Setup.T.GIVEN and self.__game_setup_board_codes is None:
                self.__game_setup = rules.Setup.T.CLASSIC
                self.__variable_setup.set(rules.Setup.to_name(self.__game_setup))

            self.__game = rules.Game(setup=self.__game_setup, board_codes=self.__game_setup_board_codes)

            self.__backend_searchers[rules.Player.T.WHITE] = self.__searcher[rules.Player.T.WHITE]
            self.__backend_searchers[rules.Player.T.BLACK] = self.__searcher[rules.Player.T.BLACK]

            self.__frontend_searchers[rules.Player.T.WHITE] = rules.HumanSearcher(self.__backend_searchers[rules.Player.T.WHITE].get_name())
            self.__frontend_searchers[rules.Player.T.BLACK] = rules.HumanSearcher(self.__backend_searchers[rules.Player.T.BLACK].get_name())

            self.__game.set_white_searcher(self.__frontend_searchers[rules.Player.T.WHITE])
            self.__game.set_black_searcher(self.__frontend_searchers[rules.Player.T.BLACK])

            self.__game.start()
            self.__game.set_turn_start(time.time())
            self.__game.set_turn_end(None)
            self.__game_setup_board_codes = self.__game.get_state().get_board_codes()

            self.__searcher_max_time = None
            self.__searcher_start_time = None

            self.__pijersi_state = self.__game.get_state()
            self.__legend = ""

            self.__turn_states = list()
            self.__turn_states.append(self.__game.get_state())
            self.__turn_actions = list()
            self.__turn_actions.append("")
            self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
            self.__variable_turn.set(len(self.__turn_states) - 1)

            self.__button_new_stop.configure(text="Stop")

            self.__variable_log.set(self.__game.get_log())
            self.__variable_summary.set(self.__game.get_summary())
            self.__progressbar['value'] = 0.

            self.__combobox_white_player.config(state="disabled")
            self.__combobox_black_player.config(state="disabled")
            self.__combobox_setup.config(state="disabled")

            self.__spinbox_turn.config(state="disabled")

            self.__text_actions.config(state="normal")
            self.__text_actions.delete('1.0', tk.END)
            self.__text_actions.config(state="disabled")
            self.__write_setup()

            self.__button_edit_actions.config(state="disabled")
            self.__button_make_pictures.config(state="disabled")

            self.__button_resume.config(state="disabled")

            self.__cmc_reset()
            self.__draw_state()

            self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        elif self.__game_played:

            self.__game_played = False
            self.__game_terminated = not self.__game.has_next_turn()

            if self.__concurrent_executor is not None:
                self.__backend_futures = [None for player in rules.Player.T]
                self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
                self.__concurrent_executor = None

            self.__button_new_stop.configure(text="New")

            self.__variable_log.set("Game stopped")
            self.__progressbar['value'] = 0.

            self.__combobox_white_player.config(state="readonly")
            self.__combobox_black_player.config(state="readonly")
            self.__combobox_setup.config(state="readonly")

            self.__spinbox_turn.config(state="enabled")

            self.__variable_action.set("")

            self.__button_edit_actions.config(state="enabled")
            self.__button_make_pictures.config(state="enabled")

            if not self.__game_terminated:
                self.__button_resume.config(state="enabled")
            else:
                self.__button_resume.config(state="disabled")

            self.__cmc_reset()
            self.__cmc_hightlight_played_hexagons()
            self.__draw_state()


    def __command_resume(self):

        # like "__command_edit_actions" but driven by the actual action list, possibly made shorter.

        resume_turn_index = int(self.__variable_turn.get())
        resume_actions = self.__turn_actions[1: resume_turn_index + 1]

        self.__text_actions.config(state="normal")
        self.__text_actions.delete('1.0', tk.END)
        self.__text_actions.config(state="disabled")

        self.__write_setup()

        # interpret actions

        self.__variable_setup.set(rules.Setup.to_name(self.__game_setup))
        self.__game = rules.Game(setup=self.__game_setup, board_codes=self.__game_setup_board_codes)

        white_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.WHITE].get_name())
        black_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.BLACK].get_name())

        self.__game.set_white_searcher(white_replayer)
        self.__game.set_black_searcher(black_replayer)

        self.__game.start()

        self.__turn_states = list()
        self.__turn_states.append(self.__game.get_state())
        self.__turn_actions = list()
        self.__turn_actions.append("")
        self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
        self.__variable_turn.set(len(self.__turn_states) - 1)

        for action in resume_actions:

            action = action.replace("!", "")

            self.__pijersi_state = self.__game.get_state()

            player = self.__pijersi_state.get_current_player()

            if player == rules.Player.T.WHITE:
                white_replayer.set_action_simple_name(action)
            else:
                black_replayer.set_action_simple_name(action)

            self.__game.next_turn()

            self.__turn_states.append(self.__game.get_state())
            self.__turn_actions.append(self.__game.get_last_action())

            self.__variable_summary.set(self.__game.get_summary())
            self.__variable_log.set(self.__game.get_log())

            self.__text_actions.config(state="normal")

            turn = self.__game.get_turn()
            notation = str(turn).rjust(4) + " " + self.__game.get_last_action().ljust(16)
            if turn % 2 == 0:
                notation = ' '*2 + notation + "\n"

            self.__text_actions.insert(tk.END, notation)
            self.__text_actions.see(tk.END)
            self.__text_actions.config(state="disabled")

        assert self.__game.has_next_turn()
        self.__game_played = True
        self.__game_terminated = False

        self.__pijersi_state = self.__game.get_state()

        if self.__game.get_turn() > 0:
            self.__legend = str(self.__game.get_turn()) + " " + self.__game.get_last_action()

            if self.__game_terminated:
                self.__legend += " " + self.__make_legend_score(self.__pijersi_state)

        else:
            self.__legend = ""

        self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
        self.__variable_turn.set(len(self.__turn_states) - 1)

        self.__variable_log.set(f"Game resumed at turn {resume_turn_index}")

        self.__cmc_reset()
        self.__cmc_hightlight_played_hexagons()
        self.__draw_state()

        # prepare next turn

        self.__searcher_max_time = None
        self.__searcher_start_time = None

        self.__concurrent_executor = PoolExecutor(max_workers=1)
        self.__backend_futures = [None for player in rules.Player.T]

        self.__backend_searchers[rules.Player.T.WHITE] = self.__searcher[rules.Player.T.WHITE]
        self.__backend_searchers[rules.Player.T.BLACK] = self.__searcher[rules.Player.T.BLACK]

        self.__frontend_searchers[rules.Player.T.WHITE] = rules.HumanSearcher(self.__backend_searchers[rules.Player.T.WHITE].get_name())
        self.__frontend_searchers[rules.Player.T.BLACK] = rules.HumanSearcher(self.__backend_searchers[rules.Player.T.BLACK].get_name())

        self.__game.set_white_searcher(self.__frontend_searchers[rules.Player.T.WHITE])
        self.__game.set_black_searcher(self.__frontend_searchers[rules.Player.T.BLACK])

        # update widgets status

        self.__pijersi_state = self.__game.get_state()
        player = self.__pijersi_state.get_current_player()
        backend_searcher = self.__backend_searchers[player]

        if backend_searcher.is_interactive():
            if player == rules.Player.T.WHITE:
                self.__progressbar.configure(style="White.Horizontal.TProgressbar")

            elif player == rules.Player.T.BLACK:
                self.__progressbar.configure(style="Black.Horizontal.TProgressbar")

            self.__progressbar['value'] = 50.
        else:
           self.__progressbar['value'] = 0.



        self.__button_new_stop.configure(text="Stop")

        self.__combobox_white_player.config(state="disabled")
        self.__combobox_black_player.config(state="disabled")
        self.__combobox_setup.config(state="disabled")

        self.__spinbox_turn.config(state="disabled")

        self.__text_actions.config(state="disabled")

        self.__button_edit_actions.config(state="disabled")
        self.__button_make_pictures.config(state="disabled")

        self.__button_resume.config(state="disabled")

        # start timer
        self.__game.set_turn_start(time.time())
        self.__game.set_turn_end(None)

        # watch next turn
        self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

    def __command_next_turn(self):

        if self.__game_timer_id is not None:
            self.__canvas.after_cancel(self.__game_timer_id)
            self.__game_timer_id = None

        if self.__game_played and self.__game.has_next_turn():

            self.__pijersi_state = self.__game.get_state()
            player = self.__pijersi_state.get_current_player()
            backend_searcher = self.__backend_searchers[player]
            frontend_searcher = self.__frontend_searchers[player]

            ready_for_next_turn = False

            if backend_searcher.is_interactive():

                if player == rules.Player.T.WHITE:
                    self.__progressbar.configure(style="White.Horizontal.TProgressbar")

                elif player == rules.Player.T.BLACK:
                    self.__progressbar.configure(style="Black.Horizontal.TProgressbar")

                self.__progressbar['value'] = 50.

                if self.__action_validated and self.__action_input is not None:
                    ready_for_next_turn = True

                    frontend_searcher.set_action_simple_name(self.__action_input)

                    self.__action_input = None
                    self.__action_validated = False

            elif not backend_searcher.is_interactive():

                if player == rules.Player.T.WHITE:
                    self.__progressbar.configure(style="White.Horizontal.TProgressbar")

                elif player == rules.Player.T.BLACK:
                    self.__progressbar.configure(style="Black.Horizontal.TProgressbar")

                if self.__backend_futures[player] is None:
                    ready_for_next_turn = False

                    self.__backend_futures[player] = self.__concurrent_executor.submit(search_task,
                                                                                       backend_searcher,
                                                                                       self.__pijersi_state)

                    self.__searcher_max_time = backend_searcher.get_time_limit()

                    if self.__searcher_max_time is None:
                        self.__progressbar['value'] = 10.

                    else:
                        self.__progressbar['value'] = 5.
                        self.__searcher_start_time = time.time()


                elif self.__backend_futures[player].done():
                    ready_for_next_turn = True

                    action_simple_name = self.__backend_futures[player].result()
                    frontend_searcher.set_action_simple_name(action_simple_name)
                    self.__backend_futures[player] = None

                    self.__progressbar['value'] = 100.


                    # Cinematic for AI action
                    # !! idea and prototype by MarcLeclere

                    if len(action_simple_name) == 5:
                        src_hex_name = action_simple_name[0:2]
                        dst_hex_name = action_simple_name[3:5]

                        src_hex = GraphicalHexagon.get(src_hex_name)
                        dst_hex = GraphicalHexagon.get(dst_hex_name)

                        if action_simple_name[2] == '-':
                            src_hex.highlighted_as_cube = True
                        else:
                            src_hex.highlighted_as_stack = True

                        if player == rules.Player.T.WHITE:
                            src_hex.highlighted_as_played_by_white = True
                        else:
                            src_hex.highlighted_as_played_by_black = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        dst_hex.highlighted_as_destination = True
                        if player == rules.Player.T.WHITE:
                            dst_hex.highlighted_as_played_by_white = True
                        else:
                            dst_hex.highlighted_as_played_by_black = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                    elif len(action_simple_name) == 8:
                        pijersi_saved_state = self.__pijersi_state
                        intermediate_move = action_simple_name[0:5]

                        src_hex_name = action_simple_name[0:2]
                        int_hex_name = action_simple_name[3:5]
                        dst_hex_name = action_simple_name[6:8]

                        src_hex = GraphicalHexagon.get(src_hex_name)
                        int_hex = GraphicalHexagon.get(int_hex_name)
                        dst_hex = GraphicalHexagon.get(dst_hex_name)

                        if action_simple_name[2] == '-':
                            src_hex.highlighted_as_cube = True
                        else:
                            src_hex.highlighted_as_stack = True

                        if player == rules.Player.T.WHITE:
                            src_hex.highlighted_as_played_by_white = True
                        else:
                            src_hex.highlighted_as_played_by_black = True
                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        int_hex.highlighted_as_destination = True
                        if player == rules.Player.T.WHITE:
                            int_hex.highlighted_as_played_by_white = True
                        else:
                            int_hex.highlighted_as_played_by_black = True
                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        intermediate_action = self.__pijersi_state.get_action_by_simple_name(intermediate_move)
                        self.__pijersi_state = self.__pijersi_state.take_action(intermediate_action)
                        src_hex.highlighted_as_cube = False
                        src_hex.highlighted_as_stack = False
                        src_hex.highlighted_as_played_by_white = False
                        src_hex.highlighted_as_played_by_black = False

                        int_hex.highlighted_as_destination = False

                        if action_simple_name[5] == '-':
                            int_hex.highlighted_as_cube = True
                        else:
                            int_hex.highlighted_as_stack = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        dst_hex.highlighted_as_destination = True
                        if player == rules.Player.T.WHITE:
                            dst_hex.highlighted_as_played_by_white = True
                        else:
                            dst_hex.highlighted_as_played_by_black = True
                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        self.__pijersi_state = pijersi_saved_state
                        pijersi_saved_state = None

                else:
                    ready_for_next_turn = False

                    progressbar_value = self.__progressbar['value']

                    if self.__searcher_max_time is None:
                        progressbar_value += 10.
                        if progressbar_value > 100.:
                            progressbar_value = 10.

                    else:
                        progress_time = time.time() - self.__searcher_start_time
                        progressbar_value = 100*progress_time/self.__searcher_max_time
                        progressbar_value = min(100., progressbar_value)
                        progressbar_value = max(5., progressbar_value)

                    self.__progressbar['value'] = progressbar_value

            if ready_for_next_turn:
                self.__progressbar['value'] = 0.

                self.__game.set_turn_end(time.time())
                self.__game.next_turn()
                self.__game.set_turn_start(time.time())
                self.__game.set_turn_end(None)

                self.__pijersi_state = self.__game.get_state()
                self.__game_terminated = not self.__game.has_next_turn()

                if self.__game.get_turn() > 0:
                    self.__legend = str(self.__game.get_turn()) + " " + self.__game.get_last_action()

                    if self.__game_terminated:
                        self.__legend += " " + self.__make_legend_score(self.__pijersi_state)

                else:
                    self.__legend = ""

                self.__draw_state()

                self.__variable_summary.set(self.__game.get_summary())
                self.__variable_log.set(self.__game.get_log())

                self.__text_actions.config(state="normal")

                turn = self.__game.get_turn()
                notation = str(turn).rjust(4) + " " + self.__game.get_last_action().ljust(16)
                if turn % 2 == 0:
                    notation = ' '*2 + notation + "\n"

                self.__text_actions.insert(tk.END, notation)
                self.__text_actions.see(tk.END)
                self.__text_actions.config(state="disabled")

                self.__turn_states.append(self.__game.get_state())
                self.__turn_actions.append(self.__game.get_last_action())
                self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                self.__variable_turn.set(len(self.__turn_states) - 1)

                self.__cmc_reset()
                self.__cmc_hightlight_played_hexagons()
                self.__draw_state()

            self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        else:

            self.__game_played = False
            self.__game_terminated = True

            self.__backend_futures = [None for player in rules.Player.T]
            self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
            self.__concurrent_executor = None

            self.__button_new_stop.configure(text="New")

            self.__combobox_white_player.config(state="readonly")
            self.__combobox_black_player.config(state="readonly")
            self.__combobox_setup.config(state="readonly")

            self.__spinbox_turn.config(state="enabled")

            self.__progressbar['value'] = 0.

            self.__button_edit_actions.config(state="enabled")
            self.__button_make_pictures.config(state="enabled")

    ### CMC (Mouse Canevas Control) methods
    ### !! idea and prototype by MarcLeclere

    def __cmc_update_mouse_over(self, event):
        """
        Manage mouse over event: if mouse pointer is over canvas, then highlight the pointed hexagon when selectable
        """

        hexagon_at_over = self.__cmc_get_hexagon_at_position(event)

        # Do nothing if the mouse has not moved to another hexagon
        # >> This avoid multiple draws
        if self.__cmc_hexagon_at_over == hexagon_at_over:
            return

        self.__cmc_hexagon_at_over = hexagon_at_over

        # Do nothing if the game is not played
        if not self.__game_played:
            return

        # Do nothing if user is viewing some previous turn
        if int(self.__variable_turn.get()) != len(self.__turn_states) - 1:
            return

        # Do nothing if user is not playing
        if not self.__searcher[self.__pijersi_state.get_current_player()].is_interactive():
            return

        # Highlight selectable hexagons
        self.__cmc_set_legal_hexagons()
        self.__cmc_hightlight_selectable_hexagons()
        self.__draw_state()

    def __cmc_update_mouse_click(self, event):
        """
        Manage click event:  if mouse is inside the canvas, manage the event regarding the CMC state
        """

        # Do nothing if the game is not played
        if not self.__game_played:
            return

        # Do nothing if user is viewing some previous turn
        if int(self.__variable_turn.get()) != len(self.__turn_states) - 1:
            return

        # Do nothing if user is not playing
        if not self.__searcher[self.__pijersi_state.get_current_player()].is_interactive():
            return

        # Dispatch the management regarding the CMC state
        if self.__cmc_state is CMCState.SELECTING_1:
            self.__cmc_update_mouse_click_1(event)

        elif self.__cmc_state is CMCState.SELECTING_2:
            self.__cmc_update_mouse_click_2(event)

        elif self.__cmc_state is CMCState.SELECTING_3:
            self.__cmc_update_mouse_click_3(event)

    def __cmc_update_mouse_click_1(self, event):
        """
        Manage click event when the CMC process is in state SELECTING_1,
        meaning wait that user selects a first hexagon.
        If user clicks on a legal hexagon, the CMC state is updated.
        Otherwise, the CMC process is reset.
        """

        hexagon_at_mouse_click = self.__cmc_get_hexagon_at_position(event)

        if hexagon_at_mouse_click in self.__cmc_legal_hexagons:
            self.__cmc_hexagon_at_click = hexagon_at_mouse_click

            # Reset all highlights
            GraphicalHexagon.reset_highlights()

            # Define highlights for cube/stack
            has_stack = self.__cmc_hexagon_has_stack_at_selection_1(self.__cmc_hexagon_at_click.name)
            self.__cmc_hexagon_at_click.highlighted_as_stack = has_stack
            self.__cmc_hexagon_at_click.highlighted_as_cube = not has_stack
            self.__cmc_hexagon_has_stack = has_stack
            self.__cmc_hexagon_has_stack_selection = has_stack

            # Update the textual-action-input widget
            self.__variable_action.set(hexagon_at_mouse_click.name)

            # Update the CMC state
            self.__cmc_state = CMCState.SELECTING_2

            # Update and highlight the legal hexagons
            self.__cmc_set_legal_hexagons()
            self.__cmc_hightlight_selectable_hexagons()
            self.__cmc_hightlight_destination_hexagons()

        else:
            self.__cmc_reset()
            self.__cmc_state = CMCState.SELECTING_1
            self.__cmc_hightlight_played_hexagons()

        self.__draw_state()

    def __cmc_update_mouse_click_2(self, event):
        """
        Manage click event when the CMC process is in state SELECTING_2,
        meaning wait that user selects a second hexagon.
        If user clicks on a legal hexagon, the CMC state is updated.
        Otherwise, the CMC process is reset.
        """

        hexagon_at_mouse_click = self.__cmc_get_hexagon_at_position(event)

        if self.__cmc_hexagon_has_stack and hexagon_at_mouse_click is self.__cmc_hexagon_at_click:
            # Manage double click on selected hexagon, meaning selecting stack's top instead of selecting the entire stack
            self.__cmc_hexagon_has_stack_selection = not self.__cmc_hexagon_has_stack_selection
            self.__cmc_hexagon_at_click.highlighted_as_stack = self.__cmc_hexagon_has_stack_selection
            self.__cmc_hexagon_at_click.highlighted_as_cube = not self.__cmc_hexagon_has_stack_selection

            self.__cmc_set_legal_hexagons()
            self.__cmc_hightlight_selectable_hexagons()
            self.__cmc_hightlight_destination_hexagons()
            # >> The CMC state is NOT changed

        elif hexagon_at_mouse_click in self.__cmc_legal_hexagons:
            # Reset all highlights
            GraphicalHexagon.reset_highlights()

            # Change the selected hexagon and filter corresponding actions
            self.__cmc_hexagon_at_click = hexagon_at_mouse_click
            actions = [action[0:5] for action in self.__cmc_legal_actions if action[3:5] == hexagon_at_mouse_click.name]
            action_name = actions[0]

            # Give correct highlights to selected hexagon
            self.__cmc_hexagon_at_click.highlighted_as_selectable = False
            # >> If stack is selected at step 1, then it cannot be selected at step 2. And vice versa.
            # >> Hypothesis: two moves are made in the action.
            # >> If the hypothesis is wrong then it does not matter, because the action terminates at this step.
            self.__cmc_hexagon_at_click.highlighted_as_stack = not self.__cmc_hexagon_has_stack_selection
            self.__cmc_hexagon_at_click.highlighted_as_cube = not self.__cmc_hexagon_at_click.highlighted_as_stack

            # Update the textual-action-input widget
            self.__variable_action.set(action_name)

            # Show the action result in a virtual pijersi state
            action = self.__pijersi_state.get_action_by_simple_name(action_name)
            self.__cmc_pijersi_state = self.__pijersi_state.take_action(action)

            # Update the CMC state
            self.__cmc_state = CMCState.SELECTING_3

            # Update and highlight the legal hexagons
            self.__cmc_set_legal_hexagons()
            self.__cmc_hightlight_selectable_hexagons()
            self.__cmc_hightlight_destination_hexagons()

            # If no more action available, this action is terminal
            if len(self.__cmc_legal_actions) == 0:
                self.__cmc_terminate()

        else:
            # User does not click on a legal hexagon
            # The CMC process is reset
            self.__cmc_reset()
            self.__cmc_state = CMCState.SELECTING_1
            self.__cmc_hightlight_played_hexagons()

        self.__draw_state()

    def __cmc_update_mouse_click_3(self, event):
        """
        Manage click event when the CMC process is in state SELECTING_3,
        meaning wait that user selects a third hexagon and finishes the CMC process.
        If user clicks on a legal hexagon, the CMC state is updated.
        Otherwise, the CMC process is reset.
        """

        hexagon_at_mouse_click = self.__cmc_get_hexagon_at_position(event)

        if hexagon_at_mouse_click is self.__cmc_hexagon_at_click:
            # If user clicks the latest target hexagon, then this terminates the action
            self.__cmc_terminate()

        elif hexagon_at_mouse_click in self.__cmc_legal_hexagons:
            actions = [action[0:8] for action in self.__cmc_legal_actions if action[6:8] == hexagon_at_mouse_click.name]
            action_name = actions[0]

            # Update the textual-action-input widget
            self.__variable_action.set(action_name)

            # Show the action result in a virtual pijersi state
            action = self.__pijersi_state.get_action_by_simple_name(action_name)
            self.__cmc_pijersi_state = self.__pijersi_state.take_action(action)

            self.__cmc_terminate()

        else:
            self.__cmc_reset()
            self.__cmc_state = CMCState.SELECTING_1
            self.__cmc_hightlight_played_hexagons()

        self.__draw_state()

    def __cmc_reset(self):
        """
        Reset the CMC process and clean the drawing
        """

        self.__cmc_pijersi_state = None
        self.__cmc_state = CMCState.SELECTING_1

        self.__cmc_legal_actions = []
        self.__cmc_legal_hexagons = []

        self.__cmc_hexagon_at_over = None
        self.__cmc_hexagon_at_click = None
        # Does the clicked hexagon has a stack ?
        self.__cmc_hexagon_has_stack = False
        # If the stack selected or just its top ?
        self.__cmc_hexagon_has_stack_selection = False

        GraphicalHexagon.reset_highlights()

    def __cmc_terminate(self):
        """
        When the CMC process is finished, transmits the action to the GUI kernel
        """

        self.__action_validated = True
        self.__action_input = self.__variable_action.get()
        self.__variable_action.set("")

        GraphicalHexagon.reset_highlights()
        self.__cmc_hightlight_played_hexagons()


    def __cmc_set_legal_actions(self):
        """
        Filter legal actions according to the CMC process state
        """

        if self.__cmc_state is CMCState.SELECTING_1:
            # Keep all legal actions
            self.__cmc_legal_actions = self.__pijersi_state.get_action_simple_names()

        elif self.__cmc_state is CMCState.SELECTING_2:
            # Keep actions containing the selected hexagon name at first selection
            self.__cmc_legal_actions.clear()

            # If stack is selected, keep only stack actions
            action_sign = "=" if self.__cmc_hexagon_has_stack_selection else "-"

            for action_name in self.__pijersi_state.get_action_simple_names():
                if action_name[0:3] == self.__cmc_hexagon_at_click.name + action_sign:
                    self.__cmc_legal_actions.append(action_name)

        elif self.__cmc_state is CMCState.SELECTING_3:
            # keep actions with 2 steps containing the selected hexagon name at second selection
            legal_actions = copy.copy(self.__cmc_legal_actions)
            self.__cmc_legal_actions.clear()
            for action_name in legal_actions:
                if action_name[0:5] == self.__variable_action.get():
                    if len(action_name) > 5:
                        self.__cmc_legal_actions.append(action_name)

    def __cmc_set_legal_hexagons(self):
        """
        Build the list of hexagons user can interact with
        """

        self.__cmc_legal_hexagons.clear()
        self.__cmc_set_legal_actions()

        if self.__cmc_state is CMCState.SELECTING_1:
            self.__cmc_set_legal_hexagons_at_step(1)

        elif self.__cmc_state is CMCState.SELECTING_2:
            self.__cmc_set_legal_hexagons_at_step(2)

        elif self.__cmc_state is CMCState.SELECTING_3:
            self.__cmc_set_legal_hexagons_at_step(3)
            # Add the current selected hexagon to interrupt the selection at step 2
            self.__cmc_legal_hexagons.append(self.__cmc_hexagon_at_click)

        else:
            # If the CMC process is deactivated, no hexagon is added to legal hexagons list
            pass

    def __cmc_set_legal_hexagons_at_step(self, step):
        """
        Build the list of graphical hexagons user can interact with at a given step of the selection process
        """

        # >> Indexes inside the action name
        hexagone_name_indexes_by_step = {1: (0, 2), 2: (3, 5), 3: (6, 8)}
        (index_1, index_2) = hexagone_name_indexes_by_step[step]

        hexagon_names = set()
        for action_name in self.__cmc_legal_actions:
            hexagon_names.add(action_name[index_1:index_2])

        for hexagon_name in hexagon_names:
            graphical_hexagon = GraphicalHexagon.get(hexagon_name)
            self.__cmc_legal_hexagons.append(graphical_hexagon)

    def __cmc_hexagon_has_stack_at_selection_1(self, hexagon_name):
        for action in self.__cmc_legal_actions:
            if action[0:3] == hexagon_name + "=":
                return True
        return False

    def __cmc_get_hexagon_at_position(self, position):
        """
        Return the hexagon at a given position
        """

        for hexagon in GraphicalHexagon.all:
            if hexagon.contains_point((position.x, position.y)):
                return hexagon

        return None

    def __cmc_hightlight_selectable_hexagons(self):
        """
        Mark selectable hexagons
        """

        GraphicalHexagon.reset_highlights_as_selectable()

        if self.__cmc_hexagon_at_over in self.__cmc_legal_hexagons:
            self.__cmc_hexagon_at_over.highlighted_as_selectable = True

    def __cmc_hightlight_destination_hexagons(self):
        """
        Mark hexagons as destinations
        """

        GraphicalHexagon.reset_highlights_as_destination()

        for hexagon in self.__cmc_legal_hexagons:
            hexagon.highlighted_as_destination = True

    def __cmc_hightlight_played_hexagons(self):
        """
        Mark played hexagons (targets of the action)
        """

        GraphicalHexagon.reset_highlights_as_played()

        played_action_name = None
        player_index = None

        turn_index = int(self.__variable_turn.get())

        if int(self.__variable_turn.get()) != len(self.__turn_states) - 1:
            # User is viewing previous turns: take the viewed action
            played_action_name = str(self.__turn_actions[turn_index])
            player_index = (turn_index + 1) % 2

        elif self.__action_validated and self.__action_input is not None:
            # User action has just been validated: take it
            played_action_name = self.__action_input
            player_index = (turn_index + 0) % 2

        else:
            # Take the lastest registered action, by either user or agent
            played_action_name = str(self.__turn_actions[turn_index])
            player_index = (turn_index + 1) % 2

        if played_action_name is not None:
            played_hexagons = self.__get_destination_hexagons(played_action_name)

            if player_index == 0:
                for hexagon in played_hexagons:
                    hexagon.highlighted_as_played_by_white = True

            elif player_index == 1:
                for hexagon in played_hexagons:
                    hexagon.highlighted_as_played_by_black = True

    def __get_destination_hexagons(self, action_name):

        simple_action_name = action_name.replace("!", "")

        if len(simple_action_name) == 5:
            hexagon_names = [simple_action_name[3:5]]

        elif len(simple_action_name) == 8:
            if simple_action_name[5] == "=":
                hexagon_names = [simple_action_name[6:8]]

            elif simple_action_name[5] == "-":
                hexagon_names = [simple_action_name[3:5], simple_action_name[6:8]]

        else:
            hexagon_names = []

        destination_hexagons = [GraphicalHexagon.get(hexagon_name) for hexagon_name in hexagon_names]
        return destination_hexagons


    def __read_setup(self, setup_items):

        cube_names = rules.Cube.get_names()
        hexagon_names = [hexagon.name for hexagon in rules.Hexagon.get_all()]

        cube_counts = {cube_name:0 for cube_name in cube_names}

        board_codes = rules.PijersiState.empty_board_codes()

        for setup_item in setup_items:

            if not re.match(r"^[a-z][1-9]{1,2}:[a-zA-Z]+$", setup_item):
                self.__variable_log.set(f"Error: setup '{setup_item}' is not well-formed")
                return None

            if re.match(r"^[a-z][1-9]:[a-zA-Z]$", setup_item):
                hexagon_name = setup_item[0:2]
                cube_name = setup_item[3]

                if hexagon_name not in hexagon_names:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong hexagon '{hexagon_name}'")
                    return None

                if cube_name not in cube_names:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong cube '{cube_name}'")
                    return None

                try:
                    rules.PijersiState.set_cube_from_names(board_codes, hexagon_name, cube_name)
                    cube_counts[cube_name] += 1
                except:
                    self.__variable_log.set(f"Error: setup '{setup_item}' is illegal")
                    return None

            elif re.match(r"^[a-z][1-9]:[a-zA-Z][a-zA-Z]$", setup_item):
                hexagon_name = setup_item[0:2]
                top_name = setup_item[3]
                bottom_name = setup_item[4]

                if hexagon_name not in hexagon_names:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong hexagon '{hexagon_name}'")
                    return None

                if top_name not in cube_names:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong top cube '{top_name}'")
                    return None

                if bottom_name not in cube_names:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong bottom cube '{bottom_name}'")
                    return None

                try:
                    rules.PijersiState.set_stack_from_names(board_codes, hexagon_name, bottom_name=bottom_name, top_name=top_name)
                    cube_counts[top_name] += 1
                    cube_counts[bottom_name] += 1
                except:
                    self.__variable_log.set(f"Error: setup '{setup_item}' is illegal")
                    return None

            elif re.match(r"^[a-z][1-9]{2}:[a-zA-Z]+$", setup_item):
                (setup_positions, setup_cubes) = setup_item.split(':')
                row_name = setup_positions[0]
                (col_start, col_end) = (int(setup_positions[1]), int(setup_positions[2]))
                if not col_start < col_end:
                    self.__variable_log.set(f"Error: setup '{setup_item}' with wrong column range")
                    return None

                setup_hexagon_names = [ f"{row_name}{col_index}" for col_index in range(col_start, col_end + 1) ]
                setup_cube_names = [cube_name for cube_name in setup_cubes]

                if len(setup_hexagon_names) != len(setup_cube_names):
                    self.__variable_log.set(f"Error: setup '{setup_item}' cubes and column range not matching")
                    return None

                for hexagon_name in setup_hexagon_names:
                    if hexagon_name not in hexagon_names:
                        self.__variable_log.set(f"Error: setup '{setup_item}' with wrong implied hexagon '{hexagon_name}'")
                        return None

                for cube_name in setup_cube_names:
                    if cube_name not in cube_names:
                        self.__variable_log.set(f"Error: setup '{setup_item}' with wrong cube '{cube_name}'")
                        return None

                for (hexagon_name, cube_name) in zip(setup_hexagon_names, setup_cube_names):
                    try:
                        rules.PijersiState.set_cube_from_names(board_codes, hexagon_name, cube_name)
                        cube_counts[cube_name] += 1
                    except:
                        self.__variable_log.set(f"Error: setup '{setup_item}' is illegal in implied '{hexagon_name}:{cube_name}'")
                        return None

            else:
                self.__variable_log.set(f"Error: setup '{setup_item}' is not well-formed")
                return None

        for (cube_name, cube_count) in cube_counts.items():
            if cube_count > (2 if cube_name in ['w', 'W'] else 4):
                self.__variable_log.set(f"Error: setup has too much cubes '{cube_name}' : {cube_count}")
                return None

        return board_codes


    def __write_setup(self):
        """Write compact setup in self.__text_actions"""

        self.__text_actions.config(state="normal")

        hex_states = [rules.HexState.decode(code) for code in self.__game_setup_board_codes]

        rows = {}

        for hexagon in rules.Hexagon.all:
            hex_state = hex_states[hexagon.index]

            row_label = hexagon.name[0]
            col_index = int(hexagon.name[1])

            if hex_state.is_empty:
                content = ""

            elif hex_state.has_stack:
                content = (rules.Cube.to_name(hex_state.player, hex_state.top) +
                           rules.Cube.to_name(hex_state.player, hex_state.bottom))

            else:
                content = rules.Cube.to_name(hex_state.player, hex_state.bottom)

            if len(content) != 0:
                if row_label not in rows:
                    rows[row_label] = {}
                rows[row_label][col_index] = content

        row_count = 0
        row_items = []

        for row_label in sorted(rows.keys(), reverse=True):
            col_content = ""
            col_start = None

            for col_index in sorted(rows[row_label].keys()):
                content = rows[row_label][col_index]

                if col_start is None:
                    col_start = col_index

                if col_index == col_start + len(col_content) and len(content) == 1:
                    col_content += content

                else:

                    if len(col_content) != 0:
                        if len(col_content) == 1:
                            row_items.append(f"{row_label}{col_start}:{col_content}")
                        else:
                            col_end = col_start + len(col_content) - 1
                            row_items.append(f"{row_label}{col_start}{col_end}:{col_content}")
                        col_content = ""

                    if len(content) > 1:
                        row_items.append(f"{row_label}{col_index}:{content}")
                        col_content = ""
                        col_start = None

                    else:
                        col_start = col_index
                        col_content = content

            if len(col_content) != 0:
                if len(col_content) == 1:
                    row_items.append(f"{row_label}{col_start}:{col_content}")
                else:
                    col_end = col_start + len(col_content) - 1
                    row_items.append(f"{row_label}{col_start}{col_end}:{col_content}")
                col_content = ""


            row_count += 1
            if row_count % 2 == 0:
                self.__text_actions.insert(tk.END, 3*" " + " ".join(row_items) + "\n")
                row_items = []

        if len(row_items) != 0:
            self.__text_actions.insert(tk.END, 3*" " + " ".join(row_items) + "\n")
            row_items = []

        self.__text_actions.insert(tk.END, "\n")
        self.__text_actions.see(tk.END)
        self.__text_actions.config(state="disabled")


    def __make_legend_score(self, pijersi_state):
        rewards = pijersi_state.get_rewards()

        if rewards[rules.Player.T.WHITE] == rules.Reward.WIN:
            legend_score = "1-0"

        elif rewards[rules.Player.T.BLACK] == rules.Reward.WIN:
            legend_score = "0-1"

        elif rewards[rules.Player.T.WHITE] == rules.Reward.DRAW:
            legend_score = "½-½"

        else:
            legend_score = ""

        return legend_score

    def __take_picture(self, picture_file: str):
        grab_canvas_only = True

        if grab_canvas_only:

            x = self.__canvas.winfo_rootx()
            y = self.__canvas.winfo_rooty()
            w = self.__canvas.winfo_width()
            h = self.__canvas.winfo_height()

            left = x
            right = x + w
            upper = y
            lower = y + h

            if self.__use_background_photo:
                upper += self.__background_tk_photo_delta_y
                lower -= self.__background_tk_photo_delta_y

                left += self.__background_tk_photo_delta_x
                right -= self.__background_tk_photo_delta_x

                upper += int(0.01*h)
                lower -= int(0.01*h)

                left += int(0.01*w)
                right -= int(0.01*w)

            picture_bbox = (left, upper, right, lower)

        else:
            picture_bbox = None

        image = ImageGrab.grab(bbox=picture_bbox, all_screens=True)
        # >> all_screens – Capture all monitors. Windows OS only
        image.save(picture_file)

    def __make_animated_pictures(self):

        if not os.path.isdir(AppConfig.TMP_ANIMATION_DIR):
            return

        if not os.path.isdir(AppConfig.TMP_PICTURE_DIR):
            os.mkdir(AppConfig.TMP_PICTURE_DIR)

        frames = []
        picture_list = glob.glob(os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-*"))

        if len(picture_list) != 0:
            for picture in picture_list:
                new_frame = Image.open(picture)
                frames.append(new_frame)

            # Save into a GIF file that loops forever
            frames[0].save(os.path.join(AppConfig.TMP_PICTURE_DIR, "all-states.gif"),
                           format='GIF',
                           append_images=frames[1:],
                           save_all=True,
                           duration=self.__picture_gif_duration, loop=0)

    ### Drawer iterators

    def __draw_state(self):

        self.__canvas.delete('all')

        if self.__use_background_photo:
            self.__draw_canvas_background()

        self.__draw_all_hexagons()
        self.__draw_all_cubes()
        self.__draw_legend()

    def __draw_canvas_background(self):
        if self.__background_tk_photo is None:

            # Create the background image
            bg_photo = Image.open(CANVAS_CONFIG.BACKGROUND_PHOTO_PATH)
            (bg_width, bg_height) = bg_photo.size

            bg_new_width = int(math.ceil(CANVAS_CONFIG.WIDTH))
            bg_new_height = int(math.ceil(CANVAS_CONFIG.WIDTH*bg_height/bg_width))

            bg_photo = bg_photo.resize((bg_new_width, bg_new_height))
            self.__background_tk_photo = ImageTk.PhotoImage(bg_photo)

            self.__background_tk_photo_delta_x = (bg_new_width - CANVAS_CONFIG.WIDTH)/2
            self.__background_tk_photo_delta_y = (bg_new_height - CANVAS_CONFIG.HEIGHT)/2

        # Add the background image
        self.__canvas.create_image(self.__background_tk_photo_delta_x, self.__background_tk_photo_delta_y,
                                   image=self.__background_tk_photo,
                                   anchor=tk.NW)

    def __draw_legend(self):

        (u, v) = (2, -4)
        hexagon_center = CANVAS_CONFIG.ORIGIN + CANVAS_CONFIG.HEXA_WIDTH*(u*CANVAS_CONFIG.UNIT_U + v*CANVAS_CONFIG.UNIT_V)

        vertex_index = 1
        vertex_angle = (1/2 + vertex_index)*CANVAS_CONFIG.HEXA_SIDE_ANGLE

        hexagon_vertex = hexagon_center
        hexagon_vertex = hexagon_vertex + CANVAS_CONFIG.HEXA_SIDE*math.cos(vertex_angle)*CANVAS_CONFIG.UNIT_X
        hexagon_vertex = hexagon_vertex + CANVAS_CONFIG.HEXA_SIDE*math.sin(vertex_angle)*CANVAS_CONFIG.UNIT_Y

        legend_position = hexagon_vertex - 1.0*CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_Y

        legend_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LEGEND_SIZE, weight='bold')

        self.__canvas.create_text(*legend_position, text=self.__legend, justify=tk.CENTER,
                                  font=legend_font, fill=CANVAS_CONFIG.FONT_LEGEND_COLOR)

    def __draw_all_cubes(self):

        if self.__cmc_pijersi_state is not None:
            pijersi_state = self.__cmc_pijersi_state
        else:
            pijersi_state = self.__pijersi_state

        hex_states = pijersi_state.get_hex_states()

        for hexagon in rules.Hexagon.all:

            hex_state = hex_states[hexagon.index]

            if hex_state.is_empty:
                # Hexagon is empty
                pass

            elif hex_state.has_stack:
                # Hexagon with a stack

                self.__draw_cube(name=hexagon.name, config=CubeLocation.TOP,
                                 cube_color=hex_state.player,
                                 cube_sort=hex_state.top,
                                 cube_label=rules.Cube.to_name(hex_state.player, hex_state.top))

                self.__draw_cube(name=hexagon.name, config=CubeLocation.BOTTOM,
                                 cube_color=hex_state.player,
                                 cube_sort=hex_state.bottom,
                                 cube_label=rules.Cube.to_name(hex_state.player, hex_state.bottom))

            elif hex_state.top is not None:
                # Hexagon with a single cube at top

                self.__draw_cube(name=hexagon.name, config=CubeLocation.MIDDLE,
                                 cube_color=hex_state.player,
                                 cube_sort=hex_state.top,
                                 cube_label=rules.Cube.to_name(hex_state.player, hex_state.top))

            elif hex_state.bottom is not None:
                # Hexagon with a single cube at bottom

                self.__draw_cube(name=hexagon.name, config=CubeLocation.MIDDLE,
                                 cube_color=hex_state.player,
                                 cube_sort=hex_state.bottom,
                                 cube_label=rules.Cube.to_name(hex_state.player, hex_state.bottom))

    def __draw_all_hexagons(self):

        for hexagon in GraphicalHexagon.all:
            self.__draw_hexagon(hexagon)

    ### Drawer primitives

    def __draw_hexagon(self, hexagon):

        label_position = (TinyVector((hexagon.vertex_data[6], hexagon.vertex_data[7])) +
                          0.25*CANVAS_CONFIG.HEXA_SIDE*(CANVAS_CONFIG.UNIT_X + 0.75*CANVAS_CONFIG.UNIT_Y))

        if self.__use_background_photo:
            polygon_line_color = ''
            fill_color = ''

        else:
            polygon_line_color = HexagonLineColor.NORMAL.value
            fill_color = hexagon.color.value

        line_width_scaling = 1

        easy_mode = self.__variable_easy_mode.get()

        # Respect priority order in lighting

        if easy_mode and hexagon.highlighted_as_selectable:
            fill_color = HexagonColor.HIGHLIGHT_SOURCE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if easy_mode and hexagon.highlighted_as_destination:
            fill_color = HexagonColor.HIGHLIGHT_DESTINATION_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_cube:
            fill_color = HexagonColor.HIGHLIGHT_CUBE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_stack:
            fill_color = HexagonColor.HIGHLIGHT_STACK_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if easy_mode:
            if hexagon.highlighted_as_played_by_white:
                polygon_line_color = HexagonLineColor.HIGHLIGHT_PLAYED_BY_WHITE.value
                line_width_scaling = 3

            elif hexagon.highlighted_as_played_by_black:
                polygon_line_color = HexagonLineColor.HIGHLIGHT_PLAYED_BY_BLACK.value
                line_width_scaling = 4

        self.__canvas.create_polygon(hexagon.vertex_data,
                                     fill=fill_color,
                                     outline=polygon_line_color,
                                     width=CANVAS_CONFIG.HEXA_LINE_WIDTH*line_width_scaling,
                                     joinstyle=tk.MITER)

        if hexagon.name:
            label_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LABEL_SIZE, weight='bold')

            self.__canvas.create_text(*label_position, text=hexagon.name, justify=tk.CENTER, font=label_font)

    def __draw_cube(self, name, config, cube_color, cube_sort, cube_label):

        hexagon = GraphicalHexagon.get(name)

        shift_value = 0.20*CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_Y

        top_shift = 0
        bottom_shift = 0

        if hexagon.highlighted_as_stack:
            top_shift = shift_value
            bottom_shift = 1.25*shift_value

        if hexagon.highlighted_as_cube:
            top_shift = shift_value

        cube_vertices = list()

        for vertex_index in range(CANVAS_CONFIG.CUBE_VERTEX_COUNT):
            vertex_angle = (1/2 + vertex_index)*CANVAS_CONFIG.CUBE_SIDE_ANGLE

            if config == CubeLocation.MIDDLE:
                cube_center = hexagon.center

            elif config == CubeLocation.BOTTOM:
                cube_center = hexagon.center - 0.40 * CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_Y + bottom_shift

            elif config == CubeLocation.TOP:
                cube_center = hexagon.center + 0.40 * CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_Y + top_shift

            cube_vertex = cube_center
            cube_vertex = cube_vertex + 0.5*CANVAS_CONFIG.HEXA_SIDE*math.cos(vertex_angle)*CANVAS_CONFIG.UNIT_X
            cube_vertex = cube_vertex + 0.5*CANVAS_CONFIG.HEXA_SIDE*math.sin(vertex_angle)*CANVAS_CONFIG.UNIT_Y

            cube_vertices.append(cube_vertex)

        if cube_color == rules.Player.T.BLACK:
            fill_color = CubeColor.BLACK.value
            face_color = CubeColor.WHITE.value

        elif cube_color == rules.Player.T.WHITE:
            fill_color = CubeColor.WHITE.value
            face_color = CubeColor.BLACK.value

        else:
            assert False

        line_color = ''

        cube_vertex_NW = cube_vertices[1]
        cube_vertex_SE = cube_vertices[3]

        if self.__cube_faces == 'faces=pictures':

            if self.__cube_photos is None:
                self.__create_cube_photos()

            cube_tk_photo = self.__cube_photos[(cube_color, cube_sort)]
            self.__canvas.create_image(cube_center[0], cube_center[1], image=cube_tk_photo, anchor=tk.CENTER)

        elif self.__cube_faces == 'faces=drawings':

            self.__canvas.create_rectangle(*cube_vertex_NW, *cube_vertex_SE,
                                           fill=fill_color,
                                           outline=line_color)
            self.__face_drawers[cube_sort](cube_center, cube_vertices, face_color)

        elif self.__cube_faces == 'faces=letters':

            self.__canvas.create_rectangle(*cube_vertex_NW, *cube_vertex_SE,
                                           fill=fill_color,
                                           outline=line_color)

            face_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_FACE_SIZE, weight='bold')

            self.__canvas.create_text(*cube_center,
                                      text=cube_label,
                                      justify=tk.CENTER,
                                      font=face_font,
                                      fill=face_color)
        else:
            assert False

    def __draw_paper_face(self, cube_center, cube_vertices, face_color):

        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        self.__canvas.create_rectangle(*face_vertex_NW, *face_vertex_SE,
                                       fill='',
                                       outline=face_color,
                                       width=CANVAS_CONFIG.CUBE_LINE_WIDTH)

    def __draw_rock_face(self, cube_center, cube_vertices, face_color):

        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        self.__canvas.create_oval(*face_vertex_NW, *face_vertex_SE,
                                  fill='',
                                  outline=face_color,
                                  width=CANVAS_CONFIG.CUBE_LINE_WIDTH)

    def __draw_scissors_face(self, cube_center, cube_vertices, face_color):

        face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        self.__canvas.create_line(*face_vertex_NE, *face_vertex_SW,
                                  fill=face_color,
                                  width=CANVAS_CONFIG.CUBE_LINE_WIDTH,
                                  capstyle=tk.ROUND)

        self.__canvas.create_line(*face_vertex_NW, *face_vertex_SE,
                                  fill=face_color,
                                  width=CANVAS_CONFIG.CUBE_LINE_WIDTH,
                                  capstyle=tk.ROUND)

    def __sleep_ms(self, duration: float):
        """Sleep duration in milli-seconds"""
        time.sleep(duration/1_000)

    def __draw_wise_face(self, cube_center, cube_vertices, face_color):

        draw_lemniscate = True

        face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        face_vertex_W = 0.5*(face_vertex_NW + face_vertex_SW)

        wise_data = list()

        if draw_lemniscate:

            # -- Equation retrieve from my GeoGebra drawings --
            # Curve(x(C) + (x(C) - x(W)) cos(t) / (1 + sin²(t)),
            #        y(C) + (x(C) - x(W)) cos(t) sin(t) / (1 + sin²(t)),
            #        t, 0, 2π)
            # C : cube_center
            # W : face_vertex_W

            delta = cube_center[0] - face_vertex_W[0]

            angle_count = 200
            for angle_index in range(angle_count):
                angle_value = angle_index*2*math.pi/angle_count

                angle_sinus = math.sin(angle_value)
                angle_cosinus = math.cos(angle_value)

                x = cube_center[0] + delta*angle_cosinus/(1 + angle_sinus**2)
                y = cube_center[1] + delta*angle_cosinus*angle_sinus/(1 + angle_sinus**2)

                wise_data.append(x)
                wise_data.append(y)

        else:
            wise_data.extend(face_vertex_NW)
            wise_data.extend(face_vertex_SE)
            wise_data.extend(face_vertex_NE)
            wise_data.extend(face_vertex_SW)

        self.__canvas.create_polygon(wise_data,
                                     fill='',
                                     outline=face_color,
                                     width=CANVAS_CONFIG.CUBE_LINE_WIDTH,
                                     joinstyle=tk.ROUND,
                                     smooth=True)

def make_ugi_clients():
    ugi_clients = {}

    if False:
        if False:
            cmalo_server_executable_path = os.path.join(_package_home, "ugi-servers", "cmalo", "pijersi_cmalo_ugi_server.exe")
        else:
            cmalo_server_executable_path = os.path.join(_package_home, "pijersi_ugi.py")

        ugi_client = UgiClient(name="ugi-cmalo", server_executable_path=cmalo_server_executable_path)
        ugi_clients[ugi_client.get_name()] = ugi_client


    natsel_server_executable_path = os.path.join(_package_home, "ugi-servers", "natsel", "pijersi_natural_selection_ugi_server_v0.1.0.exe")
    ugi_client = UgiClient(name="natsel", server_executable_path=natsel_server_executable_path)
    ugi_clients[ugi_client.get_name()] = ugi_client
    return ugi_clients


def make_searcher_catalog(ugi_clients):
    searcher_catalog = rules.SearcherCatalog()

    searcher_catalog.add( rules.HumanSearcher("human") )

    if True:
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-time-20s", max_depth=2, time_limit=20) )
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-depth-2", max_depth=2) )
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-time-2mn", max_depth=3, time_limit=2*60) )
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-depth-3", max_depth=3) )
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-time-10mn", max_depth=4, time_limit=10*60) )
        searcher_catalog.add( rules.MinimaxSearcher("cmalo-depth-4", max_depth=4) )

    if True:
        depth_list = [2, 3, 4, 5]
        time_list = [(20, '20s'), (60, '1mn'), (2*60, '2mn'), (10*60, '10mn')]

        for (ugi_client_name, ugi_client) in ugi_clients.items():

            for depth in depth_list:
                depth_searcher_name = f"{ugi_client_name}-depth-{depth}"
                depth_searcher = UgiSearcher(name=depth_searcher_name, ugi_client=ugi_client, max_depth=depth)
                searcher_catalog.add(depth_searcher)

            for (time_limit, time_label) in time_list:
                time_searcher_name = f"{ugi_client_name}-time-{time_label}"
                time_searcher = UgiSearcher(name=time_searcher_name, ugi_client=ugi_client, time_limit=time_limit)
                searcher_catalog.add(time_searcher)

    if False:
        searcher_catalog.add( rules.RandomSearcher("random") )
        searcher_catalog.add( rules.MinimaxSearcher("minimax1", max_depth=1) )

    return searcher_catalog


CANVAS_CONFIG = CanvasConfig()
GraphicalHexagon.init()


def main():
    print(f"Hello from PIJERSI-CERTU-v{rules.__version__}")

    print(64*"-")
    print(_COPYRIGHT_AND_LICENSE)
    print(64*"-")
    print(_COPYRIGHT_AND_LICENSE_NATSEL)
    print(64*"-")

    _ = GameGui()

    print("Bye")


if __name__ == "__main__":
    # >> "freeze_support()" is needed with using pijersi_gui as a single executable made by PyInstaller
    # >> otherwise when starting another process by "PoolExecutor" a second GUI windows is created
    freeze_support()

    main()


    # >> clean any residual process
    if len(multiprocessing.active_children()) > 0:
        print()
        print(f"{len(multiprocessing.active_children())} child processes are still alive")
        print("Terminating child processes ...")
        for child_process in multiprocessing.active_children():
            try:
                child_process.terminate()
            except:
                pass
        print("Terminating child processes done")

    print()
    print("PIJERSI-CERTU: Please close this window which should have closed automatically. Sorry about that ...")

    sys.exit()
