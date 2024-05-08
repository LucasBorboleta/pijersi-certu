#!/usr/bin/env python3

"""pijersi_setup_encoding.py tests a compact encoding of the starting positions of the PIJERSI boardgame"""

_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rules engine for the PIJERSI boardgame.

Copyright (C) 2019 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import math
import random
import re

from typing import Mapping


WHITE_POSITIONS = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6',
                   'b1', 'b2', 'b3',
                   'b4', 'b4t',
                   'b5', 'b6', 'b7']

WHITE_CODES = {'R': 0, 'P': 1, 'S': 2, 'W': 3}
CUBE_BASE = len(WHITE_CODES)
INVERSED_WHITE_CODES = {value:key for (key, value) in WHITE_CODES.items()}

SETUP_DIGITS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
INVERSED_SETUP_DIGITS = {digit_value:digit_index for (digit_index, digit_value) in enumerate(SETUP_DIGITS)}
SETUP_BASE = len(SETUP_DIGITS)
SETUP_LENGTH = math.ceil(len(WHITE_POSITIONS)*math.log(CUBE_BASE)/math.log(SETUP_BASE))


def generate_hr_white_positions() -> Mapping[str, str]:

    white_stack_bottom = 'b4'
    white_stack_top = 'b4t'
    white_stack_positions = [white_stack_bottom, white_stack_top]
    white_cube_positions = list(set(WHITE_POSITIONS) - set(white_stack_positions))
    white_cube_positions.sort()

    white_cubes = ['W', 'W',  'R', 'R' , 'R', 'R',  'P', 'P', 'P', 'P',  'S', 'S', 'S', 'S']
    random.shuffle(white_cubes)

    white_cube_1 = white_cubes.pop()
    white_cube_2 = white_cubes.pop()

    white_positions = {}

    if white_cube_1 == 'W':
        white_positions[white_stack_bottom] = white_cube_1
        white_positions[white_stack_top] = white_cube_2

    else:
        white_positions[white_stack_top] = white_cube_1
        white_positions[white_stack_bottom] = white_cube_2

    for (position, cube) in zip(white_cube_positions, white_cubes):
        white_positions[position] = cube


    white_positions = {key:value for (key, value) in sorted(white_positions.items())}

    return white_positions


def encode_white_positions(white_positions: Mapping[str, str]) -> str:

    cubes_encoding = ""

    for position in WHITE_POSITIONS:
        cube_code = WHITE_CODES[white_positions[position]]
        cubes_encoding = str(cube_code) + cubes_encoding

    setup_number = int(cubes_encoding, base=CUBE_BASE)

    setup_encoding = ""

    setup_rest = setup_number

    while setup_rest != 0:
        setup_modulo = setup_rest % SETUP_BASE
        setup_rest = setup_rest // SETUP_BASE
        setup_encoding = SETUP_DIGITS[setup_modulo] + setup_encoding

    setup_encoding = SETUP_DIGITS[0]*max(0, SETUP_LENGTH - len(setup_encoding)) + setup_encoding
    return setup_encoding


def decode_white_positions(white_encoding: str) -> Mapping[str, str]:

    setup_number = 0

    for (digit_index, digit) in enumerate(reversed(white_encoding)):
        setup_number += INVERSED_SETUP_DIGITS[digit]*(SETUP_BASE**digit_index)

    setup_rest = setup_number
    cubes_encoding = []

    while setup_rest != 0:
        setup_modulo = setup_rest % CUBE_BASE
        setup_rest = setup_rest // CUBE_BASE
        cubes_encoding.append(INVERSED_WHITE_CODES[setup_modulo])

    for _ in range(max(0, len(WHITE_POSITIONS) - len(cubes_encoding))):
        cubes_encoding.append(INVERSED_WHITE_CODES[0])


    white_positions = {}

    for (position_index, position) in enumerate(WHITE_POSITIONS):
        white_positions[position] = cubes_encoding[position_index]

    return white_positions


def validate_white_positions(white_positions: Mapping[str, str]) -> bool:
    cube_counts = {cube:0 for cube in WHITE_CODES.keys()}

    for cube in white_positions.values():
        cube_counts[cube] += 1

    validated = (cube_counts['W'] == 2 and
                 cube_counts['R'] == 4 and
                 cube_counts['P'] == 4 and
                 cube_counts['S'] == 4)

    return validated



def main() -> None:

    print()
    print(f"SETUP_BASE = {SETUP_BASE} ; SETUP_LENGTH = {SETUP_LENGTH}")

    std_white_positions = {
        'a1': 'R', 'a2': 'P', 'a3': 'S',
        'a4': 'R', 'a5': 'P', 'a6': 'S',

        'b1': 'P', 'b2': 'S', 'b3': 'R',
        'b4': 'W', 'b4t': 'W',
        'b5': 'S', 'b6': 'R', 'b7': 'P'}

    std_white_encoding = encode_white_positions(std_white_positions)

    print()
    print(f"std_white_positions = {std_white_positions} ; std_white_encoding = {std_white_encoding}")
    assert std_white_encoding == "GRXLLS"
    assert validate_white_positions(std_white_positions)

    actual_std_white_positions = decode_white_positions(std_white_encoding)
    assert actual_std_white_positions == std_white_positions


    for _ in range(10):
        hr_white_positions = generate_hr_white_positions()
        hr_white_encoding = encode_white_positions(hr_white_positions)
        print()
        print(f"hr_white_positions = {hr_white_positions} ; hr_white_encoding = {hr_white_encoding}")

        actual_hr_white_positions = decode_white_positions(hr_white_encoding)
        assert actual_hr_white_positions == hr_white_positions
        assert validate_white_positions(hr_white_positions)


    #-- Look for almost pronouncable setup ; just for fun
    search_count = 10_000
    hr_white_encodings = set()
    for _ in range(search_count):
        hr_white_positions = generate_hr_white_positions()
        hr_white_encoding = encode_white_positions(hr_white_positions)

        if re.match(r"^.*[BCDFGHJKLMNPQRSTVWXYZ]{2}.*$", hr_white_encoding):
            continue

        if re.match(r".*[AEIUO]{2}.*$", hr_white_encoding):
            continue

        hr_white_encodings.add(hr_white_encoding)

    print()
    print(f"{len(hr_white_encodings)} almost pronouncable hr_white_encodings over {search_count} random ones:")
    for (hr_white_encoding_index, hr_white_encoding) in enumerate(hr_white_encodings):
        hr_white_positions = decode_white_positions(hr_white_encoding)
        print(f"  {hr_white_encoding_index} {hr_white_encoding} {hr_white_positions}")


if __name__ == "__main__":
    print()
    print("Hello")

    main()

    print()
    print("Bye")

    print()
    _ = input("press enter to terminate")
