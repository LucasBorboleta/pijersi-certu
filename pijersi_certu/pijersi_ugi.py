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
        assert len(data) != 0

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

        assert len(data) != 0
        return data


class UgiClient:

    def __init__(self, server_process: Popen, channel: UgiChannel):
        self.__server_process = server_process
        self.__channel = channel
        self.__debugging = False

        self.__server_name = None
        self.__server_author = None
        self.__options = {}


    def __log(self, message: str, category=''):
        for line in message.split('\n'):
            print(f"{category}UgiClient:{line}", file=sys.stderr, flush=True)


    def __log_debug(self, message: str):
        if self.__debugging:
            self.__log(message, category='debug:')


    def __log_error(self, message: str):
        self.__log(message, category='error:')


    def __log_info(self, message: str):
        self.__log(message, category='info:')


    def __recv(self) -> List[str]:
        data =  self.__channel.recv()
        self.__log_debug(f"__recv: {data}")
        return data


    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log_debug(f"__send: {data}")


    def isready(self) -> bool:
        self.__send(['isready'])

        reply = self.__recv()
        return reply


    def query_gameover(self) -> List[str]:
        self.__send(['query', 'gameover'])

        gameover = self.__recv()
        return gameover


    def query_islegal(self, move: str) -> List[str]:
        self.__send(['query', 'islegal', move])

        islegal = self.__recv()
        return islegal


    def query_p1turn(self) -> List[str]:
        self.__send(['query', 'p1turn'])

        result = self.__recv()
        return result


    def query_result(self) -> List[str]:
        self.__send(['query', 'result'])

        result = self.__recv()
        return result


    def quit(self):
        self.__send(['quit'])

        # wait just for nicely logging when debugging
        _ = self.__server_process.wait(timeout=1)


    def uginewgame(self):
        self.__send(['uginewgame'])


    def setoption(self, name: str, value: str):
        self.__send(['setoption', 'name', name, 'value', value])


    def ugi(self):
        self.__log_debug("ugi: ...")
        self.__send(['ugi'])

        while True:
            reply = self.__recv()
            self.__log_debug(f"ugi: reply {reply}")

            reply_head = reply[0]
            reply_tail = reply[1:]

            if reply_head == 'ugiok':

                if len(reply_tail) != 0:
                    self.__log_info(f"ugi: ignoring extra tokens in reply '{reply}'")
                break

            elif reply_head == 'id':

                if len(reply) != 3:
                    self.__log_info(f"ugi: expected 3 tokens ; ignoring reply '{reply}'")
                    continue

                elif reply_tail[0] == 'name':
                    self.__server_name = reply_tail[1]

                elif reply_tail[0] == 'author':
                    self.__server_author = reply_tail[1]

                else:
                    self.__log_info(f"ugi: unexpected token '{reply_tail[0]}' ; ignoring reply '{reply}'")
                    continue

            elif reply_head == 'option':

                if len(reply_tail) < 2 or reply_tail[0] != 'name':
                    self.__log_info(f"ugi: cannot find/match token 'name' ; ignoring reply '{reply}'")
                    continue

                option_name = reply_tail[1]
                option_props = reply_tail[2:]

                if len(option_props) % 2 != 0:
                    self.__log_info(f"ugi: cannot pair property tokens ; ignoring reply '{reply}'")
                    continue

                option_prop_keys = option_props[0::2]
                option_prop_vals = option_props[1::2]
                self.__options[option_name] = {key:val for (key, val) in zip(option_prop_keys, option_prop_vals)}

            else:
                self.__log_info(f"ugi: unexpected head '{reply_head}' ; ignoring reply '{reply}'")
                continue

        self.__log_debug(f"ugi: server_name = '{self.__server_name}' ; server_author = '{self.__server_author}'")
        self.__log_debug(f"ugi: options = '{self.__options}'")

        self.__log_debug("ugi: done")


