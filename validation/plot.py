"""Module for plotting logic of validation data."""

import matplotlib.pyplot as plt
import pandas as pd


def plot_avg_error(avg_error: pd.DataFrame, **kwargs):
    """Plots the average error of a specific filter validation error dataframe."""
    fig, ax = plt.subplots()

    if kwargs.get("labels"):
        labels = kwargs.get("labels")
    else:
        labels = list(
            map(lambda name_val: f"{name_val[0]} {name_val[1]}", zip(avg_error.name, avg_error.value.sort_values().unique())))

    for name, value, label in zip(avg_error.name, avg_error.value.sort_values().unique(), labels):

        values = avg_error[avg_error.value == value]
        values = values.sort_values("lambda")
        try:
            ax.plot(avg_error["lambda"].sort_values().unique(), values.avg_error, label=label, linestyle='-', marker='o')
        except Exception as e:
            print(e)
            continue

    ax.legend(loc="right")
    ax.grid()
    ax.set_xlabel("$\lambda$")
    ax.set_ylabel("MSE")
    ax.set_title(f"MSE - {kwargs.get('title')}")

    return fig
