import os
import subprocess

# Генерируем интенсивный трафик с пиковой нагрузкой в середине симуляции
rou_content = """<routes>
    <vType id="car" accel="2.6" decel="4.5" length="5.0" minGap="2.5" maxSpeed="13.89"/>
    
    <!-- Равномерный основной поток -->
    <flow id="flow_main" type="car" begin="0" end="600" number="300" fromJunction="true"/>
    
    <!-- Всплеск трафика ("Час пик") с 150 по 450 секунду -->
    <flow id="flow_rush" type="car" begin="150" end="450" number="500" fromJunction="true"/>
</routes>"""

with open("tashkent_rush.rou.xml", "w") as f:
    f.write(rou_content)

sumocfg_content = """<configuration>
    <input>
        <net-file value="tashkent.net.xml"/>
        <route-files value="tashkent_rush.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="600"/>
    </time>
</configuration>"""

with open("tashkent_rush.sumocfg", "w") as f:
    f.write(sumocfg_content)

# Генерируем трипы
subprocess.run([
    "python", os.path.join(os.environ["SUMO_HOME"], "tools", "randomTrips.py"),
    "-n", "tashkent.net.xml",
    "-o", "tashkent_rush.trips.xml",
    "-r", "tashkent_rush.rou.xml",
    "-e", "600",
    "-p", "0.8",  # Выше плотность машин
    "-l"
], check=True)

print("Конфигурация 'Час пик' в Ташкенте успешно создана!")