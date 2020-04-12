# COVID-19

This project contains scripts that collect and transform datasets of the COVID-19 pandemic for global and Mexican data. It explains the ETL and EDA process.

The following are the summaries of the included scripts:

* step1_global.py - A Python script that downloads and merges datasets from the Johns Hopkins repository.

* step1_mx.py - A Python script that downloads a mexican government PDF file, cleans it and converts it to CSV.

## Requirements

This project uses the following Python libraries

* requests - For downloading PDF and CSV files.
* BeautifulSoup - For locating the mexican government PDF file.
* PyPDF2 - For reading the mexican government PDF file.
* pandas - For performing Data Analysis.
* NumPy - For fast matrix operations.
* Matplotlib - For creating plots.
* seaborn - Used to prettify Matplotlib plots.

# ETL Process

Data is not always presented in the most optimal way, this is why we need to pass it through a transformation process.

I'm interested in both global and Mexican specific data (my country). Let's start with the global one.

## Global Data

The university of Johns Hopkins provides various datasets that contain global data of the COVID-19 pandemic that are daily updated.

Our goal is to merge the time series datasets into one CSV file.

The first thing to do is to define the CSV urls and their kind.

```python
CSV_FILES = {
    "confirmed": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
    "deaths": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",
    "recovered": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
}
```

These CSV files have the same structure, the columns are the dates and the index are the countries/regions names.

In my experience it is better to have a datetime index than a string one. This is because `pandas` has a great support for datetime indexes.

We have a small problem, we don't know how many columns we will have since they add a new one each day.

What I did is to first 'scout' one of the CSV files and create a skeleton list that will then be filled with the real data.

```python
# Initialize the skeleton list with a header row.
data_list = [["isodate", "country", "confirmed", "deaths", "recovered"]]

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
        dates_dict[field] = datetime.strptime(field, "%m/%d/%y")

    # Extract the countries/regions by iterating over all rows.
    for row in reader:
        countries.add(row["Country/Region"])

    # Convert the countries set to a list and sort it.
    countries = sorted(list(countries))
    
    # Combine every date with every country and fill it with zero values.
    for date in dates_dict.values():

        for country in countries:
            data_list.append([date, country, 0, 0, 0])
```

Once this code is run we end up having a list similar to this one.

```python
["isodate", "country", "confirmed", "deaths", "recovered"]
[2020-01-22 00:00:00, 'Afghanistan', 0, 0, 0]
[2020-01-22 00:00:00, 'Albania', 0, 0, 0],
[2020-01-22 00:00:00, 'Algeria', 0, 0, 0]
```

Each country will have zero values for each date we find. The drawback is that we will end with several rows with zero values but that's really easy fo filter out with `pandas`.

Once we have our skeleton list ready we can start filling it with real data.

We will load the 3 CSV files and check each row to see if it matches with our skeleton list and then update the corresponding column.

```python
# Iterate over our 3 urls.
for kind, url in CSV_FILES.items():

    with requests.get(url) as response:

        # Pass the response text into a csv.DictReader object.
        reader = csv.DictReader(response.text.splitlines())

        # Iterate over each row of the CSV file.
        for row in reader:

            # Iterate over our available dates.
            for k, v in dates_dict.items():

                # Iterate over our skeleton list.
                for index, item in enumerate(data_list):

                    # If the current skeleton list row matches our CSV row we update its values.
                    if v == item[0] and row["Country/Region"] == item[1]:

                        # Depending on the kind of the CSV data is the column to update.
                        if kind == "confirmed":
                            data_list[index][2] = row[k]
                        elif kind == "deaths":
                            data_list[index][3] = row[k]
                        elif kind == "recovered":
                            data_list[index][4] = row[k]

                        break

# Save our data to a CSV file.
with open("global_data.csv", "w", encoding="utf-8", newline="") as other_file:
    csv.writer(other_file).writerows(data_list)
```

Now we have our CSV file saved on our computer, ready to be analyzed.

This can be done more efficiently with other libraries but I wanted to provide a solution that used the less external dependencies as possible.

## Mexican Data

