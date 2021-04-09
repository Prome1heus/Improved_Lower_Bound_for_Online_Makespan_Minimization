from ortools.sat.python import cp_model

from SubRound import SubRound


def solve(jobs, m, c, cutoff_value, job_size, multiplicity):
    model = cp_model.CpModel()
    indicator_variables = {}

    # create indicator variables
    for i in range(len(jobs)):
        for j in range(m):
            indicator_variables[(i, j)] = model.NewBoolVar('job_%i_machine_%i' % (i, j))

    # ensure that each job is scheduled on exactly one machine
    for i in range(len(jobs)):
        model.Add(sum(indicator_variables[(i, j)] for j in range(m)) == 1)

    # ensure that the makespan is less than the cutoff value
    for j in range(m):
        model.Add(sum(indicator_variables[(i, j)] * jobs[i] for i in range(len(jobs))) <= cutoff_value)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        return SubRound(indicator_variables, solver, jobs, cutoff_value, job_size, multiplicity, m, c)
    else:
        return None
