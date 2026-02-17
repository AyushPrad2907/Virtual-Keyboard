import cv2
import mediapipe as mp
import numpy as np
import pyperclip
import time
from collections import deque

# ---------- Config ----------
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
KEY_W = 80
KEY_H = 80
KEY_MARGIN = 10
TOP_BOX_HEIGHT = 120
FONT = cv2.FONT_HERSHEY_SIMPLEX
PRESS_COOLDOWN = 0.45  # debounce (seconds)

class Key:
    def __init__(self, x, y, w, h, label):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.label = label
    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

# ---------- Keyboard Layout ----------
def build_keyboard():
    keys = []
    rows = [
        list("1234567890"),      # New numeric row
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM")
    ]

    start_y = TOP_BOX_HEIGHT + 20
    for r, row in enumerate(rows):
        row_len = len(row)
        total_w = row_len * (KEY_W + KEY_MARGIN) - KEY_MARGIN
        start_x = (VIDEO_WIDTH - total_w) // 2
        y = start_y + r * (KEY_H + KEY_MARGIN)
        for i, ch in enumerate(row):
            x = start_x + i * (KEY_W + KEY_MARGIN)
            keys.append(Key(x, y, KEY_W, KEY_H, ch))

    # Control row: SPACE, BACKSPACE, COPY
    ctrl_y = start_y + len(rows) * (KEY_H + KEY_MARGIN)
    space_w = KEY_W * 4 + KEY_MARGIN * 3
    total_ctrl_w = KEY_W + KEY_MARGIN + KEY_W + KEY_MARGIN + space_w
    start_x = (VIDEO_WIDTH - total_ctrl_w) // 2
    keys.append(Key(start_x, ctrl_y, KEY_W, KEY_H, "BACK"))
    keys.append(Key(start_x + KEY_W + KEY_MARGIN, ctrl_y, KEY_W, KEY_H, "COPY"))
    keys.append(Key(start_x + (KEY_W + KEY_MARGIN) * 2, ctrl_y, space_w, KEY_H, "SPACE"))

    return keys

# ---------- MediaPipe Setup ----------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)

# ---------- Main ----------
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)

    keys = build_keyboard()
    typed = ""
    last_press_time = 0
    pinch_state = False
    last_feedback = ""
    feedback_time = 0
    pos_buffer = deque(maxlen=5)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera not available.")
            break
        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        h, w, _ = frame.shape

        # Typed box
        cv2.rectangle(frame, (0, 0), (VIDEO_WIDTH, TOP_BOX_HEIGHT), (30, 30, 30), -1)
        display_text = typed[-40:] if len(typed) > 40 else typed
        cv2.putText(frame, display_text, (20, 70), FONT, 1.5, (255,255,255), 2)
        cv2.putText(frame, "Hover + pinch to type | Hover COPY + pinch to copy | Press 'q' to quit",
                    (20, 105), FONT, 0.6, (190,190,190), 1)

        # Draw all keys
        for k in keys:
            cv2.rectangle(frame, (k.x, k.y), (k.x+k.w, k.y+k.h), (50,50,50), -1)
            cv2.rectangle(frame, (k.x, k.y), (k.x+k.w, k.y+k.h), (200,200,200), 2)
            font_scale = 1.0 if len(k.label) == 1 else 0.8
            text_size = cv2.getTextSize(k.label, FONT, font_scale, 2)[0]
            tx = k.x + (k.w - text_size[0]) // 2
            ty = k.y + (k.h + text_size[1]) // 2
            cv2.putText(frame, k.label, (tx, ty), FONT, font_scale, (255,255,255), 2)

        index_x, index_y = None, None
        pinch_distance_px = None

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            lm = hand.landmark
            ix, iy = int(lm[8].x * w), int(lm[8].y * h)
            tx, ty = int(lm[4].x * w), int(lm[4].y * h)
            index_x, index_y = ix, iy
            pinch_distance_px = np.hypot(ix - tx, iy - ty)

            pos_buffer.append((ix, iy))
            avg_x = int(np.mean([p[0] for p in pos_buffer]))
            avg_y = int(np.mean([p[1] for p in pos_buffer]))

            cv2.circle(frame, (ix, iy), 8, (0,255,255), -1)
            cv2.circle(frame, (tx, ty), 8, (0,255,255), -1)
            cv2.line(frame, (ix, iy), (tx, ty), (0,255,255), 2)

            pinch_threshold = 40
            is_pinched = pinch_distance_px < pinch_threshold

            hovered_key = None
            for k in keys:
                if k.contains(avg_x, avg_y):
                    hovered_key = k
                    cv2.rectangle(frame, (k.x, k.y), (k.x+k.w, k.y+k.h), (0,140,255), -1)
                    cv2.rectangle(frame, (k.x, k.y), (k.x+k.w, k.y+k.h), (255,255,255), 2)
                    font_scale = 1.0 if len(k.label) == 1 else 0.8
                    text_size = cv2.getTextSize(k.label, FONT, font_scale, 2)[0]
                    tx2 = k.x + (k.w - text_size[0])//2
                    ty2 = k.y + (k.h + text_size[1])//2
                    cv2.putText(frame, k.label, (tx2, ty2), FONT, font_scale, (255,255,255), 2)

            current_time = time.time()
            if is_pinched and not pinch_state and (current_time - last_press_time) > PRESS_COOLDOWN:
                pinch_state = True
                last_press_time = current_time
                if hovered_key:
                    key_label = hovered_key.label
                    if key_label == "SPACE":
                        typed += " "
                        last_feedback = "SPACE"
                    elif key_label == "BACK":
                        typed = typed[:-1]
                        last_feedback = "BACKSPACE"
                    elif key_label == "COPY":
                        pyperclip.copy(typed)
                        last_feedback = "Copied!"
                    else:
                        typed += key_label
                        last_feedback = f"'{key_label}'"
                    feedback_time = current_time
            elif not is_pinched:
                pinch_state = False

            if pinch_distance_px is not None:
                cv2.putText(frame, f"Pinch dist: {int(pinch_distance_px)}", (10, VIDEO_HEIGHT - 20), FONT, 0.6, (200,200,200), 1)
                if is_pinched:
                    cv2.circle(frame, (avg_x, avg_y), 30, (0,255,0), 3)

        if last_feedback and (time.time() - feedback_time) < 1.5:
            cv2.putText(frame, last_feedback, (VIDEO_WIDTH - 300, 50), FONT, 0.9, (0,255,0), 2)

        cv2.putText(frame, "Press 'c' to clear text", (20, VIDEO_HEIGHT - 50), FONT, 0.7, (200,200,200), 1)
        cv2.imshow("Virtual Keyboard", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            typed = ""

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
