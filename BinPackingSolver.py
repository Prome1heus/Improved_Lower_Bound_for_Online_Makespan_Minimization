import math
from fractions import Fraction
import numpy as np
from ortools.sat.python import cp_model

from FinalSubRound import FinalSubRound
from Round import Round
from SubRound import SubRound


class BinPackingSolver:

    def __init__(self, m: int, c: Fraction, timeout: int):
        """
        :param m:           number of machines
        :param c:           competitive ratio
        :param timeout:     timeout for the CP-SAT solver
        """
        self.m = m
        self.c = c
        self.timeout = timeout

    def get_common_denominator(self, jobs: [Fraction]) -> int:
        """
        computes the smallest integer which can be used to scale c and all jobs to integers
        :param jobs:    jobs that need to be scaled
        :returns:       the lowest common multiple multiple of the denominators of c and all jobs
        """
        current_lcm = self.c.denominator
        for job in jobs:
            current_lcm = np.lcm(current_lcm, job.denominator)
        return current_lcm

    def complete_round(
            self,
            jobs: [Fraction],
            round_id: int,
            job_size: Fraction,
            ratio_for_greedy: float,
            precision: int) -> Round:
        """
        schedules an entire round based on the size of the first job and the previously scheduled jobs
        :param jobs:                jobs scheduled in previous rounds
        :param round_id:            indicates which round it being scheduled
        :param job_size:            given size of first job in round
        :param ratio_for_greedy:    which proportion of jobs should be
        :param precision:           number of decimal places considered
        :returns                    the scheduled round
        """

        result = Round(round_id, self.m)

        # binary search the number of times the initial job can be scheduled additionally
        base_cutoff_value = Fraction(0)

        # calculate lowest possible load on any machine before the round
        for i in range(0, len(jobs), self.m):
            base_cutoff_value += jobs[i]
        base_cutoff_value += job_size

        # schedule specified job size as often as possible
        subround, count = \
            self.schedule_job_as_often_as_possible((base_cutoff_value + job_size) / self.c, jobs, job_size,
                                                   ratio_for_greedy)
        result.add_sub_round(subround)
        print("SubRound with %i jobs of size %f was successfully scheduled." %
              (subround.multiplicity, float(subround.job_size), ))
        # complete round
        while count != self.m:
            # find smallest job size
            new_job_size = self.find_smallest_possible_job_size(base_cutoff_value, jobs, precision,
                                                                ratio_for_greedy)
            if new_job_size is None:
                return None
            print(new_job_size)
            # schedule as often as possible
            subround, multiplicity = self.schedule_job_as_often_as_possible((base_cutoff_value + new_job_size) / self.c,
                                                                            jobs, new_job_size,
                                                                            ratio_for_greedy)

            result.add_sub_round(subround)
            count += multiplicity
            print("SubRound with %i jobs of size %f was successfully scheduled." %
                  (subround.multiplicity, float(subround.job_size),))
        return result

    def find_smallest_possible_job_size(
            self,
            base_cutoff_value: Fraction,
            jobs: [Fraction],
            precision: int,
            ratio_for_greedy: float,
    ):
        """
        uses binary search to determine the smallest job that can be scheduled
        :param base_cutoff_value:   summation of the first jobs in all rounds
        :param jobs:                previously scheduled jobs
        :param precision:           number of decimal points considered in the binary search
        :param ratio_for_greedy:    the ratio of jobs which should be scheduled greedily
        :returns:                   the smallest job size as a Fraction
        """

        print("Binary search for smallest possible job size")
        # binary search the lowest job size that can be scheduled job_multiplicity times
        optimal_job_size = None
        low, high = jobs[-1], Fraction(round(base_cutoff_value / (self.c - 1), precision))
        while low <= high:
            # approximate the middle value to avoid that the rescaled jobs cause an integer overflow
            tried_job_size = (low + high) / 2
            tried_job_size = Fraction(round(tried_job_size, precision))
            print(float(low), float(high), float(tried_job_size))
            jobs.append(tried_job_size)
            tried_sub_round = self.solve(jobs, (base_cutoff_value + tried_job_size) / self.c, tried_job_size,
                                         1, False, ratio_for_greedy)
            if tried_sub_round is None:
                print('Success')
                low = tried_job_size + Fraction(1, 10 ** precision)
            else:
                print('Failure')
                high = tried_job_size - Fraction(1, 10 ** precision)
                optimal_job_size = tried_job_size
                jobs.pop()

        return optimal_job_size

    def schedule_job_as_often_as_possible(
            self,
            cutoff_value: Fraction,
            jobs: [Fraction],
            job_size: Fraction,
            ratio_for_greedy: float
    ):
        """"
        iteratively increases the number of jobs with size job_size until the Subround can no longer be scheduled
        :param cutoff_value:        maximum value for resulting makespan
        :param jobs:                previously scheduled jobs, scheduled jobs are appended
        :param job_size:            size of the jobs in the subround
        :param ratio_for_greedy:    the ratio of jobs which should be scheduled greedily
        :returns                    resulting subround, number of jobs that should be scheduled
        """
        print("Trying to schedule as many jobs of size %f as possible" % float(job_size))

        # iterative search since successful solves are way faster than timeouts
        last_success = None
        for i in range(self.m - len(jobs) % self.m):
            jobs.append(job_size)
            sub_round = self.solve(jobs, cutoff_value, job_size, i + 1, False, ratio_for_greedy)
            if sub_round is None:
                for j in range(i):
                    jobs.append(job_size)
                return last_success, i
            last_success = sub_round
        return last_success, last_success.multiplicity

    def solve(self,
              jobs: [Fraction],
              cutoff_value: Fraction,
              job_size: Fraction,
              multiplicity: int,
              final=False,
              ratio_for_greedy=0.0):
        """"
        solves the bin packing problem with the given jobs, machines and cutoff value
        :param jobs:               jobs from previous (sub-)rounds
        :param cutoff_value:       maximum value for the new makespan
        :param job_size:           size of the new jobs
        :param multiplicity:       number of times the job should be scheduled
        :param final:              indicates when a FinalSubRound should be returned
        :param ratio_for_greedy:   controls which jobs will be scheduled greedily
        :returns                   a SubRound object if a schedule was found, else None
        """
        model = cp_model.CpModel()
        indicator_variables = {}

        small_jobs, big_jobs = [], []
        last_job, count_for_job = 0, 0
        for job in jobs:
            if job != last_job:
                count_for_job = 0
                last_job = job
            if job / cutoff_value < ratio_for_greedy and ((count_for_job+1) * job <= 1):
                small_jobs.append(job)
                count_for_job += 1
            else:
                big_jobs.append(job)

        scale_factor = self.get_common_denominator(big_jobs)
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
        for job, mult in multiplicity_per_job_size.items():
            for j in range(self.m):
                indicator_variables[(job, j)] = model.NewIntVar(0, mult,
                                                                'job_%i_machine_%i' % (job, j))

        # ensure that each job is scheduled on exactly once
        for job, mult in multiplicity_per_job_size.items():
            model.Add(sum(indicator_variables[(job, j)] for j in range(self.m)) == mult)

        # ensure that the makespan is less than the cutoff value
        for j in range(self.m):
            model.Add(sum(indicator_variables[(job, j)] * job for job in multiplicity_per_job_size.keys())
                      <= scaled_cutoff_value)

        # call solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL:
            try:  # greedy scheduling
                if final:
                    return FinalSubRound(indicator_variables, solver, big_jobs, small_jobs, cutoff_value, job_size,
                                         multiplicity, self.m, self.c, scale_factor)
                else:
                    return SubRound(indicator_variables, solver, big_jobs, small_jobs, cutoff_value, job_size,
                                    multiplicity, self.m, self.c, scale_factor)
            except ValueError:
                pass

        # scheduling not successful, undo alteration of jobs parameter
        for i in range(multiplicity):
            jobs.pop()
        return None
