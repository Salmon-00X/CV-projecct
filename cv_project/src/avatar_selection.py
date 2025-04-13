import cv2
import os
import mediapipe as mp
import numpy as np
from src.image_processing import ImageProcessing
import time

SAVE_DIR = "assets/images"
SCARY_DIR = "assets/scary"
for directory in [SAVE_DIR, SCARY_DIR]:
    os.makedirs(directory, exist_ok=True)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

FONT = cv2.FONT_HERSHEY_SIMPLEX
HOVER_TIME_REQUIRED = 15
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
MAX_FRAMES = 600

def load_latest_face_image() -> tuple[np.ndarray, str]:
    images = [f for f in os.listdir(SAVE_DIR) if f.endswith('.jpg')]
    if not images:
        print("❌ No face image found in 'assets/images/'. Run player registration first.")
        return None, "Unknown"
    
    images_with_mtime = [(img, os.path.getmtime(os.path.join(SAVE_DIR, img))) for img in images]
    images_with_mtime.sort(key=lambda x: x[1], reverse=True)
    latest_image = images_with_mtime[0][0]
    print(f"✅ Found latest image: {latest_image} (mtime: {images_with_mtime[0][1]})")
    
    player_name = latest_image.split("_")[0]
    print(f"✅ Player name from image: {player_name}")
    
    max_retries = 3
    for attempt in range(max_retries):
        image = cv2.imread(os.path.join(SAVE_DIR, latest_image))
        if image is not None:
            return image, player_name
        print(f"⚠️ Warning: Failed to load image (attempt {attempt + 1}/{max_retries}), retrying...")
        time.sleep(0.5)
    
    print("❌ Failed to load image after retries")
    return None, player_name

def draw_progress_bar(frame, x, y, width, height, progress):
    cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 0, 0), -1)
    fill_width = int(width * min(progress / HOVER_TIME_REQUIRED, 1))
    cv2.rectangle(frame, (x, y), (x + fill_width, y + height), (0, 255, 0), -1)
    cv2.putText(frame, f"{progress}/{HOVER_TIME_REQUIRED}", (x + 5, y + 15), FONT, 0.5, (255, 255, 255), 1)

def run_avatar_selection(image_processor: ImageProcessing) -> tuple[str, np.ndarray]:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Unable to open camera.")
        return None, None

    base_image, player_name = load_latest_face_image()
    if base_image is None:
        cap.release()
        cv2.destroyAllWindows()
        return None, None

    images = image_processor.generate_spectral_effects(base_image)
    print("✅ Generated 3 processed images")
    finger_hover_time = [-1] * 3
    selected_index = -1
    frame_count = 0

    cv2.namedWindow("Avatar Selection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Avatar Selection", WINDOW_WIDTH, WINDOW_HEIGHT)

    while selected_index == -1 and frame_count < MAX_FRAMES:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera Error: Unable to capture frame.")
            break
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
        frame_count += 1

        for i, img in enumerate(images):
            img_resized = cv2.resize(img, (200, 200))
            x_offset = 100 + i * 220
            y_offset = 150
            if y_offset + 200 <= frame.shape[0] and x_offset + 200 <= frame.shape[1]:
                frame[y_offset:y_offset+200, x_offset:x_offset+200] = img_resized
            
            button_x_offset = x_offset + 50
            button_y_offset = y_offset + 250
            button_width, button_height = 120, 40
            cv2.rectangle(frame, (button_x_offset, button_y_offset), 
                         (button_x_offset + button_width, button_y_offset + button_height), 
                         (0, 255, 0), -1 if finger_hover_time[i] >= 0 else 2)
            cv2.putText(frame, f"Hover {i+1}", (button_x_offset + 20, button_y_offset + 25), 
                        FONT, 0.8, (0, 0, 0), 2)
            if finger_hover_time[i] >= 0:
                draw_progress_bar(frame, button_x_offset, button_y_offset - 20, button_width, 10, finger_hover_time[i])

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = frame.shape
                finger_x, finger_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                cv2.circle(frame, (finger_x, finger_y), 10, (0, 0, 255), -1)
                print(f"✅ Finger position: ({finger_x}, {finger_y})")

                for i in range(3):
                    button_x_offset = 100 + i * 220 + 50
                    button_y_offset = 150 + 250
                    button_width, button_height = 120, 40
                    if (button_x_offset <= finger_x <= button_x_offset + button_width and 
                        button_y_offset <= finger_y <= button_y_offset + button_height):
                        if finger_hover_time[i] == -1:
                            finger_hover_time[i] = 0
                        finger_hover_time[i] += 1
                        print(f"✅ Hovering over button {i+1}: {finger_hover_time[i]}/{HOVER_TIME_REQUIRED}")
                        if finger_hover_time[i] >= HOVER_TIME_REQUIRED:
                            selected_index = i
                            print(f"✅ Image {i+1} selected!")
                            break
                    else:
                        finger_hover_time[i] = -1
                if selected_index != -1:
                    break

        cv2.putText(frame, f"Player: {player_name}", (50, 50), FONT, 1, (255, 255, 255), 2)
        cv2.imshow("Avatar Selection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if frame_count >= MAX_FRAMES:
            print("⚠️ Timeout reached, using default selection")
            selected_index = 0

    selected_image = images[selected_index] if selected_index != -1 else images[0]
    img_name = os.path.join(SCARY_DIR, f"{player_name}_scary.jpg")
    cv2.imwrite(img_name, selected_image)
    print(f"✅ Scary opponent face saved: {img_name}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Returning player_name: {player_name}, selected_image: {selected_image is not None}")
    return player_name, selected_image

if __name__ == "__main__":
    image_processor = ImageProcessing()
    run_avatar_selection(image_processor)