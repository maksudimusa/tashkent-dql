import os
import traci
import torch
import numpy as np
from dql_agent import DQLAgent

# State: [зеленый_затор, красный_затор, фаза, приближающиеся_машины]
STATE_DIM = 4
ACTION_DIM = 2
EPISODES = 25
STEPS_PER_EPISODE = 600

agent = DQLAgent(STATE_DIM, ACTION_DIM)
sumo_cmd = ["sumo", "-c", "tashkent_rush.sumocfg", "--no-warnings"]

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

# Добавляем считывание движущегося потока (approaching vehicles)
def get_advanced_state(tls_id):
    try:
        controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
        state_string = traci.trafficlight.getRedYellowGreenState(tls_id)
        
        green_q = 0
        red_q = 0
        approaching = 0
        
        for lane, state_char in zip(controlled_lanes, state_string):
            halting = traci.lane.getLastStepHaltingNumber(lane)
            # Машины, которые едут (не стоят), но подезжают к перекрестку
            total_on_lane = traci.lane.getLastStepVehicleNumber(lane)
            approaching += (total_on_lane - halting)
            
            if state_char in ['G', 'g']:
                green_q += halting
            elif state_char in ['r', 'R']:
                red_q += halting
                
        phase = traci.trafficlight.getPhase(tls_id)
        return [green_q, red_q, phase, approaching]
    except Exception:
        return [0, 0, 0, 0]

print("=== Обучение predictive-DQL с учетом приближающегося потока ===")

for episode in range(EPISODES):
    traci.start(sumo_cmd)
    tls_info = get_controllable_tls()
    total_reward = 0
    
    for step in range(STEPS_PER_EPISODE):
        states = {}
        actions = {}
        
        for tls_id, num_phases in tls_info:
            state = get_advanced_state(tls_id)
            states[tls_id] = state
            actions[tls_id] = agent.select_action(state)

        for tls_id, num_phases in tls_info:
            if actions[tls_id] == 1:
                curr_phase = traci.trafficlight.getPhase(tls_id)
                try:
                    traci.trafficlight.setPhase(tls_id, (curr_phase + 1) % num_phases)
                except Exception:
                    pass

        for _ in range(5):
            traci.simulationStep()

        episode_step_reward = 0
        for tls_id, num_phases in tls_info:
            next_state = get_advanced_state(tls_id)
            # Награда с штрафом за резкое накопление очередей
            reward = -(next_state[0] + next_state[1] * 1.2)
            episode_step_reward += reward
            
            done = step == STEPS_PER_EPISODE - 1
            agent.remember(states[tls_id], actions[tls_id], reward, next_state, done)
            agent.train_step()

        total_reward += episode_step_reward

    traci.close()
    print(f"Эпоха {episode + 1}/{EPISODES} | Награда: {total_reward:.2f} | Epsilon: {agent.epsilon:.3f}")

torch.save(agent.model.state_dict(), "tashkent_madql_model.pth")
print("\nПрогностическая модель сохранена!")