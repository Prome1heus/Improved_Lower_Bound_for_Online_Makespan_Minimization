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
        precision: int) -> Round:
    """
    :param jobs:
    :param c:
    :param m:
    :param round_id:
    :param job_size:
    :param ratio_for_greedy
    :param precision:
    """

    result = Round(round_id, m)

    # binary search the number of times the initial job can be scheduled additionally
    low, high, best = 1, m, 0
    base_cutoff_value = Fraction(0)

    # calculate lowest possible load on any machine before the round
    for i in range(0, len(jobs), m):
        base_cutoff_value += jobs[i]
    base_cutoff_value += job_size

    # schedule specified job size as often as possible
    subround, count = \
        schedule_job_as_often_as_possible(m, c, (base_cutoff_value + job_size) / c, jobs, job_size, ratio_for_greedy)
    result.add_sub_round(subround)
    print("SubRound", subround.job_size, subround.multiplicity)
    # complete round
    while count != m:
        # find smallest job size
        new_job_size = find_smallest_possible_job_size(m, c, base_cutoff_value, jobs, precision,
                                                       ratio_for_greedy)
        print(new_job_size)
        # schedule as often as possible
        subround, multiplicity = schedule_job_as_often_as_possible(m, c, (base_cutoff_value + new_job_size) / c, jobs, new_job_size,
                                                     ratio_for_greedy)

        result.add_sub_round(subround)
        count += multiplicity
        print("count", count)
        print("Subround", subround.job_size, subround.multiplicity)
    return result


def find_smallest_possible_job_size(
        m: int,
        c: Fraction,
        base_cutoff_value: Fraction,
        jobs: [Fraction],
        precision: int,
        ratio_for_greedy: float
):
    # binary search the lowest job size that can be scheduled job_multiplicity times
    optimal_job_size = None
    low, high = jobs[-1], Fraction(round(base_cutoff_value / (c - 1), precision))
    while low <= high:
        # approximate the middle value to avoid that the rescaled jobs cause an integer overflow
        tried_job_size = (low + high) / 2
        tried_job_size = Fraction(round(tried_job_size, precision))
        print(float(low), float(high), float(tried_job_size))
        jobs.append(tried_job_size)
        tried_sub_round = solve(jobs, m, c, (base_cutoff_value + tried_job_size) / c, tried_job_size,
                                1, False, ratio_for_greedy)
        if tried_sub_round is None:
            low = tried_job_size + Fraction(1, 10 ** precision)
        else:
            high = tried_job_size - Fraction(1, 10 ** precision)
            optimal_job_size = tried_job_size
            jobs.pop()

    return optimal_job_size


def schedule_job_as_often_as_possible(
        m: int,
        c: Fraction,
        cutoff_value: Fraction,
        jobs: [Fraction],
        job_size: Fraction,
        ratio_for_greedy: float
):
    # iterative search since successful solves are way faster than timeouts
    last_success = None
    for i in range(m - len(jobs) % m):
        jobs.append(job_size)
        sub_round = solve(jobs, m, c, cutoff_value, job_size, i + 1, False, ratio_for_greedy)
        if sub_round is None:
            for j in range(i):
                jobs.append(job_size)
            return last_success, i
        last_success = sub_round
    return last_success, last_success.multiplicity


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
    for job, mult in multiplicity_per_job_size.items():
        for j in range(m):
            indicator_variables[(job, j)] = model.NewIntVar(0, mult,
                                                            'job_%i_machine_%i' % (job, j))

    # ensure that each job is scheduled on exactly once
    for job, mult in multiplicity_per_job_size.items():
        model.Add(sum(indicator_variables[(job, j)] for j in range(m)) == mult)

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

    # scheduling not successful, undo alteration of jobs parameter
    for i in range(multiplicity):
        jobs.pop()
    return None
