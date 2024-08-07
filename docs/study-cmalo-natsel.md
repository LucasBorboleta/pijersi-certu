# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

The next table gathers the results obtained with *pijersi_certu_v2.0.0.rc5, which includes Natural Selection v1.0.0. The column "e-games", as "effective games" counts the unique games using SHA-256 over all positions of the board during each game.

Synthesis:

- At depth 1 : natsel is better than cmalo with classic setup ; with half-random setup, it seems that playing black gives an advantage.
- At depth 2 : natsel is better than cmalo with classic setup ; with half-random setup, natsel and cmalo show same strength.
- At depth 3 : cmalo is better than cmalo with classic setup ; with half-random setup, natsel and cmalo show same strength.
- natsel at depth 5 is better than cmalo at depth 3 with either classic setup or half-random setup. This is expected, but it is a sanity check.

| AI-engine  |    setup    | depth | player | games | e-games | points | average  |
| :--------: | :---------: | :---: | :----: | :---: | :-----: | :----: | :------: |
|   cmalo    |   classic   |   1   | black  | 1000  |    7    |   0    |    0     |
| **natsel** |   classic   |   1   | white  | 1000  |    7    |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   1   | white  | 1000  |   26    |  508   |   0.51   |
| **natsel** |   classic   |   1   | black  | 1000  |   26    |  1492  | **1.50** |
|            |             |       |        |       |         |        |          |
| **cmalo**  | half-random |   1   | black  | 1000  |  1000   |  1308  | **1.31** |
|   natsel   | half-random |   1   | white  | 1000  |  1000   |  692   |   0.70   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   1   | white  | 1000  |  1000   |  652   |   0.65   |
| **natsel** | half-random |   1   | black  | 1000  |  1000   |  1348  | **1.35** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   2   | black  | 1000  |   456   |  465   |   0.47   |
| **natsel** |   classic   |   2   | white  | 1000  |   456   |  1535  | **1.53** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   2   | white  | 1000  |   459   |   0    |   0.00   |
| **natsel** |   classic   |   2   | black  | 1000  |   459   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   2   | black  | 1000  |  1000   |  1009  |   1.00   |
|   natsel   | half-random |   2   | white  | 1000  |  1000   |  991   |   1.00   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   2   | white  | 1000  |  1000   |  1054  |   1.05   |
|   natsel   | half-random |   2   | black  | 1000  |  1000   |  946   |   0.95   |
|            |             |       |        |       |         |        |          |
| **cmalo**  |   classic   |   3   | black  | 1000  |   58    |  1908  | **1.91** |
|   natsel   |   classic   |   3   | white  | 1000  |   58    |   92   |   0.09   |
|            |             |       |        |       |         |        |          |
| **cmalo**  |   classic   |   3   | white  | 1000  |    4    |  2000  | **2.00** |
|   natsel   |   classic   |   3   | black  | 1000  |    4    |   0    |   0.00   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | black  | 1000  |  1000   |  982   |   0.98   |
|   natsel   | half-random |   3   | white  | 1000  |  1000   |  1018  |   1.02   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | white  | 1000  |  1000   |  1083  |   1.08   |
|   natsel   | half-random |   3   | black  | 1000  |  1000   |  917   |   0.92   |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   3   | black  | 1000  |   341   |   0    |   0.00   |
| **natsel** |   classic   | **5** | white  | 1000  |   341   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   3   | white  | 1000  |   134   |   0    |   0.00   |
| **natsel** |   classic   | **5** | black  | 1000  |   134   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | black  | 1000  |  1000   |  113   |   0.11   |
| **natsel** | half-random | **5** | white  | 1000  |  1000   |  1887  | **1.89** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | white  | 1000  |  1000   |  221   |   0.22   |
| **natsel** | half-random | **5** | black  | 1000  |  1000   |  1779  | **1.78** |

