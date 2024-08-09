# TODO
The foreseen tasks on pijersi-certu are as follows:

- [ ] Provide user of the GUI with "**game review**" ; hints :
  - The game review is performed only when the game is stopped if it is CPU demanding, otherwise it could be performed after each move.
  - Use a reference AI engine, for example natsel at level 5.
  - For each agent move the reference AI is launched on the state played by the agent and the AI score for each possible moves are returned and used to evaluate the performance of the agent using some algorithm.
  - Performance algorithm :
    - Sort the N available moves in increasing score by the reference AI ; it gives rank 1 to N.
    - Identify the agent move and its rank R.
    - Make a relative rank r=R/100 between 0 and 1.
    - Maybe: apply a transformation using a increasing function: inverse of the CDF of a truncated Gaussian distribution of mean m and variance s2.
    -   Manage the truncation to obtain all the outputs in a user friendly interval like[0 ; 10].
    -   Calibrate m and s2 regarding some not too strong AI like cmalo-2.
- [ ] Re-optimize the Minimax weights using CMA-ES to account for random setups and to account for Minimax-4.

