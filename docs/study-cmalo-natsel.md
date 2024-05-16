# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

| AI-engine  |    setup    | depth | Player | Games | Points | Average  |
| :--------: | :---------: | :---: | :----: | :---: | :----: | :------: |
| **cmalo**  |   classic   |   1   | black  |  100  |  200   | **2.00** |
|   natsel   |   classic   |   1   | white  |  100  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   1   | white  |  100  |  200   | **2.00** |
|   natsel   |   classic   |   1   | black  |  100  |   0    |   0.00   |
|            |             |       |        |       |        |          |
| **cmalo**  | half-random |   1   | black  |  100  |  142   | **1.42** |
|   natsel   | half-random |   1   | white  |  100  |   58   |   0.58   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   1   | white  |  100  |   68   |   0.68   |
| **natsel** | half-random |   1   | black  |  100  |  132   | **1.32** |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | black  |  100  |  106   |   1.06   |
|   natsel   |   classic   |   2   | white  |  100  |   94   |   0.94   |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   2   | white  |  100  |   0    |   0.00   |
| **natsel** |   classic   |   2   | black  |  100  |  200   | **2.00** |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   2   | black  |  100  |   96   |   0.96   |
|   natsel   | half-random |   2   | white  |  100  |  104   |   1.04   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   2   | white  |  100  |   96   |   0.96   |
|   natsel   | half-random |   2   | black  |  100  |  104   |   1.04   |
|            |             |       |        |       |        |          |
|   cmalo    |   classic   |   3   | black  |  10   |   12   |   1.20   |
|   natsel   |   classic   |   3   | white  |  10   |   8    |   0.80   |
|            |             |       |        |       |        |          |
| **cmalo**  |   classic   |   3   | white  |  10   |   20   | **2.00** |
|   natsel   |   classic   |   3   | black  |  10   |   0    |   0.00   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   3   | black  |  10   |   11   |   1.10   |
|   natsel   | half-random |   3   | white  |  10   |   9    |   0.90   |
|            |             |       |        |       |        |          |
|   cmalo    | half-random |   3   | white  |  10   |   9    |   0.90   |
|   natsel   | half-random |   3   | black  |  10   |   10   |   1.10   |

