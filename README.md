# COVID-19

This project contains scripts that collect and transform datasets of the COVID-19 outbreak for global and mexican data. It explains the ETL process and in the future it wlil include the EDA process as well.

The following are the summaries of the included scripts:

* step1_global.py - A Python script that downloads and merges datasets from the Johns Hopkins repository.

* step1_mx.py - A Python script that downloads a mexican government PDF file, cleans it and converts it to CSV.

## Requirements

This project uses the following Python libraries

* requests - For downloading PDF and CSV files.
* BeautifulSoup - For locating the mexican government PDF file.
* PyPDF2 - For reading the mexican government PDF file.

# ETL Process

Data is not always presented in the most optimal way, this is why we need to pass it through a transformation process.

I'm interested in both global and mexican data (my country). Let's start with the global one.

## Global Data

The university of Johns Hopkins provides various datasets that contain global data of the COVID-19 outbreak that are updated daily.

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

Each country will have zero values for each date we find. The drawback is that we will end with several rows with zero values but that's really easy fo tilter out with `pandas`.

Once we have our skeleton list ready we can start filling it with real data.

For this we load the 3 CSV files and check each row to see if it matches with our skeleton list and then update the respective column.

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

This can be done more efficiently with other libraries but I wanted to provide a solution that used the less external dependencies as possible.

## Mexican Data

The mexican government provides a tabular PDF file contaning the information of the confirmed cases of COVID-19.

The goal is to convert that PDF to CSV. There's a library named `tabula-py` that does this really quickly but I found out I needed to install Java to use it.

Instead of that we will use `PyPDF2` and a custom algorithm to identify patterns.

Let's start by loading up the PDF file and initializing our data list.

```python
# Initialize the PDF reader.
reader = PyPDF2.PdfFileReader(open("./casos_confirmados.pdf", "rb"))

# Initialize our data list with a header row (8 columns).
data_list = [["numero_caso", "estado", "sexo", "edad",
                "fecha_inicio_sintomas", "estatus", "procedencia", "fecha_llegada_mexico"]]

# Iterate over each page.
for i in range(reader.numPages):
    print("Processing page:", i+1, "of", reader.numPages)

    # Extract the raw text.
    page_data = reader.getPage(i).extractText()
```

We then iterate over each page and extract the text. For the most part this PDF file is well formatted but I noticed the resulting CSV file kept having errors.

I found out that CIUDAD DE MEXICO was written in 3 different ways. It has a new line character where it shouldn't be.

With the following dictionary I'm able to locate these errors and fix them.

```python
FIX_STRINGS = [
    ["CIUDAD DE\n \nMÉXICO", "CIUDAD DE MÉXICO"],
    ["CIUDAD\n \nDE MÉXICO", "CIUDAD DE MÉXICO"],
    ["Estados\n \nUnidos", "Estados Unidos"]
]

# Fix some small inconsistencies with the text.
for fixer in FIX_STRINGS:
    page_data = page_data.replace(fixer[0], fixer[1])

# Split the text into chunks and remove empty ones.
page_data = [item.replace("\n", "")
                for item in page_data.split("\n ") if item != " "]

```

At this point we have a list of strings. We removed the blank ones and we only have valid data. Very similar to the following list:

```python
['Casos Confirmados a enfermedad por COVID-19.', 'N° Caso', 'Estado', 'Sexo', 'Edad', 'Fecha de Inicio de síntomas', 'Identificación de COVID-19 por RT-PCR en tiempo real', 'Procedencia', 'Fecha del llegada a México', '1', 'CIUDAD DE MÉXICO', 'M', '35', '22/02/2020', 'Confirmado', 'Italia']
```

The first page of the PDF file has the header row data, we will add an if statement to ignore it on first page only.

```python
# Only on the first page the starting chunk is the 10th one.
if i == 0:
    start_index = 9
else:
    start_index = 0

# Iterate over our chunks, 8 at a time (8 columns).
for j in range(start_index, len(page_data), 8):

    # Create a list with the current chunk plus the next seven.
    temp_list = page_data[j:j+8]

    # Add the previous list to the data list if it's not empty.
    if len(temp_list) == 8 and temp_list[0] != "":
        data_list.append(temp_list)
```

We took 8 chunks of the PDF data at a time, passed them to our data list and saved that list to CSV using the `csv.writer().writerows()` method.

```python
with open("casos_confirmados.csv", "w", encoding="utf-8", newline="") as csv_file:
    csv.writer(csv_file).writerows(data_list)
    print("PDF converted.")
```

## Conclusion

Getting clean data is not always easy and can discourage people from doing their own analysis. That's why I wanted to shore these scripts with you so you can accelerate your workflow and get interesting insights.

Stay tuned for the EDA part!