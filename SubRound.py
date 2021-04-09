from fractions import Fraction

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar
import re

import SchedulePlotter


class SubRound:

    def set_schedule(
            self,
            indicator_variables: {(int, int), IntVar},
            jobs: [Fraction],  # the sizes of the jobs
            solver: cp_model,  # feasible assignment of indicator variables
            n: int,  # number of jobs to schedule
            m: int,  # number of machines
            scale_factor: int
    ):
        for job in set(jobs):
            for j in range(m):
                for i in range(solver.Value(indicator_variables[(int(job*scale_factor), j)])):
                    self.schedule[j].append(job)

    def __init__(
            self,
            indicator_variables: {(int, int), IntVar},
            solver: cp_model,
            jobs: [int],
            cutoff_value: int,
            job_size: int,
            multiplicity: int,
            m: int,
            c: float,
            scale_factor: int
    ):
        self.schedule = [[] for _ in range(m)]
        self.set_schedule(indicator_variables, jobs, solver, len(jobs), m, scale_factor)
        self.cutoff_value = cutoff_value
        self.job_size = job_size
        self.multiplicity = multiplicity
        self.m = m
        self.c = c
        self.identifier = ""
        self.name = ""

    def __str__(self):
        return str(self.schedule)

    def get_overview(self):
        if self.multiplicity == self.m:
            number_of_jobs = "m"
        else:
            number_of_jobs = "$\\frac{ " + str(self.multiplicity) + "}{" + str(self.m) + "}$m"
        return number_of_jobs + " jobs with a processing time of " + self.identifier + \
               " = " + str(float(self.job_size))

    def get_makespan(self):
        makespan = 0
        for machine in self.schedule:
            load_on_machine = 0
            for element in machine:
                load_on_machine += element
            makespan = max(makespan, load_on_machine)
        return makespan

    def get_latex_table(self):
        max_number_of_jobs_on_any_machine = 0
        for machine in self.schedule:
            max_number_of_jobs_on_any_machine = max(max_number_of_jobs_on_any_machine, len(machine))

        # format table
        result = "\\begin{table}[hp]\n"
        result += "\\centering\n"
        result += "\\begin{adjustbox}{width=1\\textwidth}\n"
        result += "\\small\n"
        result += "\\begin{tabular}{|"
        for _ in self.schedule:
            result += " c |"
        result += "}\n \\hline \n"

        # create rows
        for i in range(max_number_of_jobs_on_any_machine):
            for (j, machine) in enumerate(self.schedule):
                if len(machine) > i:
                    result += str(float(machine[i]))
                if j == self.m - 1:
                    result += "\\\\\n"
                else:
                    result += " & "
            result += "\\hline\n"
        result += "\\end{tabular}\n"
        result += "\\end{adjustbox}\n"
        result += "\\caption{Illustration of schedule with makespan of " + str(self.get_makespan()) + "}\n"
        result += "\\end{table}"
        return result

    def get_image(self):
        result = "\\begin{figure}[h]\n"
        result += "\\centering"
        result += "\\includegraphics[scale = 0.35]{" + self.name + ".png}\n"
        result += "\\caption{Example Schedule after " + self.name + " with a makespan of " + \
                  str(float(self.get_makespan())) + "}\n"
        result += "\\end{figure}\n"
        SchedulePlotter.plot_schedule(self, self.name)
        return result

    def cost_on_different_machines(self, rounds, index, sub_round_index):
        if sub_round_index == 1:
            jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if
                                i < index - 1]
            min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index - 1])
            jobs_to_consider.append("2" + self.get_identifier())
            min_cost += 2 * self.job_size
        else:
            jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if i < index]
            min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index])
            jobs_to_consider.append(self.get_identifier())
            min_cost += self.job_size
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " > " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"

    def get_analysis(self, use_images, index, sub_round_index, rounds):
        result = "By the example schedule below, the optimum makespan is at most {0}. ".format(
            str(float(self.get_makespan())))
        result += "If A does not schedule the jobs in " + self.name + " on different machines, then its makespan is at "
        result += "least " + self.cost_on_different_machines(rounds, index, sub_round_index)
        if use_images:
            result += self.get_image()
        else:
            result += self.get_latex_table()
        return result

    def get_multiplicity(self):
        return self.multiplicity

    def set_identifier(self, identifier, index):
        self.identifier = identifier
        subround_index = re.sub("[^0-9]", "", self.identifier)
        if len(subround_index) == 1:
            self.name = "Subround" + str(index) + "." + subround_index
        else:
            self.name = "Round" + str(index)

    def get_identifier(self):
        return self.identifier
