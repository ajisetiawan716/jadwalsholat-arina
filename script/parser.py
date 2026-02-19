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


def strip_lower(s):
    return re.sub(r'\W+', '', s).lower()


def get_cities():

    page = requests.get(base_url + '/brebes')
    html_text = page.text

    matches = re.findall(r'href="https://jadwalsholat\.arina\.id/([^"]+)"', html_text)

    cities = {}

    for slug in matches:
        if slug not in cities:
            cities[slug] = slug

    print("Total cities found:", len(cities))

    return cities


# ===============================
# PARSE JSON FROM wire:snapshot
# ===============================
def get_adzans(city_slug):

    url = f"{base_url}/{city_slug}"
    page = requests.get(url)
    doc = html.fromstring(page.content)

    snapshot = doc.xpath('//div[@wire:id]/@wire:snapshot')

    if not snapshot:
        print(f"no snapshot for {city_slug}")
        return []

    snapshot_json = snapshot[0]
    snapshot_json = snapshot_json.replace('&quot;', '"')

    data = json.loads(snapshot_json)
    prayer_data = data['data']['prayerTimes'][0]

    result = []

    for tanggal, val in prayer_data.items():
        times = val[0]

        dt = datetime.strptime(tanggal, "%d-%m-%Y")

        result.append({
            'tanggal': dt.strftime("%Y-%m-%d"),
            'imsyak': times.get('Imsak'),
            'shubuh': times.get('Fajr'),
            'terbit': times.get('Sunrise'),
            'dhuha': times.get('Dhuhr'),
            'dzuhur': times.get('Dhuhr'),
            'ashr': times.get('Asr'),
            'magrib': times.get('Maghrib'),
            'isya': times.get('Isha')
        })

    return result


# ===============================
# WRITE FILE (SAMA FORMAT REPO)
# ===============================
def write_file(city, adzans):

    if not adzans:
        return

    flb = './jadwal/' + city + '/'

    year = adzans[0]['tanggal'][:4]
    month = adzans[0]['tanggal'][5:7]

    fld = flb + year

    if not os.path.exists(fld):
        os.makedirs(fld, mode=0o777)

    with open(fld + '/' + month + '.json', 'w+') as fl:
        fl.write(json.dumps(adzans))


def process_city(slug, name):
    print("processing", name)
    adzans = get_adzans(slug)
    write_file(name, adzans)
    print("done", name)


def main():

    start = time.time()
    cities = get_cities()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for slug, name in cities.items():
            futures.append(executor.submit(process_city, slug, name))

        for future in concurrent.futures.as_completed(futures):
            pass

    cities = get_cities()
    print(cities)

    print("\nTook", time.time()-start, "seconds.")

    print('\n It took', time.time() - start, 'seconds.')

    print("\n Current working dir:")
    print(os.getcwd())

    print("\n List dir:")
    print(os.listdir(os.getcwd()))

    print("\n Git status:")
    os.system('git status --porcelain')

if __name__ == "__main__":
    main()
