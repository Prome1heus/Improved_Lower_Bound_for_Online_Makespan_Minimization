import math
from fractions import Fraction
import numpy as np
from ortools.sat.python import cp_model

from FinalSubRound import FinalSubRound
from Round import Round
from SubRound import SubRound


def get_common_denominator(jobs: [Fraction], c: Fraction):
    current_lcm = c.denominator
    for job in jobs:
        current_lcm = np.lcm(current_lcm, job.denominator)
    return current_lcm


def complete_round(
        jobs: [Fraction],
        c: Fraction,
        m: int,
        round_id: int,
        job_size: Fraction,
        ratio_for_greedy):
    """
    :param jobs:
    :param c:
    :param m:
    :param round_id
    :param job_size
    :param ratio_for_greedy
    :param
    """
    fround = Round(round_id, m)

    # binary search the number of times the initial job can be scheduled additionally
    low, high, best = 1, m, 0
    base_cutoff_value = 0
    for i in range(0, len(jobs), m):
        base_cutoff_value += jobs[i]
    while low <= high:
        mid = int((low + high) / 2)
        for _ in range(mid):
            jobs.append(job_size)
        if solve(jobs, m, c, (base_cutoff_value + 2 * job_size) / c, job_size, mid, False, ratio_for_greedy) is None:
            high = mid - 1
        else:
            low = mid + 1
            best = mid
            for _ in range(mid):
                jobs.pop()

    for _ in range(best):
        jobs.append(job_size)

    fround.add_sub_round(
        solve(jobs, m, c, (base_cutoff_value + 2 * job_size) / c, job_size, best, False, ratio_for_greedy))

    last_job_size = job_size
    for i in range(best, m):
        low = last_job_size
        high = Fraction(round((base_cutoff_value + job_size) / (c - 1), 4))
        print(i, low, high)
        while low <= high - Fraction(1, 1000):
            tried_job_size = (low + high)/2  # Fraction(round(float(low + high) / 2, 20))
            tried_job_size = Fraction(round(tried_job_size, 4))
            print(float(low), float(high), float(tried_job_size))
            jobs.append(tried_job_size)
            tried_sub_round = solve(jobs, m, c, (base_cutoff_value + job_size + tried_job_size) / c, tried_job_size, 1, False,
                     ratio_for_greedy)
            if tried_sub_round is None:
                low = tried_job_size
            else:
                high = tried_job_size
                optimal_job_size = tried_job_size
                optimal_sub_round = tried_sub_round
                jobs.pop()
        print(float(optimal_job_size))
        if optimal_sub_round is None:
            raise ValueError("Help")
        fround.add_sub_round(optimal_sub_round)
        jobs.append(optimal_job_size)
        last_job_size = optimal_job_size

    return fround


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

    ########################################################
    first = True
    for i in range(len(scaled_jobs)):
        if first:
            try:
                if math.log2(scaled_jobs[i]) > 31:
                    print("Alarm", scale_factor)
            except ValueError:
                print("Alarm", scaled_jobs[i], big_jobs[i])
            first = False
    #########################################################

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
    solver.parameters.max_time_in_seconds = 40
    status = solver.Solve(model)
    print(status)
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
    elif status == cp_model.MODEL_INVALID:
        print("-------------------------------------")
        print(max(big_jobs))
        print(float(cutoff_value), float(job_size))
        print("-------------------------------------")

    # scheduling not successful, undo alteration of jobs parameter
    for i in range(multiplicity):
        jobs.pop()
    return None
