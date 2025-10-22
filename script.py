import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
import sys

if len(sys.argv) < 2:
    profile = 'watermullins'
    print(f"no argument, defaulting to {profile}'s profile")
else:
    profile = sys.argv[1]

base_url = f"https://letterboxd.com/{profile}/films/ratings"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def get_film_details(film_url):
    try:
        r = requests.get(film_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return "N/A", [], "N/A", []
        soup = BeautifulSoup(r.text, "html.parser")

        year_tag = soup.select_one("a[href*='/year/']")
        year = year_tag.get_text(strip=True) if year_tag else "N/A"
        director_tags = soup.select("a[href*='/director/']")
        directors = []
        for d in director_tags:
            name = d.get_text(strip=True)
            if name and name not in directors:
                directors.append(name)
        directors = directors[:1]

        meta = soup.find("meta", {"name": "twitter:data2"})
        if meta and "out of" in meta.get("content", ""):
            try:
                avg_rating = float(meta["content"].split(" ")[0])
            except Exception:
                avg_rating = "N/A"
        else:
            avg_rating = "N/A"

        genres = [
            g.get_text(strip=True)
            for g in soup.select("a[href*='/films/genre/']")
            if g.get_text(strip=True)
        ]

        return year, directors, avg_rating, genres
    except Exception:
        return "N/A", [], "N/A", []

start_time = time.time()
film_count = 0
my_rating_sum = 0
letterboxd_rating_sum = 0
films_data = []

with open("letterboxd_ratings.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Title", "Year", "Director", "Genres", "My Rating", "Letterboxd AVG"])
    page_number = 1
    while True:
        paged_url = f"{base_url}/page/{page_number}/"
        try:
            r = requests.get(paged_url, headers=headers, timeout=10)
        except Exception as e:
            print(f"Failed to fetch page {page_number}: {e}")
            break
        if r.status_code != 200:
            print(f"Reached non-200 status ({r.status_code}) at page {page_number}")
            break
        soup = BeautifulSoup(r.text, "html.parser")
        films = soup.find_all("li", class_="griditem")
        if not films:
            break
        for film in films:
            poster = film.find("div", attrs={"data-component-class": "LazyPoster"})
            if not poster:
                continue
            title = poster.get("data-item-name", "Unknown Title")
            rating_span = film.find("span", class_=re.compile(r"rated-\d+"))
            if rating_span:
                rating_class = next((cls for cls in rating_span["class"] if cls.startswith("rated-")), None)
                my_numeric_rating = int(rating_class.split("-")[1]) / 2 if rating_class else 0
            else:
                my_numeric_rating = 0
            # if my_numeric_rating == 0:
            #     continue
            film_slug = poster.get("data-item-slug")
            film_url = f"https://letterboxd.com/film/{film_slug}/"
            year, directors, avg_user_numeric, genres = get_film_details(film_url)
            # if avg_user_numeric == "N/A":
            #     continue
            print(f"Title: {title} | Year: {year} | Directors: {', '.join(directors)} | My: {my_numeric_rating}, Avg: {avg_user_numeric}, Genres: {', '.join(genres)}")
            writer.writerow([title, year, "; ".join(directors), ", ".join(genres), my_numeric_rating, avg_user_numeric])
            films_data.append({
                "title": title,
                "year": year,
                "directors": directors,
                "genres": genres,
                "my_rating": my_numeric_rating,
                "avg_user_rating": avg_user_numeric
            })
            film_count += 1
            my_rating_sum += my_numeric_rating
            letterboxd_rating_sum = 0
            # letterboxd_rating_sum += float(avg_user_numeric)
        page_number += 1
        time.sleep(0.1)

with open("letterboxd_ratings.json", "w", encoding="utf-8") as jsonfile:
    json.dump(films_data, jsonfile, ensure_ascii=False, indent=4)

elapsed = time.time() - start_time
print(f"\nElapsed time: {elapsed:.2f} seconds.")
if film_count:
    print(f"Average time per film: {elapsed/film_count:.2f} seconds.")
print("All scores adjusted to 5-point scale")
print(f"Film count: {film_count} films.")
if film_count:
    print(f"My average score: {my_rating_sum/film_count:.2f}")
    print(f"Letterboxd average score: {letterboxd_rating_sum/film_count:.2f}")