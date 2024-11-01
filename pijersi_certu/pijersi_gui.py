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

_NATSEL_COPYRIGHT_AND_LICENSE = """
Pijersi-rs (Natural Selection) implements an engine for the Pijersi boardgame.

Copyright (C) 2024 Eclypse-Prime (eclypse.prime@gmail.com).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses.
"""

_NATSEL_COPYRIGHT = "(c) 2024 Eclypse-Prime"
_NATSEL_UGI_SERVER_NAME = "pijersi_natural_selection_ugi_server"
_NATSEL_NAME = "Natural Selection"
_NATSEL_KEY = "natsel"
_NATSEL_VERSION = "1.2.0"



import copy
import enum
import sys
import glob
import math
import os
import platform
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


# AI searchers for performing the action review
REVIEW_SUP_SEARCHER = rules.MinimaxSearcher("cmalo-depth-3-sup", max_depth=3)
REVIEW_INF_SEARCHER = rules.MinimaxSearcher("cmalo-depth-1-inf", max_depth=1)

# constant for scoring the action review
REVIEW_MAX_SCORE = 10
REVIEW_MIN_SCORE = 1
REVIEW_OUT_SCORE = 0
REVIEW_UNKNOWN_SCORE = -1



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
        # >> The "scale_factor" is just for experimenting the correctness of sizes computation and drawing methods.
        # >> The actual design for dynamic resize is to use the "resize" method.

        # Canvas x-y dimensions in hexagon width units
        # >> This complex formula is related to the construction of the background picture for the board
        self.NX = 8
        self.NY = (4 + 5/2)*2/math.sqrt(3)

        # Canvas x-y dimensions in pixels
        self.RATIO = self.NX/self.NY
        self.HEIGHT_INITIAL = 640
        self.HEIGHT = self.HEIGHT_INITIAL
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

    def resize(self, scale_factor=1):

        self.HEIGHT = scale_factor*self.HEIGHT_INITIAL
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


