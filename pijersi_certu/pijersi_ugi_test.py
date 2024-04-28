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

    finally:
        client.quit()

    log()
    log("test_ugi_protocol: done")


if __name__ == "__main__":

    test_ugi_protocol()

    log()
    _ = input("press enter to terminate")
