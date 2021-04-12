from fractions import Fraction

import matplotlib.pyplot as plt
import numpy as np


# heavily inspired by https://stackoverflow.com/a/50205834
def plot_stacked_bar(data, cutoff_value, c, show_values=False):
    ny = len(data[0])
    ind = list(range(ny))

    axes = []
    current_bottom = np.zeros(ny)

    data = np.array(data)

    for i, row_data in enumerate(data):
        axes.append(plt.bar(ind, row_data, bottom=current_bottom, color=None))
        current_bottom += row_data

    plt.grid()

    if show_values:
        for axis in axes:
            for bar in axis:
                w, h = bar.get_width(), bar.get_height()
                if bar.get_height() > 0:
                    plt.text(bar.get_x() + w / 2, bar.get_y() + h / 2,
                             h, ha="center",
                             va="center")
    # Todo replace 40 with m
    plt.hlines(cutoff_value, -1, 40)
    plt.text(1, cutoff_value + cutoff_value/10, "y = " + str(float(cutoff_value)), ha="center", va="center")
    plt.gca().axes.xaxis.set_ticklabels([])


def plot_schedule(sub_round, figure_name: str):
    max_number_of_jobs_on_machine = 0
    for machine in sub_round.schedule:
        max_number_of_jobs_on_machine = max(max_number_of_jobs_on_machine, len(machine))

    layers = [[] for _ in range(max_number_of_jobs_on_machine)]

    plt.figure(figsize=(20, 5))

    for i in range(max_number_of_jobs_on_machine):
        for j in range(sub_round.m):
            if len(sub_round.schedule[j]) > i:
                layers[i].append(float(sub_round.schedule[j][i]))
            else:
                layers[i].append(0.0)

    plot_stacked_bar(layers, sub_round.cutoff_value, sub_round.c)

    plt.savefig(figure_name + '.png')
