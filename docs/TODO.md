# TODO
The foreseen tasks on pijersi-certu are as follows:

- [ ] Provide user of the GUI with "**game review**" based on an evaluation of a position after each action: 
  - Such review is performed by a reference AI.
  - The analysis is returned for the pijersi-state corresponding to the best-action found by the AI.
  - In addition to return the name of the best-move and, maybe, the value of the AI own evaluation function, the AI must return a standard position evaluation or the AI must return the Pijersi-state found at some depth that holds such best value.
  - Here is a proposal for the standard position evaluation (SPA):
    - In priority, report "mat" in 1, 2 or 3 turns.
    - Report a numerical score denoting the advantage : position for White advantage, negative for Black advantage.
    - Compute the advantage by the difference between White and Black of a global player score (GPS).
    - GPS = 1 x "count of  rock/paper/scissors"  + 1.5 x "count of wises" + 8/"minimal distance to goal" 
    - GPS is rounded to 1 decimal
    - advantage when White = GPS_White - GPS_Black 
    - advantage when Black = GPS_Black - GPS_White
- [ ] Re-optimize the Minimax weights using CMA-ES to account for random setups and to account for Minimax-4.

