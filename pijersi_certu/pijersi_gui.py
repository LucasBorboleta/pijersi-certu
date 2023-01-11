#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_gui.py implements a GUI for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rule engine for the PIJERSI boardgame.

Copyright (C) 2022 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""


import enum
import glob
import math
import os
import shutil
import sys
import copy

from PIL import Image
from PIL import ImageTk
from PIL import ImageGrab

import tkinter as tk
from tkinter import font
from tkinter import ttk


_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)
import pijersi_rules as rules


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
        return TinyVector((-self.__x , -self.__y))


    def __pos__(self):
        return TinyVector((self.__x , self.__y))


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

    # Canvas x-y dimensions in hexagon width units
    # >> This complex formula is related to the construction of the background picture for the board
    NX = 8
    NY = (4 + 5/2)*2/math.sqrt(3)

    # Canvas x-y dimensions in pixels
    RATIO = NX/NY
    HEIGHT = 640
    WIDTH = HEIGHT*RATIO

    # Canvas background
    USE_BACKGROUND_PHOTO = True
    BACKGROUND_PHOTO_PATH = os.path.join(_package_home, 'pictures', 'pijersi-board.png')

    # Hexagon geometrical data
    HEXA_VERTEX_COUNT = 6
    HEXA_SIDE_ANGLE = 2*math.pi/HEXA_VERTEX_COUNT
    HEXA_WIDTH = WIDTH/NX
    HEXA_SIDE = HEXA_WIDTH*math.tan(HEXA_SIDE_ANGLE/2)
    HEXA_DELTA_Y = math.sqrt(HEXA_SIDE**2 -(HEXA_WIDTH/2)**2)
    HEXA_COS_SIDE_ANGLE = math.cos(HEXA_SIDE_ANGLE)
    HEXA_SIN_SIDE_ANGLE = math.sin(HEXA_SIDE_ANGLE)

    # Cube (square) geometrical data
    CUBE_VERTEX_COUNT = 4
    CUBE_SIDE_ANGLE = math.pi/2

    # Font used for text in the canvas
    FONT_FAMILY = 'Calibri'
    FONT_LABEL_SIZE = int(0.30*HEXA_SIDE) # size for 'e5', 'f5' ...
    FONT_FACE_SIZE = int(0.50*HEXA_SIDE)  # size for 'K', 'F' ...
    FONT_LEGEND_SIZE = int(0.60*HEXA_SIDE) # size for 'a1-a2!=a3!' ...
    FONT_LEGEND_COLOR = rgb_color_as_hexadecimal((166, 109, 60))


    # Geometrical line widths
    CUBE_LINE_WIDTH = 1
    HEXA_LINE_WIDTH = 1

    # Origin of the orthonormal x-y frame and the oblic u-v frame
    ORIGIN = TinyVector((WIDTH/2, HEIGHT/2))

    # Unit vectors of the orthonormal x-y frame
    UNIT_X = TinyVector((1, 0))
    UNIT_Y = TinyVector((0, -1))

    # Unit vectors of the oblic u-v frame
    UNIT_U = UNIT_X
    UNIT_V = HEXA_COS_SIDE_ANGLE*UNIT_X + HEXA_SIN_SIDE_ANGLE*UNIT_Y


class CubeConfig:
    # File path containing the icon to be displayed in the title bar of Pijersi GUI

    __cube_file_name = {}

    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.WISE)] = 'wise-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.ROCK)] = 'rock-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.PAPER)] = 'paper-black.png'
    __cube_file_name[(rules.Player.T.BLACK, rules.Cube.T.SCISSORS)] = 'scissors-black.png'

    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.WISE)] = 'wise-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.ROCK)] = 'rock-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.PAPER)] = 'paper-white.png'
    __cube_file_name[(rules.Player.T.WHITE, rules.Cube.T.SCISSORS)] = 'scissors-white.png'

    CUBE_FILE_PATH = {}

    for (file_key, file_name) in __cube_file_name.items():
        CUBE_FILE_PATH[file_key] =os.path.join(_package_home, 'pictures', file_name)


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

    # Marc-theme-1
    # HIGHLIGHT_SOURCE_SELECTION = rgb_color_as_hexadecimal((255, 255, 200))
    # HIGHLIGHT_DESTINATION_SELECTION = rgb_color_as_hexadecimal((255, 255, 100))
    # HIGHLIGHT_CUBE_SELECTION = rgb_color_as_hexadecimal((255, 150, 150))
    # HIGHLIGHT_STACK_SELECTION = rgb_color_as_hexadecimal((255, 100, 100))

    # Lucas-theme-1
    # HIGHLIGHT_SOURCE_SELECTION = rgb_color_as_hexadecimal((217, 204, 180))
    # HIGHLIGHT_DESTINATION_SELECTION = rgb_color_as_hexadecimal((138, 191, 161))
    # HIGHLIGHT_CUBE_SELECTION = rgb_color_as_hexadecimal((191, 141, 122))
    # HIGHLIGHT_STACK_SELECTION = rgb_color_as_hexadecimal((166, 52, 41))

    # Lucas-theme-2
    HIGHLIGHT_SOURCE_SELECTION = rgb_color_as_hexadecimal((217, 199, 193))
    HIGHLIGHT_DESTINATION_SELECTION = rgb_color_as_hexadecimal((140, 102, 94))
    HIGHLIGHT_CUBE_SELECTION = rgb_color_as_hexadecimal((6, 159, 191))
    HIGHLIGHT_STACK_SELECTION = rgb_color_as_hexadecimal((0, 95, 115))


@enum.unique
class HexagonLineColor(enum.Enum):
    NORMAL = 'black'
    HIGHLIGHT = 'white'


