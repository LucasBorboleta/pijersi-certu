# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 19:34:28 2023

@author: leandre
"""

import math
import os
import sys

from typing import Optional
from typing import Sequence

import multiprocessing

import cma

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

import pijersi_rules as rules



def run_one_game(game_index, alt_searcher, std_searcher):

    game_alt_points = 0
    game_std_points = 0

    if game_index % 2 == 0:
        white_searcher = alt_searcher
        black_searcher = std_searcher
    else:
        white_searcher = std_searcher
        black_searcher = alt_searcher

    pre_state_evaluator = rules.StateEvaluator(fighter_weight=44.63728045969825,
                                               cube_weight=21.408271707785577,
                                               dg_min_weight=7.447181775997062,
                                               dg_ave_weight=14.154256204653036,
                                               dc_ave_weight=3.9277270467740597,
                                               credit_weight=-2.1733667445890497)

    pre_searcher = rules.MinimaxSearcher("pre-minimax-2", max_depth=2, state_evaluator=pre_state_evaluator)

    pre_turn_count = 8


    while True:
        game = rules.Game()
        game.enable_log(False)

        game.set_white_searcher(white_searcher)
        game.set_black_searcher(black_searcher)

        game.start()

        while game.has_next_turn():
            turn_count = game.get_turn()

            if turn_count <= pre_turn_count:
                game.set_white_searcher(pre_searcher)
                game.set_black_searcher(pre_searcher)
            else:
                game.set_white_searcher(white_searcher)
                game.set_black_searcher(black_searcher)

            game.next_turn()

        turn_count = game.get_turn()
        if turn_count > pre_turn_count:
            break

    rewards = game.get_rewards()

    if game_index % 2 == 0:

        if rewards[rules.Player.T.WHITE] == rules.Reward.WIN:
            game_alt_points = 2

        elif rewards[rules.Player.T.WHITE] == rules.Reward.DRAW:
            game_alt_points = 1

        if rewards[rules.Player.T.BLACK] == rules.Reward.WIN:
            game_std_points = 2

        elif rewards[rules.Player.T.BLACK] == rules.Reward.DRAW:
            game_std_points = 1

    else:
        if rewards[rules.Player.T.WHITE] == rules.Reward.WIN:
            game_std_points = 2

        elif rewards[rules.Player.T.WHITE] == rules.Reward.DRAW:
            game_std_points = 1

        if rewards[rules.Player.T.BLACK] == rules.Reward.WIN:
            game_alt_points = 2

        elif rewards[rules.Player.T.BLACK] == rules.Reward.DRAW:
            game_alt_points = 1

    # add a bounus for long game
    bonus = 0.5*(1 - math.exp(-turn_count/40))/(1 - math.exp(-1))

    game_alt_points += bonus
    game_std_points += bonus

    return (game_alt_points, game_std_points)


def run_games_against_standard_minimax(game_count: int=2, alt_weights: Optional[Sequence[float]]=None) -> float:

    if False:
        print("=======================================")
        print(" run_games_against_standard_minimax ...")
        print("=======================================")

    assert game_count > 0
    assert game_count % 2 == 0

    max_depth = 4
    std_searcher = rules.MinimaxSearcher(f"std-minimax-{max_depth}", max_depth=max_depth)

    if alt_weights is None:
        alt_weights = [16, 8, 4, 2, 2, 1]

    assert len(alt_weights) == 6
    alt_state_evaluator = rules.StateEvaluator(fighter_weight=alt_weights[0],
                                               cube_weight=alt_weights[1],
                                               dg_min_weight=alt_weights[2],
                                               dg_ave_weight=alt_weights[3],
                                               dc_ave_weight=alt_weights[4],
                                               credit_weight=alt_weights[5])

    alt_searcher = rules.MinimaxSearcher(f"alt-minimax-{max_depth}", max_depth=max_depth, state_evaluator=alt_state_evaluator)



    with multiprocessing.Pool(processes=8) as pool:
        game_points = pool.starmap(run_one_game, ((game_index, alt_searcher, std_searcher) for game_index in range(game_count)))

    alt_points = 0
    std_points = 0

    for (alt_game_points, std_game_points) in game_points:
        alt_points += alt_game_points
        std_points += std_game_points

    std_score = std_points/game_count

    print(f"game_count={game_count}" +
          f" ; alt_points={alt_points:.3f} ; std_points={std_points:.3f} ; std_score={std_score:.3f}" +
          " ; alt_weights=" + str([f"{x:.3f}" for x in alt_weights]))

    if False:
        print("========================================")
        print(" run_games_against_standard_minimax done")
        print("========================================")

    return std_score


def optimize():

    def my_cost(x):
        return run_games_against_standard_minimax(game_count=4, alt_weights=x)

    # Minimax-1
    # mean vector found at genration 139 using 1000 games per cost evaluation:
    # 41.885392174432646 26.143263284220737 -5.88263321226207 -44.32882404147753 19.73724041099422 -18.583746217767935

    # Minimax-2
    # mean vector found at genration 90 using 100 games per cost evaluation:
    # 44.63728045969825 21.408271707785577 7.447181775997062 14.154256204653036 3.9277270467740597 -2.1733667445890497

    # Minimax-3
    # mean vector found at genration 23 using 20 games per cost evaluation:
    # 65.52573448992278 4.616227996911011 14.424683698727392 19.619155464089044 2.5543281621200737 -1.202172844784375

    # Minimax-4


    es = cma.CMAEvolutionStrategy([65.52573448992278,
                                   4.61622799691101,
                                   14.424683698727392,
                                   19.619155464089044,
                                   2.5543281621200737,
                                   -1.202172844784375], 4.)
    while not es.stop():
        solutions = es.ask()
        es.tell(solutions, [my_cost(x) for x in solutions])
        es.logger.add()  # write data to disc to be plotted
        es.disp()

    es.result_pretty()
    cma.plot()  # shortcut for es.logger.plot()


if __name__ == "__main__":

    if False:
        score = run_games_against_standard_minimax()
        print(f"__main__: score={score:.3f}")

    if True:
        optimize()


    if True:
        print()
        _ = input("main: done ; press enter to terminate")