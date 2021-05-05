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
        ratio_for_greedy: float,
        job_multiplicity: int) -> Round:
    """
    :param jobs:
    :param c:
    :param m:
    :param round_id
    :param job_size
    :param ratio_for_greedy
    :param job_multiplicity
    """

    print('Optimal %i' % cp_model.OPTIMAL)
    print('Feasible %i' % cp_model.FEASIBLE)
    print('Infeasible %i' % cp_model.INFEASIBLE)
    print('Model_Invalid %i' % cp_model.MODEL_INVALID)
    print('Unknown %i' % cp_model.UNKNOWN)

    result = Round(round_id, m)

    # binary search the number of times the initial job can be scheduled additionally
    low, high, best = 1, m, 0
    base_cutoff_value = Fraction(0)

    # calculate lowest possible load on any machine before the round
    for i in range(0, len(jobs), m):
        base_cutoff_value += jobs[i]

    # binary search how often the initial job can be scheduled
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

    result.add_sub_round(
        solve(jobs, m, c, (base_cutoff_value + 2 * job_size) / c, job_size, best, False, ratio_for_greedy))
    # complete the round
    last_job_size = job_size
    i = best
    while i < m:
        low = last_job_size
        high = Fraction(round((base_cutoff_value + job_size) / (c - 1), 6))

        if i + job_multiplicity > m:
            multiplicity = m - i
        else:
            multiplicity = job_multiplicity
        print('multiplicity %i' % multiplicity)

        print(i, low, high)
        # binary search the lowest job size that can be scheduled job_multiplicity times
        optimal_sub_round, optimal_job_size = None, None
        while low <= high:
            # approximate the middle value to avoid that the rescaled jobs cause an integer overflow
            tried_job_size = (low + high)/2
            tried_job_size = Fraction(round(tried_job_size, 6))
            print(float(low), float(high), float(tried_job_size))
            for _ in range(multiplicity):
                jobs.append(tried_job_size)
            tried_sub_round = solve(jobs, m, c, (base_cutoff_value + job_size + tried_job_size) / c, tried_job_size,
                                    multiplicity, False, ratio_for_greedy)
            if tried_sub_round is None:
                low = tried_job_size + Fraction(1, 100000)
            else:
                high = tried_job_size - Fraction(1, 100000)
                optimal_job_size = tried_job_size
                optimal_sub_round = tried_sub_round
                for _ in range(multiplicity):
                    jobs.pop()

        if optimal_sub_round is None:
            print("here")
            job_multiplicity = int(job_multiplicity/2)
            if job_multiplicity == 0:
                raise ValueError("Impossible to complete round")
        else:
            print(float(optimal_job_size))
            result.add_sub_round(optimal_sub_round)
            for _ in range(multiplicity):
                jobs.append(optimal_job_size)
            print(jobs)
            last_job_size = optimal_job_size
            i += job_multiplicity
    return result


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
    last_job, count_for_job = 0, 0
    for job in jobs:
        if job != last_job:
            count_for_job = 0
            last_job = job
        if job / cutoff_value < ratio_for_greedy and (job != Fraction(141, 500) or count_for_job < 2):
            small_jobs.append(job)
            count_for_job += 1
        else:
            big_jobs.append(job)
    #print('small jobs:', small_jobs)

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
    solver.parameters.max_time_in_seconds = 500
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

    # scheduling not successful, undo alteration of jobs parameter
    for i in range(multiplicity):
        jobs.pop()
    return None
