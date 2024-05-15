#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_ugi.py implements the UGI protocol for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CMALO-UGI-SERVER implements the Universal Game Protocol (UGI).

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
from typing import Optional
from typing import Self
from typing import TextIO
from typing import Tuple

from multiprocessing import freeze_support

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules


def log(msg: str=None):
    if msg is None:
        print("", file=sys.stderr, flush=True)
    else:
        for line in msg.split('\n'):
            print(f"{line}", file=sys.stderr, flush=True)


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


    def __init__(self, name: str, server_executable_path: str):
        self.__name = name
        self.__server_executable_path = server_executable_path

        self.__server_process = None
        self.__channel = None

        self.__debugging = False

        self.__server_name = None
        self.__server_author = None
        self.__options = {}


    def get_name(self) -> str:
        return self.__name


    def get_server_name(self) -> str:
        assert self.__server_name is not None
        return self.__server_name


    def get_server_author(self) -> str:
        assert self.__server_author is not None
        return self.__server_author


    def start(self) -> None:
        (server_process, server_channel) = make_ugi_server_process(self.__server_executable_path)
        self.__server_process = server_process
        self.__channel = server_channel.make_dual_channel()


    def __log(self, message: str, category='') -> None:
        for line in message.split('\n'):
            print(f"{category}:UgiClient:{line}", file=sys.stderr, flush=True)


    def __log_debug(self, message: str) -> None:
        if self.__debugging:
            self.__log(message, category='debug:')


    def __log_error(self, message: str) -> None:
        self.__log(message, category='error:')


    def __log_info(self, message: str) -> None:
        self.__log(message, category='info:')


    def __recv(self) -> List[str]:
        data =  self.__channel.recv()
        self.__log_debug(f"__recv: {data}")
        return data


    def __send(self, data: List[str]) -> None:
        self.__channel.send(data)
        self.__log_debug(f"__send: {data}")


    def __handle_bestmove_reply(self) -> str:

        while True:
            reply = self.__recv()
            self.__log_debug(f"__handle_bestmove_reply: reply {reply}")

            reply_head = reply[0]
            reply_tail = reply[1:]

            if reply_head == 'bestmove':

                assert len(reply_tail) >= 1
                bestmove = reply_tail[0]

                if len(reply_tail) > 1:
                    self.__log_info(f"__handle_bestmove_reply: ignoring extra tokens in reply '{reply}'")
                break

            elif reply_head == 'info':
                self.__log_info(f"__handle_bestmove_reply: '{reply}'")

            else:
                self.__log_info(f"__handle_bestmove_reply: unexpected head '{reply_head}' ; ignoring reply '{reply}'")
                continue

        return bestmove


    def go_depth_and_wait(self, depth: int) -> str:
        assert depth >= 1
        self.__send(['go', 'depth', str(depth)])

        bestmove = self.__handle_bestmove_reply()
        return bestmove


    def go_manual(self, move: str) -> None:
        self.__send(['go', 'manual', move])


    def go_movetime_and_wait(self, time_ms: float) -> str:
        assert time_ms > 0
        self.__send(['go', 'movetime', str(time_ms)])

        bestmove = self.__handle_bestmove_reply()
        return bestmove


    def isready(self) -> bool:
        self.__send(['isready'])

        reply = self.__recv()
        return reply


    def position_fen(self, fen: Optional[List[str]]=None, moves: Optional[List[str]]=None) -> None:
        send_args = ['position', 'fen']

        if fen is not None:
            send_args += fen

        if moves is not None and len(moves) != 0:
            send_args += ['moves'] + moves

        self.__send(send_args)


    def position_startpos(self, moves: Optional[List[str]]) -> None:
        if moves is None or len(moves) == 0:
            self.__send(['position', 'startpos'])
        else:
            self.__send(['position', 'startpos', 'moves'] + moves)


    def query_fen(self) -> List[str]:
        self.__send(['query', 'fen'])

        fen = self.__recv()
        return fen


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
        if self.__server_process is not None and self.__channel is not None:

            self.__send(['quit'])

            # wait just for nicely logging when debugging
            if self.__debugging:
                try:
                    _ = self.__server_process.wait(timeout=0.01)
                except:
                    pass

            else:
                try:
                    self.__server_process.terminate()
                except:
                    pass

        self.__server_process = None
        self.__channel = None


    def uginewgame(self):
        self.__send(['uginewgame'])


    def setoption(self, name: str, value: str):
        self.__send(['setoption', 'name', name, 'value', value])


    def stop(self) -> str:
        self.__log_error("stop: not implemented !")
        assert False

        self.__send(['stop'])
        bestmove = self.__handle_bestmove_reply()
        return bestmove


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

        self.__server_name = 'cmalo'
        self.__server_author = 'lucas.borboleta@free.fr'

        self.__options = {}
        self.__option_converters = {}

        # options with default values and associated converters
        self.__options['depth'] = 2
        self.__option_converters['depth'] = int

        self.__pijser_state = None


    def __log(self, message: str, category=''):
        for line in message.split('\n'):
            print(f"{category}:UgiServer:{line}", file=sys.stderr, flush=True)


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


    def run(self) -> None:
        try:
            assert not self.__running
            self.__running = True

            commands = {}
            commands['isready'] = self.__isready
            commands['go'] = self.__go
            commands['position'] = self.__position
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


    def terminate(self) -> None:
        self.__running = False


    def __go(self, args: List[str]) -> None:

        if len(args) != 2:
            self.__log_error("wrong number of 'go' arguments ; UGI server terminates itself !")
            self.terminate()
            return

        if self.__pijersi_state is None:
            self.__log_error("no pijersi state ; UGI server terminates itself !")
            self.terminate()
            return

        if args[0] == 'manual':
            move = args[1]
            new_pijersi_state = self.__pijersi_state.take_action_by_ugi_name(move)
            self.__pijersi_state = new_pijersi_state

        elif args[0] == 'depth':
            depth = int(args[1])
            searcher = rules.MinimaxSearcher(f"minimax{depth}-inf", max_depth=depth)

            action = searcher.search(self.__pijersi_state)
            bestmove = action.to_ugi_name()
            self.__send(['bestmove', bestmove])

        elif args[0] == 'movetime':
            time_ms = float(args[1])

            time_s = time_ms/1_000

            if time_s <= 20:
                depth = 2

            elif time_s <=  2*60:
                depth = 3

            else:
                depth = 4

            searcher = rules.MinimaxSearcher(f"minimax{depth}-{time_s:.0f}s", max_depth=depth, time_limit=time_s)

            action = searcher.search(self.__pijersi_state)
            bestmove = action.to_ugi_name()
            self.__send(['bestmove', bestmove])

        else:
            self.__log_error("wrong 'go' arguments ; UGI server terminates itself !")
            self.terminate()
            return


    def __isready(self, args: List[str]) -> None:

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'isready {" ".join(args)}'""")

        self.__send(['readyok'])


    def __position(self, args: List[str]) -> None:
        if len(args) < 1:
            self.__log_error("missing arguments for 'position' ; UGI server terminates itself !")
            self.terminate()
            return

        if args[0] == 'startpos':
            self.__pijersi_state = rules.PijersiState()

            if len(args) >= 2:
                if args[1] != 'moves':
                    self.__log_error(f"""missing 'moves' in 'position {" ".join(args)}' ; UGI server terminates itself !""")
                    self.terminate()
                    return

                moves = args[2:]
                for move in moves:
                    new_pijersi_state = self.__pijersi_state.take_action_by_ugi_name(move)
                    self.__pijersi_state = new_pijersi_state


        elif args[0] == 'fen':

            if "moves" in args:
                fen = args[1:args.index("moves")]
                moves = args[args.index("moves") + 1:]
            else:
                fen = args[1:]
                moves = []

            if len(fen) == 0:
                self.__pijersi_state = rules.PijersiState()
            else:

                if len(fen) != 4:
                    self.__log_error(f"""missing 'fen' tokens in 'position {" ".join(args)}' ; UGI server terminates itself !""")
                    self.terminate()
                    return

                fen_positions = fen[0]
                player = fen[1]
                half_move = int(fen[2])
                full_move = int(fen[3])

                pijersi_board_codes = rules.PijersiState.setup_from_ugi_fen(fen_positions)

                if player == 'w':
                    pijersi_player = rules.Player.T.WHITE

                elif player == 'b':
                    pijersi_player = rules.Player.T.BLACK

                else:
                    assert player in ['w', 'b']

                pijersi_credit = self.__pijersi_state.get_max_credit() - half_move

                pijersi_turn = 2*full_move
                if pijersi_player == rules.Player.T.BLACK:
                    pijersi_turn += 1

                self.__pijersi_state = rules.PijersiState(board_codes=pijersi_board_codes,
                                                          player=pijersi_player,
                                                          credit=pijersi_credit,
                                                          turn=pijersi_turn,
                                                          setup=rules.Setup.T.GIVEN)
            for move in moves:
                new_pijersi_state = self.__pijersi_state.take_action_by_ugi_name(move)
                self.__pijersi_state = new_pijersi_state

        else:
            self.__log_error(f"""unexpected argument '{args[0]}' in 'position {" ".join(args)}' ; UGI server terminates itself !""")
            self.terminate()
            return


    def __query(self, args: List[str]) -> None:

        if len(args) < 1:
            self.__log_error("nothing to query ; UGI server terminates itself !")
            self.terminate()
            return

        query_name = args[0]
        query_args = args[1:]

        if query_name not in  ['gameover', 'p1turn', 'result', 'islegal', 'fen']:
            self.__log_error(f"unknown query '{query_name}' ; UGI server terminates itself !")
            self.terminate()
            return

        if self.__pijersi_state is None:
            self.__log_error("no pijersi state to query ; UGI server terminates itself !")
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

                self.__log_error(f"""missing move in command 'query {" ".join(args)}' ; """ +
                                "UGI server terminates itself !")
                self.terminate()
                return

            if len(query_args) > 1:
                self.__log_info(f"""ignoring extra tokens in command 'query {" ".join(args)}'""")

            move = query_args[0]

            if self.__pijersi_state is None:
                self.__log_error("no pijersi state; UGI server terminates itself !")
                self.terminate()
                return

            if self.__pijersi_state.is_terminal():
                legal_moves = []
            else:
                legal_moves = self.__pijersi_state.get_action_ugi_names()

            if move in legal_moves:
                self.__send(['true'])
            else:
                self.__send(['false'])

        elif query_name == 'fen':

            if self.__pijersi_state is None:
                self.__log_error("no pijersi state; UGI server terminates itself !")
                self.terminate()
                return

            fen = self.__pijersi_state.get_ugi_fen()

            self.__send(fen)


    def __quit(self, args: List[str]) -> None:

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'quit {" ".join(args)}'""")

        self.terminate()


    def __setoption(self, args: List[str]) -> None:

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


    def __ugi(self, args: List[str]) -> None:

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


    def __uginewgame(self, args: List[str]) -> None:

        if len(args) != 0:
            self.__log_info(f"""ignoring extra tokens in command 'uginewgame {" ".join(args)}'""")

        self.__pijersi_state = rules.PijersiState()


