from fractions import Fraction

import matplotlib.pyplot as plt
import numpy as np


# heavily inspired by https://stackoverflow.com/a/50205834
def plot_stacked_bar(
        data: [[Fraction]],
        cutoff_value: Fraction,
        m: int,
        map_size_to_round: {Fraction: int},
        show_values=False,
        final=False
):
    """
    :param data:                    layers of the optimal schedule
    :param cutoff_value:            maximum allowed makespan
    :param m:                       number of machines
    :param map_size_to_round:       maps job sizes to the round they belong
    :param show_values:             TODO: to remove
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

    # TODO: remove
    if show_values:
        for axis in axes:
            for bar in axis:
                w, h = bar.get_width(), bar.get_height()
                if bar.get_height() > 0:
                    plt.text(bar.get_x() + w / 2, bar.get_y() + h / 2,
                             h, ha="center",
                             va="center")
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
    max_number_of_jobs_on_machine = 0
    for machine in schedule:
        max_number_of_jobs_on_machine = max(max_number_of_jobs_on_machine, len(machine))

    layers = [[] for _ in range(max_number_of_jobs_on_machine)]

    plt.figure(figsize=(20, 5))

    for i in range(max_number_of_jobs_on_machine):
        for j in range(m):
            if len(schedule[j]) > i:
                layers[i].append(float(schedule[j][i]))
            else:
                layers[i].append(0.0)

    plot_stacked_bar(layers, cutoff_value, m, map_size_to_round, final=final)

    plt.savefig(figure_name + '.png')
