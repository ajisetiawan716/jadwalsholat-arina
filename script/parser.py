#!/usr/bin/env python3
# Parser untuk jadwalsholat.arina.id
# Jalankan dari root folder repo:
# python3 script/parser.py

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
base_url = 'https://jadwalsholat.arina.id/'


def strip_lower(s):
    return re.sub(r'\W+', '', s).lower()


def get_cities():
    """
    Ambil semua slug kota dari homepage arina
    """
    page = requests.get(base_url)
    doc = html.fromstring(page.content)

    links = doc.xpath('//a/@href')
    cities = {}

    for link in links:
        if link.startswith('/') and len(link) > 2:
            slug = link.strip('/')
            if '/' not in slug:
                cities[slug] = slug

    return cities


def parse_month_year(doc):
    """
    Ambil bulan & tahun dari <h3>
    """
    title = doc.xpath('//h3/text()')
    if not title:
        return None, None

    match = re.search(r'Bulan\s+(\w+)\s+(\d{4})', title[0])
    if not match:
        return None, None

    bulan_text = match.group(1)
    tahun = int(match.group(2))

    bulan_map = {
        "Januari": 1, "Februari": 2, "Maret": 3,
        "April": 4, "Mei": 5, "Juni": 6,
        "Juli": 7, "Agustus": 8, "September": 9,
        "Oktober": 10, "November": 11, "Desember": 12
    }

    bulan = bulan_map.get(bulan_text)

    return bulan, tahun


def get_adzans(city):
    """
    Parse 1 bulan penuh dari kota
    """
    url = base_url + city
    page = requests.get(url)
    doc = html.fromstring(page.content)

    month, year = parse_month_year(doc)

    if not month or not year:
        print(f"Gagal baca bulan/tahun: {city}")
        return None, None, []

    rows = doc.xpath('//tbody/tr')

    result = []

    for row in rows:
        tanggal = row.xpath('.//th/text()')
        times = row.xpath('.//td/text()')

        if len(tanggal) == 1 and len(times) == 6:
            result.append({
                'tanggal': tanggal[0],
                'imsak': times[0],
                'subuh': times[1],
                'dzuhur': times[2],
                'ashar': times[3],
                'maghrib': times[4],
                'isya': times[5]
            })

    return month, year, result


def write_file(city, month, year, adzans):

    if not adzans:
        return

    base_folder = './jadwal/' + city + '/'
    year_folder = base_folder + str(year)

    if not os.path.exists(year_folder):
        os.makedirs(year_folder, mode=0o777)

    file_path = year_folder + '/' + f"{month:02d}.json"

    with open(file_path, 'w+') as f:
        f.write(json.dumps(adzans, indent=2))

    print(f"Saved: {city}/{year}/{month:02d}.json")


def process_city(name):

    month, year, adzans = get_adzans(name)

    if adzans:
        write_file(name, month, year, adzans)

    print('processing ' + name + ' done')


def main():

    start = time.time()
    cities = get_cities()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for name in cities.keys():
            print('processing ' + name)
            futures.append(executor.submit(process_city, name=name))
        for future in concurrent.futures.as_completed(futures):
            pass

    print('\n It took', time.time() - start, 'seconds.')

    print("\n Current working dir:")
    print(os.getcwd())

    print("\n List dir:")
    print(os.listdir(os.getcwd()))

    print("\n Git status:")
    os.system('git status --porcelain')


if __name__ == "__main__":
    main()
