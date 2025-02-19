import csv
articles = {"title1": ("link1", "date1"), "title2": ("link2", "date2"), "title3": ("link3", "date3")}
 # Write each article as a row
with open("articles.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "link", "date"]  # Column headers
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()  # Write the header row
        for title, (link, date) in articles.items():
             writer.writerow({"title": title, "link": link, "date": date}) 
print("Articles saved to articles.csv")