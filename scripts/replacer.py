import os
import zipfile


os.replace("./global_data.csv", "../data/global_data.csv")
print("Replaced global file.")

with zipfile.ZipFile("./mx_data.zip", "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
    print("Compressing Mexico file.")
    zip_file.write("mx_data.csv")

os.replace("./mx_data.zip", "../data/mx_data.zip")
os.remove("./mx_Data.csv")
print("Replaced Mexico file.")