from fractions import Fraction
import numpy as np

from ortools.sat.python import cp_model

from FinalSubRound import FinalSubRound
from SubRound import SubRound


def get_common_denominator(jobs: [Fraction], c: Fraction):
    current_lcm = c.denominator
    for job in jobs:
        current_lcm = np.lcm(current_lcm, job.denominator)
    return current_lcm


def solve(jobs: [Fraction],
          m: int,
          c: Fraction,
          cutoff_value: Fraction,
          job_size: Fraction,
          multiplicity: int,
          final=False,
          ratio_for_greedy=0.0):
    """"
    solves the bin packing problem with the given jobs, machines and cutoff value

    :param jobs:               jobs from previous (sub-)rounds
    :param m:                  number of machines
    :param c:                  competitive ratio
    :param cutoff_value:       maximum value for the new makespan
    :param job_size:           size of the new jobs
    :param multiplicity:       number of times the job should be scheduled
    :param final:              indicates when a FinalSubRound should be returned
    :param ratio_for_greedy:   controls which jobs will be scheduled greedily
    :return a SubRound object if a schedulong was found, else None
    """
    model = cp_model.CpModel()
    indicator_variables = {}

    small_jobs, big_jobs = [], []
    for job in jobs:
        if job / cutoff_value < ratio_for_greedy:
            small_jobs.append(job)
        else:
            big_jobs.append(job)

    scale_factor = get_common_denominator(big_jobs, c)
    scaled_jobs = [int(job * scale_factor) for job in big_jobs]
    scaled_cutoff_value = int(scale_factor * cutoff_value)

    # group jobs by size
    multiplicity_per_job_size = {}
    for job in scaled_jobs:
        if job in multiplicity_per_job_size:
            multiplicity_per_job_size[job] += 1
        else:
            multiplicity_per_job_size[job] = 1

    # create indicator variables
    for job, multiplicity in multiplicity_per_job_size.items():
        for j in range(m):
            indicator_variables[(job, j)] = model.NewIntVar(0, multiplicity,
                                                            'job_%i_machine_%i' % (job, j))

    # ensure that each job is scheduled on exactly once
    for job, multiplicity in multiplicity_per_job_size.items():
        model.Add(sum(indicator_variables[(job, j)] for j in range(m)) == multiplicity)

    # ensure that the makespan is less than the cutoff value
    for j in range(m):
        model.Add(sum(indicator_variables[(job, j)] * job for job in multiplicity_per_job_size.keys())
                  <= scaled_cutoff_value)

    # call solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        try:  # greedy scheduling
            if final:
                return FinalSubRound(indicator_variables, solver, big_jobs, small_jobs, cutoff_value, job_size,
                                     multiplicity, m, c, scale_factor)
            else:
                return SubRound(indicator_variables, solver, big_jobs, small_jobs, cutoff_value, job_size,
                                multiplicity, m, c, scale_factor)
        except ValueError:
            pass

    # scheduling not successful, undo alteration of jobs parameter
    for i in range(multiplicity):
        jobs.pop()
    return None
