#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test concurrent"""

# from concurrent.futures import ProcessPoolExecutor as PoolExecutor
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
import os
import sys
import time


_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules


class Foo:
    
    @staticmethod
    def search_task(searcher, pijersi_state):
        action = searcher.search(pijersi_state)
        action_simple_name = str(action).replace("!", "")
        return action_simple_name


def main():
    print("main: ...")

    depth = 2

    use_concurrent = True
    wait_count_max = 4

    if use_concurrent:
        concurrent_executor = PoolExecutor(max_workers=1)

    backend_searchers = [None for player in rules.Player.T] 
    backend_searchers[rules.Player.T.WHITE] = rules.MinimaxSearcher(name=f"white-minimax-{depth}", max_depth=depth)
    backend_searchers[rules.Player.T.BLACK] = rules.MinimaxSearcher(name=f"black-minimax-{depth}", max_depth=depth)
    
    frontend_searchers = [None for player in rules.Player.T]
    frontend_searchers[rules.Player.T.WHITE] = rules.HumanSearcher(backend_searchers[rules.Player.T.WHITE].get_name())
    frontend_searchers[rules.Player.T.BLACK] = rules.HumanSearcher(backend_searchers[rules.Player.T.BLACK].get_name())

    game = rules.Game()
    game.set_white_searcher(frontend_searchers[rules.Player.T.WHITE])
    game.set_black_searcher(frontend_searchers[rules.Player.T.BLACK])
    
    game.start()
    game_stopped = False
    
    while not game_stopped and game.has_next_turn():
        
        pijersi_state = game.get_state()

        player = pijersi_state.get_current_player()
        
        if use_concurrent:
            search_future = concurrent_executor.submit(Foo.search_task, backend_searchers[player], pijersi_state)
            wait_count = 0
            while True:                
                if search_future.done():
                    action_simple_name = search_future.result()
                    print(f"--- DEBUG --- from search_future action_simple_name = {action_simple_name}")
                    break
                else:
                    if wait_count > wait_count_max:
                        print("--- DEBUG --- canceling search_future ...")
                        if search_future.cancel():
                            print("--- DEBUG --- canceling search_future done")
                            time.sleep(0.5)
                            
                        if search_future.cancelled():
                            print("--- DEBUG --- search_future has been canceled")
                             
                        if search_future.running():
                            print("--- DEBUG --- search_future is running")
                           
                        game_stopped = True
                        break

                    wait_count += 1
                    print(f"--- DEBUG --- waiting for search_future wait_count = {wait_count} ...")
                    time.sleep(0.5)
        
        else:
            action_simple_name = Foo.search_task(backend_searchers[player], pijersi_state)
        
        if not game_stopped:
           frontend_searchers[player].set_action_simple_name(action_simple_name)
           game.next_turn()
           
        else:
            break
        
    if not game_stopped:
        rewards = game.get_rewards()
        print(f"rewards: {rewards}")
        
    else:
        print("game is stopped")
        
        
    if use_concurrent:
        concurrent_executor.shutdown()

    print("main:done")


if __name__ == "__main__":
    print()
    print("Hello")
    print()
    print(f"Python sys.version = {sys.version}")

    main()

    print()
    print("Bye")

    if True:
        print()
        _ = input("main: done ; press enter to terminate")
