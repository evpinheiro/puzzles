"""
Solution to the Bullseye.

This version uses PuLP as a modeling language and CBC as a solver.

Created by Eric Zettermann (Jul 11, 2021), MipMaster.org.
"""

import pulp

# region Input Data
# rows
I = {1, 2, 3}
# columns
J = {1, 2, 3, 4, 5, 6}
# digits
K = {1, 2, 3, 5, 10, 20, 25, 50}
# digits repetition
R = {3, 2, 2, 2, 3, 3, 2, 1}
# keys for decision variables x
keys = [(i, j, k) for i in I for j in J for k in K]
# endregion

# region Define the model
mdl = pulp.LpProblem('bullseye', sense=pulp.LpMaximize)

# add variables
x = pulp.LpVariable.dicts(indexs=keys, cat=pulp.LpBinary, name='x')

# add constraints
# 1 digit per cell
for i in I:
    for j in J:
        mdl.addConstraint(pulp.lpSum(x[i, j, k] for k in K) == 1, name=f'1digit_{i}_{j}')
# each row must sum 71
for i in I:
    mdl.addConstraint(pulp.lpSum(k * x[i, j, k] for j in J for k in K) == 71, name=f'sum_{i}')
# digits repetition
    mdl.addConstraint(pulp.lpSum(x[i, j, 1] for i in I for j in J) == 3, name=f'rep_1_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 2] for i in I for j in J) == 2, name=f'rep_2_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 3] for i in I for j in J) == 2, name=f'rep_3_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 5] for i in I for j in J) == 2, name=f'rep_5_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 10] for i in I for j in J) == 3, name=f'rep_10_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 20] for i in I for j in J) == 3, name=f'rep_20_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 25] for i in I for j in J) == 2, name=f'rep_25_{i}')
    mdl.addConstraint(pulp.lpSum(x[i, j, 50] for i in I for j in J) == 1, name=f'rep_50_{i}')

# set the objective function
mdl.setObjective(x[1, 1, 1])  # not really required for this problem
# endregion

# region Optimize and retrieve the solution
mdl.solve()

# retrieve and print out the solution
x_sol = {(i, j): sum(k * x[i, j, k].value() for k in K) for i in I for j in J}
print(f'x = {x_sol}')
# endregion
