import pygame
import json
import os
import cv2
import numpy as np
from pygame import mixer
from gtts import gTTS
from pygame.sprite import Sprite
from tempfile import NamedTemporaryFile
import playsound
import math

class Particle(Sprite):
    def __init__(self, x, y, color, screen, particle_type="circle"):
        super().__init__()
        self.screen = screen
        self.particle_type = particle_type
        if particle_type == "circle":
            self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(self.image, color, (4, 4), 4)
        elif particle_type == "sparkle":
            self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, color, [(5, 0), (7, 3), (10, 5), (7, 7), (5, 10), (3, 7), (0, 5), (3, 3)])
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = [np.random.uniform(-4, 4), np.random.uniform(-6, -2)]
        self.lifetime = 60
        self.angle = np.random.uniform(0, 2 * math.pi)
        self.speed = np.random.uniform(3, 6)

    def update(self):
        self.rect.x += math.cos(self.angle) * self.speed
        self.rect.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        self.image.set_alpha(max(0, int(255 * self.lifetime / 60)))
        if self.lifetime <= 0 or not self.screen.get_rect().collidepoint(self.rect.center):
            self.kill()

    def alive(self):
        return self.lifetime > 0

class BackgroundParticle(Sprite):
    """Floating particles for dynamic background."""
    def __init__(self, screen):
        super().__init__()
        self.image = pygame.Surface((5, 5), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 100), (3, 3), 3)
        self.rect = self.image.get_rect(center=(np.random.randint(0, 800), np.random.randint(0, 600)))
        self.velocity = [np.random.uniform(-1, 1), np.random.uniform(-1, 1)]
        self.screen = screen

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if self.rect.x < 0 or self.rect.x > 800 or self.rect.y < 0 or self.rect.y > 600:
            self.rect.x = np.random.randint(0, 800)
            self.rect.y = np.random.randint(0, 600)

