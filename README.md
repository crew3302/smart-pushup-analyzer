# AI Push-Up Form Analyzer

A professional desktop application that uses AI and computer vision to analyze push-up form in real time or from video, providing instant feedback, rep counting, and performance history. Built with Python, OpenCV, MediaPipe, and Tkinter.

---

## Features

- **Live Webcam Analysis:**
  - Real-time push-up detection and form analysis using your webcam.
  - Instant feedback on each rep: correct, partial, or incorrect.
  - Rep counting and form scoring.

- **Video Upload Analysis:**
  - Analyze pre-recorded push-up videos for form and rep quality.
  - Frame-by-frame navigation and feedback.

- **Performance History:**
  - Visualize your workout stats and progress over time.
  - Charts and tables for session review.

- **Modern GUI:**
  - Clean, dark-themed interface with sidebar navigation.
  - Built with Tkinter for cross-platform compatibility.

---

## Screenshots

> _Add screenshots of the main app, webcam analysis, video analysis, and history views here._

---

## Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd gym
   ```
2. **(Recommended) Create a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

---

## Usage

- **Start the application:**
  ```sh
  python main.py
  ```
- **Webcam Analysis:**
  - Click "Webcam" in the sidebar to start live analysis.
- **Video Analysis:**
  - Click "Video" to upload and analyze a push-up video.
- **History:**
  - Click "History" to view your workout stats and progress.

---

## Project Structure

```
main.py                # Entry point
requirements.txt       # Dependencies
core/
    angle_calculator.py  # Joint angle calculations
    form_analyzer.py     # Rep counting, form scoring
    pose_estimator.py    # Landmark detection (MediaPipe)
    logger.py            # Logging utilities
    ...
gui/
    app.py              # Main Tkinter app
    webcam_view.py       # Live webcam analysis
    video_view.py        # Video upload analysis
    history_view.py      # Performance history
    ...
tests/                 # (Add your tests here)
```

---

## Dependencies

- Python 3.8+
- OpenCV
- MediaPipe
- Pillow
- Matplotlib
- NumPy (<2.0)

Install all dependencies with `pip install -r requirements.txt`.

---

## How It Works

- **Pose Estimation:** Uses MediaPipe to detect body landmarks in each frame.
- **Angle Calculation:** Computes joint angles (elbow, hip, etc.) to assess push-up form.
- **Form Analysis:** State machine logic counts reps, scores form, and provides feedback.
- **GUI:** Tkinter-based interface for navigation, video display, and stats.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)
