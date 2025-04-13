import cv2
import numpy as np
import os
import datetime
import random

class ImageProcessing:
    """Handles image transformations and alignment for spectral effects and avatars."""

    def __init__(self):
        self.target_position = (400, 300)

    def generate_spectral_effects(self, face_image):
        """Generate multiple spectral effects on the face image for avatar selection."""
        if face_image is None or face_image.size == 0:
            face_image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Resize the input image to a consistent size
        face_image = cv2.resize(face_image, (200, 200))
        
        effects = [
            lambda x: cv2.GaussianBlur(x, (15, 15), 0),  # 2D Convolution: Blur
            lambda x: cv2.convertScaleAbs(x, alpha=1.2, beta=50),  # Brightness/Contrast
            lambda x: cv2.Canny(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), 100, 200),  # Edge Detection (converted to 3 channels)
            lambda x: cv2.cvtColor(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR),  # Grayscale
            lambda x: self._to_black_and_white(x),  # Black and White
            lambda x: self._apply_red_filter(x),  # Red Filter
            lambda x: cv2.bitwise_not(x),  # Invert Colors
            lambda x: self._add_noise(x)  # Add Noise
        ]
        processed_images = [effect(face_image.copy()) for effect in random.sample(effects, 3)]
        # Ensure all images have 3 channels and correct shape
        return [cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img for img in processed_images]

    def _to_black_and_white(self, image):
        """Convert image to black and white using thresholding."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

    def _apply_red_filter(self, image):
        """Apply a red tint by removing blue and green channels."""
        red_tinted = image.copy()
        red_tinted[:, :, 0] = 0  # Remove blue
        red_tinted[:, :, 1] = 0  # Remove green
        return red_tinted

    def _add_noise(self, image):
        """Add random noise to the image."""
        noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
        return cv2.add(image, noise)

    def _high_contrast_bw(self, image):
        """Convert image to high contrast black and white."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    def align_image(self, image, bbox):
        """Align the image based on the object's bounding box center."""
        center_x, center_y = self.search_position(bbox)
        shift_x = self.target_position[0] - center_x
        shift_y = self.target_position[1] - center_y
        return cv2.warpAffine(image, np.float32([[1, 0, shift_x], [0, 1, shift_y]]), (image.shape[1], image.shape[0]))

    def search_position(self, bbox):
        """Find the center position of the bounding box."""
        x, y, w, h = bbox
        return x + w // 2, y + h // 2

    def save_face(self, face_image, player_name):
        """Save the captured face image with a timestamp."""
        save_dir = os.path.join("assets", "images")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = os.path.join(save_dir, f"{player_name}_{timestamp}.jpg")
        cv2.imwrite(img_name, face_image)

    def save_avatar(self, avatar_image):
        """Save the selected avatar image with a timestamp."""
        save_dir = os.path.join("assets", "scary")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = os.path.join(save_dir, f"avatar_{timestamp}.jpg")
        cv2.imwrite(img_name, avatar_image)