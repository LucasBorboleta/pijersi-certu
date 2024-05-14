#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_rules_test.py tests the rules engine for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should h
from multiprocessing import freeze_support
import multiprocessing

import cProfile
from pstats import SortKey

ave received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

from collections import Counter
import os
import random
import sys

from typing import Optional


from multiprocessing import freeze_support
import multiprocessing
_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

from pijersi_rules import Cube
from pijersi_rules import Game
from pijersi_rules import HexState
from pijersi_rules import HumanSearcher
from pijersi_rules import MinimaxSearcher
from pijersi_rules import Player
from pijersi_rules import PathStates
from pijersi_rules import PijersiState
from pijersi_rules import RandomSearcher
from pijersi_rules import Reward

from pijersi_ugi import make_ugi_client
from pijersi_ugi import UgiSearcher


import cProfile
from pstats import SortKey


def log(msg: str=None):
    if msg is None:
        print("", file=sys.stderr, flush=True)
    else:
        for line in msg.split('\n'):
            print(f"{line}", file=sys.stderr, flush=True)


def test():


    def generate_random_hex_state(is_empty: Optional[bool]=None,
                                  has_stack: Optional[bool]=None,
                                  player: Optional[Player.T]=None,
                                  bottom: Optional[Cube.T]=None,
                                  top: Optional[Cube.T]=None) -> HexState:

        is_empty = random.choice((True, False)) if is_empty is None else is_empty
        if not is_empty:
            player = random.choice(tuple(Player.T)) if player is None else player
            bottom = random.choice(tuple(Cube.T)) if bottom is None else bottom
            has_stack = random.choice((True, False)) if has_stack is None else has_stack
            if has_stack:
                if bottom == Cube.T.WISE:
                    top = random.choice(tuple(Cube.T)) if top is None else top
                else:
                    top = random.choice((Cube.T.ROCK, Cube.T.PAPER, Cube.T.SCISSORS)) if top is None else top

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

        log()
        log("-- test_iterate_hex_states --")

        hex_codes = set()

        for hex_state in HexState.iterate_hex_states():
            hex_code = hex_state.encode()
            log(f"hex_state = {hex_state} ; hex_code={hex_code}")
            assert hex_code not in hex_codes
            hex_codes.add(hex_code)

        log(f"len(hex_codes) = {len(hex_codes)} ; min(hex_codes) = {min(hex_codes)} ; max(hex_codes) = {max(hex_codes)}")
        assert len(hex_codes) <= HexState.CODE_BASE
        assert min(hex_codes) == 0
        assert max(hex_codes) <= HexState.CODE_BASE


    def test_encode_and_decode_hex_state():

        log()
        log("-- test_encode_and_decode_hex_state --")

        hex_state_count = 100

        for _ in range(hex_state_count):

            hex_state = generate_random_hex_state()
            log()
            log(f"hex_state = {hex_state}")

            hex_state_code = hex_state.encode()
            log(f"hex_state_code = {hex_state_code}")

            hex_decoded_state = HexState.decode(hex_state_code)
            log(f"hex_decoded_state = {hex_decoded_state}")
            assert hex_decoded_state == hex_state

        hex_state_count = 100

        for _ in range(hex_state_count):

            hex_state = generate_random_hex_state(is_empty=False, has_stack=True, bottom=Cube.T.WISE)
            log()
            log(f"hex_state = {hex_state}")

            hex_state_code = hex_state.encode()
            log(f"hex_state_code = {hex_state_code}")

            hex_decoded_state = HexState.decode(hex_state_code)
            log(f"hex_decoded_state = {hex_decoded_state}")
            assert hex_decoded_state == hex_state


    def test_encode_and_decode_path_states() -> None:

        log()
        log("-- test_encode_and_decode_path_states --")

        path_state_count = 100
        path_length = 3

        for _ in range(path_state_count):
            path_state = generate_random_path_state(path_length)
            log()
            log(f"path_state = {path_state}")

            path_code = PijersiState.encode_path_states(path_state)
            log(f"path_code = {path_code}")

            path_codes = PijersiState.decode_path_code(path_code, path_length)
            log(f"path_codes = {path_codes}")

            path_decoded_state = PijersiState.decode_path_codes(path_codes)
            log(f"path_decoded_state = {path_decoded_state}")
            assert path_decoded_state == path_state


    def test_first_get_summary():

        log()
        log("-- test_first_get_summary --")

        new_state = PijersiState()
        summary = new_state.get_summary()
        log()
        log(f"summary = {summary}")
        assert summary == "Turn 1 / player white / credit 20 / alive P:4 R:4 S:4 W:2 p:4 r:4 s:4 w:2"


    def test_game_between_random_players():

        log("=====================================")
        log(" test_game_between_random_players ...")
        log("=====================================")

        default_max_credit = PijersiState.get_max_credit()
        PijersiState.set_max_credit(10_000)

        game = Game()

        game.set_white_searcher(RandomSearcher("random"))
        game.set_black_searcher(RandomSearcher("random"))

        game.start()

        while game.has_next_turn():
            game.next_turn()

        PijersiState.set_max_credit(default_max_credit)

        log("=====================================")
        log("test_game_between_random_players done")
        log("=====================================")


    def test_game_between_random_and_human_players():

        log("==============================================")
        log("test_game_between_random_and_human_players ...")
        log("==============================================")

        default_max_credit = PijersiState.get_max_credit()
        PijersiState.set_max_credit(10)

        game = Game()

        human_searcher = HumanSearcher("human")
        human_searcher.use_command_line(True)
        game.set_white_searcher(human_searcher)

        game.set_black_searcher(RandomSearcher("random"))

        game.start()

        while game.has_next_turn():
            game.next_turn()

        PijersiState.set_max_credit(default_max_credit)

        log("===============================================")
        log("test_game_between_random_and_human_players done")
        log("===============================================")


    def test_game_between_minimax_players(min_depth: int=1, max_depth: int=3, game_count: int=5, use_random_searcher: bool=True):

        log("=====================================")
        log(" test_game_between_minimax_players ...")
        log("=====================================")

        searcher_dict = {}

        if use_random_searcher:
            searcher_dict["random"] = RandomSearcher("random")

        minimax_depth_list = list(range(min_depth, max_depth + 1))

        for minimax_depth in minimax_depth_list:
            searcher_name = f"minimax{minimax_depth}"
            searcher = MinimaxSearcher(searcher_name, max_depth=minimax_depth)
            assert searcher_name not in searcher_dict
            searcher_dict[searcher_name] = searcher

        searcher_points = Counter()


        for x_searcher in searcher_dict.values():
            for y_searcher in searcher_dict.values():
                if x_searcher is y_searcher:
                    continue

                x_points = 0
                y_points = 0

                for game_index in range(game_count):

                    game = Game()
                    game.set_white_searcher(x_searcher)
                    game.set_black_searcher(y_searcher)
                    x_player = Player.T.WHITE
                    y_player = Player.T.BLACK

                    game.start()
                    while game.has_next_turn():
                        log("--> " + x_searcher.get_name() + " versus " +
                                       y_searcher.get_name() +  f" game_index: {game_index}")
                        game.next_turn()

                    rewards = game.get_rewards()

                    if rewards[x_player] == Reward.WIN:
                        x_points += 2

                    elif rewards[x_player] == Reward.DRAW:
                        x_points += 1

                    if rewards[y_player] == Reward.WIN:
                        y_points += 2

                    elif rewards[y_player] == Reward.DRAW:
                        y_points += 1


                log("game_count:", game_count, "/ x_points:", x_points, "/ y_points:", y_points)

                searcher_points[x_searcher.get_name()] += x_points
                searcher_points[y_searcher.get_name()] += y_points

        log()
        for (searcher_name, points) in sorted(searcher_points.items()):
            log(f"searcher {searcher_name} has {points} points")

        log()
        searcher_count = len(searcher_dict)
        searcher_game_count = 2*(searcher_count - 1)*game_count
        log("number of searchers:", searcher_count)
        log("number of games per searcher:", searcher_game_count)
        log()
        for (searcher_name, points) in sorted(searcher_points.items()):
            log(f"searcher {searcher_name} has {points/searcher_game_count:.3f} average points per game")

        log("=====================================")
        log("test_game_between_minimax_players done")
        log("=====================================")


    def test_two_turns_between_minimax_players():

        log("===========================================")
        log(" test_two_turns_between_minimax_players ...")
        log("===========================================")

        game = Game()

        game.set_white_searcher(MinimaxSearcher("minimax-3", max_depth=3))
        game.set_black_searcher(MinimaxSearcher("minimax-3", max_depth=3))

        game.start()

        turn_index = 0
        turn_count = 2
        while game.has_next_turn() and turn_index < turn_count  :
            turn_index += 1
            game.next_turn()


        log("===========================================")
        log("test_two_turns_between_minimax_players done")
        log("===========================================")



    def test_action_ugi_name():

        log("===========================")
        log("test_action_ugi_name ...")
        log("===========================")

        depth = 2
        searcher = MinimaxSearcher(f"minimax{depth}-inf", max_depth=depth)
        pijersi_state = PijersiState()
        action = searcher.search(pijersi_state)
        bestmove = action.to_ugi_name()
        log(f"bestmove = {bestmove}")
        assert bestmove == 'a5b6d5'

        log("===========================")
        log("test_action_ugi_name done")
        log("===========================")


    def test_game_between_ugi_players(depth: int=1, time_limit: int=20):

        log("=====================================")
        log(" test_game_between_ugi_players ...")
        log("=====================================")

        if False:
            server_executable_path = os.path.join(_package_home, "pijersi_cmalo_ugi_server.exe")
        else:
            server_executable_path = os.path.join(_package_home, "pijersi_ugi.py")

        ugi_client = make_ugi_client(server_executable_path, cerr=sys.stderr)
        ugi_client.ugi()
        isready = ugi_client.isready()
        assert isready == ['readyok']
        ugi_client_name = ugi_client.get_server_name()

        depth_searcher_name = f"{ugi_client_name}-{depth}-inf"
        time_searcher_name = f"{ugi_client_name}-x-{time_limit}s"

        depth_searcher = UgiSearcher(name=depth_searcher_name, ugi_client=ugi_client, max_depth=depth)
        time_searcher = UgiSearcher(name=time_searcher_name, ugi_client=ugi_client, time_limit=time_limit)

        game = Game()
        game.set_white_searcher(depth_searcher)
        game.set_black_searcher(time_searcher)

        game.start()

        while game.has_next_turn():
            game.next_turn()

        ugi_client.quit()

        log("=====================================")
        log("test_game_between_ugi_players done")
        log("=====================================")


    if False:
        test_encode_and_decode_hex_state()
        test_encode_and_decode_path_states()
        test_iterate_hex_states()
        PijersiState.log_tables()
        test_first_get_summary()

    if False:
        test_game_between_random_players()

    if False:
        test_game_between_random_and_human_players()

    if False:
        test_game_between_minimax_players(max_depth=2, game_count=1, use_random_searcher=True)

    if False:
        test_game_between_minimax_players(max_depth=3, game_count=1, use_random_searcher=False)

    if False:
        test_game_between_minimax_players(min_depth=2, max_depth=3, game_count=10, use_random_searcher=False)

    if False:
        test_two_turns_between_minimax_players()

    if False:
        test_action_ugi_name()

    if True:
        test_game_between_ugi_players(depth=1, time_limit=30)


