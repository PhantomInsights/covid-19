"""
This script downloads the Mexican dataset and its catalog.
It then merges them and cleans them into a new dataset.
"""

import csv
import io
import os
import zipfile

import requests
from openpyxl import load_workbook


DATA_URL = "http://datosabiertos.salud.gob.mx/gobmx/salud/datos_abiertos/datos_abiertos_covid19.zip"
DATA_FILE = "./data.zip"

CATALOG_URL = "http://epidemiologia.salud.gob.mx/gobmx/salud/datos_abiertos/diccionario_datos_covid19.zip"
CATALOG_FILE = "./catalog.zip"

# These will hold the values from the catalog workbook.
ORIGEN_DICT = dict()
SECTOR_DICT = dict()
SEXO_DICT = dict()
TIPO_PACIENTE_DICT = dict()
SI_NO_DICT = dict()
NACIONALIDAD_DICT = dict()
RESULTADO_LAB_DICT = dict()
ENTIDADES_DICT = dict()
MUNICIPIOS_DICT = dict()
CLASIFICACION_FINAL_DICT = dict()

# Used to fix encoding issues.
FIXERS = {
    "Ã±": "ñ",
    "Ã¡": "á",
    "Ã©": "é",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã": "í"
}


def download():
    """Downloads the required zip files."""

    print("Downloading ZIP files...")

    with requests.get(DATA_URL) as response:

        with open(DATA_FILE, "wb") as temp_file:
            temp_file.write(response.content)

    with requests.get(CATALOG_URL) as response:

        with open(CATALOG_FILE, "wb") as temp_file:
            temp_file.write(response.content)

    print("ZIP files downloaded.")