The Mexican government provides a tabular PDF file contaning the information of the confirmed cases of COVID-19.

The goal is to convert that PDF to CSV. There's a library named `tabula-py` that does this really quickly but I found out I needed to install Java to use it.

Instead of that we will use `PyPDF2` and a custom algorithm to identify patterns.

Let's start by loading up the PDF file and initializing our data list.

```python
# Initialize the PDF reader.
reader = PyPDF2.PdfFileReader(open("./casos_confirmados.pdf", "rb"))

# Initialize our data list with a header row (8 columns).
data_list = [["numero_caso", "estado", "sexo",
                  "edad", "fecha_inicio_sintomas", "estatus"]]

# Iterate over each page.
for i in range(reader.numPages):
    print("Processing page:", i+1, "of", reader.numPages)

    # Extract the raw text.
    page_data = reader.getPage(i).extractText()
```

We then iterate over each page and extract the text. For the most part this PDF file is well formatted but I noticed the resulting CSV file kept having errors.

I found out that CIUDAD DE MEXICO was written in 3 different ways. It has a new line character where it shouldn't be.

With the following dictionary I'm able to locate similar errors and fix them.

```python
FIX_STRINGS = [
    ["CIUDAD DE\n \nMÉXICO", "CIUDAD DE MÉXICO"],
    ["CIUDAD\n \nDE MÉXICO", "CIUDAD DE MÉXICO"],
    ["BAJA\n \nCALIFORNIA", "BAJA CALIFORNIA"],
    ["SAN LUIS\n \nPOTOSÍ", "SAN LUIS POTOSÍ"],
    ["QUINTANA\n \nROO", "QUINTANA ROO"],
    ["Estados\n \nUnidos", "Estados Unidos"]
]

# Fix some small inconsistencies with the text.
for fixer in FIX_STRINGS:
    page_data = page_data.replace(fixer[0], fixer[1])

# Split the text into chunks and remove empty ones.
page_data = [item.replace("\n", "")
                     for item in page_data.split("\n") if item != " "]

page_data = [item for item in page_data if item != ""]
```

At this point we have a list of strings. We removed the blank ones and we only have valid data.

The first page of the PDF file has the header row data, we will add an if statement to ignore it on the first page only.

```python
# Only on the first page the starting chunk is the 10th one.
if i == 0:
    start_index = 9
else:
    start_index = 0

# Iterate over our chunks, 7 at a time (7 columns).
for j in range(start_index, len(page_data), 6):

    # Create a list with the current chunk plus the next five.
    temp_list = page_data[j:j+6]

    # Add the previous list to the data list if it's not incomplete.
    if len(temp_list) == 6:

        # Fix for bad formatted dates.
        if len(temp_list[4]) == 5:
            temp_date = start_time + timedelta(days=int(temp_list[4]))
            temp_list[4] = "{:%d/%m/%Y}".format(temp_date)
```

We took 6 chunks of the PDF data at a time, passed them to our data list and saved that list to CSV using the `csv.writer().writerows()` method.

```python
with open("casos_confirmados.csv", "w", encoding="utf-8", newline="") as csv_file:
    csv.writer(csv_file).writerows(data_list)
    print("PDF converted.")
```

## Data Analysis

Now we have 2 CSV files ready to be analyzed and plotted, `global_data.csv` and `casos_confirmados.csv`.

We are going to use `pandas`, `NumPy`, `matplotlib` and `seaborn`. We will start by importing the required libraries and setting up the styles for our plots.


```python
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
```

These styles will apply an elegant dark gray palette to our plots.

Let's start with the global dataset.

*Note: You will have different numbers no your results as I did this analysis on older datasets.*

## Global Data

We start by loading our dataset and specifying the first column as our index, this will turn it into a `datetimeindex` which is very handy when managing time series data.

```python
df = pd.read_csv("global_data.csv", parse_dates=["isodate"], index_col=0)
```

Let's take a look at our `DataFrame` using the `head()`, `tail()` and `describe()` methods.

```python
df.head()
```

