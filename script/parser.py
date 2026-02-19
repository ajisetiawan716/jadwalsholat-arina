#!/usr/bin/env python3

import os
import re
import json
import time
import pytz
import requests
import concurrent.futures
from lxml import html
from datetime import datetime

tz = pytz.timezone('Asia/Jakarta')
base_url = 'https://jadwalsholat.arina.id'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ===============================
# UTILITY
# ===============================
def strip_lower(s):
    return re.sub(r'\W+', '', s).lower()


# ===============================
# GET ALL CITIES
# ===============================
def get_cities():

    page = requests.get(base_url + '/brebes', headers=HEADERS)
    doc = html.fromstring(page.content)

    links = doc.xpath('//a[contains(@href,"jadwalsholat.arina.id/")]')

    cities = {}

    for link in links:
        href = link.get("href")
        if not href:
            continue

        slug = href.split("/")[-1]

        # filter valid slug (hindari rss, images, dll)
        if slug and not slug.endswith('.xml') and not slug.endswith('.webp'):
            cities[slug] = strip_lower(slug)

    print("Total cities found:", len(cities))

    return cities


# ===============================
# GET MONTHLY PRAYER TIMES
# ===============================
def get_adzans(city_slug):

    url = f"{base_url}/{city_slug}"
    page = requests.get(url, headers=HEADERS)

    if page.status_code != 200:
        print("FAILED:", city_slug, page.status_code)
        return []

    doc = html.fromstring(page.content)

    snapshot = doc.xpath('//div[contains(@wire:snapshot)]/@wire:snapshot')

    if not snapshot:
        print("NO SNAPSHOT:", city_slug)
        return []

    snapshot_json = snapshot[0].replace('&quot;', '"')

    try:
        data = json.loads(snapshot_json)
    except Exception as e:
        print("JSON ERROR:", city_slug, e)
        return []

    if "prayerTimes" not in data["data"]:
        print("NO PRAYER DATA:", city_slug)
        return []

    prayer_data = data["data"]["prayerTimes"][0]

    result = []

    for tanggal, val in prayer_data.items():

        times = val[0]

        dt = datetime.strptime(tanggal, "%d-%m-%Y")

        result.append({
            "tanggal": dt.strftime("%Y-%m-%d"),
            "imsyak": times.get("Imsak"),
            "shubuh": times.get("Fajr"),
            "terbit": times.get("Sunrise"),
            "dhuha": None,
            "dzuhur": times.get("Dhuhr"),
            "ashr": times.get("Asr"),
            "magrib": times.get("Maghrib"),
            "isya": times.get("Isha")
        })

    print("OK:", city_slug, len(result))

    return result


# ===============================
# WRITE FILE (SAME STRUCTURE)
# ===============================
def write_file(city, adzans):

    if not adzans:
        return

    flb = './adzan/' + city + '/'

    year = adzans[0]['tanggal'][:4]
    month = adzans[0]['tanggal'][5:7]

    fld = flb + year

    if not os.path.exists(fld):
        os.makedirs(fld, mode=0o777)

    file_path = fld + '/' + month + '.json'

    with open(file_path, 'w', encoding='utf-8') as fl:
        fl.write(json.dumps(adzans, ensure_ascii=False))

    print("WROTE:", file_path)


# ===============================
# PROCESS EACH CITY
# ===============================
def process_city(slug, name):
    print("Processing:", slug)
    adzans = get_adzans(slug)
    write_file(name, adzans)


# ===============================
# MAIN
# ===============================
def main():

    start = time.time()

    cities = get_cities()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for slug, name in cities.items():
            futures.append(executor.submit(process_city, slug, name))

        for future in concurrent.futures.as_completed(futures):
            pass

    print("\nTook", time.time()-start, "seconds.")
    print("\nCurrent working dir:", os.getcwd())
    print("\nList dir:", os.listdir(os.getcwd()))
    print("\nGit status:")
    os.system('git status --porcelain')


if __name__ == "__main__":
    main()
