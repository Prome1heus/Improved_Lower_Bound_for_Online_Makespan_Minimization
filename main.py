import getopt
import sys

from BinPackingSolver import BinPackingSolver
import LaTexExporter
from Round import Round
from fractions import Fraction


def handle_next_command(job_size: Fraction):
    multiplicity = int(input('Enter the desired number of jobs\n'))

    if multiplicity == -1:
        round = handle_round(job_size, len(rounds))
        rounds[len(rounds) - 1] = round
        rounds.append(Round(len(rounds) + 1, m))
    else:
        # add subround to job list
        for i in range(multiplicity):
            jobs_so_far.append(job_size)
        cutoff_value = 0
        for i in range(0, len(jobs_so_far), m):
            cutoff_value += jobs_so_far[i]
        cutoff_value += job_size

        cutoff_value = cutoff_value / c

        print(cutoff_value)

        sub_round = solver.solve(jobs_so_far, cutoff_value, job_size, multiplicity, False, greedy_ratio)

        if sub_round is None:
            print(
                'The subround (%i, %f) could not be scheduled. Try with other values' % (multiplicity, float(job_size)))
        else:
            print('Subround successfully scheduled')
            rounds[len(rounds) - 1].add_sub_round(sub_round)
            if rounds[len(rounds) - 1].get_number_of_jobs_left() == 0:
                rounds.append(Round(len(rounds) + 1, m))


def handle_finish():
    if len(jobs_so_far) % m != 0:
        print("previous round inccomplete, exiting")
        exit(1)

    job_size = Fraction(input('Enter the last job\n'))
    last_sub_round = None
    cutoff_value = 0
    for i in range(0, len(jobs_so_far), m):
        cutoff_value += jobs_so_far[i]
    cutoff_value += job_size
    cutoff_value = cutoff_value / c
    while last_sub_round is None:
        for round in rounds:
            for sub_round in round.sub_rounds:
                print(float(sub_round.job_size), sub_round.multiplicity)
        final_m = int(input('Enter the number of machines for last subround\n'))
        if final_m % m != 0:
            print('The number of machines must be a multiple of m!\n')
            continue
        print('trying with ' + str(final_m) + "jobs")
        final_jobs = []
        for job in jobs_so_far:
            for _ in range(int(final_m / m)):
                final_jobs.append(job)
        final_jobs.append(job_size)
        last_sub_round = solver.solve(final_jobs, cutoff_value, job_size, 1, True, final_greedy_ratio)
    final_m = m
    if last_sub_round is not None:
        rounds[len(rounds) - 1].add_sub_round(last_sub_round)

    for round in rounds:
        round.initialize_identifiers(len(rounds))
    LaTexExporter.export(rounds, "test.out", m, final_m, c)


def handle_round(job_size, round_id):
    round = solver.complete_round(jobs_so_far, round_id, job_size, greedy_ratio, 3)
    if round is None:
        print('Failed to complete round for a job size of %f' % float(job_size))
        print('Job sizes of previous rounds')
        for r in rounds:
            for subround in r.sub_rounds:
                print(float(subround.job_size), subround.multiplicity)
        exit(1)
    return round


if __name__ == '__main__':
    # default values for command line options
    timeout = 40
    greedy_ratio = 0.01
    final_greedy_ratio = 0.2
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:g:f:",
                                   ["timeout=", "greedy_ratio=", "final_greedy_ratio="])
    except getopt.GetoptError:
        print("Command line arguments could not be parsed")
        exit(1)

    # parse command line arguments
    for opt, arg in opts:
        if opt in ("-t", "--timeout"):
            timeout = int(arg)
        elif opt in ("-g", "--greedy_ratio"):
            greedy_ratio = float(arg)
        elif opt in ("-f", "--final_greedy_ratio"):
            final_greedy_ratio = float(arg)
        else:
            print("unknown command line option: " + opt)
            exit(1)

    m = int(input('Enter the number of machines\n'))
    c = Fraction(input('Enter the competitive ratio\n'))
    solver = BinPackingSolver(m, c, timeout)
    jobs_so_far: [Fraction] = []
    rounds = [Round(1, m)]
    index = 2

    while True:
        next_input = Fraction(input('Enter new job size\n'))
        if next_input == 0:
            handle_finish()
            break
        handle_next_command(next_input)
