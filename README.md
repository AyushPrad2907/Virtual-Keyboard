# 🎹 Virtual Hand-Controlled Keyboard (OpenCV + MediaPipe)

Type without touching your keyboard!  
This project lets you **control a virtual keyboard using your hands**, powered by **OpenCV** and **MediaPipe**.  
Simply hover your finger over the virtual keys displayed on the screen — when your finger "presses" a key (detected by depth and gesture logic), it registers as input!

---

## 🚀 Features
- 🖐️ **Hand Tracking:** Real-time detection using MediaPipe’s hand landmarks.  
- ⌨️ **Virtual Keyboard Interface:** Interactive on-screen keyboard made using OpenCV.  
- 💡 **Hover Typing:** Press keys by moving and holding your index finger over them.  
- 🧠 **Smart Key Detection:** Detects finger distance to simulate a “key press.”  
- ⚡ **Real-Time Performance:** Smooth and responsive interface for real typing feel.  
- 🔊 **Optional Sound Feedback:** (Add feature) to play key-click sound on press.

---

## 🧠 Tech Stack
- **Language:** Python  
- **Libraries:**  
  - [OpenCV](https://opencv.org/) – for computer vision & UI  
  - [MediaPipe](https://developers.google.com/mediapipe) – for hand landmark detection  
  - [NumPy](https://numpy.org/) – for image array manipulation  
  - (Optional) `pyautogui` or `keyboard` – to simulate real key presses  

---

## 🖥️ How It Works

::contentReference[oaicite:0]{index=0}

1. The webcam captures your hand movements.  
2. MediaPipe detects **21 hand landmarks**, including fingertips and joints.  
3. OpenCV displays a **virtual keyboard layout** on screen.  
4. When your index finger hovers close enough to a key, the program interprets it as a key press.  
5. The pressed key appears in the terminal or on a text box.

---

## 🧩 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/VirtualKeyboard.git
   cd VirtualKeyboard
   ```

2. **Install dependencies**
   ```bash
   pip install opencv-python mediapipe numpy pyautogui
   ```

3. **Run the project**
   ```bash
   python virtual_keyboard.py
   ```

---

## 🧠 Demo Preview

::contentReference[oaicite:1]{index=1}

*(Add a screenshot or a short GIF of the keyboard in action — showing typing in air.)*

---

## 🧑‍💻 Author
**Ayush Pradhan**  
💼 Full Stack + AI Developer | Passionate about Human-Computer Interaction using AI & Vision  
🔗 [LinkedIn](https://linkedin.com/in/your-link) | [GitHub](https://github.com/your-username)

---

## ⭐ Support
If this project amazed you, give it a ⭐ and share it!  
Your support keeps innovation alive 💡

---

## 🧩 Future Enhancements
- Add **gesture-based Shift / Backspace / Space**  
- Add **multilingual keyboard layouts**  
- Integrate **AI auto-completion or speech feedback**  
- Use **depth estimation** for more accurate key pressing  

---

> “Touchless technology isn’t the future — it’s already here.” ✨
