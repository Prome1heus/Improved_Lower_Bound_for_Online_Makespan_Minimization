import matplotlib.pyplot as plt
import numpy as np


# heavily inspired by https://stackoverflow.com/a/50205834
def plot_stacked_bar(data, cutoff_value, show_values=False):
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
    plt.hlines(cutoff_value, 0, 40, label='y = %f' % cutoff_value)
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

    plot_stacked_bar(layers, sub_round.cutoff_value)

    plt.savefig(figure_name + '.png')