class UgiServer:

    def __init__(self, channel: UgiChannel):
        self.__channel = channel
        self.__running = False
        self.__debugging = False

        self.__server_name = 'certu'
        self.__server_author = 'lucas.borboleta@free.fr'

        self.__options = {}
        self.__option_converters = {}

        self.__options['depth'] = 2
        self.__option_converters['depth'] = int

        self.__pijser_state = None


    def __log(self, message: str, category=''):
        for line in message.split('\n'):
            print(f"{category}UgiServer:{line}", file=sys.stderr, flush=True)


    def __log_debug(self, message: str):
        if self.__debugging:
            self.__log(message, category='debug:')


    def __log_error(self, message: str):
        self.__log(message, category='error:')


    def __log_info(self, message: str):
        self.__log(message, category='info:')


    def __recv(self) -> List[str]:
        data = self.__channel.recv()
        self.__log_debug(f"__recv: {data}")
        return data


    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log_debug(f"__send: {data}")


    def run(self):
        try:
            assert not self.__running
            self.__running = True

            commands = {}
            commands['isready'] = self.__isready
            commands['query'] = self.__query
            commands['quit'] = self.__quit
            commands['setoption'] = self.__setoption
            commands['ugi'] = self.__ugi
            commands['uginewgame'] = self.__uginewgame

            while self.__running:
                data = self.__recv()

                cmd_name = data[0]
                cmd_args = data[1:]

                if cmd_name not in commands:
                    self.__log_error(f"unknown command '{cmd_name}' ; UGI server terminates itself !")
                    self.terminate()
                    continue
                else:
                    commands[cmd_name](cmd_args)
        finally:
            self.terminate()


    def terminate(self):
        self.__running = False


    def __isready(self, args: List[str]):

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'isready {" ".join(args)}'""")

        self.__send(['readyok'])


    def __query(self, args: List[str]):

        if len(args) < 1:
            self.__log_info("nothing to query ; UGI server terminates itself !")
            self.terminate()
            return

        query_name = args[0]
        query_args = args[1:]

        if query_name not in  ['gameover', 'p1turn', 'result', 'islegal']:
            self.__log_info("unknown query '{query_name}' ; UGI server terminates itself !")
            self.terminate()
            return

        if self.__pijersi_state is None:
            self.__log_info("no pijersi state to query ; UGI server terminates itself !")
            self.terminate()
            return

        if query_name == 'gameover':

            if self.__pijersi_state.is_terminal():
                self.__send(['true'])
            else:
                self.__send(['false'])

        elif query_name == 'p1turn':

            if self.__pijersi_state.is_terminal():
                self.__send(['false'])

            elif self.__pijersi_state.get_current_player() == rules.Player.T.WHITE:
                self.__send(['true'])

            else:
                self.__send(['false'])

        elif query_name == 'result':

            if not self.__pijersi_state.is_terminal():
                self.__send(['none'])
            else:
                reward = self.__pijersi_state.get_rewards()

                if reward[0] == rules.Reward.WIN:
                    self.__send(['p1win'])

                elif reward[1] == rules.Reward.WIN:
                    self.__send(['p2win'])

                elif reward[0] == rules.Reward.DRAW:
                    self.__send(['draw'])

        elif query_name == 'islegal':

            if len(query_args) < 1:

                self.__log_info(f"""missing move in command 'query {" ".join(args)}' ; """ +
                                "UGI server terminates itself !")
                self.terminate()
                return

            if len(query_args) > 1:
                self.__log_info(f"""ignoring extra tokens in command 'query {" ".join(args)}'""")

            move = query_args[0]

            if self.__pijersi_state.is_terminal():
                legal_moves = []
            else:
                legal_moves = self.__pijersi_state.get_action_ugi_names()

            if move in legal_moves:
                self.__send(['true'])
            else:
                self.__send(['false'])


    def __quit(self, args: List[str]):

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'quit {" ".join(args)}'""")

        self.terminate()


    def __setoption(self, args: List[str]):

        if len(args) != 4 or args[0] != 'name' or args[2] != 'value':
            self.__log_info("cannot find/match tokens 'name' and 'value' ; " +
                            f"""ignoring command 'setoption {" ".join(args)}'""")
        else:
            option_name = args[1]
            option_value = args[3]

            if option_name not in self.__options:
                self.__log_info(f"unknown option '{option_name}' ; " +
                                f"""ignoring command 'setoption {" ".join(args)}'""")

            else:
                self.__options[option_name] = self.__option_converters[option_name](option_value)

        self.__log_debug(f"__setoption: __options = {self.__options}")


    def __ugi(self, args: List[str]):

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'ugi {" ".join(args)}'""")

        self.__send(['id', 'name', self.__server_name])
        self.__send(['id', 'author', self.__server_author])

        self.__send(['option', 'name', 'depth',
                               'type', 'spin',
                               'default', '2',
                               'min', '1',
                               'max', '4'])

        self.__send(['ugiok'])


    def __uginewgame(self, args: List[str]):

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'uginewgame {" ".join(args)}'""")

        self.__pijersi_state = rules.PijersiState()


def make_ugi_client(server_executable_path: str, cerr: TextIO=sys.stderr) -> UgiClient:
    (server_process, server_channel) = make_ugi_server_process(server_executable_path, cerr)

    client_channel = server_channel.make_dual_channel()
    client = UgiClient(server_process=server_process, channel=client_channel)

    return client


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


def run_ugi_server_implementation():

    print("", file=sys.stderr, flush=True)
    print(f"Hello from PIJERSI-CERTU-UGI-SERVER-v{rules.__version__}", file=sys.stderr, flush=True)
    print(_COPYRIGHT_AND_LICENSE, file=sys.stderr, flush=True)

    server_channel = UgiChannel.make_std_channel()
    server = UgiServer(channel=server_channel)
    server.run()

    print("", file=sys.stderr, flush=True)
    print(f"Bye from PIJERSI-CERTU-UGI-SERVER-v{rules.__version__}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    run_ugi_server_implementation()
    sys.exit()
