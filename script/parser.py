#!/usr/bin/env python3

import os
import re
import json
import time
import pytz
import shutil
import requests
import concurrent.futures
from datetime import datetime
from lxml import html

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

        # Filter valid kota saja
        if slug and not slug.endswith('.xml') and not slug.endswith('.webp'):
            cities[slug] = strip_lower(slug)

    print("Total cities found:", len(cities))

    return cities


# ===============================
# GET MONTHLY PRAYER TIMES
# ===============================
def get_adzans(city_slug, month, year):

    url = f"{base_url}/{city_slug}?month={month}&year={year}"
    page = requests.get(url, headers=HEADERS)

    if page.status_code != 200:
        print("FAILED:", city_slug, month, year)
        return []

    html_text = page.text

    match = re.search(r'wire:snapshot="(.*?)"\s', html_text)

    if not match:
        print("NO SNAPSHOT:", city_slug, month)
        return []

    snapshot_json = match.group(1).replace('&quot;', '"')

    try:
        data = json.loads(snapshot_json)
    except Exception as e:
        print("JSON ERROR:", city_slug, month, e)
        return []

    if "prayerTimes" not in data["data"]:
        print("NO PRAYER DATA:", city_slug, month)
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
# WRITE FILE
# ===============================
def write_file(city, adzans):

    if not adzans:
        return

    base_folder = './jadwal/' + city + '/'

    year = adzans[0]['tanggal'][:4]
    month = adzans[0]['tanggal'][5:7]

    folder_path = base_folder + year

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, mode=0o777)

    file_path = folder_path + '/' + month + '.json'

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(adzans, ensure_ascii=False))

    print("WROTE:", file_path)


# ===============================
# PROCESS EACH CITY (12 BULAN)
# ===============================
def process_city(slug, name):

    current_year = datetime.now().year

    for month in range(1, 13):

        month_str = f"{month:02d}"
        year_str = str(current_year)

        adzans = get_adzans(slug, month_str, year_str)

        write_file(name, adzans)

        # delay kecil supaya tidak diblokir server
        time.sleep(0.15)


# ===============================
# MAIN
# ===============================
def main():

    start = time.time()

    # Optional: hapus folder lama biar bersih
    if os.path.exists('./jadwal'):
        shutil.rmtree('./jadwal')

    cities = get_cities()

    # Worker kecil supaya aman dari rate-limit
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
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