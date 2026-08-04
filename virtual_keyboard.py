import cv2
import mediapipe as mp
import numpy as np
import pyperclip
import time
from collections import deque

# ---------- Config & Design System ----------
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
KEY_W, KEY_H = 75, 75
KEY_MARGIN = 12
TOP_BOX_HEIGHT = 130
FONT = cv2.FONT_HERSHEY_SIMPLEX
PRESS_COOLDOWN = 0.35

# Color Palette (Dark Glassmorphism UI)
COLOR_BG_HEADER = (20, 24, 33)
COLOR_TEXT_HEADER = (240, 240, 245)
COLOR_SUBTEXT = (140, 150, 165)
COLOR_KEY_BG = (45, 48, 58)
COLOR_KEY_BORDER = (90, 95, 110)
COLOR_KEY_TEXT = (230, 235, 245)

COLOR_HOVER_BG = (180, 100, 30)      # Neon Cyan/Teal (BGR)
COLOR_HOVER_BORDER = (255, 220, 120)
COLOR_PRESS_BG = (50, 180, 80)       # Emerald Green pulse on pinch press
COLOR_PRESS_BORDER = (120, 255, 150)

COLOR_POINTER_INDEX = (255, 190, 40)
COLOR_POINTER_THUMB = (255, 100, 200)


# ---------- Rounded Rectangle Helper ----------
def draw_rounded_rectangle(img, pt1, pt2, color, thickness=-1, radius=12):
    """Draws a rounded rectangle using OpenCV shapes."""
    x1, y1 = pt1
    x2, y2 = pt2
    w = x2 - x1
    h = y2 - y1
    radius = min(radius, w // 2, h // 2)

    if thickness < 0:
        # Fill inner area
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
    else:
        # Draw outline
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)

        cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)


# ---------- Key Class ----------
class Key:
    def __init__(self, x, y, w, h, label):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.label = label
        self.press_anim_time = 0  # Timestamp for press feedback effect

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def draw(self, frame, is_hovered=False, is_pressed=False):
        current_time = time.time()
        
        # Color selection based on state
        if is_pressed or (current_time - self.press_anim_time < 0.2):
            bg_col = COLOR_PRESS_BG
            border_col = COLOR_PRESS_BORDER
        elif is_hovered:
            bg_col = COLOR_HOVER_BG
            border_col = COLOR_HOVER_BORDER
        else:
            bg_col = COLOR_KEY_BG
            border_col = COLOR_KEY_BORDER

        # Draw Key Background & Border
        draw_rounded_rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), bg_col, thickness=-1, radius=10)
        draw_rounded_rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), border_col, thickness=2, radius=10)

        # Label Centering
        font_scale = 0.9 if len(self.label) == 1 else 0.7
        font_thickness = 2
        text_size = cv2.getTextSize(self.label, FONT, font_scale, font_thickness)[0]
        tx = self.x + (self.w - text_size[0]) // 2
        ty = self.y + (self.h + text_size[1]) // 2
        
        cv2.putText(frame, self.label, (tx, ty), FONT, font_scale, COLOR_KEY_TEXT, font_thickness, cv2.LINE_AA)


# ---------- Keyboard Layout ----------
def build_keyboard():
    keys = []
    rows = [
        list("1234567890"),
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM")
    ]

    start_y = TOP_BOX_HEIGHT + 25
    for r, row in enumerate(rows):
        total_w = len(row) * (KEY_W + KEY_MARGIN) - KEY_MARGIN
        start_x = (VIDEO_WIDTH - total_w) // 2
        y = start_y + r * (KEY_H + KEY_MARGIN)
        for i, ch in enumerate(row):
            x = start_x + i * (KEY_W + KEY_MARGIN)
            keys.append(Key(x, y, KEY_W, KEY_H, ch))

    # Control keys row
    ctrl_y = start_y + len(rows) * (KEY_H + KEY_MARGIN)
    space_w = KEY_W * 4 + KEY_MARGIN * 3
    total_ctrl_w = KEY_W * 2 + KEY_MARGIN * 2 + space_w
    start_x = (VIDEO_WIDTH - total_ctrl_w) // 2

    keys.extend([
        Key(start_x, ctrl_y, KEY_W, KEY_H, "BACK"),
        Key(start_x + (KEY_W + KEY_MARGIN), ctrl_y, KEY_W, KEY_H, "COPY"),
        Key(start_x + 2 * (KEY_W + KEY_MARGIN), ctrl_y, space_w, KEY_H, "SPACE")
    ])
    return keys


