import pygame
import os
import numpy as np
import cv2
import traceback
import time
import json

from src.hand_tracking import HandTracking
from src.image_processing import ImageProcessing
from src.game_logic import GameLogic
from src.ui import UI
from src.object_detection import ObjectDetector
from src.player_registration import run_player_registration
from src.avatar_selection import run_avatar_selection

def show_mode_selection(screen, ui):
    """Display mode selection UI with enhanced visuals."""
    modes = ui.get_modes()
    buttons = [(mode, 300, 200 + i * 100) for i, mode in enumerate(modes)]
    print(f"✅ Displaying mode selection with buttons: {buttons}")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("⚠️ Mode selection: Quit event detected")
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for text, x, y in buttons:
                    button = ui._draw_animated_button(screen, text, x, y)
                    if button.collidepoint(event.pos):
                        ui.click_sound.play()
                        print(f"✅ Mode selected: {text.lower()}")
                        return text.lower()
        try:
            screen.blit(pygame.image.load(os.path.join("assets", "sprites", "background.png")), (0, 0))
        except pygame.error as e:
            print(f"❌ Failed to load background.png: {e}")
            screen.fill((0, 0, 50))
        for text, x, y in buttons:
            ui._draw_animated_button(screen, text, x, y, color=(255, 215, 0) if text == "Impossible" else (255, 255, 255))
        pygame.display.flip()
        pygame.time.delay(10)

def fade_transition(screen, direction="in"):
    """Add a fade-in/fade-out transition."""
    fade_surface = pygame.Surface((800, 600))
    fade_surface.fill((0, 0, 0))
    for alpha in range(0, 255, 5) if direction == "in" else range(255, -5, -5):
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(20)

def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("AR Spectral Showdown")

    hand_tracking = HandTracking()
    image_processing = ImageProcessing()
    game_logic = GameLogic()
    ui = UI()
    object_detector = ObjectDetector()

    leaderboard_path = os.path.join("assets", "leaderboard.json")
    if not os.path.exists(leaderboard_path):
        with open(leaderboard_path, "w") as f:
            json.dump({}, f)

    try:
        pygame.mixer.music.load(os.path.join("assets", "sounds", "music.mp3"))
        pygame.mixer.music.play(-1)
        print("✅ Music loaded and playing")
    except pygame.error as e:
        print(f"❌ Failed to load music: {e}")
        pygame.mixer.music = None

    while True:
        current_state = ui.show_main_menu(screen)
        print(f"✅ Menu action: {current_state}")
        if current_state == "start":
            try:
                player_name, face_coordinates = run_player_registration()
                print(f"✅ Player registration: {player_name}, Coordinates: {face_coordinates}")
                if player_name and face_coordinates:
                    frame = hand_tracking.get_frame()
                    if frame is not None:
                        try:
                            face_image = frame[face_coordinates[1]:face_coordinates[1]+face_coordinates[3], face_coordinates[0]:face_coordinates[0]+face_coordinates[2]]
                            image_processing.save_face(face_image, player_name)
                            print("✅ Face image saved")
                        except Exception as e:
                            print(f"⚠️ Warning: Could not extract face image: {e}, proceeding without saving")
                    else:
                        print("⚠️ Warning: No frame available for face extraction, proceeding without saving")

                    time.sleep(1)
                    max_retries = 2
                    for attempt in range(max_retries):
                        player_name, ai_avatar = run_avatar_selection(image_processor=image_processing)
                        print(f"✅ Avatar selection: {player_name}, Avatar: {ai_avatar is not None}")
                        if ai_avatar is not None:
                            mode = show_mode_selection(screen, ui)
                            print(f"✅ Mode selection returned: {mode}")
                            if mode and mode != "quit":
                                fade_transition(screen, "out")
                                play_game(screen, player_name, ai_avatar, mode, hand_tracking, game_logic, ui, object_detector, clock, face_coordinates)
                                fade_transition(screen, "in")
                                ui.show_game_over(screen, game_logic.get_scores(), player_name, game_logic.get_game_duration())
                                ui.update_leaderboard(player_name, game_logic.get_scores())
                                print("✅ Game over and leaderboard updated")
                            break
                        else:
                            print(f"❌ Avatar selection failed, retrying (attempt {attempt + 1}/{max_retries})...")
                            time.sleep(1)
                    if ai_avatar is None:
                        print("❌ Avatar selection failed after all retries, returning to main menu")
                else:
                    print("❌ Player registration or face detection failed")
            except Exception as e:
                print(f"❌ Error in start sequence: {e}")
                project_root = os.path.dirname(os.path.abspath(__file__))
                error_log_path = os.path.join(project_root, "error_log.txt")
                with open(error_log_path, "a") as f:
                    f.write(f"Error in start sequence: {e}\n{traceback.format_exc()}\n")
        elif current_state == "leaderboard":
            ui.show_leaderboard(screen)
            print("✅ Leaderboard displayed")
        elif current_state == "quit":
            print("✅ Quitting application")
            break
        clock.tick(60)

    pygame.quit()

