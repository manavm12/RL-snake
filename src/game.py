import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()

# Constants 
BLOCK_SIZE = 20
SPEED = 10  # frames per second

# Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Direction Enum
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

# Coordinate Struct
Point = namedtuple("Point", "x, y")


# Main Game Class
class SnakeGame:
    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Snake Game")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 25)

        self.reset()

    def reset(self):
        self.direction = Direction.RIGHT
        self.head = Point(self.w // 2, self.h // 2)
        self.snake = [self.head,
                      Point(self.head.x - BLOCK_SIZE, self.head.y),
                      Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()

    def _place_food(self):
        x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()

    def play_step(self, action):
        # 1. Move → update the direction based on agent's action
        self._move_agent(action)
        self.snake.insert(0, self.head)

        # 2. Check if game over
        reward = 0
        game_over = False
        if self._is_collision():
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # 3. Check if food eaten
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            self.snake.pop()  # move tail normally

        # 4. Update UI & clock
        self._update_ui()
        self.clock.tick(SPEED)

        # 5. Small step penalty to encourage efficiency
        reward += -0.1

        # 6. Return results for RL loop
        return reward, game_over, self.score


    def _is_collision(self):
        # Hit boundaries
        if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
            return True
        # Hit itself
        if self.head in self.snake[1:]:
            return True
        return False
    
    def _is_collision_point(self, pt):
        # Check wall collision
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            return True
        # Check self collision
        if pt in self.snake[1:]:
            return True
        return False


    def _update_ui(self):
        self.display.fill(BLACK)

        for pt in self.snake:
            pygame.draw.rect(self.display, BLUE, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, GREEN, pygame.Rect(pt.x + 4, pt.y + 4, 12, 12))

        pygame.draw.rect(self.display, RED, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.display.blit(score_text, [10, 10])
        pygame.display.flip()

    def _move(self):
        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE

        self.head = Point(x, y)
    
    def _move_agent(self, action):
        """
        Action: [straight, right turn, left turn]
        """
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]  # straight
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # right turn
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # left turn

        self.direction = new_dir

        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE

        self.head = Point(x, y)


    def get_state(self):
        head = self.snake[0]

        # Points immediately around the head (relative positions)
        point_l = Point(head.x - BLOCK_SIZE, head.y)
        point_r = Point(head.x + BLOCK_SIZE, head.y)
        point_u = Point(head.x, head.y - BLOCK_SIZE)
        point_d = Point(head.x, head.y + BLOCK_SIZE)

        # Current direction
        dir_l = self.direction == Direction.LEFT
        dir_r = self.direction == Direction.RIGHT
        dir_u = self.direction == Direction.UP
        dir_d = self.direction == Direction.DOWN

        # Dangers (relative to current direction)
        danger_straight = (
            (dir_r and self._is_collision_point(point_r)) or
            (dir_l and self._is_collision_point(point_l)) or
            (dir_u and self._is_collision_point(point_u)) or
            (dir_d and self._is_collision_point(point_d))
        )

        danger_right = (
            (dir_u and self._is_collision_point(point_r)) or
            (dir_d and self._is_collision_point(point_l)) or
            (dir_l and self._is_collision_point(point_u)) or
            (dir_r and self._is_collision_point(point_d))
        )

        danger_left = (
            (dir_d and self._is_collision_point(point_r)) or
            (dir_u and self._is_collision_point(point_l)) or
            (dir_r and self._is_collision_point(point_u)) or
            (dir_l and self._is_collision_point(point_d))
        )

        # Direction one-hot (4 values)
        direction_left = dir_l
        direction_right = dir_r
        direction_up = dir_u
        direction_down = dir_d

        # Food location relative to head (4 values)
        food_left = self.food.x < head.x
        food_right = self.food.x > head.x
        food_up = self.food.y < head.y
        food_down = self.food.y > head.y

        # Return numpy array (int form)
        state = np.array([
            int(danger_straight),
            int(danger_right),
            int(danger_left),
            int(direction_left),
            int(direction_right),
            int(direction_up),
            int(direction_down),
            int(food_left),
            int(food_right),
            int(food_up),
            int(food_down)
        ], dtype=int)

        return state

if __name__ == "__main__":
    game = SnakeGame()

    while True:
        action = np.random.choice([0, 1, 2])  # 0=straight, 1=right, 2=left
        action_vec = [0, 0, 0]
        action_vec[action] = 1

        reward, game_over, score = game.play_step(action_vec)
        print(f"Reward: {reward}, Score: {score}")

        if game_over:
            print("Game Over! Final Score:", score)
            break
