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
        self.schedule.sort(reverse=True, key=lambda machine: (sum(machine), machine))

    def __init__(
            self,
            indicator_variables: {(int, int), IntVar},
            solver: cp_model,
            jobs: [Fraction],
            cutoff_value: Fraction,
            job_size: Fraction,
            multiplicity: int,
            m: int,
            c: Fraction,
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
        result = "\\begin{figure}[!htbp]\n"
        result += "\\centering"
        result += "\\includegraphics[scale = 0.35]{" + self.name + ".png}\n"
        result += "\\caption{Example Schedule after " + self.name + " with a makespan of " + \
                  str(float(self.get_makespan())) + "}\n"
        result += "\\end{figure}\n"
        result += "\\FloatBarrier\n"
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

    def get_assignment_per_machine(self, rounds):
        symbol_per_job_size = {}
        for round in rounds:
            for sub_round in round.sub_rounds:
                symbol_per_job_size[sub_round.get_job_size()] = sub_round.get_identifier()
        result = "The assignment on the example schedule is as follows: \n"
        result += "\\begin{itemize}\n"

        # count how many machines have the same schedule
        multiplicity_per_schedule = {}
        for machine in self.schedule:
            if tuple(machine) in multiplicity_per_schedule:
                multiplicity_per_schedule[tuple(machine)] += 1
            else:
                multiplicity_per_schedule[tuple(machine)] = 1

        for machine, multiplicity_of_machine in multiplicity_per_schedule.items():
            number_of_jobs_per_size = {}
            for job in machine:
                if job in number_of_jobs_per_size:
                    number_of_jobs_per_size[job] += 1
                else:
                    number_of_jobs_per_size[job] = 1
            result += "\\item $\\frac{" + str(multiplicity_of_machine) + "}{" + str(self.m) + \
                      "}$ machines with a workload of "
            jobs = []
            sum = 0
            for job, multiplicity in number_of_jobs_per_size.items():
                sum += multiplicity*job
                if multiplicity > 1:
                    jobs.append(str(multiplicity) + symbol_per_job_size[job])
                else:
                    jobs.append(symbol_per_job_size[job])
            result += " + ".join(jobs) + " = " + str(float(sum)) + "\n"

        result += "\\end{itemize}\n"
        return result

    def get_analysis(self, use_images, index, sub_round_index, rounds):
        result = "By the example schedule below, the optimum makespan is at most {0}. ".format(
            str(float(self.get_makespan())))
        result += "If A does not schedule the jobs in " + self.name + " on different machines, then its makespan is at "
        result += "least " + self.cost_on_different_machines(rounds, index, sub_round_index) + ". \\newline \n "
        result += self.get_assignment_per_machine(rounds)
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

    def get_job_size(self):
        return self.job_size