| | country | confirmed | deaths |  recovered |
| --- | --- | --- | --- | --- |
| isodate | | | |
| 2020-01-22 | Afghanistan | 0 | 0 | 0 |
| 2020-01-22 | Albania | 0 | 0 | 0 |
| 2020-01-22 | Algeria | 0 | 0 | 0 |
| 2020-01-22 | Andorra | 0 | 0 | 0 |
| 2020-01-22 | Angola | 0 | 0 | 0 |

```python
df.tail()
```

| isodate             | country            |   confirmed |   deaths |   recovered |
|:--------------------|:-------------------|------------:|---------:|------------:|
| 2020-04-10 00:00:00 | West Bank and Gaza |         267 |        2 |          45 |
| 2020-04-10 00:00:00 | Western Sahara     |           4 |        0 |           0 |
| 2020-04-10 00:00:00 | Yemen              |           1 |        0 |           0 |
| 2020-04-10 00:00:00 | Zambia             |          40 |        2 |          25 |
| 2020-04-10 00:00:00 | Zimbabwe           |          13 |        3 |           0 |

```python
df.describe()
```

|       |   confirmed |    deaths |   recovered |
|:------|------------:|----------:|------------:|
| count |    14800    | 14800     |   14800     |
| mean  |     1091.58 |    53.391 |     169.777 |
| std   |    11988.7  |   698.943 |    1855.39  |
| min   |        0    |     0     |       0     |
| 25%   |        0    |     0     |       0     |
| 50%   |        0    |     0     |       0     |
| 75%   |       27    |     0     |       1     |
| max   |   496535    | 18849     |   55668     |

We can observe the countries are alphabetically sorted and our `datetimeindex` worked correctly.

We can also observe all the first rows have zero values, as predicted from the ETL process. This caused an adverse effect on the `describe()` method, where the results are biased towards zero.

Let's fix this by removing all rows with zero values on their confirmed field.

```python
df = df[df["confirmed"] > 0]
df.describe()
```

|       |   confirmed |    deaths |   recovered |
|:------|------------:|----------:|------------:|
| count |     6788    |  6788     |    6788     |
| mean  |     2380    |   116.409 |     370.092 |
| std   |    17616.3  |  1028.53  |    2726.2   |
| min   |        1    |     0     |       0     |
| 25%   |        6    |     0     |       0     |
| 50%   |       41    |     0     |       1     |
| 75%   |      379.25 |     5     |      22     |
| max   |   496535    | 18849     |   55668     |

Now, this looks better and we can now start getting interesting insights.

We will be applying this same filtering on some of the next sections.

### Top 10 Countries by Confirmed Cases, Deaths & Recoveries

To get the countries with the highest values we first need to group our `DataFrame` by the country field and selecting their max value which happenes to be the latest one.

```python
grouped_df = df.groupby("country").max()
```

Once grouped we use the `sort_values()` method on the field we are intereseted and use the descending order. From there we print the first 10 rows from the field we are interested in.

```python
# Confirmed cases
print(grouped_df.sort_values("confirmed", ascending=False)["confirmed"][:10])
```

| country     |   confirmed |
|:------------|------------:|
| US          |      461437 |
| Spain       |      153222 |
| Italy       |      143626 |
| Germany     |      118181 |
| Iran        |       66220 |
| Turkey      |       42282 |
| Belgium     |       24983 |
| Switzerland |       24051 |
| Brazil      |       18092 |
| Portugal    |       13956 |

```python
# Deaths
print(grouped_df.sort_values("deaths", ascending=False)["deaths"][:10])
```

| country     |   deaths |
|:------------|---------:|
| Italy       |    18279 |
| US          |    16478 |
| Spain       |    15447 |
| Iran        |     4110 |
| Germany     |     2607 |
| Belgium     |     2523 |
| Brazil      |      950 |
| Switzerland |      948 |
| Turkey      |      908 |
| Sweden      |      793 |

```python
# Recoveries
print(grouped_df.sort_values("recovered", ascending=False)["recovered"][:10])
```

