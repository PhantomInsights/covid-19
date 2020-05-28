"""
Generates various plots and insights from the Mexican dataset.
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
        A DataFrame containing the Mexican data.

    """

    # Only take into account confirmed cases.
    df = df[df["RESULTADO"] == "Positivo SARS-CoV-2"]

    # We will use this value to calculate the percentages.
    total_cases = len(df)

    # We pivot the table, we will use the gender as our columns and the state as our index.
    pivoted_df = df.pivot_table(
        index="ENTIDAD_RES", columns="SEXO", aggfunc="count")

    # From this MultiIndex DataFrame we will add two columns to the age column.
    # These columns will have the total percentage by state and gender.
    pivoted_df["EDAD", "female_percentage"] = np.round(
        pivoted_df["EDAD", "MUJER"] / total_cases * 100, 2)

    pivoted_df["EDAD", "male_percentage"] = np.round(
        pivoted_df["EDAD", "HOMBRE"] / total_cases * 100, 2)

    # We rename the columns so they are human readable.
    pivoted_df.rename(columns={"HOMBRE": "Male",
                               "MUJER": "Female",
                               "male_percentage": "Male %",
                               "female_percentage": "Female %"}, level=1, inplace=True)

    print(pivoted_df["EDAD"].to_markdown())


def plot_daily_symptoms_growth(df):
    """Plots the daily initial symptoms growth and daily counts.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the Mexican data.

    """

    # Only take into account confirmed cases.
    df = df[df["RESULTADO"] == "Positivo SARS-CoV-2"]

    # We group our DataFrame by day of initial symptoms and aggregate them by number of ocurrences.
    grouped_df = df.groupby("FECHA_SINTOMAS").count()

    # Convert the index to datetime.
    grouped_df.index = pd.to_datetime(grouped_df.index)

    # We add a new column that will hold the cumulative sum of the previous counts.
    grouped_df["cumsum"] = grouped_df["SECTOR"].cumsum()

    # We create a basic line plot with the previously created column.
    fig, (ax1, ax2) = plt.subplots(2)

    ax1.plot(grouped_df.index, grouped_df["cumsum"],
             label="Initial Symptoms Growth", color="lime")

    ax2.plot(grouped_df.index, grouped_df["SECTOR"],
             label="Initial Symptoms Counts", color="gold")

    # Ticker customizations. The y-axis will be formatted with month and day.
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(15))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(10))
    ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    ax2.xaxis.set_major_locator(ticker.MaxNLocator(15))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(10))
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    ax1.grid(linewidth=0.5)
    ax1.legend(loc=2)
    ax1.set_title("Initial Symptoms Growth & Daily Counts", pad=15)
    ax1.set_ylabel("COVID-19 Positive Tests", labelpad=15)

    ax2.grid(linewidth=0.5)
    ax2.legend(loc=2)
    ax2.set_ylabel("COVID-19 Positive Tests", labelpad=15)

    plt.savefig("mexico_symptoms_growth.png", facecolor="#232b2b")


def plot_daily_deaths_growth(df):
    """Plots the deaths growth and daily counts.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the Mexican data.

    """

    # Only take into account confirmed cases and deaths.
    df = df[(df["RESULTADO"] == "Positivo SARS-CoV-2")
            & (df["FECHA_DEF"] != "9999-99-99")]

    # We group our DataFrame by day of initial symptoms and aggregate them by number of ocurrences.
    grouped_df = df.groupby("FECHA_DEF").count()

    # Convert the index to datetime.
    grouped_df.index = pd.to_datetime(grouped_df.index)

    # We add a new column that will hold the cumulative sum of the previous counts.
    grouped_df["cumsum"] = grouped_df["SECTOR"].cumsum()

    # We create a basic line plot with the previously created column.
    fig, (ax1, ax2) = plt.subplots(2)

    ax1.plot(grouped_df.index, grouped_df["cumsum"],
             label="Deaths Growth", color="lime")

    ax2.plot(grouped_df.index, grouped_df["SECTOR"],
             label="Deaths Counts", color="gold")

    # Ticker customizations. The y-axis will be formatted with month and day.
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(15))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(10))
    ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    ax2.xaxis.set_major_locator(ticker.MaxNLocator(15))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(10))
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    ax1.grid(linewidth=0.5)
    ax1.legend(loc=2)
    ax1.set_title("Deaths Growth & Daily Counts", pad=15)
    ax1.set_ylabel("COVID-19 Deaths", labelpad=15)

    ax2.grid(linewidth=0.5)
    ax2.legend(loc=2)
    ax2.set_ylabel("COVID-19 Deaths", labelpad=15)

    plt.savefig("mexico_deaths_growth.png", facecolor="#232b2b")