class LabelLocation(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


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

    HIGHLIGHT_MOVED_BY_WHITE = 'white'
    HIGHLIGHT_MOVED_BY_BLACK = 'black'


class GraphicalHexagon:

    __all_sorted_hexagons = []
    __init_done = False
    __name_to_hexagon = {}

    all = None

    def __init__(self, hexagon, color, label_location):

        assert hexagon.name not in GraphicalHexagon.__name_to_hexagon
        assert color in HexagonColor

        self.name = hexagon.name
        self.position_uv = hexagon.position_uv
        self.index = hexagon.index
        self.color = color
        self.label_location = label_location

        self.highlighted_as_selectable = False
        self.highlighted_as_cube = False
        self.highlighted_as_stack = False
        self.highlighted_as_destination = False

        # >> played == final hexagon of a player action
        self.highlighted_as_played_by_white = False
        self.highlighted_as_played_by_black = False

        # >> moved == used but not final hexagon of a player action
        self.highlighted_as_moved_by_white = False
        self.highlighted_as_moved_by_black = False

        GraphicalHexagon.__name_to_hexagon[self.name] = self

        self.__compute_center_and_vertices()

    def __compute_center_and_vertices(self):

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
    def resize():
        for hexagon in GraphicalHexagon.all:
            hexagon.__compute_center_and_vertices()

    @staticmethod
    def reset_highlights():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_selectable = False
            hexagon.highlighted_as_cube = False
            hexagon.highlighted_as_stack = False
            hexagon.highlighted_as_destination = False
            hexagon.highlighted_as_played_by_white = False
            hexagon.highlighted_as_played_by_black = False
            hexagon.highlighted_as_moved_by_white = False
            hexagon.highlighted_as_moved_by_black = False

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
    def reset_highlights_as_moved():
        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_as_moved_by_white = False
            hexagon.highlighted_as_moved_by_black = False

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

        left_labels = ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1']
        right_labels = ['a6', 'b7', 'c6', 'd7', 'e6', 'f7', 'g6']

        for hexagon in rules.Hexagon.all:

            if hexagon.name in outer_ring:
                color = HexagonColor.DARK
            elif hexagon.name in inner_ring:
                color = HexagonColor.DARK
            else:
                color = HexagonColor.LIGHT

            if hexagon.name in left_labels:
                label_location = LabelLocation.LEFT
            elif hexagon.name in right_labels:
                label_location = LabelLocation.RIGHT
            else:
                label_location = None

            GraphicalHexagon(hexagon, color, label_location)


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
        self.__cube_resized_tk_photos = None

        self.__cube_faces_options = ("faces=letters", "faces=drawings", "faces=pictures")
        self.__cube_faces = self.__cube_faces_options[2]

        self.__use_background_photo = CANVAS_CONFIG.USE_BACKGROUND_PHOTO
        self.__background_photo = None
        self.__background_tk_resized_photo = None

        # For handling the game review
        self.__review_enabled = True
        self.__review_sup_searcher = REVIEW_SUP_SEARCHER
        self.__review_inf_searcher = REVIEW_INF_SEARCHER
        self.__review_running = False
        self.__review_action_index = None
        self.__review_timer_id = None
        self.__review_timer_delay = 500


        # For handling the GUI resize

        self.__resize_initial_root_width = None
        self.__resize_initial_root_height = None

        self.__resize_current_root_width = None
        self.__resize_current_root_height = None

        self.__resize_initial_canvas_width = None
        self.__resize_initial_canvas_height = None

        self.__resize_preview_photo = None
        self.__resize_scale_factor = None
        self.__resize_time = None
        self.__resize_timer_id = None
        self.__resize_timer_delay = 50
        self.__resize_last_event_is_maximize = False


        self.__legend = ""

        self.__game_timer_delay = 500
        self.__game_timer_id = None

        self.__action_animation_duration = 500

        self.__picture_canvas_delay = 125 # >> without such delay taking picture could be randomly wrong
        self.__picture_gif_duration = 750

        self.__edit_actions = False
        self.__saved_actions_text = ""

        self.__turn_states = list()
        self.__turn_actions = list()
        self.__turn_reviews = list()

        self.__game = None

        self.__game_setup_board_codes_classic = rules.PijersiState.setup_board_codes(rules.Setup.T.CLASSIC)
        self.__game_setup = rules.Setup.T.CLASSIC
        self.__game_setup_board_codes = self.__game_setup_board_codes_classic

        self.__game_time_control = None
        self.__game_time_control_catalog = {}
        self.__game_time_control_catalog["Free time"] = None
        self.__game_time_control_catalog["Max 10 seconds"] = 10
        self.__game_time_control_catalog["Max 30 seconds"] = 30
        self.__game_time_control_catalog["Max 05 minutes"] = 5*60
        self.__game_time_control_catalog["Max 10 minutes"] = 10*60
        self.__game_time_control_catalog["Max 15 minutes"] = 15*60

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
        self.__turn_reviews.append(None)

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

        # >> Fonts cannot be created before the root widget
        self.__time_font = font.Font(family='Courier New', size=16, weight='bold')

        self.__legend_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LEGEND_SIZE, weight='bold')
        self.__label_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LABEL_SIZE, weight='bold')
        self.__face_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_FACE_SIZE, weight='bold')

        title = ( "pijersi-certu for playing the pijersi boardgame and testing AI agents thanks to the UGI protocol" +
                  " ; the rules of the game can be found at https://github.com/LucasBorboleta/pijersi" )

        try:
            self.__root.title(title)
            self.__root.iconbitmap(AppConfig.ICON_FILE)
        except:
            pass

        self.__create_widgets()

        # Update widgets

        self.__draw_state()
        self.__write_setup()

        self.__command_update_players()

        self.__variable_log.set(f"pijersi-certu version {rules.__version__} is ready !")

        summary = "pijersi-certu (c) 2022 Lucas Borboleta"
        if _NATSEL_KEY in self.__ugi_clients:
            summary += f" ; {_NATSEL_NAME} version {_NATSEL_VERSION} {_NATSEL_COPYRIGHT}"
        self.__variable_summary.set(summary)

        if True:
            # Prepare the "GUI resize" feature
            self.__root.resizable(width=True, height=True)

            # >> get and memorize the widgets sizes after being rendered by Tkinter ;
            # >> doing it before is not trustable
            resize_init_delay = 50
            self.__root.after(resize_init_delay, self.__resize_gui_init)

        else:
            # Disable the "GUI resize" feature
            self.__root.resizable(width=False, height=False)

        # Wait events
        self.__root.mainloop()

    def __create_widgets(self):

        searcher_catalog_names = self.__searcher_catalog.get_names()
        searcher_catalog_names_width = max(map(len, searcher_catalog_names)) + 2

        setup_names = rules.Setup.get_names()
        setup_names_width = max(map(len, setup_names))

        time_control_catalog_names = list(sorted(self.__game_time_control_catalog.keys()))
        time_control_catalog_names_width = max([len(x) for x in time_control_catalog_names]) + 1

        self.__style = ttk.Style()
        # >> builtin theme_names()  are ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        # >> default and nice theme is 'vista'
        # >> but 'vista' does not support to change style for TProgressbar
        # >> so 'clam' is used instead, as a second nice choice
        self.__style.theme_use('clam')

        self.__style.configure("PositiveClock.TLabel", foreground='black', font=self.__time_font)
        self.__style.configure("NegativeClock.TLabel", foreground='red', font=self.__time_font)

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
        self.__frame_players.grid(row=0, column=1)

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

        self.__button_review = ttk.Button(self.__frame_commands,
                                                  text='Review',
                                                  command=self.__command_review_start_stop)


        self.__button_new_stop.grid(row=0, column=0)
        self.__button_quit.grid(row=0, column=1)

        self.__button_resume.grid(row=1, column=1)
        if False: # >> postpone the release of the "review" feature
            self.__button_review.grid(row=1, column=0)

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
        self.__variable_white_player.set(searcher_catalog_names[searcher_catalog_names.index("human")])

        self.__button_switch = ttk.Button(self.__frame_players, text='>> Switch <<', width=0, command=self.__command_switch_players)

        self.__label_black_player = ttk.Label(self.__frame_players, text='Black :')

        self.__variable_black_player = tk.StringVar()
        self.__combobox_black_player = ttk.Combobox(self.__frame_players,
                                                    width=searcher_catalog_names_width,
                                                    textvariable=self.__variable_black_player,
                                                    values=searcher_catalog_names)
        self.__combobox_black_player.config(state="readonly")
        self.__variable_black_player.set(searcher_catalog_names[searcher_catalog_names.index("cmalo-depth-2")])

        self.__progressbar = ttk.Progressbar(self.__frame_players,
                                             orient=tk.HORIZONTAL,
                                             length=390,
                                             maximum=100,
                                             mode='determinate')
        self.__progressbar.configure(style="White.Horizontal.TProgressbar")


        self.__variable_white_clock = tk.StringVar()
        self.__label_white_clock = ttk.Label(self.__frame_players, textvariable=self.__variable_white_clock, style="PositiveClock.TLabel")

        self.__variable_black_clock = tk.StringVar()
        self.__label_black_clock = ttk.Label(self.__frame_players, textvariable=self.__variable_black_clock, style="PositiveClock.TLabel")


        self.__variable_time_control = tk.StringVar()
        self.__combobox_time_control = ttk.Combobox(self.__frame_players,
                                                    width=time_control_catalog_names_width,
                                                    textvariable=self.__variable_time_control,
                                                    values=time_control_catalog_names)
        self.__combobox_time_control.config(state="readonly")
        self.__variable_time_control.set([key for (key, value ) in self.__game_time_control_catalog.items() if value == 5*60][0])


        self.__label_white_player.grid(row=0, column=0)
        self.__combobox_white_player.grid(row=0, column=1)

        self.__button_switch.grid(row=0, column=3)

        self.__label_black_player.grid(row=0, column=5)
        self.__combobox_black_player.grid(row=0, column=6)

        self.__progressbar.grid(row=1, column=0, columnspan=7, sticky='we')

        self.__label_white_clock.grid(row=2, column=0, columnspan=2)
        self.__combobox_time_control.grid(row=2, column=3)
        self.__label_black_clock.grid(row=2, column=5, columnspan=2)


        self.__frame_players.rowconfigure(0, pad=5)
        self.__frame_players.rowconfigure(1, pad=5)
        self.__frame_players.columnconfigure(0, pad=5)
        self.__frame_players.columnconfigure(1, pad=5)
        self.__frame_players.columnconfigure(2, pad=2)
        self.__frame_players.columnconfigure(3, pad=5)
        self.__frame_players.columnconfigure(4, pad=5)

        self.__variable_white_player.trace_add('write', self.__command_update_players)
        self.__variable_black_player.trace_add('write', self.__command_update_players)
        self.__variable_time_control.trace_add('write', self.__command_update_time_control)

        self.__update_clocks()

        # In __frame_board

        self.__canvas = tk.Canvas(self.__frame_board,
                                  height=CANVAS_CONFIG.HEIGHT,
                                  width=CANVAS_CONFIG.WIDTH)
        self.__canvas.pack(side=tk.TOP)

        self.__canvas.bind('<Motion>', self.__cmc_update_mouse_over)
        self.__canvas.bind('<Button-1>', self.__cmc_update_mouse_left_click)
        self.__canvas.bind('<Button-3>', self.__cmc_update_mouse_right_click)

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
        self.__button_review.config(state="disabled")
        self.__button_reset_actions.config(state="disabled")

    def __create_cube_photos(self):

        if self.__cube_photos is None:

            self.__cube_photos = {}

            for (key, file) in CubeConfig.CUBE_FILE_PATH.items():
                self.__cube_photos[key] = Image.open(file)


        if self.__cube_resized_tk_photos is None:

            self.__cube_resized_tk_photos = {}

            cube_photo_width = int(CANVAS_CONFIG.HEXA_SIDE*math.cos(math.pi/4))

            for (key, file) in CubeConfig.CUBE_FILE_PATH.items():
                cube_photo = self.__cube_photos[key]
                cube_photo = cube_photo.resize((cube_photo_width, cube_photo_width))
                cube_tk_photo = ImageTk.PhotoImage(cube_photo)
                self.__cube_resized_tk_photos[key] = cube_tk_photo

    def __command_quit(self, *_):

        if self.__concurrent_executor is not None:
            self.__backend_futures = [None for player in rules.Player.T]
            self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
            self.__concurrent_executor = None

        self.__root.destroy()


    def __resize_gui_init(self, *_):

        self.__resize_initial_root_width = self.__root.winfo_width()
        self.__resize_initial_root_height = self.__root.winfo_height()

        self.__resize_current_root_width = self.__resize_initial_root_width
        self.__resize_current_root_height = self.__resize_initial_root_height

        self.__resize_initial_canvas_width = self.__canvas.winfo_width()
        self.__resize_initial_canvas_height = self.__canvas.winfo_height()

        # ensure minimal sizes for the GUI
        self.__root.minsize(width=self.__resize_initial_root_width, height=self.__resize_initial_root_height)

        # react if the GUI is resized
        self.__root.bind("<Configure>", self.__resize_gui_preview)


    def __resize_gui_preview(self, event):

        # filter event not associated with the root widget like event triggered by children of the root widget
        if event.widget != self.__root:
            return

        # the newly requested GUI sizes
        new_root_width = event.width
        new_root_height = event.height

        # filter "moving the window" event from "resizing the window" event
        if new_root_width == self.__resize_current_root_width and new_root_height == self.__resize_current_root_height:
            return

        # compute the scale_factor of the canvas ; the other widgets of the GUI are not (forced to be) scaled
        #
        # Principles:
        #
        #   Notations:
        #       #     (R0w, R0h) : the initial width and height of the root widget
        #       #       (Rw, Rh) : the new width and height of the root widget
        #       #     (C0w, C0h) : the initial width and height of the canvas
        #       # (s*C0w, s*C0h) : the new width and height of the canvas
        #       #              s : the scale factor of the canvas
        #       #     (T0w, T0h) : the initial width and height of the textual widgets
        #       #     (M0w, M0h) : the initial width and height of the margins and paddings
        #
        #   Equations:
        #       # R0w = C0w + T0w + M0w
        #       # R0h = C0h + T0h + M0h
        #
        #       # Rw = s*C0w + Tw + Mw
        #       # Rh = s*C0h + Th + Mh
        #
        #   Requirements:
        #       # (R0w, R0h) is the smallest sizes drawn when the application is launched
        #       # (Tw + Mw) >= (T0w + M0w) so it implies (Rw - s*C0w) >= (R0w -C0w), which implies (1 + (Rw - R0w)/C0w) >= s
        #       # (Th + Mh) >= (T0h + M0h) so it implies (Rh - s*C0h) >= (R0h -C0h), which implies (1 + (Rh - R0h)/C0h) >= s
        #
        #   Conclusions:
        #       # s = min((1 + (Rw - R0w)/C0w), (1 + (Rh - R0h)/C0h))
        #       # s >= 1

        scale_factor_width = 1 + (new_root_width - self.__resize_initial_root_width)/self.__resize_initial_canvas_width
        scale_factor_height = 1 + (new_root_height - self.__resize_initial_root_height)/self.__resize_initial_canvas_height
        scale_factor = min(scale_factor_width, scale_factor_height)

        use_fast_preview = True

        # >> Disable the fast preview for "maximize" and "unmaximze/restore" events:
        # >> - the method "__take_picture" does miss the right coordinates of the canvas, for some misunderstood reasons.
        # >> - but it is OK, because the fast preview is not needed for "maximize" and "unmaximze/restore" events.
        if self.__root.state() == 'zoomed':
            use_fast_preview = False
            self.__resize_last_event_is_maximize = True

        else:
            if self.__resize_last_event_is_maximize:
                # >> should detect unmaximze/restore event
                use_fast_preview = False

            self.__resize_last_event_is_maximize = False


        if use_fast_preview:
            if self.__resize_preview_photo is None:
                self.__resize_preview_photo = self.__take_picture(with_margins=False)

        # >> it seems to fix unstable behavior when unmaximizing
        self.__root.geometry (f"{new_root_width}x{new_root_height}")

        # update the GUI sizes
        self.__resize_current_root_width = new_root_width
        self.__resize_current_root_height = new_root_height

        # update the config data of the canvas
        CANVAS_CONFIG.resize(scale_factor)

        # update the canvas sizes
        self.__canvas.config(width=CANVAS_CONFIG.WIDTH, height=CANVAS_CONFIG.HEIGHT)

        # update font sizes
        self.__legend_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LEGEND_SIZE, weight='bold')
        self.__label_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LABEL_SIZE, weight='bold')
        self.__face_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_FACE_SIZE, weight='bold')

        # >> reset photos to force the update of their sizes
        self.__background_tk_resized_photo = None
        self.__cube_resized_tk_photos = None

        if not use_fast_preview:
            # redraw the canvas

            GraphicalHexagon.resize()
            self.__draw_state()

        else:
            # draw a fast preview of the canvas

            self.__canvas.delete('all')

            bg_photo = self.__resize_preview_photo
            (bg_width, bg_height) = bg_photo.size

            bg_new_width = int(math.ceil(CANVAS_CONFIG.WIDTH))
            bg_new_height = int(math.ceil(CANVAS_CONFIG.WIDTH*bg_height/bg_width))

            bg_photo = bg_photo.resize((bg_new_width, bg_new_height))
            self.__background_tk_resized_photo = ImageTk.PhotoImage(bg_photo)

            self.__background_tk_resized_photo_delta_x = (bg_new_width - CANVAS_CONFIG.WIDTH)/2
            self.__background_tk_resized_photo_delta_y = (bg_new_height - CANVAS_CONFIG.HEIGHT)/2

            self.__canvas.create_image(self.__background_tk_resized_photo_delta_x, self.__background_tk_resized_photo_delta_y,
                                   image=self.__background_tk_resized_photo,
                                   anchor=tk.NW)

            # set data for the finalizer fo the GUI resize
            self.__resize_scale_factor = scale_factor
            self.__resize_time = time.time()

            if self.__resize_timer_id is None:
                self.__resize_timer_id = self.__canvas.after(self.__resize_timer_delay, self.__resize_gui_finalize)


    def __resize_gui_finalize(self):

        if  (time.time() - self.__resize_time)*1000 > self.__resize_timer_delay:

            # update the config data of the canvas
            CANVAS_CONFIG.resize(self.__resize_scale_factor)

            # update the canvas sizes
            self.__canvas.config(width=CANVAS_CONFIG.WIDTH, height=CANVAS_CONFIG.HEIGHT)

            # update font sizes
            self.__legend_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LEGEND_SIZE, weight='bold')
            self.__label_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_LABEL_SIZE, weight='bold')
            self.__face_font = font.Font(family=CANVAS_CONFIG.FONT_FAMILY, size=CANVAS_CONFIG.FONT_FACE_SIZE, weight='bold')

            # >> reset photos to force the update of their sizes
            self.__background_tk_resized_photo = None
            self.__cube_resized_tk_photos = None

            # redraw the canvas
            GraphicalHexagon.resize()
            self.__draw_state()

            # remove fast preview data
            self.__resize_preview_photo = None
            self.__resize_scale_factor = None
            self.__resize_time = None

            # cancel the monitor
            self.__canvas.after_cancel(self.__resize_timer_id)
            self.__resize_timer_id = None
            self.__resize_time = None

        else:
            self.__resize_timer_id = self.__canvas.after(self.__resize_timer_delay, self.__resize_gui_finalize)


    def __command_update_time_control(self, *_):
        self.__game_time_control = self.__game_time_control_catalog.get(self.__variable_time_control.get())

        if self.__game is not None:
            self.__game.set_time_control(self.__game_time_control)

        self.__update_clocks()


    def __command_update_players(self, *_):
        self.__searcher[rules.Player.T.WHITE] = self.__searcher_catalog.get(self.__variable_white_player.get())
        self.__searcher[rules.Player.T.BLACK] = self.__searcher_catalog.get(self.__variable_black_player.get())


    def __command_switch_players(self):
        new_white_player = self.__variable_black_player.get()
        new_black_player = self.__variable_white_player.get()

        self.__variable_white_player.set(new_white_player)
        self.__variable_black_player.set(new_black_player)

        self.__searcher[rules.Player.T.WHITE] = self.__searcher_catalog.get(new_white_player)
        self.__searcher[rules.Player.T.BLACK] = self.__searcher_catalog.get(new_black_player)


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

        self.__button_review.config(state="enabled")

        self.__cmc_reset()
        self.__cmc_hightlight_moved_and_played_hexagons()
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

        self.__turn_reviews = list()
        self.__turn_reviews.append(None)

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
        self.__button_review.config(state="disabled")


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
            self.__button_switch.config(state="disabled")
            self.__combobox_setup.config(state="disabled")

            self.__combobox_time_control.config(state="disabled")

            self.__spinbox_turn.config(state="disabled")
            self.__button_make_pictures.config(state="disabled")

            self.__button_resume.config(state="disabled")
            self.__button_review.config(state="disabled")

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

            # extract actions and scores
            if validated_edited_actions:
                edited_actions = list()
                action_index = 0

                actions_item_index = 0
                while actions_item_index < len(actions_items):
                    action_item = actions_items[actions_item_index]

                    if action_item != str(action_index + 1):
                        validated_edited_actions = False
                        self.__variable_log.set(f"Error: bad index '{action_item}'")
                        break

                    actions_item_index += 1
                    if actions_item_index >= len(actions_items):
                        validated_edited_actions = False
                        self.__variable_log.set(f"Error: missing action at turn '{action_index + 1}'")
                        break

                    action_item = actions_items[actions_item_index]
                    action = action_item.replace("!", "")

                    if rules.Notation.classify_simple_notation(action) == rules.Notation.SimpleCase.INVALID:
                        validated_edited_actions = False
                        self.__variable_log.set(f"Error: invalid notation for action '{action_item}' at turn '{action_index + 1}'")
                        break

                    actions_item_index += 1
                    action_score = None
                    if actions_item_index < len(actions_items):
                        action_item = actions_items[actions_item_index]

                        if action_item == f"?/{REVIEW_MAX_SCORE:02d}":
                            action_score = REVIEW_UNKNOWN_SCORE
                            actions_item_index += 1

                        elif re.match(f"[0-9][0-9]/{REVIEW_MAX_SCORE:02d}", action_item):
                            action_score = int(action_item[:2])
                            actions_item_index += 1

                            if not (REVIEW_OUT_SCORE <= action_score <= REVIEW_MAX_SCORE):
                                validated_edited_actions = False
                                self.__variable_log.set(f"Error: invalid score value '{action_item}' at turn '{action_index + 1}'")
                                break

                        elif re.match(r".*/.*", action_item):
                            validated_edited_actions = False
                            self.__variable_log.set(f"Error: invalid score syntax '{action_item}' at turn '{action_index + 1}'")
                            break

                    action_index += 1

                    edited_actions.append((action, action_score))

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

                self.__turn_reviews = list()
                self.__turn_reviews.append(None)

                self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                self.__variable_turn.set(len(self.__turn_states) - 1)

                for (action_index, (action, action_score)) in enumerate(edited_actions):

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
                    self.__turn_reviews.append(action_score)

                    self.__variable_summary.set(self.__game.get_summary())
                    self.__variable_log.set(self.__game.get_log())

                    self.__text_actions.config(state="normal")

                    turn = self.__game.get_turn()

                    action_name = str(self.__game.get_last_action())

                    action_score = self.__turn_reviews[turn]

                    if action_score is None:
                        action_score_text = ""

                    elif action_score == REVIEW_UNKNOWN_SCORE:
                        action_score_text = f" ?/{REVIEW_MAX_SCORE:02d}"

                    else:
                        action_score_text = f"{action_score:02d}/{REVIEW_MAX_SCORE:02d}"

                    notation = str(turn).rjust(4) + " " + action_name.ljust(10) + " " + action_score_text.ljust(5)
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
                self.__cmc_hightlight_moved_and_played_hexagons()
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
                self.__button_switch.config(state="enabled")
                self.__combobox_setup.config(state="readonly")

                self.__combobox_time_control.config(state="readonly")

                self.__spinbox_turn.config(state="enabled")
                self.__button_make_pictures.config(state="enabled")

                if not self.__game_terminated:
                    self.__button_resume.config(state="enabled")
                else:
                    self.__button_resume.config(state="disabled")

                self.__button_review.config(state="enabled")

            return


    def __command_reset_actions(self):
        self.__text_actions.delete('1.0', tk.END)
        self.__text_actions.insert(tk.END, self.__saved_actions_text)
        self.__variable_log.set("")


    def __command_make_pictures(self):
        if platform.system() != 'Windows':
            self.__variable_log.set(f"Making pictures not implemented for plaform '{platform.system()}'")
            return

        # Disable widgets

        self.__button_quit.config(state="disabled")
        self.__button_new_stop.config(state="disabled")
        self.__combobox_white_player.config(state="disabled")
        self.__combobox_black_player.config(state="disabled")
        self.__button_switch.config(state="disabled")
        self.__combobox_setup.config(state="disabled")

        self.__combobox_time_control.config(state="disabled")

        self.__button_resume.config(state="disabled")
        self.__button_review.config(state="disabled")

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

            GraphicalHexagon.reset_highlights()

            if turn_index != 0:
                pijersi_saved_state = self.__pijersi_state
                self.__pijersi_state = self.__turn_states[turn_index - 1]

                action_simple_name = self.__turn_actions[turn_index].replace("!", "")
                player = rules.Player.T.WHITE if turn_index % 2 == 1 else rules.Player.T.BLACK

                if len(action_simple_name) == 5:
                    src_hex_name = action_simple_name[0:2]
                    src_hex = GraphicalHexagon.get(src_hex_name)

                    if action_simple_name[2] == '-':
                        src_hex.highlighted_as_cube = True
                    else:
                        src_hex.highlighted_as_stack = True

                    if player == rules.Player.T.WHITE:
                        src_hex.highlighted_as_moved_by_white = True
                    else:
                        src_hex.highlighted_as_moved_by_black = True

                    self.__draw_state()
                    self.__canvas.update()
                    self.__sleep_ms(self.__picture_canvas_delay)
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_and_save_picture(animation_png_file)

                elif len(action_simple_name) == 8:
                    intermediate_move = action_simple_name[0:5]

                    src_hex_name = action_simple_name[0:2]
                    src_hex = GraphicalHexagon.get(src_hex_name)

                    int_hex_name = action_simple_name[3:5]
                    int_hex = GraphicalHexagon.get(int_hex_name)

                    if action_simple_name[2] == '-':
                        src_hex.highlighted_as_cube = True
                    else:
                        src_hex.highlighted_as_stack = True

                    if player == rules.Player.T.WHITE:
                        src_hex.highlighted_as_moved_by_white = True
                    else:
                        src_hex.highlighted_as_moved_by_black = True

                    self.__draw_state()
                    self.__canvas.update()
                    self.__sleep_ms(self.__picture_canvas_delay)
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_and_save_picture(animation_png_file)

                    intermediate_action = self.__pijersi_state.get_action_by_simple_name(intermediate_move)
                    self.__pijersi_state = self.__pijersi_state.take_action(intermediate_action)
                    src_hex.highlighted_as_cube = False
                    src_hex.highlighted_as_stack = False

                    if action_simple_name[5] == '-':
                        int_hex.highlighted_as_cube = True
                    else:
                        int_hex.highlighted_as_stack = True

                    if player == rules.Player.T.WHITE:
                        int_hex.highlighted_as_moved_by_white = True
                    else:
                        int_hex.highlighted_as_moved_by_black = True

                    self.__draw_state()
                    self.__canvas.update()
                    self.__sleep_ms(self.__picture_canvas_delay)
                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_and_save_picture(animation_png_file)

                self.__pijersi_state = pijersi_saved_state
                pijersi_saved_state = None

            GraphicalHexagon.reset_highlights_as_cube_or_stack()
            self.__cmc_hightlight_moved_and_played_hexagons()
            self.__draw_state()
            self.__canvas.update()
            self.__sleep_ms(self.__picture_canvas_delay)

            picture_png_file = os.path.join(AppConfig.TMP_PICTURE_DIR, "state-%3.3d" % turn_index) + '.png'
            self.__take_and_save_picture(picture_png_file)

            if turn_index != 0:
                animation_index += 1
            animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
            self.__take_and_save_picture(animation_png_file)

            # simulate thinking and let the reader thinking too
            if animation_index != 0:
                saved_legend = self.__legend
                for pause_index in range(4):
                    self.__legend =  (pause_index + 1 ) *'.' + " " + saved_legend + " " + (pause_index + 1 ) *'.'
                    self.__draw_state()
                    self.__canvas.update()
                    self.__sleep_ms(self.__picture_canvas_delay)

                    animation_index += 1
                    animation_png_file = os.path.join(AppConfig.TMP_ANIMATION_DIR, "state-%3.3d" % animation_index) + '.png'
                    self.__take_and_save_picture(animation_png_file)

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
        self.__button_switch.config(state="enabled")
        self.__combobox_setup.config(state="readonly")

        self.__combobox_time_control.config(state="readonly")

        self.__button_resume.config(state="enabled")
        self.__button_review.config(state="enabled")

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
            self.__game.set_time_control(self.__game_time_control)

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

            self.__turn_reviews = list()
            self.__turn_reviews.append(None)

            self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
            self.__variable_turn.set(len(self.__turn_states) - 1)

            self.__button_new_stop.configure(text="Stop")

            self.__variable_log.set(self.__game.get_log())
            self.__variable_summary.set(self.__game.get_summary())
            self.__progressbar['value'] = 0.

            self.__update_clocks()

            self.__combobox_white_player.config(state="disabled")
            self.__combobox_black_player.config(state="disabled")
            self.__button_switch.config(state="disabled")
            self.__combobox_setup.config(state="disabled")

            self.__combobox_time_control.config(state="disabled")

            self.__spinbox_turn.config(state="disabled")

            self.__text_actions.config(state="normal")
            self.__text_actions.delete('1.0', tk.END)
            self.__text_actions.config(state="disabled")
            self.__write_setup()

            self.__button_edit_actions.config(state="disabled")
            self.__button_make_pictures.config(state="disabled")

            self.__button_resume.config(state="disabled")
            self.__button_review.config(state="disabled")

            self.__cmc_reset()
            self.__draw_state()

            self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        elif self.__game_played:

            self.__game_played = False
            self.__game_terminated = not self.__game.has_next_turn()

            self.__game.set_turn_start(None)
            self.__game.set_turn_end(None)

            if self.__concurrent_executor is not None:
                self.__backend_futures = [None for player in rules.Player.T]
                self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
                self.__concurrent_executor = None

            self.__button_new_stop.configure(text="New")

            self.__variable_log.set("Game stopped")
            self.__progressbar['value'] = 0.

            self.__update_clocks()

            self.__combobox_white_player.config(state="readonly")
            self.__combobox_black_player.config(state="readonly")
            self.__button_switch.config(state="enabled")
            self.__combobox_setup.config(state="readonly")

            self.__combobox_time_control.config(state="readonly")

            self.__spinbox_turn.config(state="enabled")

            self.__variable_action.set("")

            self.__button_edit_actions.config(state="enabled")
            self.__button_make_pictures.config(state="enabled")

            if not self.__game_terminated:
                self.__button_resume.config(state="enabled")
            else:
                self.__button_resume.config(state="disabled")

            self.__button_review.config(state="enabled")

            self.__cmc_reset()
            self.__cmc_hightlight_moved_and_played_hexagons()
            self.__draw_state()


    def __command_resume(self):

        # like "__command_edit_actions" but driven by the actual action list, possibly made shorter.

        resume_turn_index = int(self.__variable_turn.get())
        resume_actions = self.__turn_actions[1: resume_turn_index + 1]

        self.__text_actions.config(state="normal")
        self.__text_actions.delete('1.0', tk.END)
        self.__text_actions.config(state="disabled")

        self.__write_setup()

        turn_durations = self.__game.get_turn_durations()
        resume_turn_durations = {rules.Player.T.WHITE:[], rules.Player.T.BLACK:[]}
        if resume_turn_index != 0:

            if resume_turn_index % 2 == 0:
                resume_turn_durations[rules.Player.T.BLACK] = turn_durations[rules.Player.T.BLACK][:resume_turn_index//2]
                resume_turn_durations[rules.Player.T.WHITE] = turn_durations[rules.Player.T.WHITE][:resume_turn_index//2]

            elif resume_turn_index % 2 == 1:
                resume_turn_durations[rules.Player.T.WHITE] = turn_durations[rules.Player.T.WHITE][:resume_turn_index//2 + 1]
                resume_turn_durations[rules.Player.T.BLACK] = turn_durations[rules.Player.T.BLACK][:resume_turn_index//2]

        # interpret actions

        self.__variable_setup.set(rules.Setup.to_name(self.__game_setup))

        self.__game = rules.Game(setup=self.__game_setup, board_codes=self.__game_setup_board_codes)
        self.__game.set_time_control(self.__game_time_control)

        white_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.WHITE].get_name())
        black_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.BLACK].get_name())

        self.__game.set_white_searcher(white_replayer)
        self.__game.set_black_searcher(black_replayer)

        self.__game.start()

        self.__turn_states = list()
        self.__turn_states.append(self.__game.get_state())

        self.__turn_actions = list()
        self.__turn_actions.append("")

        self.__turn_reviews = self.__turn_reviews[0: resume_turn_index + 1]

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

            action_name = str(self.__game.get_last_action())

            action_score = self.__turn_reviews[turn]

            if action_score is None:
                action_score_text = ""

            elif action_score == REVIEW_UNKNOWN_SCORE:
                action_score_text = f" ?/{REVIEW_MAX_SCORE:02d}"

            else:
                action_score_text = f"{action_score:02d}/{REVIEW_MAX_SCORE:02d}"

            notation = str(turn).rjust(4) + " " + action_name.ljust(10) + " " + action_score_text.ljust(5)
            if turn % 2 == 0:
                notation = ' '*2 + notation + "\n"

            self.__text_actions.insert(tk.END, notation)
            self.__text_actions.see(tk.END)
            self.__text_actions.config(state="disabled")

        assert self.__game.has_next_turn()

        self.__game.set_turn_durations(resume_turn_durations)

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
        self.__cmc_hightlight_moved_and_played_hexagons()
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
        self.__button_switch.config(state="disabled")
        self.__combobox_setup.config(state="disabled")

        self.__combobox_time_control.config(state="disabled")

        self.__spinbox_turn.config(state="disabled")

        self.__text_actions.config(state="disabled")

        self.__button_edit_actions.config(state="disabled")
        self.__button_make_pictures.config(state="disabled")

        self.__button_resume.config(state="disabled")
        self.__button_review.config(state="disabled")

        # start timer
        self.__game.set_turn_start(time.time())
        self.__game.set_turn_end(None)

        # watch next turn
        self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)


    def __command_review_start_stop(self):

        if not self.__review_enabled:
            return

        if not self.__review_running:

            # Disable widgets

            self.__button_new_stop.config(state="disabled")
            self.__combobox_white_player.config(state="disabled")
            self.__combobox_black_player.config(state="disabled")
            self.__button_switch.config(state="disabled")
            self.__combobox_setup.config(state="disabled")

            self.__combobox_time_control.config(state="disabled")

            self.__spinbox_turn.config(state="disabled")
            self.__button_make_pictures.config(state="disabled")

            self.__button_resume.config(state="disabled")

            self.__button_review.configure(text="Stop")

            # review the first not yet review action
            self.__review_running = True
            self.__command_review_update()

        elif self.__review_running:
            # finalize the review
            self.__review_running = False
            self.__command_review_update()


    def __command_review_update(self):

        # Compute a score for the first not yet reviewed action

        assert len(self.__turn_reviews) == len(self.__turn_actions)
        assert len(self.__turn_reviews) == len(self.__turn_states)

        self.__review_action_index = None

        if self.__review_running:

            for (action_index, action) in enumerate(self.__turn_actions):
                if action_index == 0:
                    continue

                if self.__turn_reviews[action_index] is not None:
                    continue

                self.__review_action_index = action_index
                break

        if self.__review_action_index is not None:

            self.__variable_log.set(f"action {self.__review_action_index} review ...")
            self.__label_log.update()

            action_score = self.__review_evaluate_action_score(action_name=str(action), pijersi_state=self.__turn_states[action_index - 1])
            self.__turn_reviews[self.__review_action_index] = action_score

            # Show the score of each reviewed action

            self.__text_actions.config(state="normal")
            self.__text_actions.delete('1.0', tk.END)
            self.__text_actions.config(state="disabled")

            self.__write_setup()

            for (action_index, action) in enumerate(self.__turn_actions):

                if action_index == 0:
                    continue
                turn = action_index

                action_name = str(action)

                action_score = self.__turn_reviews[turn]

                if action_score is None:
                    action_score_text = ""

                elif action_score == REVIEW_UNKNOWN_SCORE:
                    action_score_text = f" ?/{REVIEW_MAX_SCORE:02d}"

                else:
                    action_score_text = f"{action_score:02d}/{REVIEW_MAX_SCORE:02d}"

                notation = str(turn).rjust(4) + " " + action_name.ljust(10) + " " + action_score_text.ljust(5)
                if turn % 2 == 0:
                    notation = ' '*2 + notation + "\n"

                self.__text_actions.config(state="normal")
                self.__text_actions.insert(tk.END, notation)
                self.__text_actions.see(tk.END)
                self.__text_actions.config(state="disabled")

            self.__variable_log.set(f"action {self.__review_action_index} review done")
            self.__review_action_index = None

            if self.__review_running:
                self.__review_timer_id = self.__root.after(self.__review_timer_delay, self.__command_review_update)

        elif self.__review_action_index is  None:

            # compute and show simple statistics
            white_reviews = self.__turn_reviews[1::2]
            black_reviews = self.__turn_reviews[2::2]

            white_scores = [score for score in white_reviews if score is not None and score != -1]
            white_score_ave = int(sum(white_scores)/len(white_scores)) if len(white_scores) != 0 else '*'

            black_scores = [score for score in black_reviews if score is not None and score != -1]
            black_score_ave = int(sum(black_scores)/len(black_scores)) if len(black_scores) != 0 else '*'

            if self.__review_running:
                self.__variable_log.set(f"review completed ; white  average={white_score_ave}  /  black  average={black_score_ave}")
            else:
                self.__variable_log.set(f"review stopped ; white  average={white_score_ave}  /  black  average={black_score_ave}")

            self.__review_running = False

        if not self.__review_running:

            # Enable widgets

            self.__button_new_stop.config(state="enabled")
            self.__combobox_white_player.config(state="readonly")
            self.__combobox_black_player.config(state="readonly")
            self.__button_switch.config(state="enabled")
            self.__combobox_setup.config(state="readonly")

            self.__combobox_time_control.config(state="readonly")

            self.__spinbox_turn.config(state="enabled")
            self.__button_make_pictures.config(state="enabled")

            if not self.__game_terminated:
                self.__button_resume.config(state="enabled")
            else:
                self.__button_resume.config(state="disabled")

            self.__button_review.configure(text="Review")

            if self.__review_timer_id is not None:
                self.__root.after_cancel(self.__review_timer_id)
                self.__review_timer_id = None


    def __review_evaluate_action_score(self, action_name, pijersi_state):

        # >> The score of the reviewed action is based on its rank from a reference AI "review_sup_searcher".
        # >> The second AI "review_inf_searcher" is used to ignore very poor actions.
        # >> Since this review algorithm relies on ranks, it should work with any chosen pair of "review_sup_searcher" and "review_inf_searcher".

        # retrieve the evaluations by the two "sup" and "inf" AI
        sup_evaluated_actions = self.__review_sup_searcher.evaluate_actions(pijersi_state)
        inf_evaluated_actions = self.__review_inf_searcher.evaluate_actions(pijersi_state)

        # make a mapping "action -> rank" that ensures that equal values have equal ranks
        sup_ranks_by_actions = {}
        sup_unique_values = list(set(sup_evaluated_actions.values()))
        sup_unique_values.sort()
        for (sup_action_name, sup_action_value) in sup_evaluated_actions.items():
            sup_action_simple_name = sup_action_name.replace('!', '')
            sup_ranks_by_actions[sup_action_simple_name] = sup_unique_values.index(sup_action_value) + 1

        # evalute the "sup_rank"
        sup_rank = len(sup_unique_values)

        # evalute the "inf_rank": the average of all "inf" actions with max "inf" values
        inf_unique_values = list(set(inf_evaluated_actions.values()))
        inf_max_value = max(inf_unique_values)

        inf_ranks = []
        for (inf_action_name, inf_action_value) in inf_evaluated_actions.items():
            if inf_action_value == inf_max_value:
                inf_action_simple_name = inf_action_name.replace('!', '')
                if inf_action_simple_name in sup_ranks_by_actions:
                    inf_ranks.append(sup_ranks_by_actions[inf_action_simple_name])

        if len(inf_ranks) != 0:
            inf_rank = max(1, int(sum(inf_ranks)/len(inf_ranks)))
        else:
            inf_rank = 1

        # evalute the "action_rank" and deduces the "action_score"

        action_simple_name = action_name.replace('!', '')

        if action_simple_name not in sup_ranks_by_actions:
            action_score = REVIEW_UNKNOWN_SCORE

        else:
            action_rank = sup_ranks_by_actions[action_simple_name]

            if action_rank < inf_rank :
                action_score = REVIEW_MAX_SCORE

            elif inf_rank == sup_rank:

                if action_rank == inf_rank:
                    action_score = REVIEW_MAX_SCORE
                else:
                    action_score = REVIEW_OUT_SCORE
            else:
                # linearly maps [inf_rank, sup_rank] into [REVIEW_MIN_SCORE, REVIEW_MAX_SCORE]
                action_score = int( (action_rank - inf_rank)/(sup_rank - inf_rank)*REVIEW_MAX_SCORE +
                                    (sup_rank - action_rank)/(sup_rank - inf_rank)*REVIEW_MIN_SCORE )

        return action_score

    def __command_next_turn(self):

        if self.__game_timer_id is not None:
            self.__canvas.after_cancel(self.__game_timer_id)
            self.__game_timer_id = None

        if not self.__game.has_next_turn():
          self.__game.set_turn_end(time.time())

        self.__update_clocks()

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


                    # Cinematic for AI action: begin
                    # !! idea and prototype by MarcLeclere

                    # >> Handling 'stop' while displaying the cinematic causes error
                    # >> So let disable such event
                    self.__button_new_stop.config(state="disabled")

                    GraphicalHexagon.reset_highlights()

                    if len(action_simple_name) == 5:
                        src_hex_name = action_simple_name[0:2]
                        src_hex = GraphicalHexagon.get(src_hex_name)

                        if action_simple_name[2] == '-':
                            src_hex.highlighted_as_cube = True
                        else:
                            src_hex.highlighted_as_stack = True

                        if player == rules.Player.T.WHITE:
                            src_hex.highlighted_as_moved_by_white = True
                        else:
                            src_hex.highlighted_as_moved_by_black = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                    elif len(action_simple_name) == 8:
                        pijersi_saved_state = self.__pijersi_state
                        intermediate_move = action_simple_name[0:5]

                        src_hex_name = action_simple_name[0:2]
                        src_hex = GraphicalHexagon.get(src_hex_name)

                        int_hex_name = action_simple_name[3:5]
                        int_hex = GraphicalHexagon.get(int_hex_name)

                        dst_hex_name = action_simple_name[6:8]
                        dst_hex = GraphicalHexagon.get(dst_hex_name)

                        if action_simple_name[2] == '-':
                            src_hex.highlighted_as_cube = True
                        else:
                            src_hex.highlighted_as_stack = True

                        if player == rules.Player.T.WHITE:
                            src_hex.highlighted_as_moved_by_white = True
                        else:
                            src_hex.highlighted_as_moved_by_black = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        if player == rules.Player.T.WHITE:
                            int_hex.highlighted_as_moved_by_white = True
                        else:
                            int_hex.highlighted_as_moved_by_black = True

                        intermediate_action = self.__pijersi_state.get_action_by_simple_name(intermediate_move)
                        self.__pijersi_state = self.__pijersi_state.take_action(intermediate_action)
                        src_hex.highlighted_as_cube = False
                        src_hex.highlighted_as_stack = False

                        if action_simple_name[5] == '-':
                            int_hex.highlighted_as_cube = True
                        else:
                            int_hex.highlighted_as_stack = True

                        self.__draw_state()
                        self.__canvas.update()
                        self.__sleep_ms(self.__action_animation_duration)

                        if src_hex == dst_hex:
                            if player == rules.Player.T.WHITE:
                                src_hex.highlighted_as_moved_by_white = False
                            else:
                                src_hex.highlighted_as_moved_by_black = False

                        self.__pijersi_state = pijersi_saved_state
                        pijersi_saved_state = None

                    self.__button_new_stop.config(state="enabled")

                    # Cinematic for AI action: end

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
                self.__update_clocks()

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
                self.__turn_reviews.append(None)
                self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                self.__variable_turn.set(len(self.__turn_states) - 1)

                self.__cmc_reset()
                self.__cmc_hightlight_moved_and_played_hexagons()
                self.__draw_state()

            self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        else:

            self.__game_played = False
            self.__game_terminated = True

            # >> finalize the game when time control is used
            self.__pijersi_state = self.__game.get_state()
            if not self.__pijersi_state.is_terminal() and self.__game_time_control is not None:
                self.__game.next_turn()

            self.__update_clocks()

            self.__variable_summary.set(self.__game.get_summary())
            self.__variable_log.set(self.__game.get_log())

            if self.__game.get_turn() > 0:
                self.__legend = str(self.__game.get_turn()) + " " + self.__game.get_last_action() + " "

            self.__legend += self.__make_legend_score(self.__pijersi_state)


            self.__cmc_reset()
            self.__cmc_hightlight_moved_and_played_hexagons()
            self.__draw_state()

            self.__backend_futures = [None for player in rules.Player.T]
            if self.__concurrent_executor is not None:
                self.__concurrent_executor.shutdown(wait=False, cancel_futures=True)
            self.__concurrent_executor = None

            self.__button_new_stop.configure(text="New")

            self.__combobox_white_player.config(state="readonly")
            self.__combobox_black_player.config(state="readonly")
            self.__button_switch.config(state="enabled")
            self.__combobox_setup.config(state="readonly")

            self.__combobox_time_control.config(state="readonly")

            self.__spinbox_turn.config(state="enabled")

            self.__progressbar['value'] = 0.

            self.__button_edit_actions.config(state="enabled")
            self.__button_make_pictures.config(state="enabled")
            self.__button_review.config(state="enabled")


    def __update_clocks(self):

        def format_clock(clock_float):
            clock_int = round(math.fabs(clock_float))
            clock_sec = clock_int % 60
            clock_min = clock_int // 60

            clock_sign = '' if clock_float >= 0 else '-'

            if clock_min < 100:
                return f"{clock_sign}{clock_min:02d}:{clock_sec:02d}"
            else:
                return f"{clock_sign}{clock_min}:{clock_sec:02d}"

        if self.__game is not None:
            (white_clock, black_clock) = self.__game.get_clocks()

        else:
            if self.__game_time_control is None:
                (white_clock, black_clock) = (0, 0)
            else:
                (white_clock, black_clock) = (self.__game_time_control, self.__game_time_control)

        self.__variable_white_clock.set('\u23F1' + format_clock(white_clock))
        self.__variable_black_clock.set('\u23F1' + format_clock(black_clock))

        if round(white_clock) >= 0:
            self.__label_white_clock.configure(style="PositiveClock.TLabel")
        else:
            self.__label_white_clock.configure(style="NegativeClock.TLabel")

        if round(black_clock) >= 0:
            self.__label_black_clock.configure(style="PositiveClock.TLabel")
        else:
            self.__label_black_clock.configure(style="NegativeClock.TLabel")


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

    def __cmc_update_mouse_right_click(self, event):
        """ The CMC process is reset and the canvas is restored, as if user does not click on a legal hexagon"""

        self.__cmc_reset()
        self.__cmc_hightlight_moved_and_played_hexagons()
        self.__draw_state()
        self.__cmc_hexagon_at_over = None
        self.__cmc_update_mouse_over(event)

    def __cmc_update_mouse_left_click(self, event):
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
            self.__cmc_update_mouse_left_click_1(event)

        elif self.__cmc_state is CMCState.SELECTING_2:
            self.__cmc_update_mouse_left_click_2(event)

        elif self.__cmc_state is CMCState.SELECTING_3:
            self.__cmc_update_mouse_left_click_3(event)

    def __cmc_update_mouse_left_click_1(self, event):
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
            self.__cmc_hightlight_moved_and_played_hexagons()

        self.__draw_state()

    def __cmc_update_mouse_left_click_2(self, event):
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
            self.__cmc_hightlight_moved_and_played_hexagons()
            self.__draw_state()
            self.__cmc_hexagon_at_over = None
            self.__cmc_update_mouse_over(event)
            return

        self.__draw_state()

    def __cmc_update_mouse_left_click_3(self, event):
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
            self.__cmc_hightlight_moved_and_played_hexagons()
            self.__draw_state()
            self.__cmc_hexagon_at_over = None
            self.__cmc_update_mouse_over(event)
            return

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
        self.__cmc_hightlight_moved_and_played_hexagons()


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

    def __cmc_hightlight_moved_and_played_hexagons(self):
        """
        Mark moved and played hexagons
        """

        GraphicalHexagon.reset_highlights_as_moved()
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
            (moved_hexagons, played_hexagon) = self.__get_moved_and_played_hexagons(played_action_name)

            if player_index == 0:
                if played_hexagon is not None:
                    played_hexagon.highlighted_as_played_by_white = True

                for hexagon in moved_hexagons:
                    hexagon.highlighted_as_moved_by_white = True

            elif player_index == 1:
                if played_hexagon is not None:
                    played_hexagon.highlighted_as_played_by_black = True

                for hexagon in moved_hexagons:
                    hexagon.highlighted_as_moved_by_black = True

    def __get_moved_and_played_hexagons(self, action_name):
        moved_hexagons = []
        played_hexagon = None

        action_positions = action_name.replace("!", "").replace("-", "").replace("=", "")
        hexagon_names = [x + y for (x, y) in zip(action_positions[:-1:2], action_positions[1::2])]

        if len(hexagon_names) == 2:
            moved_hexagons = [GraphicalHexagon.get(hexagon_names[0])]
            played_hexagon = GraphicalHexagon.get(hexagon_names[1])

        elif len(hexagon_names) == 3:
            moved_hexagons = [GraphicalHexagon.get(hexagon_names[0]), GraphicalHexagon.get(hexagon_names[1])]
            played_hexagon = GraphicalHexagon.get(hexagon_names[2])

            if moved_hexagons[0] == played_hexagon:
                moved_hexagons = moved_hexagons[1:]

        return (moved_hexagons, played_hexagon)

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
        (white_clock, black_clock) = self.__game.get_clocks()

        if ((rewards is not None and rewards[rules.Player.T.WHITE] == rules.Reward.WIN) or
            (self.__game_time_control is not None and black_clock < 0)):
            legend_score = "1-0"

        elif ((rewards is not None and rewards[rules.Player.T.BLACK] == rules.Reward.WIN) or
              (self.__game_time_control is not None and white_clock < 0)):
            legend_score = "0-1"

        elif rewards[rules.Player.T.WHITE] == rules.Reward.DRAW:
            legend_score = "½-½"

        else:
            legend_score = ""

        return legend_score


    def __take_and_save_picture(self, picture_file: str):
        picture = self.__take_picture()
        picture.save(picture_file)


    def __take_picture(self, with_margins=True):
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
                upper += self.__background_tk_resized_photo_delta_y
                lower -= self.__background_tk_resized_photo_delta_y

                if with_margins:
                    left += self.__background_tk_resized_photo_delta_x
                    right -= self.__background_tk_resized_photo_delta_x

                    upper += int(0.01*h)
                    lower -= int(0.01*h)

                    left += int(0.01*w)
                    right -= int(0.01*w)

            picture_bbox = (left, upper, right, lower)

        else:
            picture_bbox = None

        # >> all_screens – Capture all monitors. Windows OS only
        picture = ImageGrab.grab(bbox=picture_bbox, all_screens=True)
        return picture

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

        if self.__background_photo is None:
            self.__background_photo = Image.open(CANVAS_CONFIG.BACKGROUND_PHOTO_PATH)

        if self.__background_tk_resized_photo is None:

            # Create the background image
            bg_photo = self.__background_photo
            (bg_width, bg_height) = bg_photo.size

            bg_new_width = int(math.ceil(CANVAS_CONFIG.WIDTH))
            bg_new_height = int(math.ceil(CANVAS_CONFIG.WIDTH*bg_height/bg_width))

            bg_photo = bg_photo.resize((bg_new_width, bg_new_height))
            self.__background_tk_resized_photo = ImageTk.PhotoImage(bg_photo)

            self.__background_tk_resized_photo_delta_x = (bg_new_width - CANVAS_CONFIG.WIDTH)/2
            self.__background_tk_resized_photo_delta_y = (bg_new_height - CANVAS_CONFIG.HEIGHT)/2

        # Add the background image
        self.__canvas.create_image(self.__background_tk_resized_photo_delta_x, self.__background_tk_resized_photo_delta_y,
                                   image=self.__background_tk_resized_photo,
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

        self.__canvas.create_text(*legend_position, text=self.__legend, justify=tk.CENTER,
                                  font=self.__legend_font, fill=CANVAS_CONFIG.FONT_LEGEND_COLOR)

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

        if hexagon.label_location is LabelLocation.LEFT:
            label_position = hexagon.center - 1.15*CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_X

        elif hexagon.label_location is LabelLocation.RIGHT:
            label_position = hexagon.center + 1.15*CANVAS_CONFIG.HEXA_SIDE*CANVAS_CONFIG.UNIT_X

        else:
            label_position = None

        if self.__use_background_photo:
            polygon_line_color = ''
            fill_color = ''

        else:
            polygon_line_color = HexagonLineColor.NORMAL.value
            fill_color = hexagon.color.value

        line_width_scaling = 1.0

        # played parameters
        line_dash_played_width_scaling = 4.0

        # moved parameters
        if False:
            # using dashed line
            line_dash_moved_width_scaling = 2.25
            line_dash_pattern = (int(CANVAS_CONFIG.HEXA_SIDE*0.5), int(CANVAS_CONFIG.HEXA_SIDE*0.5))
        else:
            # using thiner line
            line_dash_moved_width_scaling = 1.5
            line_dash_pattern = None

        line_dash = None

        # Respect priority order in lighting

        if hexagon.highlighted_as_destination:
            fill_color = HexagonColor.HIGHLIGHT_DESTINATION_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_selectable:
            fill_color = HexagonColor.HIGHLIGHT_SOURCE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_cube:
            fill_color = HexagonColor.HIGHLIGHT_CUBE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_stack:
            fill_color = HexagonColor.HIGHLIGHT_STACK_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_as_moved_by_white:
            polygon_line_color = HexagonLineColor.HIGHLIGHT_MOVED_BY_WHITE.value
            line_dash = line_dash_pattern
            line_width_scaling = line_dash_moved_width_scaling

        elif hexagon.highlighted_as_moved_by_black:
            polygon_line_color = HexagonLineColor.HIGHLIGHT_MOVED_BY_BLACK.value
            line_dash = line_dash_pattern
            line_width_scaling = line_dash_moved_width_scaling

        if hexagon.highlighted_as_played_by_white:
            polygon_line_color = HexagonLineColor.HIGHLIGHT_PLAYED_BY_WHITE.value
            line_width_scaling = line_dash_played_width_scaling
            line_dash = None

        elif hexagon.highlighted_as_played_by_black:
            polygon_line_color = HexagonLineColor.HIGHLIGHT_PLAYED_BY_BLACK.value
            line_width_scaling = line_dash_played_width_scaling
            line_dash = None

        self.__canvas.create_polygon(hexagon.vertex_data,
                                     fill=fill_color,
                                     outline=polygon_line_color,
                                     width=CANVAS_CONFIG.HEXA_LINE_WIDTH*line_width_scaling,
                                     joinstyle=tk.MITER,
                                     dash=line_dash,
                                     stipple='gray50')

        if label_position is not None:
            self.__canvas.create_text(*label_position, text=hexagon.name, justify=tk.CENTER, font=self.__label_font)

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

            if self.__cube_resized_tk_photos is None:
                self.__create_cube_photos()

            cube_tk_photo = self.__cube_resized_tk_photos[(cube_color, cube_sort)]
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

            self.__canvas.create_text(*cube_center,
                                      text=cube_label,
                                      justify=tk.CENTER,
                                      font=self.__face_font,
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
            cmalo_server_executable_path = os.path.join(_package_home, "ugi-servers",
                                                        "cmalo",
                                                        f"pijersi_cmalo_ugi_server_v{rules.__version__}" + "_" + make_artefact_platform_id())
        else:
            cmalo_server_executable_path = os.path.join(_package_home, "pijersi_ugi.py")

        if os.path.isfile(cmalo_server_executable_path):
            ugi_client = UgiClient(name="ugi-cmalo", server_executable_path=cmalo_server_executable_path)
            ugi_clients[ugi_client.get_name()] = ugi_client


    natsel_server_executable_path = os.path.join(_package_home, "ugi-servers",
                                                 _NATSEL_KEY,
                                                 f"{_NATSEL_UGI_SERVER_NAME}_v{_NATSEL_VERSION}" + "_" + make_artefact_platform_id())

    if os.path.isfile(natsel_server_executable_path):
        ugi_client = UgiClient(name=_NATSEL_KEY, server_executable_path=natsel_server_executable_path)
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
        depth_list = [2, 3, 4, 5, 6]
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


def make_artefact_platform_id():
    artefact_system = platform.system().lower()
    artefact_extension = ".exe" if artefact_system == "windows" else ""

    artefact_machine = platform.machine()
    if re.match(r"^.*64.*$", platform.machine()):
        artefact_machine = "x86_64"

    artefact_platform_id = f"{artefact_system}_{artefact_machine}{artefact_extension}"

    return artefact_platform_id


CANVAS_CONFIG = CanvasConfig()
GraphicalHexagon.init()


def main():
    print(f"Hello from PIJERSI-CERTU-v{rules.__version__}")

    print(64*"-")
    print(_COPYRIGHT_AND_LICENSE)
    print(64*"-")
    print(_NATSEL_COPYRIGHT_AND_LICENSE)
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
