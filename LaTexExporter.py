import SchedulePlotter
from Round import Round


def export(rounds: [Round], file_name: str, m: int, final_m: int, c: float, use_images=True):
    """
    Generates the latex source code for the proof
    :param rounds:          the rounds of the proof
    :param file_name:       name of the generated latex file
    :param m:               number of machines
    :param final_m:         number of machines in final round
    :param c:               competitive ratio
    :param use_images:      indicates whether images or tables should be used
    """
    f = open(file_name, 'w')

    # setup as subfile for LaTex project
    f.write("\\documentclass[../main.tex]{subfiles}\n")
    f.write("\\begin{document}\n")

    # write proof
    write_overview(f, rounds, m, final_m, c)
    f.write("\n")
    write_analysis(f, rounds)

    # finish document and close file
    f.write("\\end{document}\n")
    f.close()


def write_overview(f, rounds: [Round], m: int, final_m: int, c: float):
    """
    writes the overview of the proof, contains important overview of competitive ratio,
    number of machines and job sequence
    """
    f.write("Let A be a deterministic online scheduling algorithm. If A is c-competitive for all m $\\geq$" +
            str(final_m) + ", then c$\\geq$" + str(float(c)) + ". \\newline\n")
    f.write("Proof: We will construct a job sequence $\\sigma$ such that $A(\\sigma) \\geq " + str(float(c)) +
            "\\cdot OPT(\\sigma)$. The job sequence consists of several rounds. We assume that m is a multiple of "
            + str(m) + ". \\newline\n")

    for round in rounds:
        f.write(round.get_overview())

    map_size_to_round = {0.0: 0}
    for round in rounds[:-1]:
        for subround in round.sub_rounds:
            map_size_to_round[float(subround.job_size)] = round.index

    for round in rounds[:-1]:
        result =  "\\begin{figure}[!htbp]\n"
        result += "\\centering"
        result += "\\includegraphics[scale = 0.35]{overview_" + str(round.index) + ".png}\n"
        result += "\\caption{Overview of used job sizes in Round "+ str(round.index) + "}\n"
        result += "\\end{figure}\n"
        result += "\\FloatBarrier\n"
        jobs = []
        for subround in round.sub_rounds:
            for _ in range(subround.multiplicity):
                jobs.append([subround.job_size])
        SchedulePlotter.plot_schedule(jobs, "overview_" + str(round.index), m, map_size_to_round=map_size_to_round)


def write_analysis(f, rounds: [Round]):
    """"
    writes a detailed proof for each round
    """
    f.write("In the following, when analyzing the various subrounds, we will often compare " +
            "the makespan produced by an online algorithm A in a subround to the optimum " +
            "makespan at the end of the subround. It is clear that the optimum makespan during " +
            "the subround can only be smaller. \\newline \n")

    map_size_to_round = {0.0: 0}
    for round in rounds[:-1]:
        for subround in round.sub_rounds:
            map_size_to_round[float(subround.job_size)] = round.index

    for round in rounds:
        f.write(round.get_analysis(rounds, map_size_to_round))
        f.write("\\par\n")