class UI:
    def __init__(self):
        # Load assets with fallbacks
        try:
            self.button_img = pygame.image.load(os.path.join("assets", "sprites", "button.png")).convert_alpha()
        except pygame.error as e:
            print(f"❌ Failed to load button.png: {e}")
            self.button_img = pygame.Surface((100, 50))
            self.button_img.fill((255, 255, 255))

        try:
            self.background_img = pygame.image.load(os.path.join("assets", "sprites", "background.png")).convert()
        except pygame.error as e:
            print(f"❌ Failed to load background.png: {e}")
            self.background_img = pygame.Surface((800, 600))
            self.background_img.fill((0, 0, 50))

        mixer.init()
        self.click_sound = mixer.Sound(os.path.join("assets", "sounds", "click.wav"))
        self.laugh_sound = mixer.Sound(os.path.join("assets", "sounds", "laugh.wav"))
        self.cheer_sound = mixer.Sound(os.path.join("assets", "sounds", "cheer.wav"))

        self.achievements = {}
        self.level = 1
        self.avatar_trail = []
        self.font = pygame.font.Font(None, 40)
        self.large_font = pygame.font.Font(None, 60)
        self.small_font = pygame.font.Font(None, 30)
        self.emojis = {}
        emoji_files = {"rock": "rock.png", "paper": "paper.png", "scissors": "scissors.png"}
        for gesture, filename in emoji_files.items():
            try:
                self.emojis[gesture] = pygame.image.load(os.path.join("assets", "emojis", filename)).convert_alpha()
            except pygame.error as e:
                print(f"❌ Failed to load {filename}: {e}")
                self.emojis[gesture] = pygame.Surface((50, 50))
                self.emojis[gesture].fill((255, 0, 0))

        # Background particles for dynamic effect
        self.bg_particles = pygame.sprite.Group()
        for _ in range(20):
            self.bg_particles.add(BackgroundParticle(screen=pygame.display.get_surface()))

    def show_main_menu(self, screen):
        buttons = [("Start", 300, 200), ("Leaderboard", 300, 300), ("Quit", 300, 400)]
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for text, x, y in buttons:
                        button = self._draw_animated_button(screen, text, x, y)
                        if button.collidepoint(event.pos):
                            self.click_sound.play()
                            return text.lower()
            screen.blit(self.background_img, (0, 0))
            for text, x, y in buttons:
                self._draw_animated_button(screen, text, x, y, color=(255, 255, 0))
            pygame.display.flip()
            pygame.time.delay(10)

    def show_leaderboard(self, screen):
        screen.blit(self.background_img, (0, 0))
        with open(os.path.join("assets", "leaderboard.json"), "r") as f:
            leaderboard = json.load(f)
        y = 100
        for player, score in sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:5]:
            text = self.font.render(f"{player}: {score}", True, (255, 215, 0))
            screen.blit(text, (300, y))
            y += 60
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.MOUSEBUTTONDOWN:
                    return

    def start_round(self, screen, round_number):
        """Display a round start animation."""
        screen.fill((20, 20, 60))
        text = self.large_font.render(f"Round {round_number}", True, (255, 215, 0))
        screen.blit(text, (400 - text.get_width() // 2, 300 - text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(1000)

    def render_countdown(self, screen, seconds):
        """Render the countdown before each round."""
        screen.fill((20, 20, 60))
        text = self.large_font.render(f"{seconds + 1}", True, (255, 215, 0))
        screen.blit(text, (400 - text.get_width() // 2, 300 - text.get_height() // 2))
        pygame.display.flip()

    def render_status(self, screen, status_text, hand_tracking, gesture):
        """Render the current game state status with webcam feed."""
        screen.fill((20, 20, 60))
        text = self.large_font.render(status_text, True, (255, 215, 0))
        screen.blit(text, (400 - text.get_width() // 2, 200))

        # Display webcam feed
        if hand_tracking:
            frame = pygame.surfarray.make_surface(hand_tracking.get_flipped_frame().swapaxes(0, 1))
            screen.blit(pygame.transform.scale(frame, (300, 200)), (250, 300))

        # Display detected gesture if available
        if gesture:
            gesture_text = self.font.render(f"Detected: {gesture}", True, (0, 255, 0))
            screen.blit(gesture_text, (300, 520))

        self.bg_particles.update()
        self.bg_particles.draw(screen)
        pygame.display.flip()

    def show_round_result(self, screen, outcome, scores):
        """Display the winner and scores for the round."""
        screen.fill((20, 20, 60))
        result_text = self.large_font.render(f"{outcome}!", True, 
                                            (0, 255, 0) if outcome == "Win" else (255, 0, 0) if outcome == "Lose" else (255, 255, 255))
        score_text = self.font.render(f"You: {scores[0]} | AI: {scores[1]}", True, (255, 255, 255))
        screen.blit(result_text, (400 - result_text.get_width() // 2, 250))
        screen.blit(score_text, (400 - score_text.get_width() // 2, 320))

        # Fade-out effect
        fade_surface = pygame.Surface((800, 600))
        fade_surface.fill((0, 0, 0))
        for alpha in range(0, 255, 5):
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(20)

    def render_game_state(self, screen, gesture, ai_move, outcome, ai_avatar, hand_tracking, game_logic, particles, mode, objects, alignments, object_detector, face_coordinates):
        # Dynamic gradient background
        for y in range(600):
            r = 20 + (y / 600) * 30
            g = 20 + (y / 600) * 60
            b = 60 + (y / 600) * 90
            pygame.draw.line(screen, (r, g, b), (0, y), (800, y))

        # Update and draw background particles
        self.bg_particles.update()
        self.bg_particles.draw(screen)

        # Draw glowing borders
        pygame.draw.rect(screen, (0, 255, 255), (40, 40, 320, 270), 4, border_radius=15)
        pygame.draw.rect(screen, (255, 0, 255), (440, 40, 320, 270), 4, border_radius=15)

        # Camera feed
        frame = pygame.surfarray.make_surface(hand_tracking.get_flipped_frame().swapaxes(0, 1))
        screen.blit(pygame.transform.scale(frame, (300, 200)), (250, 350))

        # Player Section
        pygame.draw.rect(screen, (30, 30, 80), (50, 50, 300, 250), border_radius=10)
        gesture_img = self.emojis.get(gesture, self.emojis["rock"])
        gesture_img = pygame.transform.scale(gesture_img, (100, 100))
        screen.blit(gesture_img, (150, 80))
        text = self.font.render("Your Move", True, (0, 255, 255))
        screen.blit(text, (150, 200))

        # AI Section
        pygame.draw.rect(screen, (30, 30, 80), (450, 50, 300, 250), border_radius=10)
        ai_img = self.emojis.get(ai_move, self.emojis["rock"])
        ai_img = pygame.transform.scale(ai_img, (100, 100))
        screen.blit(ai_img, (550, 80))
        text = self.font.render("AI Move", True, (255, 0, 255))
        screen.blit(text, (550, 200))

        # Outcome
        color = (255, 215, 0) if outcome == "Win" else (255, 0, 0) if outcome == "Lose" else (255, 255, 255)
        outcome_text = self.large_font.render(outcome, True, color)
        screen.blit(outcome_text, (400 - outcome_text.get_width() // 2, 300))

        # Player Avatar (moved to left side, same size as gesture)
        if face_coordinates:
            try:
                frame_slice = hand_tracking.get_frame()[face_coordinates[1]:face_coordinates[1]+face_coordinates[3], face_coordinates[0]:face_coordinates[0]+face_coordinates[2]]
                if frame_slice.shape[0] > 0 and frame_slice.shape[1] > 0:
                    player_face = pygame.surfarray.make_surface(cv2.resize(frame_slice, (100, 100)).swapaxes(0, 1))
                    screen.blit(player_face, (50, 80))  # Left side
                else:
                    raise ValueError("Invalid face coordinates or empty frame slice")
            except Exception as e:
                print(f"⚠️ Failed to render player face: {e}")
                # Fallback: render a placeholder
                placeholder = pygame.Surface((100, 100))
                placeholder.fill((255, 0, 0))
                screen.blit(placeholder, (50, 80))
        else:
            print("⚠️ face_coordinates not provided, skipping player face render")

        # AI Avatar (moved to right side, same size as gesture)
        ai_avatar_resized = pygame.surfarray.make_surface(cv2.resize(ai_avatar, (100, 100)).swapaxes(0, 1))
        screen.blit(ai_avatar_resized, (650, 80))  # Right side

        # Scores with Progress Bars
        scores = game_logic.get_scores()
        pygame.draw.rect(screen, (50, 50, 50), (10, 10, 200, 20))  # Player score background
        pygame.draw.rect(screen, (0, 255, 255), (10, 10, (scores[0] / 5) * 200, 20))  # Player score progress
        pygame.draw.rect(screen, (50, 50, 50), (590, 10, 200, 20))  # AI score background
        pygame.draw.rect(screen, (255, 0, 255), (590, 10, (scores[1] / 5) * 200, 20))  # AI score progress
        score_text = self.small_font.render(f"You: {scores[0]}", True, (0, 255, 255))
        screen.blit(score_text, (10, 40))
        ai_score_text = self.small_font.render(f"AI: {scores[1]}", True, (255, 0, 255))
        screen.blit(ai_score_text, (590, 40))

        # Timer
        time_text = self.small_font.render(f"Time: {game_logic.get_game_duration()}", True, (255, 255, 255))
        screen.blit(time_text, (350, 10))

        # Mode
        mode_text = self.small_font.render(f"Mode: {mode.capitalize()}", True, (255, 215, 0))
        screen.blit(mode_text, (350, 40))

        # Particles
        for particle in particles:
            screen.blit(particle.image, particle.rect)

    def create_particles(self, outcome, screen):
        particles = []
        x, y = 400, 300
        color = (0, 255, 0) if outcome == "Win" else (255, 0, 0)
        particle_type = "sparkle" if outcome == "Win" else "circle"
        for _ in range(20):
            particles.append(Particle(x, y, color, screen, particle_type))
        return particles

    def show_game_over(self, screen, scores, player_name, game_duration):
        screen.fill((20, 20, 60))
        winner = "You Won!" if scores[0] > scores[1] else "AI Won!"
        title = self._get_achievement_title(scores[0])
        text = self.large_font.render(f"{winner} {player_name} - {title}", True, (255, 215, 0))
        duration_text = self.font.render(f"Game Duration: {game_duration}", True, (255, 255, 255))
        screen.blit(text, (250, 250))
        screen.blit(duration_text, (300, 350))
        confetti = self.create_particles("Win", screen)
        for _ in range(120):
            for particle in confetti:
                particle.update()
            screen.blit(text, (250, 250))
            screen.blit(duration_text, (300, 350))
            for particle in confetti:
                screen.blit(particle.image, particle.rect)
            pygame.display.flip()
            pygame.time.delay(33)
        self._speak(f"Game over! {winner} Your score: {scores[0]}")
        pygame.time.delay(2000)

    def update_leaderboard(self, player_name, scores):
        leaderboard_path = os.path.join("assets", "leaderboard.json")
        if os.path.exists(leaderboard_path):
            with open(leaderboard_path, "r") as f:
                leaderboard = json.load(f)
        else:
            leaderboard = {}
        leaderboard[player_name] = max(leaderboard.get(player_name, 0), scores[0])
        with open(leaderboard_path, "w") as f:
            json.dump(leaderboard, f)

    def update_achievements(self, player_name, scores):
        score = scores[0]
        achievements = ["Rock Novice", "Paper Master", "Scissors Pro", "Spectral Champion"]
        thresholds = [10, 20, 30, 50]
        for ach, thresh in zip(achievements, thresholds):
            if score >= thresh and ach not in self.achievements:
                self.achievements[ach] = True
                self._speak(f"Achievement unlocked: {ach}!")

    def _get_achievement_title(self, score):
        if score >= 50: return "Spectral Champion"
        if score >= 30: return "Scissors Pro"
        if score >= 20: return "Paper Master"
        if score >= 10: return "Rock Novice"
        return "Beginner"

    def get_modes(self):
        return ["Random", "Normal", "Impossible"]

    def _draw_animated_button(self, screen, text, x, y, color=(255, 255, 255)):
        button_rect = self.button_img.get_rect(center=(x, y))
        scale = 1 + 0.1 * abs(pygame.time.get_ticks() % 1000 / 500 - 1)
        scaled_button = pygame.transform.scale(self.button_img, (int(self.button_img.get_width() * scale), int(self.button_img.get_height() * scale)))
        scaled_rect = scaled_button.get_rect(center=(x, y))
        screen.blit(scaled_button, scaled_rect)
        text_surface = self.font.render(text, True, color)
        screen.blit(text_surface, (x - text_surface.get_width() // 2, y - text_surface.get_height() // 2))
        return scaled_rect

    def _speak(self, text):
        try:
            with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts = gTTS(text=text, lang='en')
                tts.save(temp_file.name)
                playsound.playsound(temp_file.name)
            os.unlink(temp_file.name)
        except Exception as e:
            print(f"Voice feedback failed: {e}")