def profile():


    def profile_get_actions():

        log()
        log("-- profile_get_actions --")

        profile_data['pijersi_state'] = PijersiState()

        cProfile.run('profile_fun_get_actions()', sort=SortKey.TIME)


    def profile_is_terminal():

        log()
        log("-- profile_is_terminal --")

        profile_data['pijersi_state'] = PijersiState()

        cProfile.run('profile_fun_is_terminal()', sort=SortKey.TIME)

    profile_is_terminal()
    profile_get_actions()


profile_data = {}


def profile_fun_get_actions():
    #>> Defined at the uper scope of the module because of "cProfile.run"

    pijersi_state = profile_data['pijersi_state']

    for _ in range(100):
        actions = pijersi_state.get_actions(use_cache=False)
        assert actions is not None


def profile_fun_is_terminal():
    #>> Defined at the uper scope of the module because of "cProfile.run"

    pijersi_state = profile_data['pijersi_state']

    for _ in range(1_000):
        assert not pijersi_state.is_terminal(use_cache=False)


def main():

    if True:
        test()

    if False:
        profile()


if __name__ == "__main__":
    # >> "freeze_support()" is needed with using pijersi_gui as a single executable made by PyInstaller
    # >> otherwise when starting another process by "PoolExecutor" a second GUI windows is created
    freeze_support()

    log()
    log("Hello")
    log()
    log(f"Python sys.version = {sys.version}")

    main()

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

    if True:
        log()
        _ = input("main: done ; press enter to terminate")
