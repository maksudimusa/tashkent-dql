import traci
import torch
from dql_agent import DQLAgent

# Загружаем прогностическую нейросеть
agent = DQLAgent(state_dim=4, action_dim=2)
agent.model.load_state_dict(torch.load("tashkent_madql_model.pth"))
agent.model.eval()
agent.epsilon = 0.0

# Запускаем GUI с замедлением --delay 150 (чтобы комфортно наблюдать за машинами)
sumo_cmd = ["sumo-gui", "-c", "tashkent_rush.sumocfg", "--start", "--delay", "150"]
traci.start(sumo_cmd)

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
        green_q, red_q, approaching = 0, 0, 0
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

tls_info = get_controllable_tls()
step = 0

print("=== Запуск интерактивной визуализации ИИ в Ташкенте ===")

while step < 600:
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
        step += 1
        if step >= 600:
            break

traci.close()