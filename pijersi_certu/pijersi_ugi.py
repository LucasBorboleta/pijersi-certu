#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_ugi.py implements the UGI protocol for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.
PIJERSI-CERTU-UGI-SERVER implements the Universal Game Protocol (UGI).

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import os
from subprocess import PIPE
from subprocess import Popen
import sys

from typing import List
from typing import Self
from typing import TextIO
from typing import Tuple


_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules

class UgiChannel:

    SEPARATOR = ' '
    TERMINATOR = '\n'

    def __init__(self, cin: TextIO, cout: TextIO):
        self.__cin = cin
        self.__cout = cout


    @staticmethod
    def make_std_channel() -> Self:
        return  UgiChannel(cin=sys.stdin, cout=sys.stdout)


    def make_dual_channel(self) -> Self:
        return  UgiChannel(cin=self.__cout, cout=self.__cin)


    def send(self, data: List[str]):
        line = UgiChannel.SEPARATOR.join(data) + UgiChannel.TERMINATOR
        self.__cout.write(line)
        self.__cout.flush()


    def recv(self) -> List[str]:
        line = self.__cin.readline()
        self.__cin.flush()

        cleaned_line = line.strip(UgiChannel.SEPARATOR + UgiChannel.TERMINATOR)

        if len(cleaned_line) == 0:
            data = []
        else:
            data = cleaned_line.split(UgiChannel.SEPARATOR)

        return data


class UgiClient:

    def __init__(self, server_process: Popen, channel: UgiChannel):
        self.__server_process = server_process
        self.__channel = channel
        self.__debugging = True


    def __log(self, message: str, category=''):
        for line in message.split('\n'):
            print(f"{category}UgiClient:{line}", file=sys.stderr, flush=True)


    def __log_debug(self, message: str):
        if self.__debugging:
            self.__log(message, category='debug:')


    def __log_error(self, message: str):
        self.__log(message, category='error:')


    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log_debug(f"__send: {data}")


    def __recv(self) -> List[str]:
        data =  self.__channel.recv()
        self.__log_debug(f"__recv: {data}")
        return data


    def ugi(self):
        self.__send(['ugi'])
        answer = self.__recv()
        self.__log_debug(f"ugi: answer {answer}")
        assert answer == ['ugiok']


    def quit(self):
        self.__send(['quit'])

        # wait just for nicely logging when debugging
        _ = self.__server_process.wait(timeout=1)


class UgiServer:

    def __init__(self, channel: UgiChannel):
        self.__channel = channel
        self.__running = False
        self.__debugging = True


    def __log(self, message: str, category=''):
        for line in message.split('\n'):
            print(f"{category}UgiServer:{line}", file=sys.stderr, flush=True)


    def __log_debug(self, message: str):
        if self.__debugging:
            self.__log(message, category='debug:')


    def __log_error(self, message: str):
        self.__log(message, category='error:')


    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log_debug(f"__send: {data}")


    def __recv(self) -> List[str]:
        data = self.__channel.recv()
        self.__log_debug(f"__recv: {data}")
        return data


    def stop(self):
        self.__running = False


    def start(self):
        assert not self.__running
        self.__running = True

        commands = {}
        commands['ugi'] = self.__ugi
        commands['quit'] = self.__quit


        while self.__running:
            data = self.__recv()

            if len(data) == 0:
                self.__log_error("no command received ; UGI server stops itself !")
                self.stop()
                continue
            else:
                name = data[0]
                args = data[1:]

            if name not in commands:
                self.__log_error(f"unknown command '{name}' ; UGI server stops itself !")
                self.stop()
                continue
            else:
                commands[name](args)


    def __ugi(self, args: List[str]):
        self.__log_debug(f"__ugi: args = {args}")
        self.__send(['ugiok'])


    def __quit(self, args: List[str]):
        self.__log_debug(f"__quit: args = {args}")
        self.stop()


def make_ugi_server_process(server_executable_path: str, cerr: TextIO=sys.stderr) -> Tuple[Popen, UgiChannel]:

    if server_executable_path.endswith(".py"):
        popen_args = [sys.executable, server_executable_path]
    else:
        popen_args = [server_executable_path]

    server_process = Popen(args=popen_args,
                           shell=False,
                           text=True,
                           stdin=PIPE, stdout=PIPE, stderr=cerr)

    server_channel = UgiChannel(cin=server_process.stdin, cout=server_process.stdout)

    return (server_process, server_channel)


def start_ugi_server_implementation():

    print("", file=sys.stderr, flush=True)
    print(f"Hello from PIJERSI-CERTU-UGI-SERVER-v{rules.__version__}", file=sys.stderr, flush=True)
    print(_COPYRIGHT_AND_LICENSE, file=sys.stderr, flush=True)

    server_channel = UgiChannel.make_std_channel()
    server = UgiServer(channel=server_channel)
    server.start()

    print("", file=sys.stderr, flush=True)
    print(f"Bye from PIJERSI-CERTU-UGI-SERVER-v{rules.__version__}", file=sys.stderr, flush=True)


def make_ugi_client(server_executable_path: str, cerr: TextIO=sys.stderr) -> UgiClient:
    (server_process, server_channel) = make_ugi_server_process(server_executable_path, cerr)

    client_channel = server_channel.make_dual_channel()
    client = UgiClient(server_process=server_process, channel=client_channel)

    return client


if __name__ == "__main__":
    start_ugi_server_implementation()
    sys.exit()
