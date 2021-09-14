"""
Solution to the Continuous Line.

This version uses PuLP as a modeling language and CBC as a solver.

The model formulation is a TSP with "Dantzig–Fulkerson–Johnson" subtour elimination constraint
"""

import gurobipy as gp
from gurobipy import GRB

from itertools import permutations

# region Input Data
num_rows = 6
num_cols = 6
# holes
H = [(1, 3), (2, 5), (4, 3), (4, 4), (5, 1), (5, 4), (5, 6), (6, 1), (6, 6)]

# endregion


# creating nodes
N = []
for i in range(1, num_rows + 1):
    for j in range(1, num_cols + 1):
        if (i, j) not in H:
            N.append((i, j))
dummy_node = (0, 0)
N.append(dummy_node)

# creating arcs
A = []
for origin in N:
    for destination in N:
        "it creates an arc if exclusively the origin or the destination is the dummy node;"
        "or if the puzzle cells connection rule is met"
        if (bool(origin == dummy_node) != bool(destination == dummy_node)) or \
                (origin[0] == destination[0] and abs(origin[1] - destination[1]) == 1 or
                 origin[1] == destination[1] and abs(origin[0] - destination[0]) == 1):
            A.append((origin, destination))

# region Define the model
mdl = gp.Model('continuous_line_tsp_dfj')

# add variables
x = mdl.addVars(A, vtype=GRB.BINARY, name='x')

# add constraints
for node in N:
    # exactly one origin
    mdl.addConstr(sum(x[out] for out in A if out[0] == node) == 1, name=f'origin_{node}')
    # exactly one destination
    mdl.addConstr(sum(x[into] for into in A if into[1] == node) == 1, name=f'destination_{node}')


# Callback - use lazy constraints to eliminate sub-tours
def subtour_constraint(model, where):
    if where == GRB.Callback.MIPSOL:
        values = model.cbGetSolution(model._x)
        solution = {a[0]: a[1] for a in model._A if values[a] > 0.5}
        cycle = subtour(solution)
        if model._n > len(cycle) > 1:
            nodes = [a[0] for a in cycle]
            model.cbLazy(gp.quicksum(model._x[i, j] for i, j in permutations(nodes, 2)
                                     if (i, j) in model._A) <= len(cycle) - 1)
            # model.cbLazy(gp.quicksum(model._vars[a] for a in tour) <= len(tour) - 1)


# Given a dict of edges, find one subtour
def subtour(solution):
    init = None
    for a in solution.keys():
        init = solution[a]
        break
    next = solution[init]
    arc_cycle = []
    while next != init:
        previous = next
        next = solution[next]
        arc_cycle.append((previous, next))

    arc_cycle.append((arc_cycle[len(arc_cycle) - 1][1], arc_cycle[0][0]))
    return arc_cycle


mdl.Params.lazyConstraints = 1
mdl._x = x
mdl._A = A
mdl._n = len(N)

# set the objective function
mdl.setObjective(sum(x[a] for a in A))  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
mdl.optimize(subtour_constraint)

# retrieve and print out the solution
sol = {a[0]: a[1] for a in A if x[a].X > 0.5}
tour = subtour(sol)
path = {}
for arc in tour:
    path[(arc[0][0], arc[0][1])] = (arc[1][0], arc[1][1])
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
