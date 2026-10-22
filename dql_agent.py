import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque

# 1. Архитектура нейросети (Q-Network)
class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(QNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.fc(x)

# 2. Агент Deep Q-Learning
class DQLAgent:
    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.memory = deque(maxlen=2000)
        
        # Гиперпараметры DQL
        self.gamma = 0.95        # Коэффициент дисконтирования
        self.epsilon = 1.0       # Исследование (Exploration)
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32
        
        # Нейросеть и оптимизатор
        self.model = QNetwork(state_dim, action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

    def select_action(self, state):
        # Epsilon-Greedy выбор действия
        if random.random() <= self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        state_t = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.model(state_t)
        return torch.argmax(q_values).item()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states_t = torch.FloatTensor(states)
        actions_t = torch.LongTensor(actions).unsqueeze(1)
        rewards_t = torch.FloatTensor(rewards)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones)

        # Вычисление Q(s, a)
        q_values = self.model(states_t).gather(1, actions_t).squeeze(1)
        
        # Вычисление Target Q = r + gamma * max(Q(s', a'))
        with torch.no_grad():
            max_next_q = self.model(next_states_t).max(1)[0]
            target_q = rewards_t + (1 - dones_t) * self.gamma * max_next_q

        loss = self.criterion(q_values, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay