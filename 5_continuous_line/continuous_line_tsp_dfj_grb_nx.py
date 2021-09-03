"""
Solution to the Continuous Line.

This version uses PuLP as a modeling language and CBC as a solver.

The model formulation is a TSP with "Dantzig–Fulkerson–Johnson" subtour elimination constraint
"""

import gurobipy as gp
from gurobipy import GRB

from itertools import combinations

import networkx as nx


# region Input Data
num_rows = 16
num_cols = 16
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
            A.append(Arc(origin, destination))

print(len(A) + len(N))
# region Define the model
mdl = gp.Model('continuous_line_tsp')

# add variables
x = mdl.addVars(A, vtype=GRB.BINARY, name='x')


# add constraints
for node in N + [dummy_node]:
    # exactly one origin
    mdl.addConstr(sum(x[out] for out in node.ongoing_arcs) == 1, name=f'origin_{node}')
    # exactly one destination
    mdl.addConstr(sum(x[into] for into in node.incoming_arcs) == 1, name=f'destination_{node}')

# sequence
n = len(N) + 1
for arc in A:
    if arc.origin != dummy_node and arc.destination != dummy_node:
        mdl.addConstr(u[arc.origin] - u[arc.destination] + 1 <= n * (1 - x[arc]),
                      name=f'seq{arc.origin}{arc.destination}')


# Callback - use lazy constraints to eliminate sub-tours
def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        # selected = gp.tuplelist((i, j) for i, j in model._vars.keys()
        #                         if vals[i, j] > 0.5)
        # find the shortest cycle in the selected edge list
        tour = subtour(vars)
        if len(tour) < n:
            # add subtour elimination constr. for every pair of cities in tour
            model.cbLazy(gp.quicksum(model._vars[i, j]
                                     for i, j in combinations(tour, 2))
                         <= len(tour) - 1)


# Given a tuplelist of edges, find the shortest subtour
def subtour(vars):
    G = nx.DiGraph()
    for a in A:
        G.add_edge(a.origin, a.destination, capacity=vars[a].X)
    for (u, v) in F:
        val, (S, NS) = nx.minimum_cut(G, u, v)


mdl._vars = vars
mdl.Params.lazyConstraints = 1

# set the objective function
mdl.setObjective(sum(x[a] for a in A))  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
mdl.optimize(subtourelim)

# retrieve and print out the solution
u_sol = {(node.cell.row, node.cell.col): int(round(u[node].X)) for node in N if node != dummy_node}
for i in range(1, num_rows + 1):
    row = [u_sol[i, j] if (i, j) in u_sol else 0 for j in range(1, num_cols + 1)]
    print(row)
# endregion
