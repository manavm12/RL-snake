from agent import Agent
from game import SnakeGame
import matplotlib.pyplot as plt
from IPython import display

plt.ion()  # enable live plotting

def plot(scores, mean_scores):
    display.clear_output(wait=True)
    display.display(plt.gcf())
    plt.clf()
    plt.title('Training...')
    plt.xlabel('Number of Games')
    plt.ylabel('Score')
    plt.plot(scores)
    plt.plot(mean_scores)
    plt.ylim(ymin=0)
    plt.text(len(scores) - 1, scores[-1], str(scores[-1]))
    plt.text(len(mean_scores) - 1, mean_scores[-1], str(mean_scores[-1]))
    plt.show(block=False)
    plt.pause(.1)


def train():
    scores = []
    mean_scores = []
    total_score = 0
    record = 0

    agent = Agent()
    game = SnakeGame()

    while True:
        # 1️⃣ Get the current state
        state_old = game.get_state()

        # 2️⃣ Get the action from the agent
        final_move = agent.get_action(state_old)

        # 3️⃣ Perform the action in the environment
        reward, done, score = game.play_step(final_move)

        # 4️⃣ Get the new state after taking that action
        state_new = game.get_state()

        # 5️⃣ Train short memory (immediate feedback)
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # 6️⃣ Remember this experience for long-term replay
        agent.remember(state_old, final_move, reward, state_new, done)

        # 7️⃣ If the game is over, reset and train on long memory
        if done:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            # Save best performing model
            if score > record:
                record = score
                agent.model.save()

            # Print progress
            print(f'Game {agent.n_games} | Score: {score} | Record: {record}')

            # Update plot
            scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            mean_scores.append(mean_score)
            plot(scores, mean_scores)


if __name__ == '__main__':
    train()
