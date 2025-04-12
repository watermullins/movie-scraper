import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import re
import sys

if len(sys.argv) < 2:
    print("no argument, defaulting to watermullins' profile")
    profile = 'watermullins'
else:
    profile = sys.argv[1]

base_url = f"https://letterboxd.com/{profile}/films/ratings"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def get_api_key():
    try:
        with open('api_key.txt', 'r') as file:
            key = file.read().strip()
            return key
    except FileNotFoundError:
        print("Missing the file called api_key.txt with your API key for www.omdbapi.com")
    sys.exit(1)

api_key = get_api_key()

def get_imdb_id(film_url):
    response = requests.get(film_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        imdb_link = soup.find("a", href=re.compile(r"^http://www.imdb.com/title/tt"))
        if imdb_link:
            imdb_id = imdb_link["href"].split("/")[4]
            return imdb_id
    return None

def get_imdb_rating(imdb_id):
    url = f'http://www.omdbapi.com/?i={imdb_id}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    if data.get('Response') == 'True':
        imdb_rating = data.get('imdbRating', '0')
        try:
            return float(imdb_rating)
        except ValueError:
            return 0
    return 0

start_time = time.time()
films_data = []

with open("letterboxd_ratings.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Title", "My Rating", "Letterboxd AVG", "IMDb AVG"])

    page_number = 1
    while True:
        paged_url = f"{base_url}/page/{page_number}/"
        response = requests.get(paged_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            films = soup.find_all("li", class_="poster-container")

            if not films:
                print("No films found on this page. Exiting.")
                break

            for film in films:
                img_tag = film.find("img")
                title = img_tag["alt"] if img_tag else "Unknown Title"

                rating_tag = film.find("span", class_=re.compile(r"rated-\d+"))
                if rating_tag:
                    class_names = rating_tag.get("class", [])
                    rating_class = next((cls for cls in class_names if cls.startswith("rated-")), None)
                    my_numeric_rating = int(rating_class.split("-")[1]) / 2 if rating_class else 0
                else:
                    my_numeric_rating = 0

                if my_numeric_rating == 0:
                    continue

                film_div = film.find("div", class_="really-lazy-load")
                film_slug = film_div["data-film-slug"] if film_div and "data-film-slug" in film_div.attrs else None

                if film_slug:
                    film_url = f"https://letterboxd.com/film/{film_slug}/"
                    imdb_id = get_imdb_id(film_url)
                    imdb_rating = get_imdb_rating(imdb_id) if imdb_id else 0

                    film_response = requests.get(film_url, headers=headers)
                    if film_response.status_code == 200:
                        film_soup = BeautifulSoup(film_response.text, 'html.parser')
                        avg_rating_tag = film_soup.find("meta", {"name": "twitter:data2"})
                        if avg_rating_tag and "out of" in avg_rating_tag["content"]:
                            avg_user_numeric = float(avg_rating_tag["content"].split(" ")[0])
                        else:
                            avg_user_numeric = "N/A"

                        print(f"{title}: My Rating: {my_numeric_rating}, Average Rating: {avg_user_numeric}, IMDb Rating: {imdb_rating}")
                        writer.writerow([title, my_numeric_rating, avg_user_numeric, imdb_rating])
                        films_data.append({
                            "title": title,
                            "my_rating": my_numeric_rating,
                            "avg_user_rating": avg_user_numeric,
                            "imdb_rating": imdb_rating
                        })
                    else:
                        print(f"  → Failed to get film page: {film_response.status_code}")
                        writer.writerow([title, my_numeric_rating, "N/A", imdb_rating])

                        films_data.append({
                            "title": title,
                            "my_rating": my_numeric_rating,
                            "avg_user_rating": "N/A",
                            "imdb_rating": imdb_rating
                        })
                else:
                    print(f"  → No slug found for {title}. Skipping.")
                    writer.writerow([title, my_numeric_rating, "N/A", "N/A"])

                    films_data.append({
                        "title": title,
                        "my_rating": my_numeric_rating,
                        "avg_user_rating": "N/A",
                        "imdb_rating": "N/A"
                    })

                time.sleep(0.1)

            page_number += 1
        else:
            print(f"Failed to get ratings page. Status: {response.status_code}")
            break

with open("letterboxd_ratings.json", "w", encoding="utf-8") as jsonfile:
    json.dump(films_data, jsonfile, ensure_ascii=False, indent=4)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Scraping complete. Elapsed time: {elapsed_time:.2f} seconds.")
