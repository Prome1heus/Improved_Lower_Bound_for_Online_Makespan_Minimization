from Round import Round


def export(rounds: [Round], file_name: str, m: int, c: float):
    f = open(file_name, 'w')

    # setup as subfile for LaTex project
    f.write("\\documentclass[../main.tex]{subfiles}\n")
    f.write("\\begin{document}\n")

    # write proof
    write_overview(f, rounds, m, c)
    f.write("\n")
    write_analysis(f, rounds, m, c)

    # finish document and close file
    f.write("\end{document}\n")
    f.close()


def write_overview(f, rounds: [Round], m: int, c: float):
    f.write("Let A be a deterministic online scheduling algorithm. If A is c-competitive for all m $\\geq$" + str(m)
            + ", then $\\geq$" + str(c) + ". \\newline\n")
    f.write("Proof: We will construct a job sequence $\\sigma$ such that $A(\\sigma) \\geq " + str(c) +
            "\\cdot OPT(\\sigma)$. The job sequence consists of several rounds. We assume that m is a multiple of "
            + str(m) + ". \\newline\n")


    for round in rounds:
        f.write(round.get_overview(len(rounds)))


def write_analysis(f, rounds: [Round], m: int, c: float):
    f.write("In the following, when analyzing the various subrounds, we will often compare " +
            "the makespan produced by an online algorithm A in a subround to the optimum" +
            "makespan at the end of the subround. It is clear that the optimum makespan during" +
            "the subround can only be smaller. \\newline \n")

    for round in rounds:
        f.write(round.get_analysis())
        f.write("\\par\n")
