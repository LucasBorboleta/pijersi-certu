#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_ugi.py implements the UGI protocol for the PIJERSI boardgame."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import subprocess
import sys

from typing import List
from typing import Self
from typing import TextIO


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
        
        data = (line
                .strip(UgiChannel.SEPARATOR + UgiChannel.TERMINATOR)
                .split(UgiChannel.SEPARATOR))
        return data
       

class UgiClient:
     
    def __init__(self, channel: UgiChannel):
        self.__channel = channel
        self.__debug = True
        
        
    def __log(self, msg: str):
        if self.__debug:
            sys.stderr.write(f"UgiClient.{msg}\n")
            sys.stderr.flush()

    
    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log(f"__send: {data}")
    
    
    def __recv(self) -> List[str]:
        data =  self.__channel.recv()
        self.__log(f"__recv: {data}")
        return data
   
    
    def ugi(self):
        self.__send(['ugi'])
        answer = self.__recv()
        self.__log(f"ugi: answer {answer}")
        assert answer == ['ugiok']
   
    
    def quit(self):
        self.__send(['quit'])
    
    
    def test(self, x):
        self.__send(['test', str(x)])


class UgiServer:
     
    def __init__(self, channel: UgiChannel):
        self.__channel = channel
        self.__running = False
        self.__debug = True
         
        
    def __log(self, msg: str):
        if self.__debug:
            sys.stderr.write(f"UgiServer.{msg}\n")
            sys.stderr.flush()

    
    def __send(self, data: List[str]):
        self.__channel.send(data)
        self.__log(f"__send: {data}")
    
    
    def __recv(self) -> List[str]:
        data = self.__channel.recv()
        self.__log(f"__recv: {data}")
        return data
        
    
    def get_channel(self) -> UgiChannel:
        return self.__channel
        

    def stop(self):
        self.__running = False


    def start(self):
        assert not self.__running
        self.__running = True
        
        commands = {}
        commands['ugi'] = self.__ugi
        commands['quit'] = self.__quit
        commands['test'] = self.__test
        
        
        while self.__running:
            data = self.__recv()
            
            assert len(data) >= 1
            name = data[0]
            args = data[1:]
          
            assert name in commands
            commands[name](args)
        
    
    def __ugi(self, args: List[str]):
        self.__log(f"__ugi: args = {args}")
        assert len(args) == 0
        self.__send(['ugiok'])
        
    
    def __quit(self, args: List[str]):
        self.__log(f"__quit: args = {args}")
        assert len(args) == 0
        self.stop()
   
    
    def __test(self, args: List[str]):
        self.__log(f"__test: args = {args}")


def make_ugi_server():
    
    process = subprocess.Popen(args=[sys.executable, sys.argv[0], "--ugi-server"], 
                                    shell=False, 
                                    text=True, 
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    process_channel = UgiChannel(cin=process.stdin, cout=process.stdout)
    server = UgiServer(channel=process_channel)
    return server


def start_ugi_server():
    server_channel = UgiChannel.make_std_channel()
    server = UgiServer(channel=server_channel)
    server.start()


def make_ugi_client(server: UgiServer) -> UgiClient:
    client_channel = server.get_channel().make_dual_channel()
    client = UgiClient(channel=client_channel)
    return client
    

def test_ugi_protocol():
    
    print()
    print("test_ugi_protocol: ...")
    
    server = make_ugi_server()
    client = make_ugi_client(server)
    
    client.ugi()
    client.test(1)
    client.test(2)
    client.test(3)
    client.quit()
    
    print()
    print("test_ugi_protocol: done")
    

if __name__ == "__main__":
    
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--ugi-server":
            start_ugi_server()
            sys.exit()
                
    else:
        test_ugi_protocol()
    
        print()
        _ = input("press enter to terminate")