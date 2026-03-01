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
    "User-Agent": "Mozilla/5.0"
}

REQUEST_TIMEOUT = 15
MAX_WORKERS = 4
RETRY_COUNT = 3


# ===============================
# GET ALL CITIES
# ===============================
def get_cities():

    try:
        page = requests.get(base_url + '/brebes', headers=HEADERS, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print("FAILED FETCH CITY LIST:", e)
        return {}

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
# GET MONTHLY SCHEDULE
# ===============================
def get_schedule(city_slug):

    url = f"{base_url}/{city_slug}"

    for attempt in range(RETRY_COUNT):

        try:
            page = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            print("REQUEST ERROR:", city_slug, e)
            time.sleep(1)
            continue

        if page.status_code != 200:
            print("FAILED:", city_slug, page.status_code)
            return []

        html_text = page.text

        match = re.search(r'wire:snapshot="(.*?)"\s', html_text)

        print("FOUND SNAPSHOT?", city_slug, bool(match))

        if not match:
            time.sleep(1)
            continue

        snapshot_raw = match.group(1)
        snapshot_json = snapshot_raw.replace('&quot;', '"')

        try:
            data = json.loads(snapshot_json)
        except Exception as e:
            print("JSON ERROR:", city_slug, e)
            return []

        if "prayerTimes" not in data["data"]:
            print("NO PRAYER DATA:", city_slug)
            return []

        prayer_data = data["data"]["prayerTimes"][0]

        schedules = []

        for tanggal in sorted(prayer_data.keys()):

            val = prayer_data[tanggal]
            times = val[0]

            dt = datetime.strptime(tanggal, "%d-%m-%Y")

            schedules.append({
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

        print("OK:", city_slug, len(schedules))
        return schedules

    print("FAILED AFTER RETRY:", city_slug)
    return []


# ===============================
# WRITE FILE
# ===============================
def write_file(city_slug, schedules):
    """
    Menyimpan file jadwal ke folder berdasarkan slug kota
    dengan menghapus tanda strip (-)
    """
    if not schedules:
        return

    # Hapus tanda strip dari slug untuk nama folder
    folder_city = city_slug.replace('-', '')

    year = schedules[0]['tanggal'][:4]
    month = schedules[0]['tanggal'][5:7]

    folder_path = f'./jadwal/{folder_city}/{year}'
    os.makedirs(folder_path, exist_ok=True)

    file_path = f"{folder_path}/{month}.json"

    if os.path.exists(file_path):
        print("SKIP (exists):", file_path)
        return

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False)

    print("WROTE:", file_path)


# ===============================
# PROCESS EACH CITY
# ===============================
def process_city(slug):
    print("Processing:", slug)
    schedules = get_schedule(slug)
    if schedules:
        write_file(slug, schedules)
    else:
        print("No data for:", slug)


# ===============================
# MAIN
# ===============================
def main():

    start = time.time()

    cities = get_cities()

    if not cities:
        print("No cities found. Exit.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_city, slug) for slug in cities.keys()]

        for future in concurrent.futures.as_completed(futures):
            pass

    print("\nTook", time.time()-start, "seconds.")
    print("\nCurrent working dir:", os.getcwd())
    print("\nGit status:")
    os.system('git status --porcelain')


if __name__ == "__main__":
    main()