from fractions import Fraction

import matplotlib.pyplot as plt
import numpy as np


def plot_stacked_bar(
        data: [[Fraction]],
        cutoff_value: Fraction,
        m: int,
        map_size_to_round: {Fraction: int},
        final=False
):
    """
    heavily inspired by https://stackoverflow.com/a/50205834
    :param data:                    layers of the optimal schedule
    :param cutoff_value:            maximum allowed makespan
    :param m:                       number of machines
    :param map_size_to_round:       maps job sizes to the round they belong
    :param final:                   indicates if it is the final round
    """
    ind = list(range(m))
    axes = []
    current_bottom = np.zeros(m)
    data = np.array(data)

    # count number of rounds
    num_rounds = 0
    for value in map_size_to_round.values():
        num_rounds = max(num_rounds, value)

    # construct stacked bar chart
    for row_data in data:
        color = [plt.cm.Set1(num_rounds - map_size_to_round[job]) for job in row_data]
        if final:
            color[0] = 'black'
        axes.append(plt.bar(ind, row_data,
                            bottom=current_bottom,
                            color=color,
                            edgecolor='black',
                            linewidth=0.5))
        current_bottom += row_data

    plt.grid()

    # visualize cutoff value
    if cutoff_value is not None:
        plt.hlines(cutoff_value, -1, m)
        plt.text(1, cutoff_value + cutoff_value / 10, "y = " + str(float(cutoff_value)), ha="center", va="center")

    plt.gca().axes.xaxis.set_ticklabels([])


def plot_schedule_for_subround(sub_round, map_size_to_round, final):
    """
    wrapper for plot_schedule
    :param sub_round:               subround to plot
    :param map_size_to_round:       maps job sizes to the rounds they belong
    :param final:                   indicates if the subround is the final round
    """
    plot_schedule(sub_round.schedule, sub_round.name, sub_round.m, sub_round.cutoff_value, map_size_to_round, final)


def plot_schedule(
        schedule: [[Fraction]],
        figure_name: str,
        m: int,
        cutoff_value: Fraction = None,
        map_size_to_round=None,
        final=False
):
    # compute number of bar chars that need to be stacked
    max_number_of_jobs_on_machine = 0
    for machine in schedule:
        max_number_of_jobs_on_machine = max(max_number_of_jobs_on_machine, len(machine))

    # go from jobs per machine to layers of jobs in stacked bar chart
    layers = [[] for _ in range(max_number_of_jobs_on_machine)]
    for i in range(max_number_of_jobs_on_machine):
        for j in range(m):
            if len(schedule[j]) > i:
                layers[i].append(float(schedule[j][i]))
            else:
                layers[i].append(0.0)

    plt.figure(figsize=(20, 5))
    plot_stacked_bar(layers, cutoff_value, m, map_size_to_round, final=final)
    plt.savefig(figure_name + '.png')
