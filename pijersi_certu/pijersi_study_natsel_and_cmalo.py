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

import os
import sys

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


def study(setup: Setup.T=Setup.T.CLASSIC, natsel_start=True, depth: int=1, game_count: int=2):

    log("=====================================")
    log(" study ...")
    log("=====================================")

    natsel_server_executable_path = os.path.join(_package_home, "ugi-servers", "natsel", "pijersi_natural_selection_ugi_server_v0.1.0.exe")

    ugi_client = UgiClient(name="natsel", server_executable_path=natsel_server_executable_path, permanent=True)
    ugi_client_name = ugi_client.get_name()
    ugi_client.run()

    natsel_searcher_name = f"{ugi_client_name}-depth-{depth}"
    natsel_searcher = UgiSearcher(name=natsel_searcher_name, ugi_client=ugi_client, max_depth=depth)

    cmalo_searcher_name = f"cmalo-depth-{depth}"
    cmalo_searcher = MinimaxSearcher(cmalo_searcher_name, max_depth=depth)

    searcher_dict = {}
    searcher_dict[cmalo_searcher_name] = cmalo_searcher
    searcher_dict[natsel_searcher_name] = natsel_searcher

    if natsel_start:
        white_searcher = natsel_searcher
        black_searcher = cmalo_searcher
    else:
       white_searcher = cmalo_searcher
       black_searcher = natsel_searcher

    searcher_points = Counter()

    white_points = 0
    black_points = 0

    white_player = Player.T.WHITE
    black_player = Player.T.BLACK

    for game_index in range(game_count):

        game = Game(setup=setup)

        game.set_white_searcher(white_searcher)
        game.set_black_searcher(black_searcher)

        game.start()
        while game.has_next_turn():
            log("--> " + white_searcher.get_name() + " versus " +
                         black_searcher.get_name() +  f" game_index: {game_index}")
            game.next_turn()

        rewards = game.get_rewards()

        if rewards[white_player] == Reward.WIN:
            white_points += 2

        elif rewards[white_player] == Reward.DRAW:
            white_points += 1

        if rewards[black_player] == Reward.WIN:
            black_points += 2

        elif rewards[black_player] == Reward.DRAW:
            black_points += 1

    log("=====================================")

    log()
    log(f"setup: {Setup.to_name(setup)} / white player: {white_searcher.get_name()} / black player: {black_searcher.get_name()}")

    log()
    log(f"game_count: {game_count} / white_points: {white_points} / black_points: {black_points}")

    searcher_points[white_searcher.get_name()] += white_points
    searcher_points[black_searcher.get_name()] += black_points

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

    ugi_client.quit()

    log("=====================================")
    log("study done")
    log("=====================================")


def main():

    if False:
        study(setup=Setup.T.CLASSIC, natsel_start=True, depth=1, game_count=100)
        _ = """
        setup: classic / white player: natsel-depth-1 / black player: cmalo-depth-1
        
        game_count: 100 / white_points: 0 / black_points: 200
        
        searcher cmalo-depth-1 has 200 points
        searcher natsel-depth-1 has 0 points
        
        number of searchers: 2
        number of games per searcher: 100
        
        searcher cmalo-depth-1 has 2.000 average points per game
        searcher natsel-depth-1 has 0.000 average points per game
        """

    if False:
        study(setup=Setup.T.CLASSIC, natsel_start=False, depth=1, game_count=100)
        _ = """
        setup: classic / white player: cmalo-depth-1 / black player: natsel-depth-1
        
        game_count: 100 / white_points: 200 / black_points: 0
        
        searcher cmalo-depth-1 has 200 points
        searcher natsel-depth-1 has 0 points
        
        number of searchers: 2
        number of games per searcher: 100
        
        searcher cmalo-depth-1 has 2.000 average points per game
        searcher natsel-depth-1 has 0.000 average points per game
        """

    if False:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=True, depth=1, game_count=100)
        _ = """
        setup: half-random / white player: natsel-depth-1 / black player: cmalo-depth-1
        
        game_count: 100 / white_points: 58 / black_points: 142
        
        searcher cmalo-depth-1 has 142 points
        searcher natsel-depth-1 has 58 points
        
        number of searchers: 2
        number of games per searcher: 100
        
        searcher cmalo-depth-1 has 1.420 average points per game
        searcher natsel-depth-1 has 0.580 average points per game
        """

    if False:
        study(setup=Setup.T.HALF_RANDOM, natsel_start=False, depth=1, game_count=100)
        _ = """
        setup: half-random / white player: cmalo-depth-1 / black player: natsel-depth-1
        
        game_count: 100 / white_points: 68 / black_points: 132
        
        searcher cmalo-depth-1 has 68 points
        searcher natsel-depth-1 has 132 points
        
        number of searchers: 2
        number of games per searcher: 100
        
        searcher cmalo-depth-1 has 0.680 average points per game
        searcher natsel-depth-1 has 1.320 average points per game
        """

    if True:
        study(setup=Setup.T.CLASSIC, natsel_start=True, depth=2, game_count=100)
        _ = """

        """

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
