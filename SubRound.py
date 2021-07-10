import string
from fractions import Fraction

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar
import re

import SchedulePlotter


class SubRound:

    def extract_indicator_variables(
            self,
            indicator_variables: {(int, int), IntVar},
            scheduled_jobs: [Fraction],
            solver: cp_model,
            scale_factor: int,
            m: int
    ) -> [[Fraction]]:
        """
        extracts the schedule from the indicator variables to a list of jobs for each machine
        :param indicator_variables:     indicate the number of jobs of a specific size on each machine
        :param scheduled_jobs:          jobs for which indicator variables exist
        :param solver:                  the CP-SAT solver
        :param scale_factor:            factor by which the jobs have been scaled
        """
        result = [[] for _ in range(m)]

        # create assignment based on indicator variables
        for job in set(scheduled_jobs):
            for j in range(m):
                for i in range(solver.Value(indicator_variables[(int(job * scale_factor), j)])):
                    result[j].append(job)
        return result

    def schedule_greedily(self, small_jobs: [Fraction], schedule: [[Fraction]]):
        # try to schedule the remaining jobs greedily
        self.jobs_left = []
        for job in reversed(small_jobs):
            schedule.sort(reverse=False, key=lambda machine: (sum(machine), machine))
            if sum(schedule[0]) + job <= self.cutoff_value:
                schedule[0].append(job)
            else:
                self.jobs_left.append(job)

    def set_schedule(
            self,
            indicator_variables: {(int, int), IntVar},
            scheduled_jobs: [Fraction],
            small_jobs: [Fraction],
            solver: cp_model,
            scale_factor: int
    ):
        """
        sets the schedule attribute, if it is not possible to greedily schedule the small jobs with
        respect to the cutoff value, an error is thrown

        :param indicator_variables: indicate how many jobs of each type are scheduled on each machine
        :param scheduled_jobs:      jobs that can be assigned with the indicator variables
        :param small_jobs:          jobs that need to be assigned greedily
        :param solver:              contains the values for the indicator variables
        :param scale_factor:        needed to map job sizes to indicator variables
        """

        self.schedule = self.extract_indicator_variables(indicator_variables, scheduled_jobs, solver, scale_factor, self.m)
        self.schedule_greedily(small_jobs, self.schedule)

        # sort the schedule for visual uniformity
        self.schedule.sort(reverse=True, key=lambda machine: (sum(machine), machine))

        # check if greedy scheduling was successfull
        if len(self.jobs_left) > 0:
            raise ValueError("The small jobs could not be scheduled greedily")

    def __init__(
            self,
            indicator_variables: {(int, int), IntVar},
            solver: cp_model,
            jobs: [Fraction],
            small_jobs: [Fraction],
            cutoff_value: Fraction,
            job_size: Fraction,
            multiplicity: int,
            m: int,
            c: Fraction,
            scale_factor: int
    ):
        """
        :param indicator_variables:     indicate the number of jobs of each size on each machine
        :param solver:                  the CP-SAT solver with the values of the indicator variables
        :param jobs:                    jobs that have been scheduled
        :param small_jobs:              jobs that still have to be scheduled greedily
        :param cutoff_value:            maximum allowed makespan
        :param job_size:                size of the jobs in the subround
        :param multiplicity:            number of jobs in the subround
        :param m:                       number of machines
        :param c:                       competitive ratio
        :param scale_factor:            integer by which the jobs have been scaled for the integer variables
        """
        self.schedule = None
        self.jobs_left = None
        self.cutoff_value = cutoff_value
        self.job_size = job_size
        self.multiplicity = multiplicity
        self.m = m
        self.c = c
        self.identifier = ""
        self.name = ""
        self.set_schedule(indicator_variables, jobs, small_jobs, solver, scale_factor)

    def __str__(self):
        return str(self.schedule)

    def get_overview(self):
        """
        :return: description of the subround by multiplicity and job size
        """
        if self.multiplicity == self.m:
            number_of_jobs = "m"
        else:
            number_of_jobs = "$\\frac{ " + str(self.multiplicity) + "}{" + str(self.m) + "}$m"
        return number_of_jobs + " jobs with a processing time of " + self.identifier + \
               " = " + str(float(self.job_size))

    def get_makespan(self):
        """
        :return: a fraction representing the makespan of the schedule
        """
        makespan = 0
        for machine in self.schedule:
            load_on_machine = 0
            for element in machine:
                load_on_machine += element
            makespan = max(makespan, load_on_machine)
        return makespan

    def get_image(self, map_size_to_round, final=False):
        """
        :param          map_size_to_round: maps job sizes to the round they belong to
        :param final:   indicates if it is the last subround
        :return:        latex code for embedding the image as string
        """
        result = "\\begin{figure}[!htbp]\n"
        result += "\\centering"
        result += "\\includegraphics[scale = 0.35]{" + self.name + ".png}\n"
        result += "\\caption{Example Schedule after " + self.get_formatted_name() + " with a makespan of " + \
                  str(float(self.get_makespan())) + "}\n"
        result += "\\end{figure}\n"
        result += "\\FloatBarrier\n"
        SchedulePlotter.plot_schedule_for_subround(self, map_size_to_round, final)
        return result

    def cost_on_different_machines(self, rounds: Fraction, index: int, sub_round_index: int) -> string:
        """
        :param rounds:                  all rounds of the job sequence
        :param index:                   index of the current round
        :param sub_round_index:         index of the current subround
        :return: calculation using symbols of the makespan if two jobs from
                the current round are scheduled on the same machine
        """
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
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " \geq " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"

    def get_assignment_per_machine(self, rounds: [Fraction]):
        """
        :param rounds:  all rounds of the job sequence
        :return:        a description of load on each machine
        """
        symbol_per_job_size = {}
        for round in rounds:
            for sub_round in round.sub_rounds:
                if sub_round.get_job_size() in symbol_per_job_size:
                    symbol_per_job_size[sub_round.get_job_size()] += "/" + sub_round.get_identifier()
                else:
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

        # describe load for each type of machine
        for machine, multiplicity_of_machine in multiplicity_per_schedule.items():
            number_of_jobs_per_size = {}
            for job in machine:
                if job in number_of_jobs_per_size:
                    number_of_jobs_per_size[job] += 1
                else:
                    number_of_jobs_per_size[job] = 1
            result += "\\item $\\frac{" + str(multiplicity_of_machine) + "}{" + str(self.m) + \
                      "}$m machines with a workload of "
            jobs = []
            sum = 0
            for job, multiplicity in number_of_jobs_per_size.items():
                sum += multiplicity * job
                if multiplicity > 1:
                    jobs.append(str(multiplicity) + symbol_per_job_size[job])
                else:
                    jobs.append(symbol_per_job_size[job])
            result += " + ".join(jobs) + " = " + str(float(sum)) + "\n"

        result += "\\end{itemize}\n"
        return result

    def get_analysis(self,  index, sub_round_index, rounds, map_size_to_round):
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
        result += "If A does not schedule the jobs in " + self.get_formatted_name() + " on different machines, then "
        result += "its makespan is at least " + self.cost_on_different_machines(rounds, index, sub_round_index)
        result += ". \\newline \n "
        result += self.get_assignment_per_machine(rounds)
        result += self.get_image(map_size_to_round)
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

    def get_formatted_name(self):
        return "d ".join(self.name.split("d"))