def plot_test_results(df):
    """Plots the tests results by day.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the Mexican data.

    """

    # The RESULTADO column has 3 possible values. We create
    # one column for each one.
    df["tests"] = 1

    df["positive"] = df["RESULTADO"].apply(
        lambda x: 1 if x == "Positivo SARS-CoV-2" else 0)

    df["not_positive"] = df["RESULTADO"].apply(
        lambda x: 1 if x == "No positivo SARS-CoV-2" else 0)

    df["pending"] = df["RESULTADO"].apply(
        lambda x: 1 if x == "Resultado pendiente" else 0)

    # We group the DataFrame by the date of entry and aggregate them by sum.
    df = df.groupby("FECHA_INGRESO").sum()

    # Convert the index to datetime.
    df.index = pd.to_datetime(df.index)

    # These percentages will be used for the plots labels.
    total = df["tests"].sum()
    positive = round(df["positive"].sum() / total * 100, 2)
    not_positive = round(df["not_positive"].sum() / total * 100, 2)
    pending = round(df["pending"].sum() / total * 100, 2)

    # We create a vertical bar plot with the previously created columns.
    fix, ax = plt.subplots()

    ax.bar(df.index, df["positive"], color="#ef6c00",
           label=f"SARS-CoV-2 Positive ({positive}%)", linewidth=0)

    ax.bar(df.index, df["not_positive"], color="#42a5f5",
           label=f"SARS-CoV-2 Not Positive ({not_positive}%)", bottom=df["positive"] + df["pending"], linewidth=0)

    ax.bar(df.index, df["pending"], color="#ffca28",
           label=f"Pending Result ({pending}%)", bottom=df["positive"], linewidth=0)

    # Ticker customtzations.
    ax.xaxis.set_major_locator(ticker.MaxNLocator(15))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(12))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.title("COVID-19 Test Results", pad=15)
    plt.legend(loc=2)
    plt.grid(linewidth=0.5)
    plt.ylabel("Number of Daily Results", labelpad=15)
    plt.xlabel("2020", labelpad=15)

    plt.savefig("mexico_tests.png", facecolor="#232b2b")


def plot_age_groups(df):
    """Plots the age groups by gender.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the Mexican data.

    """

    # Only take into account confirmed cases.
    df = df[df["RESULTADO"] == "Positivo SARS-CoV-2"]

    # Create one DataFrame for each gender.
    male_df = df[df["SEXO"] == "HOMBRE"]
    female_df = df[df["SEXO"] == "MUJER"]

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

    # We use the previous tuples to build our indexer and slice our DataFrames with it.
    male_values = list()
    female_values = list()

    for start, end in age_groups:
        
        male_values.append(
            male_df[male_df["EDAD"].between(start, end)]["EDAD"].count())

        female_values.append(
            female_df[female_df["EDAD"].between(start, end)]["EDAD"].count())

    fig, ax = plt.subplots()

    bars = ax.bar(
        [i - 0.225 for i in range(len(labels))], height=male_values,  width=0.45,  color="#1565c0", linewidth=0)

    # This loop creates small texts with the absolute values above each bar (first set of bars).
    for bar in bars:
        height = bar.get_height()

        plt.text(bar.get_x() + bar.get_width()/2.0, height * 1.01,
                 "{:,}".format(height), ha="center", va="bottom")

    bars2 = ax.bar(
        [i + 0.225 for i in range(len(labels))], height=female_values,  width=0.45,  color="#f06292", linewidth=0)

    # This loop creates small texts with the absolute values above each bar (second set of bars).
    for bar2 in bars2:
        height2 = bar2.get_height()

        plt.text(bar2.get_x() + bar2.get_width()/2.0, height2 * 1.01,
                 "{:,}".format(height2), ha="center", va="bottom")

    # Ticker customizations.
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.grid(linewidth=0.5)
    plt.legend(["Male", "Female"], loc=2)
    plt.xticks(range(len(labels)), labels)
    plt.title("Age and Sex Distribution", pad=15)
    plt.xlabel("Age Range", labelpad=15)
    plt.ylabel("Confirmed Cases", labelpad=15)

    plt.savefig("mexico_age_sex.png", facecolor="#232b2b")


if __name__ == "__main__":

    main_df = pd.read_csv("mx_data.csv")

    # get_confirmed_by_state(main_df)
    # plot_daily_symptoms_growth(main_df)
    # plot_daily_deaths_growth(main_df)
    # plot_test_results(main_df)
    # plot_age_groups(main_df)
