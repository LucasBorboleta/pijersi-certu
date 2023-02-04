#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test concurrent"""

import concurrent.futures
import os
import sys
import time


_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules


def search_task(searcher, pijersi_state):
    
    action = searcher.search(pijersi_state)
    action_simple_name = str(action).replace("!", "")
    return action_simple_name


def main():
    print("main: ...")

    depth = 2

    use_concurrent = True
    wait_count_max = 2

    if use_concurrent:
        concurrent_executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)

    real_searchers = [None for player in rules.Player.T]
    proxy_searchers = [None for player in rules.Player.T]
    
    real_searchers[rules.Player.T.WHITE] = rules.MinimaxSearcher(name=f"white-minimax-{depth}", max_depth=depth)
    real_searchers[rules.Player.T.BLACK] = rules.MinimaxSearcher(name=f"black-minimax-{depth}", max_depth=depth)
    
    proxy_searchers[rules.Player.T.WHITE] = rules.HumanSearcher(real_searchers[rules.Player.T.WHITE].get_name())
    proxy_searchers[rules.Player.T.BLACK] = rules.HumanSearcher(real_searchers[rules.Player.T.BLACK].get_name())

    game = rules.Game()
    game.set_white_searcher(proxy_searchers[rules.Player.T.WHITE])
    game.set_black_searcher(proxy_searchers[rules.Player.T.BLACK])
    
    game.start()
    game_stopped = False
    
    while not game_stopped and game.has_next_turn():
        
        pijersi_state = game.get_state()

        player = pijersi_state.get_current_player()
        
        if use_concurrent:
            search_future = concurrent_executor.submit(search_task, real_searchers[player], pijersi_state)
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
            action_simple_name = search_task(real_searchers[player], pijersi_state)
        
        if not game_stopped:
           proxy_searchers[player].set_action_simple_name(action_simple_name)
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
