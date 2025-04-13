import cv2
import os
import mediapipe as mp
from datetime import datetime
import time

SAVE_DIR = "assets/images"
os.makedirs(SAVE_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

BUTTON_POS = (400, 400, 200, 80)
FONT = cv2.FONT_HERSHEY_SIMPLEX
HOVER_TIME_REQUIRED = 15

def draw_ui(frame, player_name, hover_status=""):
    overlay = frame.copy()
    cv2.rectangle(overlay, (30, 10), (610, 80), (50, 50, 50), -1)
    pt1 = (BUTTON_POS[0], BUTTON_POS[1])
    pt2 = (BUTTON_POS[0] + BUTTON_POS[2], BUTTON_POS[1] + BUTTON_POS[3])
    cv2.rectangle(overlay, pt1, pt2, (0, 200, 0), -1 if hover_status else 2)
    alpha = 0.7 if hover_status else 0.3
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    cv2.putText(frame, "Player Name:", (50, 50), FONT, 1, (255, 255, 255), 2)
    cv2.rectangle(frame, (250, 20), (500, 60), (255, 255, 255), -1)
    cv2.putText(frame, player_name, (260, 50), FONT, 1, (0, 0, 0), 2)
    cv2.putText(frame, "NEXT", (BUTTON_POS[0] + 60, BUTTON_POS[1] + 50), FONT, 1.5, (0, 0, 0), 2)
    if hover_status:
        cv2.putText(frame, f"Selecting... {hover_status}/{HOVER_TIME_REQUIRED}", (BUTTON_POS[0], BUTTON_POS[1] - 20), FONT, 0.8, (0, 255, 255), 2)

def is_finger_on_button(finger_x, finger_y):
    x, y, w, h = BUTTON_POS
    return x <= finger_x <= x + w and y <= finger_y <= y + h

def capture_face(player_name, frame, face_coordinates):
    if face_coordinates is not None:
        x, y, w, h = face_coordinates
        face_crop = frame[y:y+h, x:x+w]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = os.path.join(SAVE_DIR, f"{player_name}_{timestamp}.jpg")
        cv2.imwrite(img_name, face_crop)
        with open(img_name, 'a') as f:
            f.flush()
        time.sleep(0.5)
        print(f"✅ Face saved: {img_name}, file exists: {os.path.exists(img_name)}")
        return True
    return False

def run_player_registration():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not access camera, trying alternative...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("❌ Error: No webcam available.")
            return None, None

    player_name = ""
    finger_hover_time = 0
    next_selected = False
    face_coordinates = None

    while not next_selected:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Warning: Could not read frame, retrying...")
            time.sleep(0.1)
            continue

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
            face_coordinates = (x, y, w, h)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        draw_ui(frame, player_name, str(finger_hover_time) if finger_hover_time > 0 else "")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 8 and player_name:
            player_name = player_name[:-1]
        elif key == 13 and player_name:
            next_selected = True
        elif len(player_name) < 15 and 32 <= key <= 126:
            player_name += chr(key)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                h, w, _ = frame.shape
                finger_x, finger_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                cv2.circle(frame, (finger_x, finger_y), 10, (0, 0, 255), -1)

                if is_finger_on_button(finger_x, finger_y):
                    finger_hover_time += 1
                    if finger_hover_time >= HOVER_TIME_REQUIRED:
                        next_selected = True
                        print("✅ NEXT button selected via hand hover")
                else:
                    finger_hover_time = 0

        cv2.imshow("Player Registration", frame)

    if player_name and face_coordinates and capture_face(player_name, frame, face_coordinates):
        print(f"✅ Player {player_name} registered successfully!")
    else:
        print("❌ Registration failed or no face detected.")
        cap.release()
        cv2.destroyAllWindows()
        return None, None

    cap.release()
    cv2.destroyAllWindows()
    return player_name, face_coordinates