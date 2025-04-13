import cv2
import numpy as np

class ObjectDetector:
    """Detects, classifies, counts, and aligns objects using computer vision techniques."""

    def __init__(self):
        self.min_area = 500
        self.color_ranges = {
            "coin": [(np.array([15, 100, 100]), np.array([40, 255, 255]))],  # Yellow
            "marker": [
                (np.array([0, 120, 70]), np.array([10, 255, 255])),  # Red (0-10)
                (np.array([170, 120, 70]), np.array([180, 255, 255]))  # Red (170-180)
            ],
            "bonus": [(np.array([100, 100, 100]), np.array([130, 255, 255]))]  # Blue bonus
        }
        self.target_position = (400, 300)

    def detect_objects(self, frame: np.ndarray, object_type: str = "coin") -> tuple[list, np.ndarray]:
        """Detect objects based on HSV color range and contour analysis."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower, upper = self.color_ranges.get(object_type, [(np.array([0, 0, 0]), np.array([255, 255, 255]))])[0]
        mask = cv2.inRange(hsv, lower, upper)
        if object_type == "marker":
            mask2 = cv2.inRange(hsv, self.color_ranges["marker"][1][0], self.color_ranges["marker"][1][1])
            mask = cv2.bitwise_or(mask, mask2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        objects = [(x, y, w, h) for contour in contours if (area := cv2.contourArea(contour)) > self.min_area 
                   for x, y, w, h in [cv2.boundingRect(contour)]]
        return objects, mask

    def classify_object(self, frame: np.ndarray, bbox: tuple) -> str:
        """Classify the object based on dominant hue and edge density."""
        x, y, w, h = bbox
        roi = frame[y:y+h, x:x+w]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv_roi], [0], None, [180], [0, 180])
        dominant_hue = np.argmax(hist)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges) / (w * h)
        if 15 <= dominant_hue <= 40:  # Yellow (coin)
            return "coin"
        elif dominant_hue < 10 or dominant_hue > 170:  # Red (marker)
            return "marker"
        elif 100 <= dominant_hue <= 130:  # Blue (bonus)
            return "bonus"
        return "coin" if edge_density > 0.15 else "marker"

    def count_objects(self, objects: list) -> int:
        """Count the number of detected objects."""
        return len(objects)

    def search_position(self, bbox: tuple) -> tuple:
        """Find the center position of the bounding box."""
        x, y, w, h = bbox
        return x + w // 2, y + h // 2

    def check_alignment(self, bbox: tuple) -> bool:
        """Check if the object is aligned with the target position."""
        center_x, center_y = self.search_position(bbox)
        distance = np.sqrt((center_x - self.target_position[0])**2 + (center_y - self.target_position[1])**2)
        return distance < 50