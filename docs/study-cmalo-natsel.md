# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

The next table gathers the results obtained with *pijersi_certu_v2.0.0.rc2*.

| AI-engine  |    setup    | depth | player | games | points | average  |
| :--------: | :---------: | :---: | :----: | :---: | :----: | :------: |
| **cmalo**  |   classic   |   1   | black  |  100  |  200   | **2.00** |
|   natsel   |   classic   |   1   | white  |  100  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   1   | white  |  100  |  200   | **2.00** |
|   natsel   |   classic   |   1   | black  |  100  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   1   | black  |  100  |  118   | **1.18** |
|   natsel   | half-random |   1   | white  |  100  |   82   |   0.82   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   1   | white  |  100  |   54   |   0.54   |
| **natsel** | half-random |   1   | black  |  100  |  146   | **1.46** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | black  |  100  |   88   |   0.88   |
| **natsel** |   classic   |   2   | white  |  100  |  112   | **1.12** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | white  |  100  |   0    |   0.00   |
| **natsel** |   classic   |   2   | black  |  100  |  200   | **2.00** |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   2   | black  |  100  |   96   |   0.96   |
|   natsel   | half-random |   2   | white  |  100  |  104   |   1.04   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   2   | white  |  100  |  121   | **1.21** |
|   natsel   | half-random |   2   | black  |  100  |   79   |   0.79   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   3   | black  |  100  |  140   | **1.40** |
|   natsel   |   classic   |   3   | white  |  100  |   60   |   0.60   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   3   | white  |  100  |  190   | **1.90** |
|   natsel   |   classic   |   3   | black  |  100  |   10   |   0.10   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   3   | black  |  100  |   96   |   0.96   |
|   natsel   | half-random |   3   | white  |  100  |  104   |   1.04   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   3   | white  |  10   |   12   |   1.20   |
|   natsel   | half-random |   3   | black  |  10   |   8    |   0.80   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   3   | black  |  10   |   12   | **1.20** |
|   natsel   | half-random | **5** | white  |  10   |   8    |   0.80   |

