#!/usr/bin/env python3

import os
import re
import json
import time
import pytz
import shutil
import requests
import concurrent.futures
from lxml import html
from datetime import datetime, timedelta

tz = pytz.timezone('Asia/Jakarta')
base_url = 'https://jadwalsholat.arina.id'

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===============================
# DETECT CURRENT & NEXT MONTH
# ===============================
def get_target_months():
    now = datetime.now(tz)

    current_month = f"{now.month:02d}"
    current_year = str(now.year)

    first_day_next = (now.replace(day=1) + timedelta(days=32)).replace(day=1)

    next_month = f"{first_day_next.month:02d}"
    next_year = str(first_day_next.year)

    return [
        (current_month, current_year),
        (next_month, next_year)
    ]


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

        if slug and not slug.endswith('.xml') and not slug.endswith('.webp'):
            cities[slug] = slug

    print("Total cities found:", len(cities))

    return cities


# ===============================
# GET MONTHLY DATA
# ===============================
def get_adzans(city_slug, month, year):

    url = f"{base_url}/{city_slug}?month={month}&year={year}"
    page = requests.get(url, headers=HEADERS)

    if page.status_code != 200:
        print("FAILED:", city_slug, page.status_code)
        return []

    match = re.search(r'wire:snapshot="(.*?)"\s', page.text)

    if not match:
        print("NO SNAPSHOT:", city_slug)
        return []

    snapshot_json = match.group(1).replace('&quot;', '"')

    try:
        data = json.loads(snapshot_json)
    except Exception as e:
        print("JSON ERROR:", city_slug, e)
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

    print("OK:", city_slug, month, len(result))

    return result


# ===============================
# WRITE FILE (NO OVERWRITE)
# ===============================
def write_file(city, adzans, month, year):

    if not adzans:
        return

    folder_path = f'./jadwal/{city}/{year}'
    os.makedirs(folder_path, exist_ok=True)

    file_path = f"{folder_path}/{month}.json"

    # Skip kalau sudah ada
    if os.path.exists(file_path):
        print("SKIP (exists):", file_path)
        return

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(adzans, f, ensure_ascii=False)

    print("WROTE:", file_path)


# ===============================
# CLEANUP OLD YEARS (KEEP 2)
# ===============================
def cleanup_old_years():

    base_path = './jadwal'

    if not os.path.exists(base_path):
        return

    for city in os.listdir(base_path):

        city_path = os.path.join(base_path, city)

        if not os.path.isdir(city_path):
            continue

        years = sorted([
            y for y in os.listdir(city_path)
            if y.isdigit()
        ])

        # keep max 2 tahun
        if len(years) > 2:
            oldest = years[0]
            remove_path = os.path.join(city_path, oldest)
            shutil.rmtree(remove_path)
            print("REMOVED OLD YEAR:", remove_path)


# ===============================
# PROCESS CITY
# ===============================
def process_city(slug, targets):

    print("Processing:", slug)

    for month, year in targets:

        adzans = get_adzans(slug, month, year)
        write_file(slug, adzans, month, year)

        time.sleep(0.1)  # anti rate-limit


# ===============================
# MAIN
# ===============================
def main():

    start = time.time()

    targets = get_target_months()
    print("Generating for:", targets)

    cities = get_cities()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for slug in cities.keys():
            futures.append(executor.submit(process_city, slug, targets))

        for future in concurrent.futures.as_completed(futures):
            pass

    cleanup_old_years()

    print("\nTook", time.time()-start, "seconds.")
    print("\nGit status:")
    os.system('git status --porcelain')


if __name__ == "__main__":
    main()