#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://jadwalsholat.arina.id/"
OUTPUT_DIR = "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; arina-scraper/1.0)"
}

PRAYER_KEYS = ["imsak", "subuh", "dzuhur", "ashar", "maghrib", "isya"]


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text


def get_all_locations():
    html = fetch(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    locations = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") and len(href) > 2:
            slug = href.strip("/")
            if "/" not in slug:
                locations.add(slug)

    return sorted(locations)


def parse_month_and_year(soup):
    title = soup.find("h3")
    if not title:
        return None, None

    text = title.get_text(strip=True)
    match = re.search(r"Bulan\s+(\w+)\s+(\d{4})", text)

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

    bulan = bulan_map.get(bulan_text, None)
    return bulan, tahun


def parse_table(soup):
    table = soup.find("table")
    if not table:
        return []

    rows = table.find("tbody").find_all("tr")
    data = []

    for row in rows:
        tanggal = row.find("th").get_text(strip=True)
        cols = [td.get_text(strip=True) for td in row.find_all("td")]

        if len(cols) == 6:
            data.append({
                "tanggal": tanggal,
                "imsak": cols[0],
                "subuh": cols[1],
                "dzuhur": cols[2],
                "ashar": cols[3],
                "maghrib": cols[4],
                "isya": cols[5]
            })

    return data


def save_json(city, year, month, data):
    path = os.path.join(OUTPUT_DIR, city, str(year))
    os.makedirs(path, exist_ok=True)

    filename = os.path.join(path, f"{month:02d}.json")

    output = {
        "kota": city,
        "tahun": year,
        "bulan": month,
        "data": data
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def scrape_city(city):
    url = urljoin(BASE_URL, city)
    print("Scraping:", city)

    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    month, year = parse_month_and_year(soup)

    if not month or not year:
        print("Gagal baca bulan/tahun:", city)
        return

    data = parse_table(soup)

    if data:
        save_json(city, year, month, data)
        print(f"Saved: {city}/{year}/{month:02d}.json")
    else:
        print("Tidak ada data tabel:", city)


def main():
    cities = get_all_locations()
    print("Total kota ditemukan:", len(cities))

    for city in cities:
        try:
            scrape_city(city)
        except Exception as e:
            print("Error:", city, e)


if __name__ == "__main__":
    main()
