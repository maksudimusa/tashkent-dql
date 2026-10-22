import urllib.request
import subprocess
import os

# Координаты фрагмента проспекта Амира Темура в Ташкенте (bbox: min_lon, min_lat, max_lon, max_lat)
bbox = "69.278,41.312,69.288,41.325"
osm_url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"

print("1. Скачиваем реальную карту Ташкента из OpenStreetMap...")
urllib.request.urlretrieve(osm_url, "tashkent.osm")
print("   Карта успешно загружена в tashkent.osm!")

print("2. Конвертируем карту в формат SUMO (.net.xml)...")
subprocess.run([
    "netconvert",
    "--osm-files=tashkent.osm",
    "-o", "tashkent.net.xml",
    "--geometry.remove",
    "--ramps.guess",
    "--junctions.join",
    "--tls.discard-simple",
    "--tls.join"
], check=True)

print("   Сеть Ташкента успешно создана: tashkent.net.xml")