"""
Generates various plots and insights from the global dataset.
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


COUNTRIES = [
    ["US", "United States", "lightblue"],
    ["Italy", "Italy", "pink"],
    ["Spain", "Spain", "orange"],
    ["France", "France", "yellow"],
    ["United Kingdom", "United Kingdom", "lime"]
]


def get_top_10(df):
    """Gets the top 10 countries in each field.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    """

    grouped_df = df.groupby("country").max()

    # Confirmed cases
    print(grouped_df.sort_values("confirmed",
                                 ascending=False)["confirmed"][:10])

    # Deaths
    print(grouped_df.sort_values("deaths", ascending=False)["deaths"][:10])

    # Recoveries
    print(grouped_df.sort_values("recovered",
                                 ascending=False)["recovered"][:10])

    a = grouped_df.sort_values("recovered", ascending=False)["recovered"][:10]
    print(a.to_markdown())


def get_global_counts_growths(df, field):
    """Gets the daily confirmed cases, deaths or recoveries for all countries combined.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    field : str
        The field to check, it can be 'confirmed', 'deaths' or 'recovered'.

    """

    # Resample the DataFrame by 1 day intervals.
    resampled_df = df.resample("D").sum()

    # We add 2 new columns to know the daily totals and their percent change.
    resampled_df["difference"] = resampled_df[field].diff()
    resampled_df["change"] = resampled_df["difference"].pct_change()

    # We drop all NaN values.
    resampled_df.dropna(inplace=True)

    # We format the previous 2 columns so they can be easier to read.
    resampled_df["difference"] = resampled_df["difference"].apply(int)

    resampled_df["change"] = resampled_df["change"].apply(
        lambda x: str(np.round(x * 100, 2)) + "%")

    print(resampled_df[[field, "difference", "change"]][-10:])


def get_country_counts_growths(df, country, field):
    """Gets the daily confirmed cases, deaths or recoveries for a specified country.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    country : str
        The country/region name.

    field : str
        The field to check, it can be 'confirmed', 'deaths' or 'recovered'.

    """

    # Filter our DataFrame so it only reads data from the country we are interested in.
    filtered_df = df[df["country"] == country].copy()

    # We add 2 new columns to know the daily totals and their percent change.
    filtered_df["difference"] = filtered_df[field].diff()
    filtered_df["change"] = filtered_df["difference"].pct_change()

    # We drop all NaN values.
    filtered_df.dropna(inplace=True)

    # We format the previous 2 columns so they can be easier to read.
    filtered_df["difference"] = filtered_df["difference"].apply(int)

    filtered_df["change"] = filtered_df["change"].apply(
        lambda x: str(np.round(x * 100, 2)) + "%")

    print(filtered_df[[field, "difference", "change"]][-10:])


def get_100_to_3200(df):
    """Gets the number of days of confirmed cases between exponential growth bins.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    """

    # We remove all rows lower than 100.
    df = df[df["confirmed"] >= 100]

    # We define our bins and their labels.
    bins = [(100, 199), (200, 399), (400, 799), (800, 1599), (1600, 3200)]
    labels = ["100-199", "200-399", "400-799", "800-1599", "1600-3200"]

    # We extract all the available countries in the dataset.
    all_countries = sorted(df["country"].unique().tolist())

    # These lists will be filled with values in the next step.
    valid_countries = list()
    data_list = list()

    # We iterate over all the countries we have and create temporary DataFrames with them.
    for country in all_countries:

        temp_df = df[df["country"] == country]

        # Only process countries if their confirmed cases are equal or greater than 3,200.
        if temp_df["confirmed"].max() >= 3200:
            temp_list = list()

            # We iterate over our bins and count how many days each one has.
            for item in bins:
                temp_list.append(temp_df[(temp_df["confirmed"] >= item[0]) & (
                    temp_df["confirmed"] <= item[1])]["confirmed"].count())

            data_list.append(temp_list)
            valid_countries.append(country)

    # We create a final DataFrame with the results and a new column with the total days from 100 to 3,200.
    final_df = pd.DataFrame(data_list, index=valid_countries, columns=labels)
    final_df["total"] = final_df.sum(axis=1)
    print(final_df)


def plot_global_daily_growth(df):
    """Plots the daily global growth.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    """

    # Filter out rows with zero confirmed cases.
    df = df[df["confirmed"] > 0]

    # Resample the data by 1 day intervals and sum the daily totals.
    resampled_df = df.resample("D").sum()

    # Create 3 line plots on the same axis, one for each field.
    fig, ax = plt.subplots()

    ax.plot(resampled_df.index,
            resampled_df["confirmed"], label="Confirmed", color="gold")

    ax.plot(resampled_df.index,
            resampled_df["deaths"], label="Deaths", color="lightblue")

    ax.plot(resampled_df.index,
            resampled_df["recovered"], label="Recoveries", color="lime")

    # Customize tickers.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.grid(linewidth=0.5)
    plt.legend(loc=2)
    plt.title("Daily Confirmed Cases, Deaths & Recoveries Growth", pad=15)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Cumulative Count", labelpad=15)
    plt.savefig("daily_global_growth.png", facecolor="#232b2b")


def plot_country_daily_growth(df, country):
    """Plots the daily growth for a specified country.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    country: str
        The contry or region name.

    """

    # Filter out rows with zero confirmed cases and only select rows that belong
    # to the specified country.
    df = df[(df["confirmed"] > 0) & (df["country"] == country)]

    # Create 3 line plots on the same axis, one for each field.
    fig, ax = plt.subplots()

    ax.plot(df.index, df["confirmed"], label="Confirmed", color="gold")
    ax.plot(df.index, df["deaths"], label="Deaths", color="lightblue")
    ax.plot(df.index, df["recovered"], label="Recoveries", color="lime")

    # Customize tickers.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.grid(linewidth=0.5)
    plt.legend(loc=2)
    plt.title("Daily Confirmed Cases, Deaths & Recoveries Growth", pad=15)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Cumulative Count", labelpad=15)
    plt.savefig("daily_country_growth.png", facecolor="#232b2b")


def plot_global_daily_counts(df):
    """Plots the daily global counts.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    """

    # Filter out rows with zero confirmed cases.
    df = df[df["confirmed"] > 0]

    # Resample the data by 1 day intervals and sum the daily totals.
    resampled_df = df.resample("D").sum()

    # Add 3 new columns, one for each field counts.
    resampled_df["confirmed_difference"] = resampled_df["confirmed"].diff()
    resampled_df["deaths_difference"] = resampled_df["deaths"].diff()
    resampled_df["recovered_difference"] = resampled_df["recovered"].diff()

    # Create 3 line plots on the same axis, one for each field counts.
    fig, ax = plt.subplots()

    ax.plot(resampled_df.index,
            resampled_df["confirmed_difference"], label="Confirmed", color="gold")

    ax.plot(resampled_df.index,
            resampled_df["deaths_difference"], label="Deaths", color="lightblue")

    ax.plot(resampled_df.index,
            resampled_df["recovered_difference"], label="Recoveries", color="lime")

    # Customize tickers.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.grid(linewidth=0.5)
    plt.legend(loc=2)
    plt.title("Daily Confirmed Cases, Deaths & Recoveries Counts", pad=15)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Daily Count", labelpad=15)
    plt.savefig("daily_global_counts.png", facecolor="#232b2b")


def plot_country_daily_counts(df, country):
    """Plots the daily counts for a specified country.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    country: str
        The contry or region name.

    """

    # Filter out rows with zero confirmed cases and only select rows that belong
    # to the specified country.
    df = df[(df["confirmed"] > 0) & (df["country"] == country)].copy()

    # Add 3 new columns, one for each field counts.
    df["confirmed_difference"] = df["confirmed"].diff()
    df["deaths_difference"] = df["deaths"].diff()
    df["recovered_difference"] = df["recovered"].diff()

    # Create 3 line plots on the same axis, one for each field counts.
    fig, ax = plt.subplots()

    ax.plot(df.index, df["confirmed_difference"],
            label="Confirmed", color="gold")
    ax.plot(df.index, df["deaths_difference"],
            label="Deaths", color="lightblue")
    ax.plot(df.index, df["recovered_difference"],
            label="Recoveries", color="lime")

    # Customize tickers.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    plt.grid(linewidth=0.5)
    plt.legend(loc=2)
    plt.title("Daily Confirmed Cases, Deaths & Recoveries Counts", pad=15)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Daily Count", labelpad=15)
    plt.savefig("daily_country_counts.png", facecolor="#232b2b")


def plot_daily_comparison(df, field):
    """Plots the daily deaths for the specified countries.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing the global data.

    field : str
        The field to check, it can be 'confirmed', 'deaths' or 'recovered'.

    """

    # Filter out rows with zero confirmed cases.
    df = df[df[field] > 0]

    # Create a line plot for each country and add it to the same axis.
    fig, ax = plt.subplots()

    for country in COUNTRIES:
        temp_df = df[df["country"] == country[0]].copy()
        temp_df["difference"] = temp_df[field].diff()

        ax.plot(temp_df.index, temp_df["difference"],
                label=country[1], color=country[2])

    # Ticker customizations.
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_locator(ticker.MaxNLocator())
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Add final customizations.
    ax.grid(linewidth=0.5)
    ax.legend(loc=2)
    plt.title("Daily Comparison Between Countries", pad=15)
    plt.xlabel("Date (2020)", labelpad=15)
    plt.ylabel("Daily Count", labelpad=15)
    plt.savefig("daily_comparison.png", facecolor="#232b2b")


if __name__ == "__main__":

    main_df = pd.read_csv("global_data.csv", parse_dates=[
                          "isodate"], index_col=0)

    # get_top_10(main_df)
    # get_global_counts_growths(main_df, "deaths")
    # get_country_counts_growths(main_df, "US", "deaths")
    # get_100_to_3200(main_df)

    # plot_global_daily_growth(main_df)
    # plot_country_daily_growth(main_df, "US")
    # plot_global_daily_counts(main_df)
    # plot_country_daily_counts(main_df, "US")
    # plot_daily_comparison(main_df, "deaths")
