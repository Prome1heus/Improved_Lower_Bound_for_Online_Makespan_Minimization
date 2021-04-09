import BinPackingSolver
import LaTexExporter
from Round import Round
from fractions import Fraction


def handle_next_command(job_size: Fraction):
    multiplicity = int(input('Enter the desired number of jobs\n'))

    # add subround to job list
    for i in range(multiplicity):
        jobs_so_far.append(job_size)
    cutoff_value = 0
    for i in range(0, len(jobs_so_far), m):
        cutoff_value += jobs_so_far[i]
    cutoff_value += job_size

    cutoff_value = cutoff_value/c

    sub_round = BinPackingSolver.solve(jobs_so_far, m, c, cutoff_value, job_size, multiplicity)

    if sub_round is None:
        print('The subround could not be scheduled. Try with other values')
    else:
        print('Subround successfully scheduled')
        rounds[len(rounds) - 1].add_sub_round(sub_round)
        if rounds[len(rounds) - 1].get_number_of_jobs_left() == 0:
            rounds.append(Round(len(rounds) + 1, m))


def handle_finish():
    for round in rounds:
        round.initialize_identifiers(len(rounds))
    LaTexExporter.export(rounds, "test.out", m, c)


if __name__ == '__main__':
    m = int(input('Enter the number of machines\n'))
    c = Fraction(input('Enter the competitive ratio\n'))
    jobs_so_far: [Fraction] = []
    rounds = [Round(1, m)]
    index = 2

    while True:
        next_input = Fraction(input('Enter new job size\n'))
        if next_input == 0:
            handle_finish()
            break
        handle_next_command(next_input)