def convert():
    """Extracts the data from the zip files and creates a new dataset with them."""

    data_list = list()

    with zipfile.ZipFile(CATALOG_FILE) as catalog_zip:
        print("Reading catalog file...")

        with catalog_zip.open(catalog_zip.namelist()[1]) as cat_file:
            print("Processing catalog file...")

            workbook = load_workbook(io.BytesIO(
                cat_file.read()), read_only=True)

            # Origen
            sheet = workbook["Catálogo ORIGEN"]

            for row in sheet.rows:
                ORIGEN_DICT[str(row[0].value)] = str(row[1].value).strip()

            # Sectores de Salud
            sheet = workbook["Catálogo SECTOR"]

            for row in sheet.rows:
                SECTOR_DICT[str(row[0].value)] = str(row[1].value).strip()

            # Sexo
            sheet = workbook["Catálogo SEXO"]

            for row in sheet.rows:
                SEXO_DICT[str(row[0].value)] = str(row[1].value).strip()

            # Tipo Paciente
            sheet = workbook["Catálogo TIPO_PACIENTE"]

            for row in sheet.rows:
                TIPO_PACIENTE_DICT[str(row[0].value)] = str(
                    row[1].value).strip()

            # Si / No
            sheet = workbook["Catálogo SI_NO"]

            for row in sheet.rows:
                SI_NO_DICT[str(row[0].value)] = str(row[1].value).strip()

            # Nacionalidad
            sheet = workbook["Catálogo NACIONALIDAD"]

            for row in sheet.rows:
                NACIONALIDAD_DICT[str(row[0].value)] = str(
                    row[1].value).strip()

            # Resultado Lab
            sheet = workbook["Catálogo RESULTADO_LAB"]

            for row in sheet.rows:

                # This one has an issue with rows that are not empty.
                if len(row) > 0:
                    RESULTADO_LAB_DICT[str(row[0].value)] = str(
                        row[1].value).strip()

            # Clasificación Final
            sheet = workbook["Catálogo CLASIFICACION_FINAL"]

            for row in sheet.rows:

                # Skip None row.
                if row[0].value:

                    row_value = row[1].value

                    # Fix encoding issues.
                    for k, v in FIXERS.items():
                        row_value = row_value.replace(k, v).strip()

                    CLASIFICACION_FINAL_DICT[str(row[0].value)] = row_value


            # Entidades Federativas
            sheet = workbook["Catálogo de ENTIDADES"]

            for row in sheet.rows:
                ENTIDADES_DICT[str(row[0].value)] = str(row[1].value).strip()

            # Municipios
            sheet = workbook["Catálogo MUNICIPIOS"]

            for row in sheet.rows:
                # This one requires to combine the state and municipality codes.
                state_with_municipality = "{}-{}".format(
                    row[0].value, row[2].value)

                MUNICIPIOS_DICT[state_with_municipality] = str(
                    row[1].value).strip()

            print("Catalog file processed.")

    # Extract the CSV file from the ZIP file.
    with zipfile.ZipFile(DATA_FILE) as data_zip:
        print("Reading CSV file...")

        with data_zip.open(data_zip.namelist()[0], "r") as csv_file:
            print("Procesing CSV file...")

            reader = csv.DictReader(
                io.TextIOWrapper(csv_file, encoding="latin-1"))

            for row in reader:

                # we start with the municipality one so it doesn't break the states column.
                state_with_municipality = "{}-{}".format(
                    row["MUNICIPIO_RES"], row["ENTIDAD_RES"])

                row["MUNICIPIO_RES"] = MUNICIPIOS_DICT.get(
                    state_with_municipality, "NO ETIQUETADO")

                row["ENTIDAD_UM"] = ENTIDADES_DICT[row["ENTIDAD_UM"]]
                row["ENTIDAD_NAC"] = ENTIDADES_DICT[row["ENTIDAD_NAC"]]
                row["ENTIDAD_RES"] = ENTIDADES_DICT[row["ENTIDAD_RES"]]
                row["ORIGEN"] = ORIGEN_DICT[row["ORIGEN"]]
                row["SECTOR"] = SECTOR_DICT[row["SECTOR"]]
                row["SEXO"] = SEXO_DICT[row["SEXO"]]
                row["TIPO_PACIENTE"] = TIPO_PACIENTE_DICT[row["TIPO_PACIENTE"]]
                row["NACIONALIDAD"] = NACIONALIDAD_DICT[row["NACIONALIDAD"]]
                row["RESULTADO_LAB"] = RESULTADO_LAB_DICT[row["RESULTADO_LAB"]]
                row["RESULTADO_ANTIGENO"] = RESULTADO_LAB_DICT[row["RESULTADO_ANTIGENO"]]
                row["CLASIFICACION_FINAL"] = CLASIFICACION_FINAL_DICT[row["CLASIFICACION_FINAL"]]

                # Yes or No fields.
                row["MIGRANTE"] = SI_NO_DICT[row["MIGRANTE"]]
                row["INTUBADO"] = SI_NO_DICT[row["INTUBADO"]]
                row["NEUMONIA"] = SI_NO_DICT[row["NEUMONIA"]]
                row["EMBARAZO"] = SI_NO_DICT[row["EMBARAZO"]]
                row["HABLA_LENGUA_INDIG"] = SI_NO_DICT[row["HABLA_LENGUA_INDIG"]]
                row["INDIGENA"] = SI_NO_DICT[row["INDIGENA"]]
                row["TOMA_MUESTRA_LAB"] = SI_NO_DICT[row["TOMA_MUESTRA_LAB"]]
                row["TOMA_MUESTRA_ANTIGENO"] = SI_NO_DICT[row["TOMA_MUESTRA_ANTIGENO"]]
                row["DIABETES"] = SI_NO_DICT[row["DIABETES"]]
                row["EPOC"] = SI_NO_DICT[row["EPOC"]]
                row["ASMA"] = SI_NO_DICT[row["ASMA"]]
                row["INMUSUPR"] = SI_NO_DICT[row["INMUSUPR"]]
                row["HIPERTENSION"] = SI_NO_DICT[row["HIPERTENSION"]]
                row["OTRA_COM"] = SI_NO_DICT[row["OTRA_COM"]]
                row["CARDIOVASCULAR"] = SI_NO_DICT[row["CARDIOVASCULAR"]]
                row["OBESIDAD"] = SI_NO_DICT[row["OBESIDAD"]]
                row["RENAL_CRONICA"] = SI_NO_DICT[row["RENAL_CRONICA"]]
                row["TABAQUISMO"] = SI_NO_DICT[row["TABAQUISMO"]]
                row["OTRO_CASO"] = SI_NO_DICT[row["OTRO_CASO"]]
                row["UCI"] = SI_NO_DICT[row["UCI"]]

                # Special case where a country is not defined.
                if str(row["PAIS_ORIGEN"]) == "99":
                    row["PAIS_ORIGEN"] = "NO ESPECIFICADO"

                # Fix encoding issues.
                for k, v in FIXERS.items():
                    row["PAIS_NACIONALIDAD"] = row["PAIS_NACIONALIDAD"].replace(
                        k, v).strip()

                data_list.append(row)

            print("CSV file processed.")

    with open("./mx_data.csv", "w", encoding="utf-8", newline="") as result_csv:
        writer = csv.DictWriter(result_csv, reader.fieldnames)
        writer.writeheader()
        writer.writerows(data_list)
        print("Dataset saved.")

    # Clean up.
    os.remove(DATA_FILE)
    os.remove(CATALOG_FILE)


if __name__ == "__main__":

    download()
    convert()
