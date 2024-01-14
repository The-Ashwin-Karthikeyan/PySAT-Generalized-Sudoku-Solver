import pysat
import pysat.solvers
from pysat.card import CardEnc
import math
import pyapproxmc as mc

import tkinter as tk

class GridApp:
    def __init__(self, master, L):
        self.master = master
        self.master.title("Sudoku Grid")
        self.size = L.dim
        size = L.dim
        self.L = L
        self.block_size = [L.p, L.q] if L.p != 0 else [1, 1]
        self.cells = [[None for _ in range(size)] for _ in range(size)]
        self.inputs = {}

        # Styling parameters
        self.button_height = 1
        self.button_width = 2
        self.button_font = ('Arial', 7)
        self.button_bg = 'lightgray'
        self.button_active_bg = 'lightblue'

        # Create frames for each block
        for block_row in range(0, size, self.block_size[0]):
            for block_col in range(0, size, self.block_size[1]):
                frame = tk.Frame(master, borderwidth=2, relief='ridge', highlightbackground='black', 
                                 highlightcolor='black', 
                                 highlightthickness=1)
                frame.grid(row=block_row//self.block_size[0], column=block_col//self.block_size[1])
                self.populate_block(frame, block_row, block_col)

        # Done button to finish the input process
        done_button = tk.Button(master, text="Done", command=self.finish_input, height=2, width=10)
        done_button.grid(row=size//self.block_size[0], columnspan=size//self.block_size[1], pady=10)

    def populate_block(self, frame, block_row, block_col):
        for i in range(self.block_size[0]):
            for j in range(self.block_size[1]):
                cell = tk.Button(
                    frame,
                    text='',
                    height=self.button_height,
                    width=self.button_width,
                    font=self.button_font,
                    bg=self.button_bg,
                    activebackground=self.button_active_bg
                )

                # Use default arguments in lambda to capture the current values of i and j
                cell.bind('<Button-1>', lambda event, row=block_row + i, col=block_col + j: self.on_click(event, row, col))
                cell.bind('<Key>', lambda event, row=block_row + i, col=block_col + j: self.on_key(event, row, col))

                cell.grid(row=i, column=j, padx=5, pady=5)
                self.cells[block_row + i][block_col + j] = cell

    def on_click(self, event, i, j):
        # Set focus on the clicked button
        self.cells[i][j].focus_set()

    def on_key(self, event, i, j):
        # Check for Backspace key
        if event.keysym == 'BackSpace':
            current_text = self.cells[i][j].cget('text')
            new_text = current_text[:-1]
            self.cells[i][j].config(text=new_text)
            self.inputs[(i,j)] = int(new_text)
        elif event.char.isnumeric():
            # Update button text with the pressed key
            current_text = self.cells[i][j].cget('text')
            new_text = current_text + event.char
            self.cells[i][j].config(text=new_text)
            self.inputs[(i, j)] = int(new_text)
        elif event.keysym == 'Left':
            if j > 0:
                self.cells[i][j - 1].focus_set()

        # Handling Right arrow key
        elif event.keysym == 'Right':
            if j < self.size - 1:  # Assuming self.max_columns is the number of columns
                self.cells[i][j + 1].focus_set()

        # Handling Up arrow key
        elif event.keysym == 'Up':
            if i > 0:
                self.cells[i - 1][j].focus_set()

        # Handling Down arrow key
        elif event.keysym == 'Down':
            if i < self.size - 1:  # Assuming self.max_rows is the number of rows
                self.cells[i + 1][j].focus_set()


    def finish_input(self):
        inputs = self.get_inputs()
        initial_conditions = [[i, j, value - 1] for (i, j), value in inputs.items()]
        self.L.set_initial_conditions(initial_conditions)
        g, vm = decide(self.L)
        if g.solve():
            solution = print_grid(g, vm)
            self.display_solution(solution)
        else:
            print("No solution found")

    def get_inputs(self):
        return self.inputs
    
    def display_solution(self, solution):
        """ Updates the grid to display the solved puzzle """
        for i in range(self.size):
            for j in range(self.size):
                self.cells[i][j].config(text=str(solution[i][j]))

class Grid:
    def __init__(self, dim):
        self.dim = dim
        self.is_prime = self.check_if_prime()
        self.is_square = self.check_if_square()
        self.p = int(math.sqrt(dim)) if self.is_square else 0
        self.q = int(math.sqrt(dim)) if self.is_square else 0
        self.initial_conditions = []

    def check_if_prime(self):
        for i in range(2, int(math.sqrt(self.dim))+1):
            if self.dim%i == 0:
                return False
        return True

    def check_if_square(self):
        return (self.dim/int(math.sqrt(self.dim)) == math.sqrt(self.dim))

    def set_initial_conditions(self, initial_conditions):
        self.initial_conditions = initial_conditions

    def set_p(self, p):
        self.p = p

    def set_q(self, q):
        self.q = q
        
    

def variables(n):
    # Create a 3D-array where the integer in index [i][j][k] represents a boolean variable 
    # indicating whether the value at square (i,j) = k
    variable_matrix = [[[(i*n*n)+(j*n)+k+1 for k in range(n)] for j in range(n)] for i in range(n)]
    return variable_matrix

def index_val_given_var(v, n):
    # Given an integer, return (index, var) pair where index = (i,j) and the returned value
    # reveals the significance of the value 
    # (i.e. the boolean var that indicates (i,j) = var)
    val = ((v-1)%n) + 1
    i = int((v-1)/(n*n))
    j = int(((v-1)%(n*n))/n)
    index = (i,j)
    return index, val

def row_clauses(variable_matrix):
    # Given a variable matrix, create a list of clauses that ensure that for any given
    # row, no number is repeated along that row in the sudoku grid.
    n = len(variable_matrix)
    clauses = []
    for k in range(n):
        for i in range(n):
            lits_k_i = []
            for j in range(n):
                lits_k_i.append(variable_matrix[i][j][k])
            row_i_clauses = CardEnc.equals(lits_k_i, bound = 1, encoding = 0).clauses
            clauses.extend(row_i_clauses)
    return clauses

def col_clauses(variable_matrix):
    # Given a variable matrix, create a list of clauses that ensure that for any given
    # row, no number is repeated along that row in the sudoku grid.
    n = len(variable_matrix)
    clauses = []
    for k in range(n):
        for j in range(n):
            lits_k_j = []
            for i in range(n):
                lits_k_j.append(variable_matrix[i][j][k])
            col_j_clauses = CardEnc.equals(lits_k_j, bound = 1, encoding = 0).clauses
            clauses.extend(col_j_clauses)
    return clauses

def one_num_per_box_clauses(variable_matrix):
    n = len(variable_matrix)
    clauses = []
    for j in range(n):
        for i in range(n):
            lits_k_i_j = []
            for k in range(n):
                lits_k_i_j.append(variable_matrix[i][j][k])
            box_i_j_clauses = CardEnc.equals(lits_k_i_j, bound = 1, encoding = 0).clauses            
            clauses.extend(box_i_j_clauses)
    return clauses

def subbox_clauses(variable_matrix, L: Grid):
    n = len(variable_matrix)
    clauses = []
    if L.is_prime:
        return []
    if L.is_square:
        sqrt = int(math.sqrt(n))
        for k in range(n):
            for m in range(n):
                horizontal_shift = m%sqrt
                vertical_shift = int(m/sqrt)
                lits_m_k = []
                for i in range(sqrt):
                    for j in range(sqrt):
                        lits_m_k.append(variable_matrix[i + (vertical_shift*sqrt)][j + (horizontal_shift*sqrt)][k])
                subbox_m_clauses_for_k = CardEnc.equals(lits_m_k, bound = 1, encoding = 0).clauses
                clauses.extend(subbox_m_clauses_for_k)
        return clauses
    else:
        for k in range(n):
            for m in range(int((n*n)/(L.p*L.q))):
                horizontal_shift = m%L.p
                vertical_shift = int(m/L.p)
                lits_m_k = []
                for i in range(L.p):
                    for j in range(L.q):
                        lits_m_k.append(variable_matrix[i + (vertical_shift*L.p)][j + (horizontal_shift*L.q)][k])
                subbox_m_clauses_for_k = CardEnc.equals(lits_m_k, bound = 1, encoding = 0).clauses
                clauses.extend(subbox_m_clauses_for_k)
        return clauses

def print_grid(g, vm):
    n = len(vm)
    grid = [[0 for i in range(n)] for j in range(n)]
    model = g.get_model()
    for var in model:
        if var > 0:
            ind, val = index_val_given_var(var, n)
            i, j = ind
            grid[i][j] = val
    return grid
    
def decide(L: Grid):
    g = pysat.solvers.Glucose3()
    vm = variables(L.dim)
    rc = row_clauses(vm)
    cc = col_clauses(vm)
    bc = one_num_per_box_clauses(vm)
    sc = subbox_clauses(vm, L)
    clauses = []
    clauses.extend(rc)
    clauses.extend(cc)
    clauses.extend(bc)
    if sc != []:
        clauses.extend(sc)
    for clause in clauses:
        g.add_clause(clause)
    for lst in L.initial_conditions:
        g.add_clause([vm[lst[0]][lst[1]][lst[2]]])
    return g, vm

def approx_count(L: Grid):
    g = mc.Counter()
    vm = variables(L.dim)
    rc = row_clauses(vm)
    cc = col_clauses(vm)
    bc = one_num_per_box_clauses(vm)
    sc = subbox_clauses(vm, L)
    clauses = []
    clauses.extend(rc)
    clauses.extend(cc)
    clauses.extend(bc)
    if sc != []:
        clauses.extend(sc)
    for clause in clauses:
        g.add_clause(clause)
    for lst in L.initial_conditions:
        g.add_clause([vm[lst[0]][lst[1]][lst[2]]])
    return g, vm

def input_grid_layout():
    print("We'll start by getting the grid layout first. \n")
    n = input("Enter size of sudoku grid: ")
    n = int(n)
    L = Grid(n)
    if (L.is_prime or L.is_square):
        return L
    else:
        print("This is not a perfect square.")
        factor = True
        while(factor):
            print("You will need to enter two factors for the size.")
            p = input("Enter the first factor: ")
            q = input("Enter the second factor: ")
            p = int(p)
            q = int(q)
            factor = (p*q != n)
            if p*q != n:
                print("Incorrect factors.")
            else:
                L.set_p(p)
                L.set_q(q)
    return L

if __name__ == "__main__":
    L = input_grid_layout()

    root = tk.Tk()
    app = GridApp(root, L)
    root.mainloop()
    g, vm = approx_count(L)
    count = g.count()
    num_count = count[0]*2**count[1]
    print(num_count)