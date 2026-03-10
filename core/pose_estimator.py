"""
Pose Estimator Module
Wraps MediaPipe Pose for real-time body landmark detection.
"""

import cv2
import mediapipe as mp
import numpy as np


class PoseEstimator:
    """Detects body pose landmarks using MediaPipe Pose."""

    # Key landmark indices from MediaPipe
    LANDMARKS = {
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28,
    }

    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_frame(self, frame):
        """
        Process a single BGR frame.

        Returns:
            annotated_frame: frame with skeleton overlay drawn
            landmarks: dict of {name: (x, y, z, visibility)} or None if no pose
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose.process(rgb)
        rgb.flags.writeable = True

        annotated = frame.copy()
        landmarks = None

        if results.pose_landmarks:
            # Draw skeleton
            self.mp_drawing.draw_landmarks(
                annotated,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style(),
            )

            # Extract key landmarks as pixel coordinates
            h, w, _ = frame.shape
            landmarks = {}
            for name, idx in self.LANDMARKS.items():
                lm = results.pose_landmarks.landmark[idx]
                landmarks[name] = (
                    int(lm.x * w),
                    int(lm.y * h),
                    lm.z,
                    lm.visibility,
                )

        return annotated, landmarks

    def release(self):
        """Release MediaPipe resources."""
        self.pose.close()
