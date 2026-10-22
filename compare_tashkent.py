import traci
import torch
import numpy as np
import matplotlib.pyplot as plt
from dql_agent import DQLAgent

STEPS = 600

def get_controllable_tls():
    all_tls = traci.trafficlight.getIDList()
    valid_tls = []
    for tls_id in all_tls:
        try:
            defs = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
            if defs and len(defs[0].phases) > 1:
                valid_tls.append((tls_id, len(defs[0].phases)))
        except Exception:
            pass
    return valid_tls

def get_advanced_state(tls_id):
    try:
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
        state_string = traci.trafficlight.getRedYellowGreenState(tls_id)
        green_q = 0
        red_q = 0
        approaching = 0
        for lane, state_char in zip(controlled_lanes, state_string):
            halting = traci.lane.getLastStepHaltingNumber(lane)
            total = traci.lane.getLastStepVehicleNumber(lane)
            approaching += (total - halting)
            if state_char in ['G', 'g']:
                green_q += halting
            elif state_char in ['r', 'R']:
                red_q += halting
        phase = traci.trafficlight.getPhase(tls_id)
        return [green_q, red_q, phase, approaching]
    except Exception:
        return [0, 0, 0, 0]

def run_default_tashkent():
    sumo_cmd = ["sumo", "-c", "tashkent_rush.sumocfg", "--no-warnings"]
    traci.start(sumo_cmd)
    tls_info = get_controllable_tls()
    queues = []
    for _ in range(STEPS):
        traci.simulationStep()
        total_q = sum(traci.lane.getLastStepHaltingNumber(l) for tls_id, _ in tls_info for l in set(traci.trafficlight.getControlledLanes(tls_id)))
        queues.append(total_q)
    traci.close()
    return queues

def run_sensor_tashkent():
    sumo_cmd = ["sumo", "-c", "tashkent_rush.sumocfg", "--no-warnings"]
    traci.start(sumo_cmd)
    tls_info = get_controllable_tls()
    queues = []
    for step in range(STEPS):
        if step % 5 == 0:
            for tls_id, num_phases in tls_info:
                st = get_advanced_state(tls_id)
                if st[1] > st[0] + 2:
                    curr_phase = traci.trafficlight.getPhase(tls_id)
                    try:
                        traci.trafficlight.setPhase(tls_id, (curr_phase + 1) % num_phases)
                    except Exception:
                        pass
        traci.simulationStep()
        total_q = sum(traci.lane.getLastStepHaltingNumber(l) for tls_id, _ in tls_info for l in set(traci.trafficlight.getControlledLanes(tls_id)))
        queues.append(total_q)
    traci.close()
    return queues

def run_madql_tashkent():
    agent = DQLAgent(state_dim=4, action_dim=2)
    agent.model.load_state_dict(torch.load("tashkent_madql_model.pth"))
    agent.model.eval()
    agent.epsilon = 0.0

    sumo_cmd = ["sumo", "-c", "tashkent_rush.sumocfg", "--no-warnings"]
    traci.start(sumo_cmd)
    tls_info = get_controllable_tls()
    queues = []
    step = 0

    while step < STEPS:
        for tls_id, num_phases in tls_info:
            state = get_advanced_state(tls_id)
            state_t = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                action = torch.argmax(agent.model(state_t)).item()
                
            if action == 1:
                curr_phase = traci.trafficlight.getPhase(tls_id)
                try:
                    traci.trafficlight.setPhase(tls_id, (curr_phase + 1) % num_phases)
                except Exception:
                    pass

        for _ in range(5):
            traci.simulationStep()
            total_q = sum(traci.lane.getLastStepHaltingNumber(l) for tls_id, _ in tls_info for l in set(traci.trafficlight.getControlledLanes(tls_id)))
            queues.append(total_q)
            step += 1
            if step >= STEPS:
                break

    traci.close()
    return queues

print("Запуск прогностического сравнения...")
default_q = run_default_tashkent()
sensor_q = run_sensor_tashkent()
madql_q = run_madql_tashkent()

avg_def = np.mean(default_q)
avg_sen = np.mean(sensor_q)
avg_madql = np.mean(madql_q)

print(f"\n=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")
print(f"Стандартные таймеры OSM: {avg_def:.2f} авто")
print(f"Датчики (Greedy):        {avg_sen:.2f} авто")
print(f"Multi-Agent DQL (ИИ):    {avg_madql:.2f} авто")

plt.figure(figsize=(11, 6))
plt.plot(default_q, label=f"Стандартные таймеры OSM ({avg_def:.1f})", color="red", alpha=0.6)
plt.plot(sensor_q, label=f"Датчики / Sensor ({avg_sen:.1f})", color="orange", linestyle="--")
plt.plot(madql_q, label=f"Predictive Multi-Agent DQL ({avg_madql:.1f})", color="green", linewidth=2.0)

plt.title("Сравнение алгоритмов с учетом прогностического потока")
plt.xlabel("Время (секунды)")
plt.ylabel("Суммарное число стоящих машин")
plt.legend()
plt.grid(True)
plt.savefig("tashkent_madql_comparison.png", dpi=300)
plt.show()