| country      |   recovered |
|:-------------|------------:|
| Germany      |       52407 |
| Spain        |       52165 |
| Iran         |       32309 |
| Italy        |       28470 |
| US           |       25410 |
| Switzerland  |       10600 |
| Korea, South |        6973 |
| Austria      |        5240 |
| Belgium      |        5164 |
| Canada       |        5162 |

### Daily Global Confirmed Cases, Deaths or Recoveries

Thanks fo the `datetimeindex` knowing the daily totals is really easy. We will only require to resample our `DataFrame` by 1 day intervals.

We will start by defining our field (`confirmed`, `deaths` or `recovered`) and resampling method.

```python
field = "deaths"
resampled_df = df.resample("D").sum()
```

We add 2 new columns to know the daily field totals (`difference`) and their percent change (`change`).

```python
resampled_df["difference"] = resampled_df[field].diff()
resampled_df["change"] = resampled_df["difference"].pct_change()
```

Now we drop `NaN` values, we do this so the next step doesn't crash the script.

```python
resampled_df.dropna(inplace=True)
```

This step is optional, the purpose of it is to display the results in a more human readable way.

The `difference` column gets converted from `float` to `int` and the `change` column gets some string formatting, which includes adding a percent sign and rounding up the numbers to the second decimal.

```python
resampled_df["difference"] = resampled_df["difference"].apply(int)

resampled_df["change"] = resampled_df["change"].apply(
    lambda x: str(np.round(x * 100, 2)) + "%")
```

And finally, we print the latest 10 rows.

```python
print(resampled_df[[field, "difference", "change"]][-10:])
```

| isodate             |   deaths |   difference | change   |
|:--------------------|---------:|-------------:|:---------|
| 2020-04-01 00:00:00 |    35792 |         3475 | 0.93%    |
| 2020-04-02 00:00:00 |    39836 |         4044 | 16.37%   |
| 2020-04-03 00:00:00 |    43636 |         3800 | -6.03%   |
| 2020-04-04 00:00:00 |    47481 |         3845 | 1.18%    |
| 2020-04-05 00:00:00 |    50944 |         3463 | -9.93%   |
| 2020-04-06 00:00:00 |    54671 |         3727 | 7.62%    |
| 2020-04-07 00:00:00 |    59493 |         4822 | 29.38%   |
| 2020-04-08 00:00:00 |    64298 |         4805 | -0.35%   |
| 2020-04-09 00:00:00 |    68945 |         4647 | -3.29%   |
| 2020-04-10 00:00:00 |    73872 |         4927 | 6.03%    |

### Daily Confirmed Cases, Deaths or Recoveries for any Country

Now we will know the daily confirmed cases, deaths or recoveries and their growth for any given country. We will use the US for this example.

We start by defining the country and which field we want (`confirmed`, `deaths` or `recovered`). Afterwards we filter our `DataFrame` so it only includes values of that country.

```python
field = "deaths"
country = "US"
filtered_df = df[df["country"] == country].copy()
```

We add 2 new columns to know the daily field totals (`difference`) and their percent change (`change`).

```python
filtered_df["difference"] = filtered_df[field].diff()
filtered_df["change"] = filtered_df["difference"].pct_change()
```

Now we drop `NaN` values, we do this so the next step doesn't crash the script.

```python
filtered_df.dropna(inplace=True)
```

This step is optional, the purpose of it is to display the results in a more human readable way.

The `difference` column gets converted from `float` to `int` and the `change` column gets some string formatting, which includes adding a percent sign and rounding up the numbers to the second decimal.

```python
filtered_df["difference"] = filtered_df["difference"].apply(int)

filtered_df["change"] = filtered_df["change"].apply(
    lambda x: str(np.round(x * 100, 2)) + "%")
```

And finally, we print the latest 10 rows.

```python
print(filtered_df[[field, "difference", "change"]][-10:])
```

