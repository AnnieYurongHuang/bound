
import csv

# Assuming the CSV content is stored in a file named "movies.csv"
file_path = "movies_metadata.csv"

# Read the CSV and extract movie names
movie_names = []

with open(file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        movie_names.append(row["title"])

# Write the list of movie names to a file
with open("movie_names.txt", "w", encoding="utf-8") as outfile:
    for name in movie_names:
        outfile.write(name + "\n")

# print(movie_names)