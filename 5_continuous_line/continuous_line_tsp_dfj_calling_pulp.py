"""
Solution to the Continuous Line.

This version uses PuLP as a modeling language and CBC as a solver.

The model formulation is a TSP with "Dantzig–Fulkerson–Johnson" subtour elimination constraint
"""
import time

import pulp

from itertools import combinations
from itertools import permutations

# region Input Data
num_rows = 8
num_cols = 8
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
dummy_node = Node(Cell(0, 0))
N.append(dummy_node)

# creating arcs
A = []
for origin in N:
    for destination in N:
        "it creates an arc if exclusively the origin or the destination is the dummy node;"
        "or if the puzzle cells connection rule is met"
        if (bool(origin == dummy_node) != bool(destination == dummy_node)) or \
                (origin.cell.row == destination.cell.row and abs(origin.cell.col - destination.cell.col) == 1 or
                 origin.cell.col == destination.cell.col and abs(origin.cell.row - destination.cell.row) == 1):
            A.append((origin, destination))
            origin.ongoing_arcs.append((origin, destination))
            destination.incoming_arcs.append((origin, destination))

print(len(A) + len(N))
# region Define the model
mdl = pulp.LpProblem('continuous_line_tsp')

# add variables
x = pulp.LpVariable.dicts(indexs=A, cat=pulp.LpBinary, name='x')

# add constraints
for node in N:
    # exactly one origin
    mdl.addConstraint(sum(x[out] for out in node.ongoing_arcs) == 1, name=f'origin_{node}')
    # exactly one destination
    mdl.addConstraint(sum(x[into] for into in node.incoming_arcs) == 1, name=f'destination_{node}')

n = len(N)


# Given a tuplelist of edges, find the shortest subtour
def subtour(model):
    sol = {a[0]: a[1] for a in A if x[a].value() == 1}
    init = None
    for a in A:
        if x[a].value() == 1:
            init = a[0]
    next = sol[init]
    arc_cycle = []
    while next != dummy_node:
        previous = next
        next = sol[next]
        arc_cycle.append((previous, next))

    arc_cycle.append((arc_cycle[len(arc_cycle) - 1][1], arc_cycle[0][0]))
    return arc_cycle


mdl._vars = x

# set the objective function
mdl.setObjective(sum(x[a] for a in A))  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
solver = pulp.PULP_CBC_CMD(msg=False)
star_time = time.time()
tour_length = 0
while tour_length < n:
    mdl.solve(solver)
    tour = subtour(mdl)
    tour_length = len(tour)
    if n > len(tour) > 1:
        nodes = [a[0] for a in tour]
        mdl.addConstraint(sum(x[(i,j)] for i, j in permutations(nodes, 2) if (i, j) in A) <= len(tour) - 1)
        # mdl.addConstraint(sum(x[a] for a in tour) <= len(tour) - 1)
    print(len(mdl.constraints), tour_length, mdl.objective.value(), nodes)
    # print(tour)
end_time = time.time()
print('execution time', end_time-star_time)


# retrieve and print out the solution
tour = subtour(mdl)
assert len(tour) == n
path = {}
for arc in tour:
    path[(arc[0].cell.row, arc[0].cell.col)] = (arc[1].cell.row, arc[1].cell.col)
print(path)
sol = {}
next_node = path[(0, 0)]
k = 1
while next_node != (0, 0):
    sol[next_node] = k
    next_node = path[next_node]
    k += 1
for i in range(1, num_rows + 1):
    row = [sol[(i, j)] if (i, j) in sol else 0 for j in range(1, num_cols + 1)]
    print(row)

# endregion
