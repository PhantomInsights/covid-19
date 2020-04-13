"""
This script includes several functions to generate plots and get insights from the MExican dataset.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


sns.set(style="ticks",
        rc={
            "figure.figsize": [15, 10],
            "text.color": "white",
            "legend.fontsize": "large",
            "xtick.labelsize": "x-large",
            "ytick.labelsize": "x-large",
            "axes.labelsize": "x-large",
            "axes.titlesize": "x-large",
            "axes.labelcolor": "white",
            "axes.edgecolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.facecolor": "#111111",
            "figure.facecolor": "#232b2b"}
        )


def get_confirmed_by_state(df):
    """Gets the total confirmed cases by state and gender.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing Mexican data.

    """

    # We will use this value to calculate the percentages.
    total_cases = len(df)

    # We pivot the table, we will use the gender as our columns and the state as our index.
    pivoted_df = df.pivot_table(
        index="estado", columns="sexo", aggfunc="count")

    # From this MultiIndex DataFrame we will add two columns to the age column.
    # These columns will have the total percentage of each state and gender.
    pivoted_df["edad", "female_percentage"] = np.round(
        pivoted_df["edad", "FEMENINO"] / total_cases * 100, 2)

    pivoted_df["edad", "male_percentage"] = np.round(
        pivoted_df["edad", "MASCULINO"] / total_cases * 100, 2)

    # We rename the columns so they are human readable.
    pivoted_df.rename(columns={"MASCULINO": "Male",
                               "FEMENINO": "Female",
                               "male_percentage": "Male %",
                               "female_percentage": "Female %"}, level=1, inplace=True)

    print(pivoted_df["edad"])


def plot_daily_growth(df):
    """Plots the daily initial symptoms count.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing Mexican data.

    """

    # We group our DataFrame by day of initial symptoms and aggregate them by number of ocurrences.
    grouped_df = df.groupby("fecha_inicio_sintomas").count()

    # We add a new column that will hold the cumulative sum of the previous counts.
    grouped_df["cumsum"] = grouped_df["estado"].cumsum()

    # We create a basic line plot with the previously created column.
    fig, ax = plt.subplots()

    ax.plot(grouped_df.index, grouped_df["cumsum"],
            label="Initial Symptoms", color="lime")

    # Customize the tickers. The y-axis will be formatted with date and month in 7 day intervals.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.title("Confirmed Cases Growth", pad=15)
    plt.legend(loc=2)
    plt.grid(linewidth=0.5)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Number of Confirmed Cases", labelpad=15)

    plt.savefig("./mexico_growth.png", facecolor="#232b2b")


def plot_age_groups(df):
    """Plots the age groups by gender.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing Mexican data.

    """

    # Create one DataFrame for each gender.
    male_df = df[df["sexo"] == "MASCULINO"]
    female_df = df[df["sexo"] == "FEMENINO"]

    # These lists will be used for our bins.
    age_groups = list()
    labels = list()

    for i in range(0, 100, 10):

        # Our latest bin will be for ages >= 90.
        if i == 90:
            age_groups.append((i, i+30))
            labels.append("≥ 90")
        else:
            age_groups.append((i, i+9))
            labels.append("{}-{}".format(i, i+9))

    # We build our indexer and cut our DataFrames with it.
    bins = pd.IntervalIndex.from_tuples(age_groups)

    male_df = male_df.groupby(pd.cut(male_df["edad"], bins)).count()
    female_df = female_df.groupby(pd.cut(female_df["edad"], bins)).count()

    fig, ax = plt.subplots()

    bars = ax.bar(
        [i - 0.225 for i in range(len(labels))], height=male_df["edad"],  width=0.45,  color="#1565c0", linewidth=0)

    # This loop creates small texts with the absolute values above each bar (first set of bars).
    for bar in bars:
        height = bar.get_height()

        plt.text(bar.get_x() + bar.get_width()/2.0, height,
                 "{:,}".format(height), ha="center", va="bottom")

    bars2 = ax.bar(
        [i + 0.225 for i in range(len(labels))], height=female_df["edad"],  width=0.45,  color="#ec407a", linewidth=0)

    # This loop creates small texts with the absolute values above each bar (second set of bars).
    for bar2 in bars2:
        height2 = bar2.get_height()

        plt.text(bar2.get_x() + bar2.get_width()/2.0, height2,
                 "{:,}".format(height2), ha="center", va="bottom")

    # Customize our tickers.
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.title("Age and Sex Distribution", pad=15)
    plt.legend(["Male", "Female"], loc=2)
    plt.grid(linewidth=0.5)
    plt.xticks(range(len(labels)), labels)
    plt.xlabel("Age Range", labelpad=15)
    plt.ylabel("Confirmed Cases", labelpad=15)

    plt.savefig("./age_sex.png", facecolor="#232b2b")


if __name__ == "__main__":

    main_df = pd.read_csv("casos_confirmados.csv", index_col=0, parse_dates=[
                          "fecha_inicio_sintomas"], dayfirst=True)

    # get_confirmed_by_state(main_df)
    # plot_daily_growth(main_df)
    # plot_age_groups(main_df)
