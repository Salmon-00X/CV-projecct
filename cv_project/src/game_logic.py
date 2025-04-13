import random
import pygame

class GameLogic:
    def __init__(self):
        self.player_score = 0
        self.ai_score = 0
        self.bonus_points = 0
        self.power_ups = 0
        self.mode_difficulty = {"easy": 0.0, "normal": 0.5, "impossible": 1.0}
        self.last_gesture = "rock"
        self.last_ai_move = "rock"
        self.last_outcome = "Draw"
        self.move_history = []
        self.start_time = 0
        self.game_duration = 0

    def initialize_game(self, mode):
        self.player_score = 0
        self.ai_score = 0
        self.bonus_points = 0
        self.power_ups = 0
        self.move_history = []
        self.start_time = pygame.time.get_ticks()
        self.game_duration = 0
        print(f"✅ Game initialized in {mode} mode")

    def get_ai_move(self, player_gesture, mode):
        moves = ["rock", "paper", "scissors"]
        self.move_history.append(player_gesture)
        self.last_gesture = player_gesture

        if mode == "easy":
            ai_move = random.choice(moves)
        elif mode == "normal":
            # 50% random, 50% counter based on history
            if random.random() < self.mode_difficulty["normal"] and len(self.move_history) >= 2:
                move_counts = {m: self.move_history.count(m) for m in moves}
                most_frequent = max(move_counts, key=move_counts.get)
                ai_move = {"rock": "paper", "paper": "scissors", "scissors": "rock"}[most_frequent]
            else:
                ai_move = random.choice(moves)
        else:  # impossible mode
            # 90% chance to counter the most frequent move
            if random.random() < self.mode_difficulty["impossible"] and len(self.move_history) >= 2:
                move_counts = {m: self.move_history.count(m) for m in moves}
                most_frequent = max(move_counts, key=move_counts.get)
                ai_move = {"rock": "paper", "paper": "scissors", "scissors": "rock"}[player_gesture]
            else:
                ai_move = random.choice(moves)

        self.last_ai_move = ai_move
        return ai_move

    def evaluate_round(self, player_gesture, ai_move):
        outcome = "Draw"
        if player_gesture == ai_move:
            outcome = "Draw"
        elif (player_gesture == "rock" and ai_move == "scissors") or \
             (player_gesture == "paper" and ai_move == "rock") or \
             (player_gesture == "scissors" and ai_move == "paper"):
            outcome = "Win"
        else:  # All other cases where AI wins
            outcome = "Lose"
        self.last_outcome = outcome
        print(f"Evaluating round: Player: {player_gesture}, AI: {ai_move}, Outcome: {outcome}")
        return outcome

    def update_scores(self, outcome, gesture, objects, alignments):
        if outcome == "Win":
            self.player_score += 1 + sum(alignments)
            self.bonus_points += 1
        elif outcome == "Lose":
            self.ai_score += 1
        self.power_ups += len(objects)

        # Update game duration
        current_time = pygame.time.get_ticks()
        self.game_duration = (current_time - self.start_time) // 1000

    def get_scores(self):
        return [self.player_score, self.ai_score]

    def get_bonus_points(self):
        return self.bonus_points

    def get_power_ups(self):
        return self.power_ups

    def get_game_duration(self):
        minutes = self.game_duration // 60
        seconds = self.game_duration % 60
        return f"{minutes:02d}:{seconds:02d}"

    def is_game_over(self):
        return False