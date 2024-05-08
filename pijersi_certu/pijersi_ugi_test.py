#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_ugi_test.py tests the UGI protocol for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import os
import sys
import time

from multiprocessing import freeze_support
import multiprocessing

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)


from pijersi_ugi import make_ugi_client


def log(msg: str=None):
    if msg is None:
        print("", file=sys.stderr, flush=True)
    else:
        for line in msg.split('\n'):
            print(f"pijersi_ugi_test: {line}", file=sys.stderr, flush=True)


def test_ugi_protocol():

    log()
    log("test_ugi_protocol: ...")

    if True:
        server_executable_path = os.path.join(_package_home, "pijersi_ugi.py")
    else:
        server_executable_path = os.path.join(_package_home, "pijersi_certu_ugi_server.exe")


    log()
    log(f"server_executable_path = {server_executable_path}")

    client = make_ugi_client(server_executable_path, cerr=sys.stderr)

    log()

    try:
        client.ugi()

        client.setoption(name='depth', value='2')

        isready = client.isready()
        assert isready == ['readyok']


        client.uginewgame()

        gameover = client.query_gameover()
        assert gameover == ['false']

        p1turn = client.query_p1turn()
        assert p1turn == ['true']

        result = client.query_result()
        assert result == ['none']

        islegal = client.query_islegal('a5b5d6')
        assert islegal == ['true']

        islegal = client.query_islegal('b7c6')
        assert islegal == ['true']

        islegal = client.query_islegal('b4c4c4')
        assert islegal == ['true']

        islegal = client.query_islegal('b4c2')
        assert islegal == ['false']

        fen = client.query_fen()
        assert fen == ['s-p-r-s-p-r-/p-r-s-wwr-s-p-/6/7/6/P-S-R-WWS-R-P-/R-P-S-R-P-S-', 'w', '0', '1']

        client.go_manual('b7c6')
        fen = client.query_fen()
        assert fen == ['s-p-r-s-p-r-/p-r-s-wwr-s-p-/6/7/5P-/P-S-R-WWS-R-1/R-P-S-R-P-S-', 'b', '1', '1']

        client.go_manual('f7f6d5')
        fen = client.query_fen()
        assert fen == ['s-p-r-s-p-r-/p-r-s-wwr-2/6/4sp2/5P-/P-S-R-WWS-R-1/R-P-S-R-P-S-', 'w', '2', '2']

        client.go_manual('a6b6d5')
        fen = client.query_fen()
        assert fen == ['s-p-r-s-p-r-/p-r-s-wwr-2/6/4RS2/5P-/P-S-R-WWS-2/R-P-S-R-P-1', 'b', '0', '2']

        client.go_manual('g6g5f6')
        fen = client.query_fen()
        assert fen == ['s-p-r-s-2/p-r-s-wwr-pr1/6/4RS2/5P-/P-S-R-WWS-2/R-P-S-R-P-1', 'w', '1', '3']


        client.uginewgame()

        gameover = client.query_gameover()
        assert gameover == ['false']

        p1turn = client.query_p1turn()
        assert p1turn == ['true']

        result = client.query_result()
        assert result == ['none']

        bestmove = client.go_depth_and_wait(2)
        # assert bestmove == 'a5b6d5'

        bestmove = client.go_movetime_and_wait(2_000)
        # assert bestmove == 'a5b6c6' # >> best opening move from minimax-4

        if True:
            log()
            client.uginewgame()

            iter_index = -1
            while True:
                iter_index += 1

                fen = client.query_fen()
                log()
                log(f"fen = {fen}")

                gameover = client.query_gameover()
                if gameover == ['true']:
                    break

                if iter_index % 2 == 0:
                    bestmove = client.go_movetime_and_wait(10_000)
                    log(f"bestmove = {bestmove} after client.go_movetime_and_wait")
                else:
                    client.go_movetime(10_000)
                    time.sleep(0.001)
                    bestmove = client.stop()
                    log(f"bestmove = {bestmove} after client.go_movetime")

                client.go_manual(bestmove)

            result = client.query_result()
            log(f"result = {result}")

        if False:
            log()
            client.uginewgame()

            while True:
                fen = client.query_fen()
                log(f"fen = {fen}")

                gameover = client.query_gameover()
                if gameover == ['true']:
                    break

                bestmove = client.go_depth_and_wait(2)
                log(f"bestmove = {bestmove}")
                client.go_manual(bestmove)

            result = client.query_result()
            log(f"result = {result}")


    finally:
        client.quit()

    log()
    log("test_ugi_protocol: done")


if __name__ == "__main__":
    # >> "freeze_support()" is needed with using pijersi_gui as a single executable made by PyInstaller
    # >> otherwise when starting another process by "PoolExecutor" a second GUI windows is created
    freeze_support()

    test_ugi_protocol()

    # >> clean any residual process
    if len(multiprocessing.active_children()) > 0:

        for child_process in multiprocessing.active_children():
            try:
                child_process.terminate()
            except:
                pass

    log()
    _ = input("press enter to terminate")
