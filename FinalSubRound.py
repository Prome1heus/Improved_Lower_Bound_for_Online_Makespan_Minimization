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
        schedule = self.extract_indicator_variables(indicator_variables, scheduled_jobs, solver, scale_factor, self.m)
        self.schedule_greedily(small_jobs, schedule)

        if len(self.jobs_left) > 0:
            print(self.jobs_left)
            multiply_by = 1
            sub_round = None
            while sub_round is None:
                multiply_by += 1
                print('trying with %i jobs' % (self.m * multiply_by))
                jobs = []
                for _ in range(multiply_by):
                    for job in self.jobs_left:
                        jobs.append(job)
                solver = BinPackingSolver.BinPackingSolver(multiply_by-1, self.c)
                sub_round = solver.solve(jobs, self.cutoff_value, 0, 0)

            print(len(schedule))
            schedule.remove([Fraction(1)])
            print(len(schedule))

            print(sub_round)

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

    def cost_on_different_machines(self, rounds, index, sub_round_index):
        jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if i < index]
        min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index])
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " > " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"

    def get_overview(self):
        return " 1 job with a processing time of " + self.identifier + " = " + str(float(self.job_size))

    def get_analysis(self, use_images, index, sub_round_index, rounds):
        result = "By the example schedule below, the optimum makespan is at most {0}. ".format(
            str(float(self.get_makespan())))
        result += "No matter where A schedules the last job, "
        result += "its makespan is at least " + self.cost_on_different_machines(rounds, index, sub_round_index)
        result += ". \\newline \n "
        result += self.get_assignment_per_machine(rounds)
        if use_images:
            result += self.get_image()
        else:
            result += self.get_latex_table()
        return result