def play_game(screen, player_name, ai_avatar, mode, hand_tracking, game_logic, ui, object_detector, clock, face_coordinates):
    game_logic.initialize_game(mode)
    particles = []
    print(f"✅ Starting game with mode: {mode}")
    frame_skip = 3 if mode == "easy" or mode == "impossible" else 5  # Increase frame_skip for Normal mode
    frame_counter = 0
    round_active = False
    round_number = 0

    # Load gameplay music with fallback
    gameplay_music_loaded = False
    try:
        pygame.mixer.music.load(os.path.join("assets", "sounds", "gameplay_music.mp3"))
        pygame.mixer.music.play(-1)
        gameplay_music_loaded = True
        print("✅ Gameplay music loaded and playing")
    except pygame.error as e:
        print(f"⚠️ Failed to load gameplay_music.mp3: {e}, continuing without music")

    # Load countdown sound with fallback
    countdown_sound = None
    try:
        countdown_sound = pygame.mixer.Sound(os.path.join("assets", "sounds", "countdown_tick.wav"))
        print("✅ Countdown sound loaded")
    except pygame.error as e:
        print(f"⚠️ Failed to load countdown_tick.wav: {e}, continuing without sound")

    while True:
        try:
            frame_counter += 1

            # State machine for round flow
            if not round_active:
                round_number += 1
                ui.start_round(screen, round_number)
                detection_start = pygame.time.get_ticks()
                input_start = 0
                ai_start = 0
                outcome_start = 0
                current_state = "detection"
                round_active = True

            if current_state == "detection":
                ui.render_status(screen, "Detecting Hand...", hand_tracking, None)
                pygame.display.flip()
                clock.tick(60)
                if frame_counter % frame_skip == 0:
                    gesture, _ = hand_tracking.detect_gesture(mode)
                    if gesture != "rock" and gesture != "unknown":
                        input_start = pygame.time.get_ticks()
                        current_state = "input"
                        print(f"✅ Hand detected, starting input phase: {gesture}")
                if pygame.time.get_ticks() - detection_start > 5000:
                    input_start = pygame.time.get_ticks()
                    current_state = "input"
                    print("⚠️ Detection timeout, proceeding to input phase")

            elif current_state == "input":
                elapsed_time = (pygame.time.get_ticks() - input_start) // 1000
                remaining_time = max(0, 3 - elapsed_time)
                ui.render_status(screen, f"Choose Move... ({remaining_time}s)", hand_tracking, gesture)
                pygame.display.flip()
                clock.tick(60)
                if frame_counter % frame_skip == 0:
                    gesture, _ = hand_tracking.detect_gesture(mode)
                if elapsed_time >= 3:
                    ai_start = pygame.time.get_ticks()
                    current_state = "ai_response"
                    print(f"✅ Input phase ended, gesture: {gesture}")

            elif current_state == "ai_response":
                ui.render_status(screen, "AI Thinking...", hand_tracking, gesture)
                pygame.display.flip()
                clock.tick(60)
                if frame_counter % frame_skip == 0:
                    ai_move = game_logic.get_ai_move(gesture, mode)
                    print(f"✅ AI Move: {ai_move}")
                    outcome = game_logic.evaluate_round(gesture, ai_move)
                    game_logic.update_scores(outcome, gesture, [], [])
                    outcome_start = pygame.time.get_ticks()
                    current_state = "outcome"
                    particles.extend(ui.create_particles(outcome, screen))
                    if outcome == "Win":
                        ui.cheer_sound.play()
                    elif outcome == "Lose":
                        ui.laugh_sound.play()

            elif current_state == "outcome":
                ui.render_game_state(screen, gesture, ai_move, outcome, ai_avatar, hand_tracking, game_logic, particles, mode, [], [], object_detector, face_coordinates)
                if pygame.time.get_ticks() - outcome_start < 2000:
                    pygame.display.flip()
                    clock.tick(60)
                else:
                    ui.show_round_result(screen, outcome, game_logic.get_scores())
                    pygame.display.flip()
                    pygame.time.delay(2000)
                    round_active = False
                    current_state = "detection"

            for particle in particles[:]:
                particle.update()
                if not particle.alive():
                    particles.remove(particle)

            # Check for 5 wins
            scores = game_logic.get_scores()
            if scores[0] >= 5 or scores[1] >= 5:
                print("✅ Game over after 5 wins reached")
                break
        except Exception as e:
            print(f"❌ Error in game loop: {e}")
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt"), "a") as f:
                f.write(f"Error in game loop: {e}\n{traceback.format_exc()}\n")
            break

    # Stop gameplay music and reload menu music
    if gameplay_music_loaded:
        try:
            pygame.mixer.music.load(os.path.join("assets", "sounds", "music.mp3"))
            pygame.mixer.music.play(-1)
            print("✅ Menu music reloaded")
        except pygame.error as e:
            print(f"❌ Failed to reload menu music: {e}")

if __name__ == "__main__":
    main()