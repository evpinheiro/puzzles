"""
Solution to the Continuous Line.

This version uses PuLP as a modeling language and CBC as a solver.

The model formulation is a TSP with "Dantzig–Fulkerson–Johnson" subtour elimination constraint
"""

import gurobipy as gp
from gurobipy import GRB

from itertools import combinations


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
mdl = gp.Model('continuous_line_tsp')

# add variables
x = mdl.addVars(A, vtype=GRB.BINARY, name='x')

# add constraints
for node in N:
    # exactly one origin
    mdl.addConstr(sum(x[out] for out in node.ongoing_arcs) == 1, name=f'origin_{node}')
    # exactly one destination
    mdl.addConstr(sum(x[into] for into in node.incoming_arcs) == 1, name=f'destination_{node}')

n = len(N)


# Callback - use lazy constraints to eliminate sub-tours
def subtourelim(model, where):
    if where == 6:
        return
    print('Here1')
    print(where)
    print('but', GRB.Callback.MIPSOL)
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = gp.tuplelist((i, j) for i, j in model._vars.keys()
                                if vals[i, j] > 0.5)
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        print('Here2')
        if n > len(tour) > 1:
            # add subtour elimination constr. for every pair of cities in tour
            model.cbLazy(gp.quicksum(model._vars[a] for a in tour) <= len(tour) - 1)
            print('Here3')


# Given a tuplelist of edges, find the shortest subtour
def subtour(edges):
    unvisited = list(range(n))
    cycle = range(n + 1)  # initial length has 1 more city
    while unvisited:  # true if list is non-empty
        thiscycle = []
        neighbors = unvisited
        while neighbors:
            current = neighbors[0]
            thiscycle.append(current)
            unvisited.remove(current)
            neighbors = [j for i, j in edges.select(current, '*')
                         if j in unvisited]
        if len(cycle) > len(thiscycle):
            cycle = thiscycle
    arc_cicles = []
    for i in range(1, len(cycle)):
        arc_cicles.append((cycle[i-1], cycle[i]))
    arc_cicles.append((cycle[len(cycle)-1], cycle[0]))
    return arc_cicles


mdl.Params.lazyConstraints = 1
mdl._vars = x

# set the objective function
mdl.setObjective(sum(x[a] for a in A))  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
mdl.optimize(subtourelim)

# retrieve and print out the solution
# u_sol = {(node.cell.row, node.cell.col): int(round(u[node].X)) for node in N if node != dummy_node}
# for i in range(1, num_rows + 1):
#     row = [u_sol[i, j] if (i, j) in u_sol else 0 for j in range(1, num_cols + 1)]
#     print(row)
vals = mdl.getAttr('x', x)
# print(vals)
selected = gp.tuplelist((i, j) for i, j in vals.keys() if vals[i, j] > 0.5)
# print(selected)

tour = subtour(selected)
# print(tour)
assert len(tour) == n

#
# sol = {a[0]: a[1] for a in A if x[a].X == 1}
# print(sol)
# init = dummy_node
# next = sol[init]
# path = {next: 1}
# k = 2
# while next != dummy_node:
#     next = sol[next]
#     path[next] = k
#     k += 1
# print(path)
# for i in range(1, num_rows + 1):
#     row = [sol[(i, j)] if (i, j) not in H else 0 for j in range(1, num_cols + 1)]
#     print(row)

# endregion
