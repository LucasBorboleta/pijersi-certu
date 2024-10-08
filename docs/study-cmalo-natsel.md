# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

The next table gathers the results obtained with *pijersi_certu_v2.1.0, which includes Natural Selection v1.0.1. The column "e-games", as "effective games" counts the unique games using SHA-256 over all positions of the board during each game.

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
|   cmalo    |   classic   |   1   | white  | 1000  |   26    |  454   |   0.45   |
| **natsel** |   classic   |   1   | black  | 1000  |   26    |  1546  | **1.55** |
|            |             |       |        |       |         |        |          |
| **cmalo**  | half-random |   1   | black  | 1000  |  1000   |  1250  | **1.25** |
|   natsel   | half-random |   1   | white  | 1000  |  1000   |  750   |   0.75   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   1   | white  | 1000  |  1000   |  638   |   0.64   |
| **natsel** | half-random |   1   | black  | 1000  |  1000   |  1362  | **1.36** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   2   | black  | 1000  |   444   |  470   |   0.47   |
| **natsel** |   classic   |   2   | white  | 1000  |   444   |  1530  | **1.53** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   2   | white  | 1000  |   436   |   0    |   0.00   |
| **natsel** |   classic   |   2   | black  | 1000  |   436   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   2   | black  | 1000  |  1000   |  984   |   0.98   |
|   natsel   | half-random |   2   | white  | 1000  |  1000   | 1.016  |   1.02   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   2   | white  | 1000  |  1000   |  1062  |   1.06   |
|   natsel   | half-random |   2   | black  | 1000  |  1000   |  938   |   0.94   |
|            |             |       |        |       |         |        |          |
| **cmalo**  |   classic   |   3   | black  | 1000  |   58    |  1904  | **1.90** |
|   natsel   |   classic   |   3   | white  | 1000  |   58    |   96   |   0.19   |
|            |             |       |        |       |         |        |          |
| **cmalo**  |   classic   |   3   | white  | 1000  |    4    |  2000  | **2.00** |
|   natsel   |   classic   |   3   | black  | 1000  |    4    |   0    |   0.00   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | black  | 1000  |  1000   |  982   |   0.98   |
|   natsel   | half-random |   3   | white  | 1000  |  1000   |  1018  |   1.02   |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | white  | 1000  |  1000   |  1086  |   1.09   |
|   natsel   | half-random |   3   | black  | 1000  |  1000   |  914   |   0.91   |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   3   | black  | 1000  |   345   |   0    |   0.00   |
| **natsel** |   classic   | **5** | white  | 1000  |   345   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    |   classic   |   3   | white  | 1000  |   137   |   0    |   0.00   |
| **natsel** |   classic   | **5** | black  | 1000  |   137   |  2000  | **2.00** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | black  | 1000  |  1000   |  109   |   0.11   |
| **natsel** | half-random | **5** | white  | 1000  |  1000   |  1891  | **1.89** |
|            |             |       |        |       |         |        |          |
|   cmalo    | half-random |   3   | white  | 1000  |  1000   |  218   |   0.22   |
| **natsel** | half-random | **5** | black  | 1000  |  1000   |  1782  | **1.78** |

