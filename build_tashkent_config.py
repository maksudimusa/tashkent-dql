import subprocess
import traci
import os

# 1. Создаем файлы маршрутов для реальной сети
rou_content = """<routes>
    <vType id="car" accel="2.6" decel="4.5" length="5.0" minGap="2.5" maxSpeed="13.89"/>
    
    <!-- Потоки транспорта через участок -->
    <flow id="flow_main1" type="car" begin="0" end="1000" number="400" fromJunction="true"/>
    <flow id="flow_main2" type="car" begin="0" end="1000" number="300" fromJunction="true"/>
</routes>"""

# 2. Создаем конфигурационный файл SUMO
sumocfg_content = """<configuration>
    <input>
        <net-file value="tashkent.net.xml"/>
        <route-files value="tashkent.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="1000"/>
    </time>
</configuration>"""

with open("tashkent.sumocfg", "w") as f:
    f.write(sumocfg_content)

# Автоматически генерируем случайные валидные маршруты по дорогам Ташкента
subprocess.run([
    "python", os.path.join(os.environ["SUMO_HOME"], "tools", "randomTrips.py"),
    "-n", "tashkent.net.xml",
    "-o", "tashkent.trips.xml",
    "-r", "tashkent.rou.xml",
    "-e", "1000",
    "-l"
], check=True)

print("Конфигурация Ташкента готова!")