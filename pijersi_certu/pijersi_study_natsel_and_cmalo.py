#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_study_natsel_and_cmalo.py compares the two AI-engines NATURAL-SELECTION and CMALO"""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

from datetime import datetime
import hashlib
import os
import sys
import time

from collections import Counter
import multiprocessing

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)


from pijersi_rules import Game
from pijersi_rules import MinimaxSearcher
from pijersi_rules import Player
from pijersi_rules import Setup
from pijersi_rules import Reward

from pijersi_ugi import UgiClient
from pijersi_ugi import UgiSearcher


def log(msg: str=None):
    if msg is None:
        print("", file=sys.stderr, flush=True)
    else:
        for line in msg.split('\n'):
            print(f"{line}", file=sys.stderr, flush=True)


def run_one_game(setup, white_searcher, black_searcher):
    game = Game(setup=setup)
    game.enable_log(False)

    game.set_white_searcher(white_searcher)
    game.set_black_searcher(black_searcher)

    game.start()
    game_hasher = hashlib.sha256()

    while game.has_next_turn():
        game_hasher.update(game.get_state().get_board_codes())
        game.next_turn()
        
    game_hasher.update(game.get_state().get_board_codes())
    game_hash = game_hasher.digest()

    rewards = game.get_rewards()
    
    (white_points, black_points) = (0, 0)

    if rewards[Player.T.WHITE] == Reward.WIN:
        white_points = 2

    elif rewards[Player.T.WHITE] == Reward.DRAW:
        white_points = 1

    if rewards[Player.T.BLACK] == Reward.WIN:
        black_points = 2

    elif rewards[Player.T.BLACK] == Reward.DRAW:
        black_points = 1

    return (white_points, black_points, game_hash)


def study(setup: Setup.T=Setup.T.CLASSIC, natsel_start=True, natsel_depth: int=None, cmalo_depth: int=None, depth: int=1, game_count: int=1):

    study_start = time.time()

    log()
    log("===================================================================")
    log(f" study ... / start = {datetime.fromtimestamp(study_start).isoformat()}")
    log("===================================================================")


    if natsel_depth is None:
        natsel_depth = depth

    if cmalo_depth is None:
        cmalo_depth = depth

    natsel_server_executable_path = os.path.join(_package_home, "ugi-servers", "natsel", "pijersi_natural_selection_ugi_server_v1.2.1_windows_x86_64.exe")

    ugi_client = UgiClient(name="natsel", server_executable_path=natsel_server_executable_path, permanent=False)
    ugi_client_name = ugi_client.get_name()

    natsel_searcher_name = f"{ugi_client_name}-depth-{natsel_depth}"
    natsel_searcher = UgiSearcher(name=natsel_searcher_name, ugi_client=ugi_client, max_depth=natsel_depth)

    cmalo_searcher_name = f"cmalo-depth-{cmalo_depth}"
    cmalo_searcher = MinimaxSearcher(cmalo_searcher_name, max_depth=cmalo_depth)

    searcher_dict = {}
    searcher_dict[cmalo_searcher_name] = cmalo_searcher
    searcher_dict[natsel_searcher_name] = natsel_searcher

    if natsel_start:
        white_searcher = natsel_searcher
        black_searcher = cmalo_searcher
    else:
       white_searcher = cmalo_searcher
       black_searcher = natsel_searcher

    log(f"setup: {Setup.to_name(setup)} / white player: {white_searcher.get_name()} / black player: {black_searcher.get_name()} / game_count: {game_count}")

    with multiprocessing.Pool(processes=10) as pool:
        game_outputs = pool.starmap(run_one_game, ((setup, white_searcher, black_searcher) for game_index in range(game_count)))

    searcher_points = Counter()
    searcher_points[white_searcher.get_name()] = sum((white_points for (white_points, _, _) in game_outputs))
    searcher_points[black_searcher.get_name()] = sum((black_points for (_, black_points, _) in game_outputs))
    
    game_hash_set = set((game_hash for (_, _, game_hash) in game_outputs))

    log()
    log(f"effective game count: {len(game_hash_set)}")

    log()
    log(f"white_points: {searcher_points[white_searcher.get_name()]} / black_points: {searcher_points[black_searcher.get_name()]}")
    log()
    for (searcher_name, points) in sorted(searcher_points.items()):
        log(f"searcher {searcher_name} has {points} points")

    log()
    searcher_count = len(searcher_dict)
    searcher_game_count = game_count
    log(f"number of searchers: {searcher_count}")
    log(f"number of games per searcher: {searcher_game_count}")
    log()
    for (searcher_name, points) in sorted(searcher_points.items()):
        log(f"searcher {searcher_name} has {points/searcher_game_count:.3f} average points per game")

    study_end = time.time()
    study_duration = study_end - study_start

    log("===================================================================")
    log(f" study done / end = {datetime.fromtimestamp(study_end).isoformat()} / duration = {study_duration:.0f} s")
    log("===================================================================")


def main():

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=True, depth=1, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=False, depth=1, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=True, depth=1, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=False, depth=1, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=True, depth=2, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=False, depth=2, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=True, depth=2, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=False, depth=2, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=True, depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=False, depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=True, depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=False, depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=True, natsel_depth=5, cmalo_depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=False, natsel_depth=5, cmalo_depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=True, natsel_depth=5, cmalo_depth=3, game_count=1_000)

    if True:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=False, natsel_depth=5, cmalo_depth=3, game_count=1_000)

if __name__ == "__main__":

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