class UgiSearcher(rules.Searcher):

    __slots__ = ('__ugi_client', '__max_depth', '__time_limit')


    def __init__(self, name: str, ugi_client: str, max_depth: int=None, time_limit: Optional[int]=None):
        super().__init__(name)

        self.__ugi_client = ugi_client

        assert max_depth is None or time_limit is None
        assert not (max_depth is None and time_limit is None)
        self.__max_depth = max_depth
        self.__time_limit = time_limit


    def search(self, state: rules.PijersiState) -> rules.PijersiAction:

        self.__ugi_client.start()

        self.__ugi_client.ugi()
        isready = self.__ugi_client.isready()
        assert isready == ['readyok']

        self.__ugi_client.uginewgame()

        fen = state.get_ugi_fen()
        self.__ugi_client.position_fen(fen=fen)

        if self.__max_depth is not None:
            ugi_action = self.__ugi_client.go_depth_and_wait(self.__max_depth)

        elif self.__time_limit is not None:
            ugi_action = self.__ugi_client.go_movetime_and_wait(self.__time_limit*1_000)

        action = state.get_action_by_ugi_name(ugi_action)

        self.__ugi_client.quit()

        return action


def make_ugi_server_process(server_executable_path: str) -> Tuple[Popen, UgiChannel]:

    if server_executable_path.endswith(".py"):
        popen_args = [sys.executable, server_executable_path]
    else:
        popen_args = [server_executable_path]

    server_process = Popen(args=popen_args,
                           shell=False,
                           text=True,
                           stdin=PIPE, stdout=PIPE)

    server_channel = UgiChannel(cin=server_process.stdin, cout=server_process.stdout)

    return (server_process, server_channel)


def run_ugi_server_implementation() -> None:

    log()
    log(f"Hello from PIJERSI-CMALO-UGI-SERVER-v{rules.__version__}")

    server_channel = UgiChannel.make_std_channel()
    server = UgiServer(channel=server_channel)
    server.run()

    log()
    log(f"Bye from PIJERSI-CMALO-UGI-SERVER-v{rules.__version__}")


if __name__ == "__main__":
    # >> "freeze_support()" is needed with using pijersi_gui as a single executable made by PyInstaller
    # >> otherwise when starting another process by "PoolExecutor" a second GUI windows is created
    freeze_support()

    run_ugi_server_implementation()

    sys.exit()


