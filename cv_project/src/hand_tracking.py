import cv2
import mediapipe as mp
import numpy as np
import time

class HandTracking:
    def __init__(self, resolution=(320, 240)):
        self.resolution = resolution  # Make resolution an instance variable
        self.cap = None
        self._initialize_camera()
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.4, min_tracking_confidence=0.4)
        self.mp_draw = mp.solutions.drawing_utils
        self.frame = None
        self.flipped_frame = None
        self.last_gesture = "rock"
        self.gesture_buffer = []  # Increased buffer size for smoothing
        self.gesture_confidence = 0  # Track confidence for debugging

    def _initialize_camera(self):
        """Initialize or reinitialize the camera with retries."""
        max_attempts = 3
        for attempt in range(max_attempts):
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                print(f"✅ Camera initialized on attempt {attempt + 1}")
                return
            print(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed to initialize camera")
            time.sleep(1)  # Wait before retry
        raise Exception("Could not initialize any webcam after multiple attempts")

    def capture_frame(self):
        """Capture a frame with multiple retries and reinitialization if needed."""
        max_attempts = 5
        for attempt in range(max_attempts):
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                self.flipped_frame = cv2.flip(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 1)
                return True, frame
            print(f"⚠️ Attempt {attempt + 1}/{max_attempts} failed to capture frame")
            time.sleep(0.2)  # Short delay between retries
        print("❌ Failed to capture frame after multiple attempts, attempting to reinitialize camera")
        self._reinitialize_camera()
        # Return a black frame with the instance resolution
        return False, np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

    def _reinitialize_camera(self):
        """Reinitialize the camera if it fails."""
        try:
            if self.cap:
                self.cap.release()
            self._initialize_camera()
            print("✅ Camera reinitialized successfully")
        except Exception as e:
            print(f"❌ Failed to reinitialize camera: {e}")

    def detect_gesture(self, mode):
        ret, frame = self.capture_frame()
        if not ret and frame is None:
            print("⚠️ Using last gesture due to frame capture failure")
            return self.last_gesture, []

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        hand_positions = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                gesture, confidence = self._classify_gesture(hand_landmarks)
                self.gesture_confidence = confidence
                self.gesture_buffer.append(gesture)
                if len(self.gesture_buffer) > 10:
                    self.gesture_buffer.pop(0)
                gesture_counts = {}
                for g in self.gesture_buffer:
                    gesture_counts[g] = gesture_counts.get(g, 0) + 1
                self.last_gesture = max(gesture_counts, key=gesture_counts.get)
                bbox = self._get_hand_bounding_box(hand_landmarks, frame.shape[1], frame.shape[0])
                hand_positions.append((bbox[0] + bbox[2] // 2, bbox[1]))
                print(f"✅ Detected gesture: {self.last_gesture}, Confidence: {self.gesture_confidence:.2f}")
                return self.last_gesture, hand_positions
        print(f"⚠️ No hand detected, using last gesture: {self.last_gesture}, Confidence: {self.gesture_confidence:.2f}")
        return self.last_gesture, hand_positions

    def _classify_gesture(self, hand_landmarks):
        landmarks = hand_landmarks.landmark
        finger_status = [
            1 if landmarks[8].y < landmarks[6].y else 0,  # Index
            1 if landmarks[12].y < landmarks[10].y else 0,  # Middle
            1 if landmarks[16].y < landmarks[14].y else 0,  # Ring
            1 if landmarks[20].y < landmarks[18].y else 0  # Pinky
        ]
        thumb_status = 1 if landmarks[4].x < landmarks[3].x else 0  # Thumb
        total_fingers = sum(finger_status) + thumb_status

        # Calculate confidence based on finger positions
        confidence = max(landmarks[8].visibility, landmarks[12].visibility, landmarks[16].visibility, landmarks[20].visibility)

        if total_fingers == 0:
            return "rock", confidence
        elif total_fingers >= 4:
            return "paper", confidence
        elif finger_status[0] == 1 and finger_status[1] == 1 and sum(finger_status[2:]) == 0:
            return "scissors", confidence
        return "rock", confidence  # Fallback

    def _get_hand_bounding_box(self, hand_landmarks, frame_width, frame_height):
        xs = [int(lm.x * frame_width) for lm in hand_landmarks.landmark]
        ys = [int(lm.y * frame_height) for lm in hand_landmarks.landmark]
        x_min, y_min, x_max, y_max = min(xs), min(ys), max(xs), max(ys)
        return (x_min, y_min, x_max - x_min, y_max - y_min)

    def get_frame(self):
        return self.frame if self.frame is not None else np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

    def get_flipped_frame(self):
        return self.flipped_frame if self.flipped_frame is not None else np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

    def __del__(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()