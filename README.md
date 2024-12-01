# Generalized nxn Sudoku Solver

## What is Generalized nxn Sudoku?
In this version of Sudoku, if $ n $ is not prime, it is factored into two integers $ p $ and $ q $ such that the grid is composed of $\( p \times q \)$ rectangles (these rectangles are referred to as subboxes, and there are $n$ such subboxes.). The standard rules of Sudoku apply: each number must appear exactly once in each row, column, and subbox.

## How is this implemented?
The solver uses the Glucose3 model from PySat. The current encoding is fairly straightforward (a detailed document explaining the encoding will be released soon).

## Acknowledgements
The GUI was developed with the assistance of GPT-4.

