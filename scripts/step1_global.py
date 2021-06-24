"""
This script downloads the Johns Hopkins COVID-19 time series datasets and merges them into one CSV file.
"""

import csv
from datetime import datetime

import requests

CSV_FILES = {
    "confirmed": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
    "deaths": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",
    "recovered": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
}


def main():
    """Prepares our data structures and parses the original CSV files."""

    # Start by generating a skeleton dict and getting all the available dates.
    data_dict, dates_dict = generate_list()

    # Iterate over our 3 urls.
    for kind, url in CSV_FILES.items():

        with requests.get(url) as response:

            # Pass the response text into a csv.DictReader object.
            reader = csv.DictReader(response.text.splitlines())

            # Iterate over each row of the CSV file.
            for row in reader:

                # Iterate over our available dates.
                for k, v in dates_dict.items():

                    # Construct the key for our look up.
                    temp_key = "{}_{}".format(v, row["Country/Region"])

                    # Update the corresponding value depending on the CSV data kind.
                    if kind == "confirmed":
                        data_dict[temp_key][0] += int(row[k])
                    elif kind == "deaths":
                        data_dict[temp_key][1] += int(row[k])
                    elif kind == "recovered":
                        data_dict[temp_key][2] += int(row[k])

    # Save our data to a CSV file.
    with open("global_data.csv", "w", encoding="utf-8", newline="") as other_file:

        # Initialize the data list with the header row.
        data_list = [
            ["isodate", "country", "confirmed", "deaths", "recovered"]]

        # Iterate over our data dict and pass the values to the data list.
        for k, v in data_dict.items():
            isodate, country = k.split("_")
            data_list.append([isodate, country, v[0], v[1], v[2]])

        csv.writer(other_file).writerows(data_list)


def generate_list():
    """Prepares a list with all the available countries and all the available dates.
    This list will contain dummy values that will be later filled.

    Returns
    -------
    tup
        A tuple containing a skeleton list and a dict with the date strings and their datetime objects.

    """

    # Initialize the skeleton dict.
    data_dict = dict()

    # This dictionary will hold all our available dates.
    dates_dict = dict()

    # This set will hold all the countries/regions we find.
    countries = set()

    # We will load the first CSV url.
    file = list(CSV_FILES.values())[0]

    with requests.get(file) as response:

        # Pass the response text into a csv.DictReader object.
        reader = csv.DictReader(response.text.splitlines())

        # Extract the header row and select from the fifth column onwards.
        fields = reader.fieldnames[4:]

        # Convert the header row dates to datetime objects.
        for field in fields:
            dates_dict[field] = "{:%Y-%m-%d}".format(
                datetime.strptime(field, "%m/%d/%y"))

        # Extract the countries/regions by iterating over all rows.
        for row in reader:
            countries.add(row["Country/Region"])

        # Convert the countries set to a list and sort it.
        countries = sorted(list(countries))

        # Combine every date with every country and fill it with zero values.
        for date in dates_dict.values():

            for country in countries:

                temp_key = "{}_{}".format(date, country)
                data_dict[temp_key] = [0, 0, 0]

        return data_dict, dates_dict


if __name__ == "__main__":

    main()
