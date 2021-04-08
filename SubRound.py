from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar


class SubRound:

    def set_schedule(
            self,
            indicator_variables: {(int, int), IntVar},
            jobs: [int],        # the sizes of the jobs
            solver: cp_model,   # feasible assignment of indicator variables
            n: int,             # number of jobs to schedule
            m: int              # number of machines
    ):
        for i in range(n):
            for j in range(m):
                if solver.Value(indicator_variables[(i, j)]):
                    self.schedule[j].append(jobs[i])

    def __init__(
            self,
            indicator_variables: {(int, int), IntVar},
            solver: cp_model,
            jobs: [int],
            cutoff_value: int,
            job_size: int,
            multiplicity: int,
            m: int
    ):
        self.schedule = [[] for _ in range(m)]
        self.set_schedule(indicator_variables, jobs, solver, len(jobs), m)
        self.cutoff_value = cutoff_value
        self.job_size = job_size
        self.multiplicity = multiplicity
        self.m = m
        self.identifier = ""

    def __str__(self):
        return str(self.schedule)

    def get_overview(self):
        return str(self.multiplicity) + " jobs with a processing time of " + self.identifier + \
               " = " + str(self.job_size)

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
                    result += str(machine[i])
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

    def get_makespan(self):
        makespan = 0
        for machine in self.schedule:
            load_on_machine = 0
            for element in machine:
                load_on_machine += element
            makespan = max(makespan, load_on_machine)
        return makespan

    def get_analysis(self):
        return self.get_latex_table()

    def get_multiplicity(self):
        return self.multiplicity

    def set_identifier(self, identifier):
        self.identifier = identifier
