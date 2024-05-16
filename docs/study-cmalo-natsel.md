# Introduction

This memo performs a comparison study of the two AI-engines : *cmalo* and *natsel* (alias Natural Selection).

For each game, the points are given as follow:

- Win: 2 points;
- Draw: 1 point;
- Loss: 0 point.

# Study

| AI-engine |    setup    | depth | Player | Games | Points | Average |
| :-------: | :---------: | :---: | :----: | :---: | :----: | :-----: |
|   cmalo   |   classic   |   1   | black  |  100  |  200   |  2.00   |
|  natsel   |   classic   |   1   | white  |  100  |   0    |  0.00   |
|           |             |       |        |       |        |         |
|   cmalo   |   classic   |   1   | white  |  100  |  200   |  2.00   |
|  natsel   |   classic   |   1   | black  |  100  |   0    |  0.00   |
|           |             |       |        |       |        |         |
|   cmalo   | half-random |   1   | black  |  100  |  142   |  1.42   |
|  natsel   | half-random |   1   | white  |  100  |   58   |  0.58   |
|           |             |       |        |       |        |         |
|   cmalo   | half-random |   1   | white  |  100  |   68   |  0.68   |
|  natsel   | half-random |   1   | black  |  100  |  132   |  1.32   |
|           |             |       |        |       |        |         |
|           |             |       |        |       |        |         |
|           |             |       |        |       |        |         |
|           |             |       |        |       |        |         |

