import torch
from collections import namedtuple
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

Transition = namedtuple('Transition', ('reward', 'action_prob'))


class MLPPolicy(nn.Module):
    def __init__(self, d_state, d_hidden, d_action):
        super(MLPPolicy, self).__init__()
        self.linear1 = nn.Linear(d_state, d_hidden)
        self.linear2 = nn.Linear(d_hidden, d_action)
        self.head = nn.Softmax(dim=1)

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = self.linear2(x)
        return self.head(x)


class VPGAgent:
    def __init__(self, device, lr, gamma=0.99):
        self.replay_buffer = []
        self.time_step = 0
        self.policy_net = None
        self.device = device
        self.gamma = torch.tensor([gamma], device=device)
        self.optimizer = None
        self.lr = lr

    def act(self, state):
        self.time_step += 1
        action_probs = self.policy_net(state)
        action = torch.multinomial(action_probs, 1)
        action_prob = action_probs.gather(1, action)
        return action, action_prob

    def memorize(self, reward, action_prob):
        reward = torch.tensor([reward]).to(self.device)
        self.replay_buffer.append(Transition(reward, action_prob))
        return

    def learn(self):
        if self.optimizer is None:
            self.optimizer = optim.RMSprop(self.policy_net.parameters(), lr=self.lr)
        self.optimizer.zero_grad()
        accumulative_loss = 0
        total_return = 0
        for t, transition in enumerate(reversed(self.replay_buffer)):
            total_return *= self.gamma
            total_return += transition.reward
            loss = - torch.log(transition.action_prob) * total_return
            accumulative_loss += loss
            loss.backward(retain_graph=True)
        self.optimizer.step()
        self.replay_buffer.clear()
        return accumulative_loss