| isodate             |   deaths |   difference | change   |
|:--------------------|---------:|-------------:|:---------|
| 2020-03-31 00:00:00 |     3873 |          895 | 75.15%   |
| 2020-04-01 00:00:00 |     4757 |          884 | -1.23%   |
| 2020-04-02 00:00:00 |     5926 |         1169 | 32.24%   |
| 2020-04-03 00:00:00 |     7087 |         1161 | -0.68%   |
| 2020-04-04 00:00:00 |     8407 |         1320 | 13.7%    |
| 2020-04-05 00:00:00 |     9619 |         1212 | -8.18%   |
| 2020-04-06 00:00:00 |    10783 |         1164 | -3.96%   |
| 2020-04-07 00:00:00 |    12722 |         1939 | 66.58%   |
| 2020-04-08 00:00:00 |    14695 |         1973 | 1.75%    |
| 2020-04-09 00:00:00 |    16478 |         1783 | -9.63%   |

Feel free to try this with other country names, such as Italy, Spain or Iran.

## Mexican Data

We start by loading our dataset and specifying the fifth column (`fecha_inicio_sintomas`) as datetime.

```python
main_df = pd.read_csv("casos_confirmados.csv", index_col=0, parse_dates=[
                          "fecha_inicio_sintomas"], dayfirst=True)
```

Let's take a look at our `DataFrame` using the `head()`, `tail()` and `describe()` methods.

```python
df.head()
```

|   numero_caso | estado           | sexo      |   edad | fecha_inicio_sintomas   | estatus    |
|--------------:|:-----------------|:----------|-------:|:------------------------|:-----------|
|             1 | MÉXICO           | FEMENINO  |     75 | 2020-03-28 00:00:00     | Confirmado |
|             2 | TAMAULIPAS       | MASCULINO |     22 | 2020-04-04 00:00:00     | Confirmado |
|             3 | CIUDAD DE MÉXICO | MASCULINO |     40 | 2020-03-17 00:00:00     | Confirmado |
|             4 | CIUDAD DE MÉXICO | FEMENINO  |     29 | 2020-03-26 00:00:00     | Confirmado |
|             5 | GUERRERO         | FEMENINO  |     61 | 2020-04-06 00:00:00     | Confirmado |

```python
df.tail()
```

|   numero_caso | estado           | sexo      |   edad | fecha_inicio_sintomas   | estatus    |
|--------------:|:-----------------|:----------|-------:|:------------------------|:-----------|
|          3840 | MÉXICO           | MASCULINO |     61 | 2020-03-14 00:00:00     | Confirmado |
|          3841 | MÉXICO           | FEMENINO  |     28 | 2020-03-26 00:00:00     | Confirmado |
|          3842 | CIUDAD DE MÉXICO | FEMENINO  |     62 | 2020-03-18 00:00:00     | Confirmado |
|          3843 | CAMPECHE         | FEMENINO  |     32 | 2020-03-31 00:00:00     | Confirmado |
|          3844 | PUEBLA           | FEMENINO  |     66 | 2020-03-15 00:00:00     | Confirmado |

```python
df.describe()
```

|       |      edad |
|:------|----------:|
| count | 3844      |
| mean  |   45.4389 |
| std   |   15.8237 |
| min   |    0      |
| 25%   |   33      |
| 50%   |   45      |
| 75%   |   56      |
| max   |  102      |

We have 5 columns, state, age, gender, date of initial symptoms and status. We will work with the first four and discard the last one since it has the same value for all rows.

It is very important to note that the column of date of initial symptoms is not a confirmed cases date. That data is not available in this dataset but it is available on the global one.

### Confirmed Cases by State

Mexico has 32 states and as of now all of them have confirmed cases.

To know how many cases each state has we use the `value_counts()` method on the `estado` column.

```python
print(df["estado"].value_counts())
```

|                     |   estado |
|:--------------------|---------:|
| CIUDAD DE MÉXICO    |     1117 |
| MÉXICO              |      498 |
| BAJA CALIFORNIA     |      278 |
| PUEBLA              |      243 |
| QUINTANA ROO        |      216 |
| SINALOA             |      214 |
| COAHUILA            |      156 |
| JALISCO             |      150 |
| TABASCO             |      143 |
| NUEVO LEÓN          |      119 |
| YUCATÁN             |      103 |
| BAJA CALIFORNIA SUR |      102 |
| GUANAJUATO          |       81 |
| VERACRUZ            |       73 |
| SONORA              |       65 |
| QUERETARO           |       57 |
| GUERRERO            |       56 |
| AGUASCALIENTES      |       55 |
| CHIHUAHUA           |       54 |
| HIDALGO             |       53 |
| SAN LUIS POTOSÍ     |       51 |
| MICHOACÁN           |       50 |
| TAMAULIPAS          |       49 |
| OAXACA              |       43 |
| MORELOS             |       40 |
| CHIAPAS             |       39 |
| TLAXCALA            |       38 |
| NAYARIT             |       21 |
| CAMPECHE            |       18 |
| DURANGO             |       16 |
| ZACATECAS           |       14 |
| COLIMA              |        7 |

The state with most cases is the capital of the country (Mexico City).

That was really simple, let's up our game and do some table pivoting and MultiIndex calculations.

We will use this value to calculate the percentages.

```python
total_cases = len(df)
```

We pivot the table, we will use the gender as our columns and the state as our index.

```python
pivoted_df = df.pivot_table(
    index="estado", columns="sexo", aggfunc="count")
```

From this MultiIndex DataFrame we will add two columns to the age column. These columns will have the total percentage of each state and gender.

```python
pivoted_df["edad", "female_percentage"] = np.round(
    pivoted_df["edad", "FEMENINO"] / total_cases * 100, 2)

pivoted_df["edad", "male_percentage"] = np.round(
    pivoted_df["edad", "MASCULINO"] / total_cases * 100, 2)
```

We rename the columns so they are human readable.

```python
pivoted_df.rename(columns={"MASCULINO": "Male",
                            "FEMENINO": "Female",
                            "male_percentage": "Male %",
                            "female_percentage": "Female %"}, level=1, inplace=True)

print(pivoted_df["edad"])
```

| estado              |   Female |   Male |   Female % |   Male % |
|:--------------------|---------:|-------:|-----------:|---------:|
| AGUASCALIENTES      |       29 |     26 |       0.69 |     0.62 |
| BAJA CALIFORNIA     |      126 |    152 |       2.99 |     3.6  |
| BAJA CALIFORNIA SUR |       47 |     55 |       1.11 |     1.3  |
| CAMPECHE            |        5 |     13 |       0.12 |     0.31 |
| CHIAPAS             |       10 |     29 |       0.24 |     0.69 |
| CHIHUAHUA           |       19 |     35 |       0.45 |     0.83 |
| CIUDAD DE MÉXICO    |      436 |    681 |      10.33 |    16.14 |
| COAHUILA            |       69 |     87 |       1.64 |     2.06 |
| COLIMA              |        3 |      4 |       0.07 |     0.09 |
| DURANGO             |        7 |      9 |       0.17 |     0.21 |
| GUANAJUATO          |       43 |     38 |       1.02 |     0.9  |
| GUERRERO            |       20 |     36 |       0.47 |     0.85 |
| HIDALGO             |       19 |     34 |       0.45 |     0.81 |
| JALISCO             |       58 |     92 |       1.37 |     2.18 |
| MICHOACÁN           |       20 |     30 |       0.47 |     0.71 |
| MORELOS             |       19 |     21 |       0.45 |     0.5  |
| MÉXICO              |      214 |    284 |       5.07 |     6.73 |
| NAYARIT             |       14 |      7 |       0.33 |     0.17 |
| NUEVO LEÓN          |       38 |     81 |       0.9  |     1.92 |
| OAXACA              |       22 |     21 |       0.52 |     0.5  |
| PUEBLA              |      117 |    126 |       2.77 |     2.99 |
| QUERETARO           |       26 |     31 |       0.62 |     0.73 |
| QUINTANA ROO        |       71 |    145 |       1.68 |     3.44 |
| SAN LUIS POTOSÍ     |       25 |     26 |       0.59 |     0.62 |
| SINALOA             |       90 |    124 |       2.13 |     2.94 |
| SONORA              |       33 |     32 |       0.78 |     0.76 |
| TABASCO             |       73 |     70 |       1.73 |     1.66 |
| TAMAULIPAS          |       22 |     27 |       0.52 |     0.64 |
| TLAXCALA            |       17 |     21 |       0.4  |     0.5  |
| VERACRUZ            |       33 |     40 |       0.78 |     0.95 |
| YUCATÁN             |       47 |     56 |       1.11 |     1.33 |
| ZACATECAS           |        5 |      9 |       0.12 |     0.21 |

