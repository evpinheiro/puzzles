"""
Solution to the Continuous Line.

This version uses PuLP as a modeling language and CBC as a solver.

The model formulation is a TSP with "Dantzig–Fulkerson–Johnson" subtour elimination constraint
"""

import pulp

# region Input Data
num_rows = 6
num_cols = 6
# holes
H = [(1, 3), (2, 5), (4, 3), (4, 4), (5, 1), (5, 4), (5, 6), (6, 1), (6, 6)]


# cell representation
class Cell:

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __str__(self):
        return f'({self.row},{self.col})'

    def __repr__(self):
        return self.__str__()


# region defining graph structure
class Node:

    def __init__(self, cell: Cell):
        # self.id = code
        self.cell = cell
        self.ongoing_arcs = []
        self.incoming_arcs = []

    def __str__(self):
        return str(self.cell)

    def __repr__(self):
        return self.__str__()


class Arc:

    def __init__(self, origin: Node, destination: Node):
        # self.id = id
        self.origin = origin
        self.destination = destination
        self.origin.ongoing_arcs.append(self)
        self.destination.incoming_arcs.append(self)

    def __str__(self):
        return f'{str(self.origin)}{str(self.destination)}'

    def __repr__(self):
        return self.__str__()
# endregion


# creating nodes
N = []
for i in range(1, num_rows + 1):
    for j in range(1, num_cols + 1):
        if (i, j) not in H:
            N.append(Node(Cell(i, j)))
dummy_node = Node(Cell(-1, -1))

# creating arcs
A = []
for node in N:
    A.append(Arc(node, dummy_node))
    A.append(Arc(dummy_node, node))
for origin in N:
    for destination in N:
        if origin.cell.row == destination.cell.row and abs(origin.cell.col - destination.cell.col) == 1 or \
                origin.cell.col == destination.cell.col and abs(origin.cell.row - destination.cell.row) == 1:
            A.append(Arc(origin, destination))

# region Define the model
mdl = pulp.LpProblem('continuous_line_tsp', sense=pulp.LpMinimize)

# add variables
x = pulp.LpVariable.dicts(indexs=A, cat=pulp.LpBinary, name='x')
u = pulp.LpVariable.dicts(indexs=N + [dummy_node], cat=pulp.LpInteger, upBound=len(N), name='u')

# add constraints
for node in N + [dummy_node]:
    # exactly one origin
    mdl.addConstraint(pulp.lpSum(x[out] for out in node.ongoing_arcs) == 1, name=f'origin_{node}')
    # exactly one destination
    mdl.addConstraint(pulp.lpSum(x[into] for into in node.incoming_arcs) == 1, name=f'destination_{node}')

# sequence
n = len(N) + 1
for arc in A:
    if arc.origin != dummy_node and arc.destination != dummy_node:
        mdl.addConstraint(u[arc.origin] - u[arc.destination] + 1 <= n * (1 - x[arc]),
                          name=f'seq{arc.origin}{arc.destination}')

# set the objective function
mdl.setObjective(pulp.lpSum(x[a] for a in A))  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
mdl.solve()

# retrieve and print out the solution
u_sol = {(node.cell.row, node.cell.col): int(round(u[node].value())) for node in N}
for i in range(1, num_rows + 1):
    row = [u_sol[i, j] if (i, j) in u_sol else 'X' for j in range(1, num_rows + 1)]
    print(row)
# endregion
