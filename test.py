import numpy as np
import random
import os
import multiprocessing
import gymnasium as gym
import matplotlib.pyplot as plt


def discretize_state(state, bins):
    state_bins = [
        np.linspace(-1.0, 1.0, bins),  # cos(theta1)
        np.linspace(-1.0, 1.0, bins),  # sin(theta1)
        np.linspace(-1.0, 1.0, bins),  # cos(theta2)
        np.linspace(-1.0, 1.0, bins),  # sin(theta2)
        np.linspace(-12.0, 12.0, bins),  # angular velocity 1
        np.linspace(-28.0, 28.0, bins),  # angular velocity 2
    ]
    discretized = tuple(
        np.digitize(state[i], state_bins[i]) - 1 for i in range(len(state))
    )
    return discretized


def init_q_table(state_bins, action_space):
    Qtable = np.zeros(state_bins + [action_space])
    return Qtable


def greedy_policy(Qtable, state):
    return np.argmax(Qtable[state])


def ucb_policy(Qtable, state, total_steps, c=2.0):
    actions = range(len(Qtable[state]))  # Get the actions available
    visit_counts = np.sum(Qtable[state] > 0, axis=0)  # Count visits for each action
    ucb_values = []

    # Calculate UCB for each action
    for a in actions:
        # Avoid division by zero by adding a small constant to visit counts
        visit_count = visit_counts + 1e-5
        exploitation = Qtable[state][a]  # Exploit the value from the Q-table
        exploration = c * np.sqrt(np.log(total_steps + 1) / visit_count)  # UCB Exploration term
        ucb_values.append(exploitation + exploration)

    # Return the action with the highest UCB value
    return np.argmax(ucb_values)

def boltzmann_policy(Qtable, state, tau):
    q_values = Qtable[state]
    exp_values = np.exp(q_values / tau)
    probabilities = exp_values / np.sum(exp_values)
    if np.isnan(probabilities).any():
        return np.random.random_integers(0, 1)
    return np.random.choice(len(q_values), p=probabilities)


def save_q_table(Qtable, filename="q_table.npy"):
    np.save(filename, Qtable)
    print(f"Q-table saved to {filename}")


def train_episode(strategy, tau, learning_rate, env, max_steps, Qtable, total_steps, c_value):
    gamma = 0.99
    obs, _ = env.reset()
    state = discretize_state(obs, 10)
    total_reward = 0

    for step in range(max_steps):
        if strategy == "greedy":
            action = greedy_policy(Qtable, state)
        elif strategy == "ucb":
            action = ucb_policy(Qtable, state, total_steps, c_value)
        elif strategy == "boltzmann":
            action = boltzmann_policy(Qtable, state, tau)

        new_state, reward, terminated, done, _ = env.step(action)
        new_state = discretize_state(new_state, 10)

        Qtable[state][action] = Qtable[state][action] + learning_rate * (
            reward + gamma * np.max(Qtable[new_state]) - Qtable[state][action]
        )

        state = new_state
        total_reward += reward

        if terminated or done:
            break

        total_steps += 1

    return Qtable, total_reward, total_steps


def test_model(Qtable, env, n_eval):
    env = gym.make("Acrobot-v1", render_mode="human")

    rewards = []
    for _ in range(n_eval):
        obs, _ = env.reset()
        state = discretize_state(obs, 10)
        total_reward = 0
        done = False

        while not done:
            action = greedy_policy(Qtable, state)
            new_state, reward, terminated, done, _ = env.step(action)
            state = discretize_state(new_state, 10)
            total_reward += reward

        rewards.append(total_reward)

    return rewards


def load_q_table(filename="q_table.npy"):
    if os.path.exists(filename):
        return np.load(filename)
    else:
        print(f"No saved Q-table found at {filename}. Returning a new Q-table.")
        return None

if __name__ == "__main__":
    env = gym.make("Acrobot-v1")
    action_space = env.action_space.n
    state_bins = [10] * 6
    Q_table = load_q_table()
    rewards = test_model(Q_table, env, 10)

    plt.plot(rewards)
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.title("Total Reward per Episode")
    plt.show()
    