# ---------- MediaPipe Setup ----------
mp_hands = mp.solutions.hands


# ---------- Main Application ----------
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)

    keys = build_keyboard()
    typed = ""
    cleared_buffer = ""
    last_press_time = 0
    pinch_state = False
    feedback, feedback_time = "", 0
    pos_buffer = deque(maxlen=4)
    swipe_x_buffer = deque(maxlen=10)
    last_swipe_time = 0
    SWIPE_COOLDOWN = 1.0
    prev_time = 0

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75, min_tracking_confidence=0.75) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera feed unreadable.")
                break

            frame = cv2.flip(frame, 1)
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(img_rgb)
            h, w, _ = frame.shape

            # Dark Overlay / Glass Header
            draw_rounded_rectangle(frame, (15, 10), (VIDEO_WIDTH - 15, TOP_BOX_HEIGHT), COLOR_BG_HEADER, thickness=-1, radius=15)
            draw_rounded_rectangle(frame, (15, 10), (VIDEO_WIDTH - 15, TOP_BOX_HEIGHT), (60, 70, 90), thickness=2, radius=15)

            # Display Typed Text
            display_text = typed[-42:] if len(typed) > 42 else typed
            cv2.putText(frame, display_text if display_text else "Type something...", (40, 70), 
                        FONT, 1.3, (255, 255, 255) if display_text else (100, 110, 130), 2, cv2.LINE_AA)

            # Instructions Subtext
            cv2.putText(frame, "Pinch: Type | Swipe R->L: Clear | Swipe L->R: Retrieve | Snap: Exit | 'c': Clear | 'q': Quit",
                        (40, 110), FONT, 0.52, COLOR_SUBTEXT, 1, cv2.LINE_AA)

            hovered_key = None
            is_pinched = False
            avg_x, avg_y = 0, 0

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                lm = hand.landmark

                # --- Hand Swipe Detection (Right->Left: Clear, Left->Right: Retrieve) ---
                palm_center_x = int(lm[9].x * w)
                swipe_x_buffer.append((time.time(), palm_center_x))
                current_time = time.time()

                if len(swipe_x_buffer) >= 6 and (current_time - last_swipe_time) > SWIPE_COOLDOWN:
                    t_old, x_old = swipe_x_buffer[0]
                    t_new, x_new = swipe_x_buffer[-1]
                    dt = t_new - t_old
                    dx = x_new - x_old

                    if dt > 0.05 and dt < 0.4:
                        velocity = dx / dt  # pixels per second
                        # Swipe Right to Left (dx < -250 px, velocity < -1200 px/s)
                        if dx < -220 and velocity < -1000:
                            if typed:
                                cleared_buffer = typed
                                typed = ""
                                feedback = "Cleared (Swipe R->L)"
                            else:
                                feedback = "Already Empty"
                            feedback_time = current_time
                            last_swipe_time = current_time
                            swipe_x_buffer.clear()
                        # Swipe Left to Right (dx > 220 px, velocity > 1000 px/s)
                        elif dx > 220 and velocity > 1000:
                            if cleared_buffer:
                                typed = cleared_buffer
                                feedback = "Retrieved (Swipe L->R)"
                            else:
                                feedback = "Nothing to Retrieve"
                            feedback_time = current_time
                            last_swipe_time = current_time
                            swipe_x_buffer.clear()

                # --- Snap Gesture Detection ---
                mid_tip = np.array([lm[12].x * w, lm[12].y * h])
                thumb_tip = np.array([lm[4].x * w, lm[4].y * h])
                palm_center = np.array([lm[9].x * w, lm[9].y * h])
                wrist = np.array([lm[0].x * w, lm[0].y * h])
                
                mid_pip = np.array([lm[10].x * w, lm[10].y * h])
                ring_tip = np.array([lm[16].x * w, lm[16].y * h])
                ring_pip = np.array([lm[14].x * w, lm[14].y * h])
                pinky_tip = np.array([lm[20].x * w, lm[20].y * h])
                pinky_pip = np.array([lm[18].x * w, lm[18].y * h])
                index_tip = np.array([lm[8].x * w, lm[8].y * h])
                index_pip = np.array([lm[6].x * w, lm[6].y * h])

                hand_size = np.linalg.norm(wrist - palm_center)
                dist_mid_palm = np.linalg.norm(mid_tip - palm_center)

                middle_curled_to_palm = dist_mid_palm < (hand_size * 0.45)
                ring_curled = np.linalg.norm(ring_tip - wrist) < np.linalg.norm(ring_pip - wrist)
                pinky_curled = np.linalg.norm(pinky_tip - wrist) < np.linalg.norm(pinky_pip - wrist)
                index_extended = np.linalg.norm(index_tip - wrist) > np.linalg.norm(index_pip - wrist)
                
                if middle_curled_to_palm and ring_curled and pinky_curled and index_extended:
                    print("Finger snap gesture detected! Terminating program...")
                    cv2.putText(frame, "SNAP DETECTED! TERMINATING...", (VIDEO_WIDTH // 2 - 250, VIDEO_HEIGHT // 2),
                                FONT, 1.1, (0, 0, 255), 3, cv2.LINE_AA)
                    cv2.imshow("Virtual Keyboard — Antigravity Edition", frame)
                    cv2.waitKey(800)
                    break

                # Index & Thumb Tip Coordinates
                ix, iy = int(lm[8].x * w), int(lm[8].y * h)
                tx, ty = int(lm[4].x * w), int(lm[4].y * h)

                # Adaptive Pinch Scale
                wx, wy = int(lm[0].x * w), int(lm[0].y * h)
                mx, my = int(lm[9].x * w), int(lm[9].y * h)
                hand_scale = np.hypot(wx - mx, wy - my)
                dynamic_pinch_threshold = max(25, hand_scale * 0.35)

                pinch_dist_px = np.hypot(ix - tx, iy - ty)
                is_pinched = pinch_dist_px < dynamic_pinch_threshold

                # Freeze cursor drift when fingers are close to pinching
                is_approaching_pinch = pinch_dist_px < (dynamic_pinch_threshold * 1.5)
                if not is_approaching_pinch or len(pos_buffer) == 0:
                    pos_buffer.append((ix, iy))

                avg_x = int(np.mean([p[0] for p in pos_buffer]))
                avg_y = int(np.mean([p[1] for p in pos_buffer]))

                # Find Hovered Key
                for k in keys:
                    if k.contains(avg_x, avg_y):
                        hovered_key = k
                        break

                # Draw Finger Nodes & Pinch Connector
                line_color = COLOR_PRESS_BG if is_pinched else (255, 220, 100)
                cv2.line(frame, (ix, iy), (tx, ty), line_color, 2, cv2.LINE_AA)
                cv2.circle(frame, (ix, iy), 7, COLOR_POINTER_INDEX, -1, cv2.LINE_AA)
                cv2.circle(frame, (tx, ty), 7, COLOR_POINTER_THUMB, -1, cv2.LINE_AA)
                cv2.circle(frame, (avg_x, avg_y), 10, (255, 255, 255), 2, cv2.LINE_AA)

                # Pinch Press Action
                current_time = time.time()
                if is_pinched and not pinch_state and (current_time - last_press_time) > PRESS_COOLDOWN:
                    pinch_state = True
                    last_press_time = current_time
                    if hovered_key:
                        hovered_key.press_anim_time = current_time
                        label = hovered_key.label
                        if label == "SPACE":
                            typed += " "
                            feedback = "[SPACE]"
                        elif label == "BACK":
                            typed = typed[:-1]
                            feedback = "[BACKSPACE]"
                        elif label == "COPY":
                            pyperclip.copy(typed)
                            feedback = "Copied to Clipboard!"
                        else:
                            typed += label
                            feedback = f"Pressed '{label}'"
                        feedback_time = current_time
                elif not is_pinched:
                    pinch_state = False

            # Draw All Keyboard Keys
            for k in keys:
                is_hover = (k == hovered_key)
                is_press = (k == hovered_key and is_pinched)
                k.draw(frame, is_hovered=is_hover, is_pressed=is_press)

            # Feedback Toast Notification
            if feedback and (time.time() - feedback_time) < 1.2:
                cv2.putText(frame, feedback, (VIDEO_WIDTH - 290, 70), FONT, 0.75, (100, 255, 120), 2, cv2.LINE_AA)

            # Performance FPS Counter
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if prev_time != 0 else 0
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (VIDEO_WIDTH - 110, VIDEO_HEIGHT - 20), FONT, 0.55, COLOR_SUBTEXT, 1, cv2.LINE_AA)

            cv2.imshow("Virtual Keyboard — Antigravity Edition", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                typed = ""

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

    