And now we have a more complete and useful table of summaries.

### Confirmed Cases Daily Growth

Let's start our plots section with a simple one. This plot will show us the daily progression of the pandemic in Mexico.

Remember that this dataset does not contain the dates when the cases were confirmed, it contains the date when the symptoms first appeared. Let's see what we will get.

We group our `DataFrame` by day of initial symptoms and aggregate them by number of ocurrences.

```python
grouped_df = df.groupby("fecha_inicio_sintomas").count()
```

We add a new column that will hold the cumulative sum of the previous counts.

```python
grouped_df["cumsum"] = grouped_df["estado"].cumsum()
```

We create a basic line plot with the previously created column.

```python
fig, ax = plt.subplots()

ax.plot(grouped_df.index, grouped_df["cumsum"],
        label="Initial Symptoms", color="lime")
```

Customize the tickers. The y-axis will be formatted with date and month in 7 day intervals.

```python
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax.yaxis.set_major_locator(ticker.MaxNLocator())
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
```

Add final customizations.

```python
plt.title("Confirmed Cases Growth", pad=15)
plt.legend(loc=2)
plt.grid(linewidth=0.5)
plt.xlabel("Date (2020)", labelpad=15)
plt.ylabel("Number of Confirmed Cases", labelpad=15)

plt.show()
```

![Age Mexico Growth](./figs/mexico_growth.png)

It does resemble the confirmed cases curve.

### Age and Sex Distribution

Knowing the age groups is very important and for this exercise we will bin our data and then group it by gender. We will use custom bins that wlil  hold values in steps of 10 (0-9, 10-19, 20-29 and so on.).

On the 90-99 bin we will make an exception and define it has 90-120 since that age group has the least values of them all.

We start by cCreating one `DataFrame` for each gender.

```python
male_df = df[df["sexo"] == "MASCULINO"]
female_df = df[df["sexo"] == "FEMENINO"]
```

We then define 2 lists that will be used for our bins.

```python
age_groups = list()
labels = list()
```

We start a loop from 0 to 100 with steps of 10. This will fill our previous 2 lists.

```python
for i in range(0, 100, 10):

    # Our latest bin will be for ages >= 90.
    if i == 90:
        age_groups.append((i, i+30))
        labels.append("≥ 90")
    else:
        age_groups.append((i, i+9))
        labels.append("{}-{}".format(i, i+9))
```

We build our indexer and cut our `DataFrames` with it.

```python
bins = pd.IntervalIndex.from_tuples(age_groups)

male_df = male_df.groupby(pd.cut(male_df["edad"], bins)).count()
female_df = female_df.groupby(pd.cut(female_df["edad"], bins)).count()
```

We create a 2 bar plots in the same axis, each plot will have the values for their respective `DataFrame`.

```python
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

```

Customize our tickers.

```python
ax.yaxis.set_major_locator(ticker.MaxNLocator())
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
```

Add final customizations.

```python
plt.title("Age and Sex Distribution", pad=15)
plt.legend(["Male", "Female"], loc=2)
plt.grid(linewidth=0.5)
plt.xticks(range(len(labels)), labels)
plt.xlabel("Age Range", labelpad=15)
plt.ylabel("Confirmed Cases", labelpad=15)

plt.show()
```

![Age Distribution](./figs/age_sex.png)

We can observe that most cases fall within the 30-60 age range and men have most registered cases than women in almost all age groups.

And that's it for this dataset. We got as much information as we could from the four usable fields we had (state, age, gender and initial symptoms date).

Thir dataset used to have 2 other fields; country of procedence and arrival date but they were removed for no reason.

## Conclusion

Getting clean data is not always easy and can discourage people from doing their own analysis. That's why I wanted to shore these scripts with you so you can accelerate your workflow and get interesting insights.

There's still more to come!