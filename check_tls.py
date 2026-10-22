import traci

sumo_cmd = ["sumo", "-c", "tashkent.sumocfg", "--no-warnings"]
traci.start(sumo_cmd)

# Получаем список всех светофоров на карте Ташкента
tls_list = traci.trafficlight.getIDList()

print(f"\nНайдено светофоров на карте Ташкента: {len(tls_list)}")
print(f"Список ID светофоров: {tls_list}")

traci.close()