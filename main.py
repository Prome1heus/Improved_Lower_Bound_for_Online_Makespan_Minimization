import BinPackingSolver
import LaTexExporter
from Round import Round
from fractions import Fraction


def handle_next_command(job_size: Fraction):
    multiplicity = int(input('Enter the desired number of jobs\n'))

    if multiplicity == -1:
        job_multiplicity = int(input('Enter the job multiplicity\n'))
        round = handle_round(job_size, len(rounds), job_multiplicity)
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

        sub_round = BinPackingSolver.solve(jobs_so_far, m, c, cutoff_value, job_size, multiplicity, False, 0)

        if sub_round is None:
            print(
                'The subround (%i, %f) could not be scheduled. Try with other values' % (multiplicity, float(job_size)))
        else:
            print('Subround successfully scheduled')
            rounds[len(rounds) - 1].add_sub_round(sub_round)
            if rounds[len(rounds) - 1].get_number_of_jobs_left() == 0:
                rounds.append(Round(len(rounds) + 1, m))


def handle_finish():
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
                print(sub_round.job_size, sub_round.multiplicity)
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
        last_sub_round = BinPackingSolver.solve(final_jobs, final_m, c, cutoff_value, job_size, 1, True, 0.2825)
    final_m = m
    if last_sub_round is not None:
        rounds[len(rounds) - 1].add_sub_round(last_sub_round)

    for round in rounds:
        round.initialize_identifiers(len(rounds))
    LaTexExporter.export(rounds, "test.out", m, final_m, c)


def handle_round(job_size, round_id, job_multiplicity):
    round = BinPackingSolver.complete_round(jobs_so_far, c, m, round_id, job_size, 0, job_multiplicity)
    return round


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
