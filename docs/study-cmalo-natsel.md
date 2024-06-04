# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

The next table gathers the results obtained with *pijersi_certu_v2.0.0.rc4, which includes Natural Selection v0.1.0.

| AI-engine  |    setup    | depth | player | games | points | average  |
| :--------: | :---------: | :---: | :----: | :---: | :----: | :------: |
| **cmalo**  |   classic   |   1   | black  | 1000  |  2000  | **2.00** |
|   natsel   |   classic   |   1   | white  | 1000  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   1   | white  | 1000  |  2000  | **2.00** |
|   natsel   |   classic   |   1   | black  | 1000  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   1   | black  | 1000  |  1260  | **1.26** |
|   natsel   | half-random |   1   | white  | 1000  |  740   |   0.74   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   1   | white  | 1000  |  620   |   0.62   |
| **natsel** | half-random |   1   | black  | 1000  |  1380  | **1.38** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | black  | 1000  |  894   |   0.89   |
| **natsel** |   classic   |   2   | white  | 1000  |  1106  | **1.11** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | white  | 1000  |   0    |   0.00   |
| **natsel** |   classic   |   2   | black  | 1000  |  2000  | **2.00** |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   2   | black  | 1000  |  939   |   0.94   |
|   natsel   | half-random |   2   | white  | 1000  |  1061  |   1.06   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   2   | white  | 1000  |  995   |   0.99   |
|   natsel   | half-random |   2   | black  | 1000  |  1005  |   1.00   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   3   | black  | 1000  |  1446  | **1.45** |
|   natsel   |   classic   |   3   | white  | 1000  |  554   |   0.55   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   3   | white  | 1000  |  1653  | **1.65** |
|   natsel   |   classic   |   3   | black  | 1000  |  347   |   0.35   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   3   | black  | 1000  |  1046  |   1.05   |
|   natsel   | half-random |   3   | white  | 1000  |  954   |   0.95   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   3   | white  | 1000  |  1273  | **1.27** |
|   natsel   | half-random |   3   | black  | 1000  |  727   |   0.73   |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   3   | black  | 1000  |  773   |   0.77   |
| **natsel** |   classic   | **5** | white  | 1000  |  1227  | **1.23** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   3   | white  | 1000  |  266   |   0.27   |
| **natsel** |   classic   | **5** | black  | 1000  |  1734  | **1.73** |