class GuiInputStep(enum.Enum):
    NONE = enum.auto()

    # No hexagon selected
    WAIT_SELECTION = enum.auto()

    # Starting hexagon selected
    SELECTED_STEP_1 = enum.auto()

    # First move done
    SELECTED_STEP_2 = enum.auto()

    # Second move done
    FINISHED = enum.auto()


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

        self.highlighted_for_source_selection = False
        self.highlighted_for_destination_selection = False
        self.highlighted_for_cube_selection = False
        self.highlighted_for_stack_selection = False


        GraphicalHexagon.__name_to_hexagon[self.name] = self

        (u, v) = self.position_uv

        self.center = CanvasConfig.ORIGIN + CanvasConfig.HEXA_WIDTH*(u*CanvasConfig.UNIT_U + v*CanvasConfig.UNIT_V)

        self.vertex_data = list()

        for vertex_index in range(CanvasConfig.HEXA_VERTEX_COUNT):
            vertex_angle = (1/2 + vertex_index)*CanvasConfig.HEXA_SIDE_ANGLE

            hexagon_vertex = self.center
            hexagon_vertex = hexagon_vertex + CanvasConfig.HEXA_SIDE*math.cos(vertex_angle)*CanvasConfig.UNIT_X
            hexagon_vertex = hexagon_vertex + CanvasConfig.HEXA_SIDE*math.sin(vertex_angle)*CanvasConfig.UNIT_Y

            self.vertex_data.append(hexagon_vertex[0])
            self.vertex_data.append(hexagon_vertex[1])


    def contains_point(self, point):
        """ Is the point inside the current hexagon ?"""

        #>> This implementation relies of the following properties:
        #>> - All hexagons of the Pijersi board are regular hexagons: all the 6 sides are of equal lengths.
        #>> - All hexagons have the same sizes.
        #>> - All hexagons can be translated to the central hexagon and does match it.
        #>> - The x-axis is orthogonal to an hexagon side.

        SAFE_RELATIVE_INSIDE_WIDTH = 0.99

        is_inside = True

        (hexagon_x, hexagon_y) = (self.center[0], self.center[1])
        (point_x, point_y) = point

        # Compute the standardized point : translated and scaled regarding the actual hexagon
        x = (point_x - hexagon_x)/(CanvasConfig.HEXA_WIDTH/2)
        y = (point_y - hexagon_y)/(CanvasConfig.HEXA_WIDTH/2)

        if is_inside:
            is_inside = math.fabs(x) < SAFE_RELATIVE_INSIDE_WIDTH


        if is_inside:
            # first rotation by CanvasConfig.HEXA_SIDE_ANGLE
            (x, y) = (CanvasConfig.HEXA_COS_SIDE_ANGLE*x - CanvasConfig.HEXA_SIN_SIDE_ANGLE*y,
                      CanvasConfig.HEXA_SIN_SIDE_ANGLE*x + CanvasConfig.HEXA_COS_SIDE_ANGLE*y)

            is_inside = math.fabs(x) < SAFE_RELATIVE_INSIDE_WIDTH


        if is_inside:
            # second rotation by CanvasConfig.HEXA_SIDE_ANGLE
            (x, y) = (CanvasConfig.HEXA_COS_SIDE_ANGLE*x - CanvasConfig.HEXA_SIN_SIDE_ANGLE*y,
                      CanvasConfig.HEXA_SIN_SIDE_ANGLE*x + CanvasConfig.HEXA_COS_SIDE_ANGLE*y)

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
        self.__use_background_photo = CanvasConfig.USE_BACKGROUND_PHOTO

        self.__legend = ""

        self.__game_timer_delay = 500
        self.__game_timer_id = None

        self.__do_take_picture = False
        self.__picture_timer_id = None
        self.__picture_timer_delay = 100
        self.__picture_gif_duration = 2_000
        assert self.__picture_timer_delay < self.__game_timer_delay


        self.__edit_actions = False
        self.__turn_states = list()
        self.__turn_actions = list()

        self.__game = None
        self.__game_started = False
        self.__pijersi_state = rules.PijersiState()
        self.__pijersi_state_gui_input = None
        self.__searcher = [None, None]

        self.__action_input = None
        self.__action_validated = False

        self.__turn_states.append(self.__pijersi_state)
        self.__turn_actions.append("")

        # Mouse control management

        self.__legal_hexagons = []
        self.__gui_input_step = GuiInputStep.NONE
        self.__selected_hexagon = None

        self.__legal_gui_actions = []

        self.__gui_stack_selected = False
        self.__move_stack = False

        # Create widgets

        self.__root = tk.Tk()

        try:
            self.__root.title("pijersi-certu : for playing the pijersi boardgame and testing AI agents")
            self.__root.iconbitmap(AppConfig.ICON_FILE)
        except:
            pass

        self.__create_widgets()

        # Update widgets

        self.__draw_state()

        self.__command_update_faces()
        self.__command_update_players()

        self.__variable_log.set(f"pijersi-certu version {rules.__version__} is ready !")
        self.__variable_summary.set("(c) 2022 Lucas Borboleta ; pijersi software license : GNU GPL ; pijersi rules license : CC-BY-NC-SA")

        # Wait events
        self.__root.mainloop()


    def __create_widgets(self):

        searcher_catalog_names = rules.SEARCHER_CATALOG.get_names()
        searcher_catalog_names_width = max(map(len, searcher_catalog_names)) + 1

        # Frames

        self.__frame_left = ttk.Frame(self.__root)
        self.__frame_right = ttk.Frame(self.__root)

        self.__frame_left.pack(side=tk.LEFT)
        self.__frame_right.pack(side=tk.TOP)

        self.__frame_commands_and_players = ttk.Frame(self.__frame_right)
        self.__frame_actions = ttk.Frame(self.__frame_right)

        self.__frame_commands_and_players.pack(side=tk.TOP)

        self.__frame_board = ttk.Frame(self.__frame_left, padding=10)

        self.__frame_actions.pack(side=tk.TOP)
        self.__frame_board.pack(side=tk.TOP)

        self.__frame_commands = ttk.Frame(self.__frame_commands_and_players, padding=20)
        self.__frame_players = ttk.Frame(self.__frame_commands_and_players, padding=20)

        self.__frame_commands.pack(side=tk.LEFT)
        self.__frame_players.pack(side=tk.LEFT)

        self.__frame_human_actions = ttk.Frame(self.__frame_actions, padding=10)
        self.__frame_text_actions = ttk.Frame(self.__frame_actions)

        # In __frame_commands

        self.__button_quit = ttk.Button(self.__frame_commands,
                                 text='Quit',
                                 command=self.__root.destroy)

        self.__button_start_stop = ttk.Button(self.__frame_commands,
                                  text='Start',
                                  command=self.__command_start_stop)


        self.__variable_faces = tk.StringVar()
        self.__combobox_button_faces = ttk.Combobox(self.__frame_commands,
                                                  width=max(map(len, self.__cube_faces_options)),
                                                  textvariable=self.__variable_faces,
                                                  values=self.__cube_faces_options)
        self.__combobox_button_faces.set(self.__cube_faces_options[2])
        self.__variable_faces.trace_add('write', self.__command_update_faces)

        self.__easy_mode = tk.BooleanVar()
        self.__easy_mode.set(True)
        self.__easy_gui_mode = ttk.Checkbutton (self.__frame_commands,
                                                text='Easy mode',
                                                variable=self.__easy_mode,
                                                command=self.__switch_easy_mode)

        self.__button_start_stop.grid(row=0, column=0)
        self.__button_quit.grid(row=0, column=1)

        self.__easy_gui_mode.grid(row=1, column=0)
        self.__combobox_button_faces.grid(row=1, column=1)

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
        self.__variable_black_player.set(searcher_catalog_names[0])


        self.__progressbar = ttk.Progressbar(self.__frame_players,
                                            orient=tk.HORIZONTAL,
                                            length=300,
                                            maximum=100,
                                            mode='determinate')

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
                                height=CanvasConfig.HEIGHT,
                                width=CanvasConfig.WIDTH)
        self.__canvas.pack(side=tk.TOP)

        self.__canvas.bind('<Motion>', self.__mouse_over)
        self.__canvas.bind('<Button-1>', self.__click)

       # In __frame_actions

        self.__variable_log = tk.StringVar()
        self.__label_log = ttk.Label(self.__frame_actions,
                                  textvariable=self.__variable_log,
                                  width=90,
                                  padding=5,
                                  foreground='red',
                                  borderwidth=2, relief="groove")

        self.__variable_summary = tk.StringVar()
        self.__label_summary = ttk.Label(self.__frame_actions,
                                  textvariable=self.__variable_summary,
                                  width=90,
                                  padding=5,
                                  foreground='black',
                                  borderwidth=2, relief="groove")

       # In __frame_human_actions

        self.__label_action = ttk.Label(self.__frame_human_actions, text='Action :')

        self.__variable_action = tk.StringVar()
        self.__entry_action = ttk.Entry(self.__frame_human_actions, textvariable=self.__variable_action)
        self.__entry_action.bind("<KeyPress>", self.__reset_gui_process)

        self.__button_action_confirm = ttk.Button(self.__frame_human_actions,
                                  text='OK',
                                  command=self.__command_action_confirm)

        self.__variable_edit_actions = tk.BooleanVar()
        self.__variable_edit_actions.set(self.__edit_actions)
        self.__button_edit_actions = ttk.Checkbutton (self.__frame_human_actions,
                                       text='Edit actions',
                                       command=self.__command_update_edit_actions,
                                       variable=self.__variable_edit_actions)
        self.__button_edit_actions.config(state="enabled")

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


        self.__variable_take_pictures = tk.BooleanVar()
        self.__variable_take_pictures.set(self.__do_take_picture)
        self.__button_take_pictures = ttk.Checkbutton (self.__frame_human_actions,
                                       text='Take pictures',
                                       command=self.__command_update_take_pictures,
                                       variable=self.__variable_take_pictures)
        self.__button_take_pictures.config(state="enabled")


       # In __frame_text_actions

        self.__text_actions = tk.Text(self.__frame_text_actions,
                                  width=60,
                                  background='lightgrey',
                                  borderwidth=2, relief="groove")

        self.__scrollbar_actions = ttk.Scrollbar(self.__frame_text_actions, orient = 'vertical')

        self.__text_actions.config(yscrollcommand=self.__scrollbar_actions.set)
        self.__scrollbar_actions.config(command=self.__text_actions.yview)

        self.__label_log.pack(side=tk.TOP)
        self.__label_summary.pack(side=tk.TOP, pady=10)

        self.__frame_human_actions.pack(side=tk.TOP)


        self.__label_action.grid(row=0, column=0)
        self.__entry_action.grid(row=0, column=1)
        self.__button_action_confirm.grid(row=0, column=2)
        self.__button_edit_actions.grid(row=0, column=3)
        self.__label_turn.grid(row=0, column=4)
        self.__spinbox_turn.grid(row=0, column=5)
        self.__button_take_pictures.grid(row=0, column=6)

        self.__frame_human_actions.rowconfigure(0, pad=5)
        self.__frame_human_actions.columnconfigure(0, pad=5)
        self.__frame_human_actions.columnconfigure(1, pad=5)
        self.__frame_human_actions.columnconfigure(2, pad=5)
        self.__frame_human_actions.columnconfigure(3, pad=5)
        self.__frame_human_actions.columnconfigure(4, pad=5)
        self.__frame_human_actions.columnconfigure(5, pad=5)
        self.__frame_human_actions.columnconfigure(6, pad=10)


        self.__frame_text_actions.pack(side=tk.TOP)
        self.__scrollbar_actions.pack(side=tk.LEFT, fill=tk.Y)
        self.__text_actions.pack(side=tk.LEFT)

        self.__entry_action.config(state="disabled")
        self.__button_action_confirm.config(state="disabled")
        self.__text_actions.config(state="disabled")


    def __create_cube_photos(self):
        if self.__cube_photos is None:

            cube_photo_width = int(CanvasConfig.HEXA_SIDE*math.cos(math.pi/4))

            self.__cube_photos = {}

            for (key, file) in CubeConfig.CUBE_FILE_PATH.items():
                cube_photo = Image.open(CubeConfig.CUBE_FILE_PATH[key])
                cube_photo = cube_photo.resize((cube_photo_width, cube_photo_width))
                cube_tk_photo = ImageTk.PhotoImage(cube_photo)
                self.__cube_photos[key] = cube_tk_photo


    def __command_update_faces(self, *_):
        self.__cube_faces = self.__variable_faces.get()
        self.__draw_state()


    def __command_update_players(self, *_):
        self.__searcher[rules.Player.T.WHITE] = rules.SEARCHER_CATALOG.get(self.__variable_white_player.get())
        self.__searcher[rules.Player.T.BLACK] = rules.SEARCHER_CATALOG.get(self.__variable_black_player.get())


    def __command_update_turn(self, *_):
        try:
            turn_index = int(self.__variable_turn.get())

            if 0 <= turn_index < len(self.__turn_states):
                self.__pijersi_state = self.__turn_states[turn_index]
                self.__legend = self.__turn_actions[turn_index]
                self.__draw_state()
                self.__variable_turn.set(turn_index)

            else:
                return

        except ValueError:
            return

        except:
            assert False

    def __entry_action_gui_protection(self, a, b, c):
        """
        If user interacts with action input, gui input process is interrupted
        """
        if self.__gui_input_step is not GuiInputStep.NONE:
            self.__reset_gui_process(back_to_gui_step=GuiInputStep.NONE)

    def __set_legal_gui_actions(self):
        """
        Filter __legal_gui_actions according to gui input step
        """

        # All legal actions from rules are selected
        if self.__gui_input_step is GuiInputStep.WAIT_SELECTION:
            self.__legal_gui_moves = self.__pijersi_state.get_action_simple_names()
        # keep actions containing selected hexagon name at first position
        if self.__gui_input_step is GuiInputStep.SELECTED_STEP_1:
            self.__legal_gui_moves.clear()
            # If stack is selected, keep only stack moves
            sign = "-"
            if self.__move_stack:
                sign = "="
            for action_name in self.__pijersi_state.get_action_simple_names():
                if action_name[0:3] == self.__selected_hexagon.name + sign:
                    self.__legal_gui_moves.append(action_name)
        # keep 2-step actions containing selected hexagon name at second position
        if self.__gui_input_step is GuiInputStep.SELECTED_STEP_2:
            legal_moves = copy.copy(self.__legal_gui_moves)
            self.__legal_gui_moves.clear()
            for action_name in legal_moves:
                if action_name[0:5] == self.__variable_action.get():
                    # keep actions with a second move
                    if len(action_name) > 5:
                        self.__legal_gui_moves.append(action_name)


    def __set_legal_hexagons(self):
        """
        Build the list of hexagons user can interact with
        """

        self.__legal_hexagons.clear()
        self.__set_legal_gui_actions()

        # If GUI input is deactivated, no hexagon is added to legal hexagons list

        # If no selection has been made, all starting hexagons are legal
        # Selection is done on first hexagon name in action names
        if self.__gui_input_step is GuiInputStep.WAIT_SELECTION:
            self.__set_legal_hexagon_from_action_moves(0,2)

        # If starting hexagon is selected, first arrival hexagons are legal
        # Selection is done on second hexagon name in action names
        if self.__gui_input_step is GuiInputStep.SELECTED_STEP_1:
            self.__set_legal_hexagon_from_action_moves(3,5)

        # If target hexagon is selected, second arrival hexagons are legal
        # Selection is done on third hexagon name in action names
        if self.__gui_input_step is GuiInputStep.SELECTED_STEP_2:
            self.__set_legal_hexagon_from_action_moves(6,8)
            # Add selected hexagon to interrupt move
            self.__legal_hexagons.append(self.__selected_hexagon)

    def __set_legal_hexagon_from_action_moves(self, pos1, pos2):
        """
        Build the list of hexagons user can interact with from action names position
        """

        hexagon_names = set()
        for action_name in self.__legal_gui_moves:
            hexagon_names.add(action_name[pos1:pos2])
        # Add them to available hexagon
        for name in hexagon_names:
            graphical_hexagon = GraphicalHexagon.get(name)
            self.__legal_hexagons.append(graphical_hexagon)

    def __mouse_over(self, event):
        """
        If mouse pointer is over drawing canvas, mark hexagons to highlight.
        """

        # If not in easy mode, do not highlight hexagons
        if not self.__easy_mode.get():
            return

        if self.__gui_input_step in [GuiInputStep.WAIT_SELECTION, GuiInputStep.SELECTED_STEP_1, GuiInputStep.SELECTED_STEP_2]:
            # Update only if change occurs to avoid multiple draw_state calls
            redraw = False
            hexagon_mouse_over = self.__position_to_hexagon(event)
            for hexagon in self.__legal_hexagons:
                if hexagon is hexagon_mouse_over:
                    if not hexagon.highlighted_for_source_selection:
                        hexagon.highlighted_for_source_selection = True
                        redraw = True
                else:
                    if hexagon.highlighted_for_source_selection:
                        redraw = True
                    hexagon.highlighted_for_source_selection = False
            if redraw:
                self.__draw_state()

    def __hexagon_has_stack(self, name):
        for action in self.__legal_gui_moves:
            if action[0:3] == name + "=":
                return True
        return False


    def __click(self, event):
        """
        Manage click event. Call legit function according to gui input current step
        """

        if self.__gui_input_step is GuiInputStep.WAIT_SELECTION:
            self.__click_wait_selection_step(event)

        elif self.__gui_input_step is GuiInputStep.SELECTED_STEP_1:
            self.__click_step_1(event)

        elif self.__gui_input_step is GuiInputStep.SELECTED_STEP_2:
            self.__click_step_2(event)


    def __click_wait_selection_step(self, event):
        """
        Manage click event when gui input process is at step 0, meaning waiting that user
        selects a starting hexagon.
        If user clicks on a legal hexagon, next GUI step is invoked.
        Otherwise, current process is cancelled.
        """

        hexagon_mouse_click = self.__position_to_hexagon(event)

        if hexagon_mouse_click in self.__legal_hexagons:
            self.__selected_hexagon = hexagon_mouse_click
            # Give proper color (priority to stack)
            self.__selected_hexagon.highlighted_for_cube_selection = True
            self.__selected_hexagon.highlighted_for_source_selection = False
            has_egal = self.__hexagon_has_stack(self.__selected_hexagon.name)
            self.__selected_hexagon.highlighted_for_stack_selection = has_egal
            self.__gui_stack_selected = has_egal
            self.__move_stack = has_egal
            # Parameter input gui process to next step
            self.__gui_input_step = GuiInputStep.SELECTED_STEP_1
            self.__hightlight_legal_hexagons()
            self.__variable_action.set(hexagon_mouse_click.name)

        else:
            self.__reset_gui_process(event)

        self.__draw_state()


    def __click_step_1(self, event):
        """
        Manage click event when gui input process is at step 1, meaning that a
        starting hexagon is selected, waiting for a target selection.
        If user clicks on a legal hexagon, next GUI step is invoked.
        Otherwise, current process is cancelled.
        """

        hexagon_mouse_click = self.__position_to_hexagon(event)
        # Manage double click on selected hexagon, meaning unstack instead of moving the entire stack
        if self.__gui_stack_selected and hexagon_mouse_click is self.__selected_hexagon:
            self.__move_stack = not self.__move_stack
            self.__selected_hexagon.highlighted_for_stack_selection = self.__move_stack
            self.__hightlight_legal_hexagons()
        elif hexagon_mouse_click in self.__legal_hexagons:
            # Uncolor first selected hexagon
            self.__selected_hexagon.highlighted_for_source_selection = False
            self.__selected_hexagon.highlighted_for_stack_selection = False
            self.__selected_hexagon.highlighted_for_cube_selection = False
            # Change selected hexagon and filter corresponding actions
            self.__selected_hexagon = hexagon_mouse_click
            actions = [a[0:5] for a in self.__legal_gui_moves if a[3:5] == hexagon_mouse_click.name]
            actions.sort()
            # If stack is selected, determine if stack moves or unstack
            if len(actions) > 1:
                if self.__move_stack:
                    action_name = actions[-1]
                else:
                    action_name = actions[0]
            else:
                action_name = actions[0]
            # Give correct color to selected hexagon
            self.__selected_hexagon.highlighted_for_source_selection = False
            self.__selected_hexagon.highlighted_for_cube_selection = True
            self.__selected_hexagon.highlighted_for_stack_selection = (not self.__move_stack) and len(actions) > 1
            # Store action in text field of action entry
            self.__variable_action.set(action_name)
            # Show move result in an alternative pijersi state
            action = self.__pijersi_state.get_action_by_simple_name(action_name)
            self.__pijersi_state_gui_input = self.__pijersi_state.take_action(action)
             # Parameter input gui process to next step
            self.__gui_input_step = GuiInputStep.SELECTED_STEP_2
            self.__hightlight_legal_hexagons()
            # If no more action available, this action is terminal
            if len(self.__legal_gui_moves) == 0:
                self.__terminate_gui_action()
        else:
            self.__reset_gui_process(event)
        self.__draw_state()


    def __click_step_2(self, event):
        """
        Manage click event when gui input process is at step 2, meaning that first target
        is selected, waiting for a finish move.
        If user clicks on a legal hexagon, next GUI step is invoked.
        Otherwise, current process is cancelled.
        """

        hexagon_mouse_click = self.__position_to_hexagon(event)
        # Manage half move. If user clicks the first target hexagon, terminate the action
        if hexagon_mouse_click is self.__selected_hexagon:
            self.__terminate_gui_action()

        elif hexagon_mouse_click in self.__legal_hexagons:
            actions = [a[0:8] for a in self.__legal_gui_moves if a[6:8] == hexagon_mouse_click.name]
            action_name = actions[0]
            self.__variable_action.set(action_name)
            action = self.__pijersi_state.get_action_by_simple_name(action_name)
            self.__pijersi_state_gui_input = self.__pijersi_state.take_action(action)
            # The action is terminal by definition
            self.__terminate_gui_action()

        else:
            self.__reset_gui_process(event)

        self.__draw_state()


    def __terminate_gui_action(self):
        """
        When gui input process is finished, transmits action to the kernel
        """
        self.__action_validated = True
        self.__action_input = self.__variable_action.get()
        self.__gui_input_step = GuiInputStep.FINISHED


    def __hightlight_legal_hexagons(self):
        """
        Mark hexagons user can click
        """

        self.__set_legal_hexagons()

        for hexagon in GraphicalHexagon.all:
            if hexagon in self.__legal_hexagons:
                if self.__gui_input_step in [GuiInputStep.SELECTED_STEP_1, GuiInputStep.SELECTED_STEP_2]:
                    # If not in easy mode, do not highlight hexagons
                    hexagon.highlighted_for_destination_selection = self.__easy_mode.get()
                else:
                    hexagon.highlighted_for_destination_selection = False
            else:
                hexagon.highlighted_for_destination_selection = False


    def __reset_gui_process(self, event=None, back_to_gui_step=GuiInputStep.WAIT_SELECTION):
        """
        Reset gui input process and clean the drawing
        """
        self.__selected_hexagon = None

        for hexagon in GraphicalHexagon.all:
            hexagon.highlighted_for_destination_selection = False
            hexagon.highlighted_for_source_selection = False
            hexagon.highlighted_for_cube_selection = False
            hexagon.highlighted_for_stack_selection = False

        self.__gui_input_step = back_to_gui_step

        self.__set_legal_hexagons()

        if event is not None:
            self.__mouse_over(event)

        self.__pijersi_state_gui_input = None
        self.__draw_state()


    def __switch_easy_mode(self):
        """
        If user changes easy mode checkbox during a game, redo the right drawing
        """

        self.__hightlight_legal_hexagons()
        self.__draw_state()


    def __position_to_hexagon(self, position):
        """
        Return the hexagon given a drawing position
        """
        for hexagon in self.__legal_hexagons:
            if hexagon.contains_point((position.x, position.y)):
                return hexagon
        if self.__selected_hexagon is not None:
            if self.__selected_hexagon.contains_point((position.x, position.y)):
                return self.__selected_hexagon
        return None


    def __command_action_confirm(self):

        self.__action_input = self.__variable_action.get()
        self.__action_input = self.__action_input.replace("!", "")


        (self.__action_validated,
         message) = rules.Notation.validate_simple_notation(self.__action_input,
                                                            self.__pijersi_state.get_action_simple_names())

        if self.__action_validated:
            self.__variable_log.set(message)
            self.__variable_action.set("")

        else:
            self.__variable_log.set(message)

        self.__reset_gui_process(back_to_gui_step=GuiInputStep.NONE)


    def __command_update_edit_actions(self):

        self.__edit_actions = self.__variable_edit_actions.get()

        if self.__edit_actions:
            self.__button_start_stop.configure(text="Resume")
            self.__text_actions.config(state="normal")

        else:
           self.__button_start_stop.configure(text="Start")
           self.__text_actions.config(state="disabled")


    def __command_update_take_pictures(self):

        self.__do_take_picture = self.__variable_take_pictures.get()


    def __command_start_stop(self):

        if self.__game_timer_id is not None:
            self.__canvas.after_cancel(self.__game_timer_id)
            self.__game_timer_id = None

        self.__entry_action.config(state="disabled")
        self.__button_action_confirm.config(state="disabled")
        self.__button_edit_actions.config(state="disabled")

        self.__game_started = not self.__game_started

        self.__reset_gui_process(back_to_gui_step=GuiInputStep.NONE)

        if self.__game_started:

           self.__game = rules.Game()
           self.__game.set_white_searcher(self.__searcher[rules.Player.T.WHITE])
           self.__game.set_black_searcher(self.__searcher[rules.Player.T.BLACK])
           self.__game.start()

           self.__pijersi_state = self.__game.get_state()
           self.__legend = ""

           self.__turn_states = list()
           self.__turn_states.append(self.__game.get_state())
           self.__turn_actions = list()
           self.__turn_actions.append("")
           self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
           self.__variable_turn.set(len(self.__turn_states) - 1)

           self.__button_start_stop.configure(text="Stop")

           self.__variable_log.set(self.__game.get_log())
           self.__variable_summary.set(self.__game.get_summary())
           self.__progressbar['value'] = 50.

           self.__combobox_white_player.config(state="disabled")
           self.__combobox_black_player.config(state="disabled")

           if self.__edit_actions:
               actions_text = self.__text_actions.get('1.0', tk.END)

               self.__text_actions.config(state="normal")
               self.__text_actions.delete('1.0', tk.END)
               self.__text_actions.config(state="disabled")

               validated_edited_actions = True
               actions_items = actions_text.split()

               # check length of action items
               if validated_edited_actions and not len(actions_items) % 2 == 0:
                  validated_edited_actions = False
                  self.__variable_log.set("error: not an even count of words")

               # check action indices
               if validated_edited_actions:
                  action_count = int(len(actions_items)/2)
                  for action_index in range(action_count):
                      even_action_item = actions_items[2*action_index]
                      if even_action_item != str(action_index + 1):
                          validated_edited_actions = False
                          self.__variable_log.set("error: bad index '%s'" % even_action_item)

               # extract actions
               if validated_edited_actions:
                   edited_actions = list()
                   for action_index in range(action_count):
                       action = actions_items[2*action_index + 1]
                       action = action.replace("!", "")
                       edited_actions.append(action)

               # interpet actions
               if validated_edited_actions:

                    white_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.WHITE].get_name())
                    black_replayer = rules.HumanSearcher(self.__searcher[rules.Player.T.BLACK].get_name())

                    self.__game.set_white_searcher(white_replayer)
                    self.__game.set_black_searcher(black_replayer)

                    for (action_index, action) in enumerate(edited_actions):

                        if not self.__game.has_next_turn():
                            validated_edited_actions = False
                            self.__variable_log.set("error: too much actions")
                            break

                        self.__pijersi_state = self.__game.get_state()

                        (action_validated, message) = rules.Notation.validate_simple_notation(action,
                                                                  self.__pijersi_state.get_action_simple_names())
                        if not action_validated:
                            validated_edited_actions = False
                            self.__variable_log.set("error at turn %d: %s" % (action_index + 1, message))
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

                    self.__game.set_white_searcher(self.__searcher[rules.Player.T.WHITE])
                    self.__game.set_black_searcher(self.__searcher[rules.Player.T.BLACK])

                    self.__pijersi_state = self.__game.get_state()
                    self.__legend = self.__game.get_last_action()
                    self.__draw_state()

                    self.__spinbox_turn.config(values=list(range(len(self.__turn_states))))
                    self.__variable_turn.set(len(self.__turn_states) - 1)


               if not validated_edited_actions:
                   self.__game_started = False

                   self.__text_actions.config(state="normal")
                   self.__text_actions.delete('1.0', tk.END)
                   self.__text_actions.config(state="disabled")

                   self.__text_actions.config(state="normal")
                   self.__text_actions.insert(tk.END, actions_text)
                   self.__text_actions.see(tk.END)

                   self.__combobox_white_player.config(state="readonly")
                   self.__combobox_black_player.config(state="readonly")

                   self.__entry_action.config(state="disabled")
                   self.__button_action_confirm.config(state="disabled")

                   self.__button_edit_actions.config(state="enabled")
                   self.__edit_actions = True
                   self.__variable_edit_actions.set(self.__edit_actions)

                   self.__button_start_stop.configure(text="Resume")
                   self.__progressbar['value'] = 0.

               else:
                   self.__game_started = True

                   self.__button_edit_actions.config(state="disabled")
                   self.__edit_actions = False
                   self.__variable_edit_actions.set(self.__edit_actions)

                   self.__picture_timer_id = self.__canvas.after(self.__picture_timer_delay, self.__take_picture)
                   self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

           else:
               self.__text_actions.config(state="normal")
               self.__text_actions.delete('1.0', tk.END)
               self.__text_actions.config(state="disabled")

               self.__button_edit_actions.config(state="disabled")
               self.__edit_actions = False
               self.__variable_edit_actions.set(self.__edit_actions)

               self.__picture_timer_id = self.__canvas.after(self.__picture_timer_delay, self.__take_picture)
               self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        else:
           self.__combobox_white_player.config(state="readonly")
           self.__combobox_black_player.config(state="readonly")

           self.__entry_action.config(state="enabled")
           self.__variable_action.set("")
           self.__entry_action.config(state="disabled")
           self.__button_action_confirm.config(state="disabled")

           self.__button_edit_actions.config(state="enabled")
           self.__edit_actions = False
           self.__variable_edit_actions.set(self.__edit_actions)

           self.__variable_log.set("pijersi stopped")
           self.__button_start_stop.configure(text="Start")
           self.__progressbar['value'] = 0.


    def __command_next_turn(self):

        if self.__game_timer_id is not None:
            self.__canvas.after_cancel(self.__game_timer_id)
            self.__game_timer_id = None

        if self.__game_started and self.__game.has_next_turn():

            self.__pijersi_state = self.__game.get_state()
            player = self.__pijersi_state.get_current_player()
            searcher = self.__searcher[player]

            self.__progressbar['value'] = 50.

            ready_for_next_turn = False

            if searcher.is_interactive():
                self.__entry_action.config(state="enabled")
                self.__button_action_confirm.config(state="enabled")
                self.__progressbar['value'] = 0.
                if self.__gui_input_step == GuiInputStep.NONE:
                    self.__reset_gui_process()

                if self.__action_validated and self.__action_input is not None:
                    ready_for_next_turn = True

                    searcher.set_action_simple_name(self.__action_input)

                    self.__action_input = None
                    self.__action_validated = False
                    self.__entry_action.config(state="disabled")
                    self.__button_action_confirm.config(state="disabled")
                    self.__reset_gui_process(back_to_gui_step=GuiInputStep.NONE)

            else:
                ready_for_next_turn = True
            if ready_for_next_turn:
                self.__progressbar['value'] = 50.
                self.__game.next_turn()
                self.__pijersi_state = self.__game.get_state()
                self.__legend = self.__game.get_last_action()
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

            self.__picture_timer_id = self.__canvas.after(self.__picture_timer_delay, self.__take_picture)
            self.__game_timer_id = self.__canvas.after(self.__game_timer_delay, self.__command_next_turn)

        else:
           self.__combobox_white_player.config(state="readonly")
           self.__combobox_black_player.config(state="readonly")

           self.__progressbar['value'] = 0.

           self.__game_started = False
           self.__button_start_stop.configure(text="Start")

           self.__button_edit_actions.config(state="enabled")
           self.__edit_actions = False
           self.__variable_edit_actions.set(self.__edit_actions)

           self.__make_animated_pictures()


    def __take_picture(self):

        if self.__picture_timer_id is not None:
            self.__canvas.after_cancel(self.__picture_timer_id)
            self.__picture_timer_id = None

        if self.__do_take_picture:

            assert self.__game is not None
            turn = self.__game.get_turn()

            if turn is None:
                if os.path.isdir(AppConfig.TMP_PICTURE_DIR):
                    shutil.rmtree(AppConfig.TMP_PICTURE_DIR)
                os.mkdir(AppConfig.TMP_PICTURE_DIR)

                picture_index = 0

            else:
                picture_index = turn

            picture_export_path = os.path.join(AppConfig.TMP_PICTURE_DIR, "state-%3.3d" % picture_index)

            picture_png_file = picture_export_path + '.png'


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

            image = ImageGrab.grab(bbox=picture_bbox)
            image.save(picture_png_file)


    def __make_animated_pictures(self):
         if self.__do_take_picture:
             if os.path.isdir(AppConfig.TMP_PICTURE_DIR):

                frames = []
                picture_list = glob.glob(os.path.join(AppConfig.TMP_PICTURE_DIR, "state-*"))

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

                    print()
                    print("pictures are available in directory '%s'" % AppConfig.TMP_PICTURE_DIR)


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
            bg_photo = Image.open(CanvasConfig.BACKGROUND_PHOTO_PATH)
            (bg_width, bg_height) = bg_photo.size

            bg_new_width = int(math.ceil(CanvasConfig.WIDTH))
            bg_new_height = int(math.ceil(CanvasConfig.WIDTH*bg_height/bg_width))

            bg_photo = bg_photo.resize((bg_new_width, bg_new_height))
            self.__background_tk_photo = ImageTk.PhotoImage(bg_photo)

            self.__background_tk_photo_delta_x = (bg_new_width - CanvasConfig.WIDTH)/2
            self.__background_tk_photo_delta_y = (bg_new_height - CanvasConfig.HEIGHT)/2

        # Add the background image
        self.__canvas.create_image(self.__background_tk_photo_delta_x, self.__background_tk_photo_delta_y,
                                   image=self.__background_tk_photo,
                                   anchor=tk.NW)


    def __draw_legend(self):

        (u, v) = (2, -4)
        hexagon_center = CanvasConfig.ORIGIN + CanvasConfig.HEXA_WIDTH*(u*CanvasConfig.UNIT_U + v*CanvasConfig.UNIT_V)

        vertex_index = 1
        vertex_angle = (1/2 + vertex_index)*CanvasConfig.HEXA_SIDE_ANGLE

        hexagon_vertex = hexagon_center
        hexagon_vertex = hexagon_vertex + CanvasConfig.HEXA_SIDE*math.cos(vertex_angle)*CanvasConfig.UNIT_X
        hexagon_vertex = hexagon_vertex + CanvasConfig.HEXA_SIDE*math.sin(vertex_angle)*CanvasConfig.UNIT_Y

        legend_position = hexagon_vertex - 1.0*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y


        legend_font = font.Font(family=CanvasConfig.FONT_FAMILY, size=CanvasConfig.FONT_LEGEND_SIZE, weight='bold')

        self.__canvas.create_text(*legend_position, text=self.__legend, justify=tk.CENTER,
                                  font=legend_font, fill=CanvasConfig.FONT_LEGEND_COLOR)


    def __draw_all_cubes(self):

        pijersi_state = self.__pijersi_state

        if self.__pijersi_state_gui_input is not None:
            pijersi_state = self.__pijersi_state_gui_input

        hex_states = pijersi_state.get_hexStates()

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

        label_position = ( TinyVector((hexagon.vertex_data[6], hexagon.vertex_data[7])) +
                          0.25*CanvasConfig.HEXA_SIDE*(CanvasConfig.UNIT_X + 0.75*CanvasConfig.UNIT_Y))

        if self.__use_background_photo:
            polygon_line_color = ''
            fill_color = ''

        else:
            polygon_line_color = HexagonLineColor.NORMAL.value
            fill_color = hexagon.color.value

        # Respect priority order in lighting
        if hexagon.highlighted_for_destination_selection:
            fill_color = HexagonColor.HIGHLIGHT_DESTINATION_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_for_cube_selection:
            fill_color = HexagonColor.HIGHLIGHT_CUBE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_for_stack_selection:
            fill_color = HexagonColor.HIGHLIGHT_STACK_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        if hexagon.highlighted_for_source_selection:
            fill_color = HexagonColor.HIGHLIGHT_SOURCE_SELECTION.value
            polygon_line_color = HexagonLineColor.HIGHLIGHT.value

        self.__canvas.create_polygon(hexagon.vertex_data,
                              fill=fill_color,
                              outline=polygon_line_color,
                              width=CanvasConfig.HEXA_LINE_WIDTH,
                              joinstyle=tk.MITER)

        if hexagon.name:
            label_font = font.Font(family=CanvasConfig.FONT_FAMILY, size=CanvasConfig.FONT_LABEL_SIZE, weight='bold')

            self.__canvas.create_text(*label_position, text=hexagon.name, justify=tk.CENTER, font=label_font)


    def __draw_cube(self, name, config, cube_color, cube_sort, cube_label):

        hexagon = GraphicalHexagon.get(name)

        shift_value = 0.20*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y

        top_shift = 0
        bottom_shift = 0

        if hexagon.highlighted_for_stack_selection:
            top_shift = shift_value
            bottom_shift = 1.25*shift_value

        if hexagon.highlighted_for_cube_selection:
            top_shift = shift_value

        (u, v) = hexagon.position_uv

        cube_vertices = list()

        for vertex_index in range(CanvasConfig.CUBE_VERTEX_COUNT):
            vertex_angle = (1/2 + vertex_index)*CanvasConfig.CUBE_SIDE_ANGLE

            if  config == CubeLocation.BOTTOM or config == CubeLocation.MIDDLE:
                cube_center = hexagon.center - 0.40*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y + bottom_shift

            elif config == CubeLocation.TOP:
                cube_center = hexagon.center + 0.40*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y + top_shift

            # if config == CubeLocation.MIDDLE:
            #     cube_center = hexagon.center

            # elif config == CubeLocation.BOTTOM:
            #     cube_center = hexagon.center - 0.40*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y

            # elif config == CubeLocation.TOP:
            #     cube_center = hexagon.center + 0.40*CanvasConfig.HEXA_SIDE*CanvasConfig.UNIT_Y

            cube_vertex = cube_center
            cube_vertex = cube_vertex + 0.5*CanvasConfig.HEXA_SIDE*math.cos(vertex_angle)*CanvasConfig.UNIT_X
            cube_vertex = cube_vertex + 0.5*CanvasConfig.HEXA_SIDE*math.sin(vertex_angle)*CanvasConfig.UNIT_Y

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

            face_font = font.Font(family=CanvasConfig.FONT_FAMILY, size=CanvasConfig.FONT_FACE_SIZE, weight='bold')

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
                                width=CanvasConfig.CUBE_LINE_WIDTH)


    def __draw_rock_face(self, cube_center, cube_vertices, face_color):

        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        self.__canvas.create_oval(*face_vertex_NW, *face_vertex_SE,
                           fill='',
                           outline=face_color,
                           width=CanvasConfig.CUBE_LINE_WIDTH)


    def __draw_scissors_face(self, cube_center, cube_vertices, face_color):

        face_vertex_NE = 0.5*cube_center + 0.5*cube_vertices[0]
        face_vertex_NW = 0.5*cube_center + 0.5*cube_vertices[1]
        face_vertex_SW = 0.5*cube_center + 0.5*cube_vertices[2]
        face_vertex_SE = 0.5*cube_center + 0.5*cube_vertices[3]

        self.__canvas.create_line(*face_vertex_NE, *face_vertex_SW,
                           fill=face_color,
                           width=CanvasConfig.CUBE_LINE_WIDTH,
                           capstyle=tk.ROUND)

        self.__canvas.create_line(*face_vertex_NW, *face_vertex_SE,
                           fill=face_color,
                           width=CanvasConfig.CUBE_LINE_WIDTH,
                           capstyle=tk.ROUND)


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

            angle_count = 20
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
                              width=CanvasConfig.CUBE_LINE_WIDTH,
                              joinstyle=tk.ROUND,
                              smooth=True)


GraphicalHexagon.init()


def main():
    print("Hello")
    print(_COPYRIGHT_AND_LICENSE)

    _ = GameGui()

    print("Bye")


if __name__ == "__main__":
    main()


