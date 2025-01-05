#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Attempt to reproduce the "issue-92" on "pijersi-rs"
"""

import os
import sys

from typing import List
from typing import Optional

_package_home = os.path.abspath(os.path.dirname(__file__))
sys.path.append(_package_home)

from pijersi_ugi import UgiClient
from pijersi_ugi import NatselSearcher
from pijersi_gui import make_artefact_platform_id

_NATSEL_UGI_SERVER_NAME = "pijersi_natural_selection_ugi_server"
_NATSEL_NAME = "Natural Selection"
_NATSEL_KEY = "natsel"
_NATSEL_VERSION = "1.2.1"

_NATSEL_EXECUTABLE_PATH = os.path.join(_package_home,
                                             "ugi-servers",
                                             _NATSEL_KEY,
                                             f"{_NATSEL_UGI_SERVER_NAME}_v{_NATSEL_VERSION}" + "_" + make_artefact_platform_id())


ugi_fen = ['s-3p-r-/p-r-s-rprss-p-/3W-2/2w-w-W-2/1RS3RP/P-S-2S-1P-/R-P-1R-1S-', 'w', '6', '4']

ugi_actions = []
ugi_actions.append('a1a2')
ugi_actions.append('a1a2a3')
ugi_actions.append('a1a2a1')
ugi_actions.append('a1a2b3')
ugi_actions.append('a1a2c3')
ugi_actions.append('a1b1')
ugi_actions.append('a1b1a1')
ugi_actions.append('a1b1c1')
ugi_actions.append('a1b1d2')
ugi_actions.append('a1b2')
ugi_actions.append('a1b2b3')
ugi_actions.append('a1b2b4')
ugi_actions.append('a1b2a1')
ugi_actions.append('a1b2c1')
ugi_actions.append('a1b2d1')
ugi_actions.append('a2a3')
ugi_actions.append('a2a1')
ugi_actions.append('a2a1a2')
ugi_actions.append('a2a1a3')
ugi_actions.append('a2b2')
ugi_actions.append('a2b2b3')
ugi_actions.append('a2b2b4')
ugi_actions.append('a2b2a2')
ugi_actions.append('a2b2c1')
ugi_actions.append('a2b2d1')
ugi_actions.append('a2b3')
ugi_actions.append('a4a5')
ugi_actions.append('a4a3')
ugi_actions.append('a4b4')
ugi_actions.append('a4b5')
ugi_actions.append('a4b5b6')
ugi_actions.append('a4b5a5')
ugi_actions.append('a4b5a4')
ugi_actions.append('a4b5b4')
ugi_actions.append('a4b5b3')
ugi_actions.append('a4b5c4')
ugi_actions.append('a4b5c5')
ugi_actions.append('a4b5d6')
ugi_actions.append('a6a5')
ugi_actions.append('a6b6')
ugi_actions.append('a6b7')
ugi_actions.append('a6b7a6')
ugi_actions.append('a6b7b6')
ugi_actions.append('b1b2')
ugi_actions.append('b1b2b3')
ugi_actions.append('b1b2b4')
ugi_actions.append('b1b2b1')
ugi_actions.append('b1b2c1')
ugi_actions.append('b1b2d1')
ugi_actions.append('b1a1')
ugi_actions.append('b1a1b1')
ugi_actions.append('b1c1')
ugi_actions.append('b2b3')
ugi_actions.append('b2a2')
ugi_actions.append('b2a2a3')
ugi_actions.append('b2a2b2')
ugi_actions.append('b2a2c1')
ugi_actions.append('b2a2b3')
ugi_actions.append('b2a2c3')
ugi_actions.append('b2a1')
ugi_actions.append('b2a1b2')
ugi_actions.append('b2b1')
ugi_actions.append('b2b1b2')
ugi_actions.append('b2b1b3')
ugi_actions.append('b2b1c1')
ugi_actions.append('b2b1d2')
ugi_actions.append('b2c1')
ugi_actions.append('b5b6')
ugi_actions.append('b5a5')
ugi_actions.append('b5a4')
ugi_actions.append('b5a4a5')
ugi_actions.append('b5a4a3')
ugi_actions.append('b5a4b4')
ugi_actions.append('b5a4c3')
ugi_actions.append('b5a4b5')
ugi_actions.append('b5a4c5')
ugi_actions.append('b5b4')
ugi_actions.append('b5c4')
ugi_actions.append('b5c5')
ugi_actions.append('b7a6')
ugi_actions.append('b7a6a5')
ugi_actions.append('b7a6b6')
ugi_actions.append('b7a6c5')
ugi_actions.append('b7a6b7')
ugi_actions.append('b7b6')
ugi_actions.append('c2c2c3')
ugi_actions.append('c2c3c3')
ugi_actions.append('c2c3c4')
ugi_actions.append('c2c3b4')
ugi_actions.append('c2c3b3')
ugi_actions.append('c2c3c2')
ugi_actions.append('c2c4c4')
ugi_actions.append('c2c4c5')
ugi_actions.append('c2c4b5')
ugi_actions.append('c2c4b4')
ugi_actions.append('c2c4c3')
ugi_actions.append('c2c4d5')
ugi_actions.append('c2c2b3')
ugi_actions.append('c2b3b3')
ugi_actions.append('c2b3b4')
ugi_actions.append('c2b3a3')
ugi_actions.append('c2b3a2')
ugi_actions.append('c2b3b2')
ugi_actions.append('c2b3c2')
ugi_actions.append('c2b3c3')
ugi_actions.append('c2a3a3')
ugi_actions.append('c2a3a4')
ugi_actions.append('c2a3a2')
ugi_actions.append('c2a3b3')
ugi_actions.append('c2a3b4')
ugi_actions.append('c2c2b2')
ugi_actions.append('c2b2b3')
ugi_actions.append('c2b2b4')
ugi_actions.append('c2b2c1')
ugi_actions.append('c2b2d1')
ugi_actions.append('c2c2c1')
ugi_actions.append('c2c1c1')
ugi_actions.append('c2c1c2')
ugi_actions.append('c2c1b2')
ugi_actions.append('c2c1b1')
ugi_actions.append('c2c1d1')
ugi_actions.append('c2c1d2')
ugi_actions.append('c2c2d2')
ugi_actions.append('c2d2d2')
ugi_actions.append('c2d2c2')
ugi_actions.append('c2d2c1')
ugi_actions.append('c2d2d1')
ugi_actions.append('c2d2e1')
ugi_actions.append('c2d2e2')
ugi_actions.append('c2e1e1')
ugi_actions.append('c2e1e2')
ugi_actions.append('c2e1d2')
ugi_actions.append('c2e1d1')
ugi_actions.append('c2e1f1')
ugi_actions.append('c6c6b7')
ugi_actions.append('c6b7b6')
ugi_actions.append('c6c6b6')
ugi_actions.append('c6b6b6')
ugi_actions.append('c6b6b7')
ugi_actions.append('c6b6a6')
ugi_actions.append('c6b6a5')
ugi_actions.append('c6b6b5')
ugi_actions.append('c6b6c5')
ugi_actions.append('c6b6c6')
ugi_actions.append('c6a5a5')
ugi_actions.append('c6a5a6')
ugi_actions.append('c6a5a4')
ugi_actions.append('c6a5b5')
ugi_actions.append('c6a5b6')
ugi_actions.append('c6c6c5')
ugi_actions.append('c6c5c5')
ugi_actions.append('c6c5c6')
ugi_actions.append('c6c5b6')
ugi_actions.append('c6c5b5')
ugi_actions.append('c6c5c4')
ugi_actions.append('c6c5d5')
ugi_actions.append('c6c5d6')
ugi_actions.append('c6c4c4')
ugi_actions.append('c6c4c5')
ugi_actions.append('c6c4b5')
ugi_actions.append('c6c4b4')
ugi_actions.append('c6c4c3')
ugi_actions.append('c6c4d5')
ugi_actions.append('c6c6d6')
ugi_actions.append('c6d6d6')
ugi_actions.append('c6d6d7')
ugi_actions.append('c6d6c6')
ugi_actions.append('c6d6c5')
ugi_actions.append('c6d6d5')
ugi_actions.append('c6d6e5')
ugi_actions.append('c6d6e6')
ugi_actions.append('c6e5e5')
ugi_actions.append('c6e5e6')
ugi_actions.append('c6e5d6')
ugi_actions.append('c6e5d5')
ugi_actions.append('c6e5e4')
ugi_actions.append('c6c6d7')
ugi_actions.append('c6d7d7')
ugi_actions.append('c6d7c6')
ugi_actions.append('c6d7d6')
ugi_actions.append('c6d7e6')
ugi_actions.append('d5d6')
ugi_actions.append('d5c5')
ugi_actions.append('d5c4')
ugi_actions.append('d5e4')
ugi_actions.append('d5e4e5')
ugi_actions.append('d5e4e6')
ugi_actions.append('d5e4d5')
ugi_actions.append('d5e4c5')
ugi_actions.append('d5e4e3')
ugi_actions.append('d5e4e2')
ugi_actions.append('d5e5')
ugi_actions.append('e4e5')
ugi_actions.append('e4d5')
ugi_actions.append('e4d5d6')
ugi_actions.append('e4d5d7')
ugi_actions.append('e4d5c5')
ugi_actions.append('e4d5b6')
ugi_actions.append('e4d5c4')
ugi_actions.append('e4d5b4')
ugi_actions.append('e4d5e4')
ugi_actions.append('e4d5e5')
ugi_actions.append('e4e3')


class TheSearcher(NatselSearcher):


    def __init__(self, name, ugi_client, max_depth):
        super().__init__(name=name, ugi_client=ugi_client, max_depth=max_depth)


    def __extract_score(self, infos: List[List[str]]) -> Optional[float]:
        """extract "score" from "infos" """
        score = None
        last_depth = None
        depth_is_next = False
        score_is_next = False
        for info in infos:
            # example: ['info', 'book', 'depth', '2', 'time', '0', 'score', '-524288', 'pv', 'g6g5']
            for token in info:

                if depth_is_next:
                    depth = float(token)
                    depth_is_next = False
                    if last_depth is None:
                        last_depth = depth
                    else:
                        assert depth > last_depth

                elif score_is_next:
                    score = float(token)
                    score_is_next = False

                if token == 'depth':
                    depth_is_next = True

                elif token == 'score':
                    score_is_next = True
        return score


    def evaluate_given_actions(self):
        evaluated_actions = {}

        ugi_client = self.get_ugi_client()
        ugi_is_permanent = ugi_client.is_permanent()

        if not ugi_is_permanent or not ugi_client.is_running():
            ugi_client.run()

        if not ugi_client.is_prepared():
            ugi_client.prepare()

        max_depth = self.get_max_depth()

        for ugi_action in ugi_actions:
            ugi_client.position_fen(fen=ugi_fen)
            ugi_client.go_manual(ugi_action)
            (best_ugi_action, infos) = ugi_client.go_depth_and_wait(max_depth - 1)

            score = self.__extract_score(infos)
            assert score is not None
            evaluated_actions[ugi_action] = -score

        if not ugi_is_permanent:
            ugi_client.quit()

        return evaluated_actions


    def evaluate_given_first_action(self):
        evaluated_actions = {}

        ugi_action = ugi_actions[0]

        ugi_client = self.get_ugi_client()
        ugi_is_permanent = ugi_client.is_permanent()

        assert not ugi_is_permanent
        assert not  ugi_client.is_running()
        assert not ugi_client.is_prepared()

        ugi_client.run()
        ugi_client.prepare()

        max_depth = self.get_max_depth()

        ugi_client.position_fen(fen=ugi_fen)
        ugi_client.go_manual(ugi_action)
        (best_ugi_action, infos) = ugi_client.go_depth_and_wait(max_depth - 1)

        score = self.__extract_score(infos)
        assert score is not None
        evaluated_actions[ugi_action] = -score

        ugi_client.quit()

        return evaluated_actions


def test_1():
    print()
    print("-- test_1 ------------------------------------------------------")

    best_score_set = set()
    best_action_set = set()

    ugi_client = UgiClient(name=_NATSEL_KEY, server_executable_path=_NATSEL_EXECUTABLE_PATH, permanent=False)
    review_searcher = TheSearcher(name="natsel-5", ugi_client=ugi_client, max_depth=5)

    iter_count = 100
    for iter_index in range(iter_count):

        evaluated_actions = review_searcher.evaluate_given_actions()

        if iter_index == 0:
            print()
            print(f"ugi_fen = {ugi_fen}")
            print()
            print(f"evaluated_actions = {evaluated_actions}")
            print()

        print()

        best_score = min(evaluated_actions.values())
        print(f"iter_index = {iter_index} ; best_score = {best_score}")

        best_actions = [action for (action, score) in sorted(evaluated_actions.items()) if score == best_score]
        print(f"{len(best_actions)} best_actions = {best_actions}")

        best_score_set.add(best_score)
        best_action_set.update(best_actions)

    print()
    print(f"best_score_set of {len(best_score_set)} values = {best_score_set} for {iter_count} iterations")

    print()
    print(f"best_action_set of {len(best_action_set)} actions = {best_action_set} for {iter_count} iterations")



def test_2():
    print()
    print("-- test_2 ------------------------------------------------------")

    score_set = set()

    iter_count = 100
    for iter_index in range(iter_count):

        ugi_client = UgiClient(name=_NATSEL_KEY, server_executable_path=_NATSEL_EXECUTABLE_PATH, permanent=False)
        review_searcher = TheSearcher(name="natsel-5", ugi_client=ugi_client, max_depth=5)
        evaluated_actions = review_searcher.evaluate_given_first_action()

        if iter_index == 0:
            print()
            print(f"ugi_fen = {ugi_fen}")
            print()
            print(f"evaluated_actions = {evaluated_actions}")
            print()

        print()

        assert len(evaluated_actions) == 1
        first_action = list(evaluated_actions.keys())[0]
        first_score = evaluated_actions[first_action]
        print(f"iter_index = {iter_index} ; first_action = {first_action} ; first_score = {first_score}")

        score_set.add(first_score)

    print()
    print(f"score_set of {len(score_set)} values = {score_set} for {iter_count} iterations")


if __name__ == "__main__":

    print()
    print("Hello")
    print()
    print(f"Python sys.version = {sys.version}")

    print()
    print(f"_NATSEL_VERSION = {_NATSEL_VERSION}")

    if True:
        test_1()

    if True:
        test_2()

    print()
    print("Bye")

    print()
    _ = input("main: done ; press enter to terminate")

