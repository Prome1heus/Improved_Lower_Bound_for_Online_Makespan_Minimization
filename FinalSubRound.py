from fractions import Fraction

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

import BinPackingSolver
from SubRound import SubRound


class FinalSubRound(SubRound):

    def set_schedule(
            self,
            indicator_variables: {(int, int), IntVar},
            scheduled_jobs: [Fraction],
            small_jobs: [Fraction],
            solver: cp_model,
            scale_factor: int
    ):
        """
        overrides method of SubRound to allow upscaling
        :param indicator_variables: indicate how many jobs of each type are scheduled on each machine
        :param scheduled_jobs:      jobs that can be assigned with the indicator variables
        :param small_jobs:          jobs that need to be assigned greedily
        :param solver:              contains the values for the indicator variables
        :param scale_factor:        needed to map job sizes to indicator variables
        """
        schedule = self.extract_indicator_variables(indicator_variables, scheduled_jobs, solver, scale_factor, self.m)
        self.schedule_greedily(small_jobs, schedule)

        # try to fit the remaining jobs by increasing the number of machines
        if len(self.jobs_left) > 0:
            multiply_by = 1
            sub_round = None
            while sub_round is None and multiply_by < 5:
                multiply_by += 1
                print('trying with %i jobs' % (self.m * multiply_by))
                jobs = []
                # create other instance of the CSP for upscaling
                for _ in range(multiply_by):
                    for job in self.jobs_left:
                        jobs.append(job)
                solver = BinPackingSolver.BinPackingSolver(multiply_by-1, self.c, 10)
                sub_round = solver.solve(jobs, self.cutoff_value, 0, 0)

            if sub_round is None:
                print('Upscaling not possible')
                exit(1)

            schedule.pop(0)
            self.schedule = []
            for _ in range(multiply_by):
                for machine in schedule:
                    self.schedule.append(machine)
            print(len(self.schedule))
            self.schedule.extend(sub_round.schedule)
            self.schedule.append([Fraction(1)])
            print(len(self.schedule))
            self.m *= multiply_by
        else:
            self.schedule = schedule

        # sort the schedule for visual uniformity
        self.schedule.sort(reverse=True, key=lambda machine: (sum(machine), machine))

    def cost_on_different_machines(self, rounds: [Fraction], index: int, sub_round_index: int):
        """
        :param rounds:                  all rounds of the job sequence
        :param index:                   index of the current round
        :param sub_round_index:         index of the current subround
        :return: calculation using symbols of the makespan if two jobs from
                the current round are scheduled on the same machine
        """
        jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if i < index]
        min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index])
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " \geq " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"

    def get_overview(self):
        return " 1 job with a processing time of " + self.identifier + " = " + str(float(self.job_size))

    def get_analysis(self, index, sub_round_index, rounds, map_size_to_round):
        """
        :param index:               index of the round
        :param sub_round_index:     index of the sub round
        :param rounds:              all round of the job sequence
        :param map_size_to_round:   maps job sizes to round indices
        :return:                    the proof that each online algorithm with a competitive ratio of at most c
                                    does not schedule two jobs from the same round on one machine
        """
        result = "By the example schedule below, the optimum makespan is at most {0}. ".format(
            str(float(self.get_makespan())))
        result += "No matter where A schedules the last job, "
        result += "its makespan is at least " + self.cost_on_different_machines(rounds, index, sub_round_index)
        result += ". \\newline \n "
        result += self.get_assignment_per_machine(rounds)
        result += self.get_image(map_size_to_round, final=True)
        return result
