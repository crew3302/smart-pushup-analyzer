"""
Form Analyzer Module
State machine for push-up rep counting, form scoring, and feedback generation.
"""

import time
from core.angle_calculator import get_pushup_angles


class RepState:
    """Push-up repetition states."""
    UP = "UP"
    GOING_DOWN = "GOING_DOWN"
    DOWN = "DOWN"
    GOING_UP = "GOING_UP"


class FormVerdict:
    """Form quality labels."""
    CORRECT = "Correct"
    PARTIAL = "Partially Correct"
    INCORRECT = "Incorrect"


class FormAnalyzer:
    """
    Analyzes push-up form using a state machine.
    Tracks reps, scores each rep, and generates feedback.
    """

    # Angle thresholds
    ELBOW_DOWN_THRESHOLD = 110       # Elbow angle to consider "down"
    ELBOW_UP_THRESHOLD = 160         # Elbow angle to consider "up"
    ELBOW_CORRECT_MAX = 90           # Perfect depth
    ELBOW_PARTIAL_MAX = 110          # Acceptable depth

    HIP_CORRECT_MIN = 170            # Perfect alignment
    HIP_PARTIAL_MIN = 150            # Acceptable alignment

    EXTENSION_CORRECT_MIN = 160      # Full extension
    EXTENSION_PARTIAL_MIN = 140      # Acceptable extension

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all tracking state."""
        self.state = RepState.UP
        self.total_reps = 0
        self.correct_reps = 0
        self.partial_reps = 0
        self.incorrect_reps = 0
        self.rep_history = []           # list of dicts per rep
        self.current_feedback = []      # feedback for last rep
        self.current_form_status = ""   # live status string

        # Per-rep tracking
        self._rep_start_time = None
        self._min_elbow_angle = 180
        self._min_hip_angle = 180
        self._max_extension_angle = 0
        self._rep_times = []

    def update(self, landmarks):
        """
        Process one frame's landmarks.

        Args:
            landmarks: dict from PoseEstimator.process_frame

        Returns:
            dict with current stats and feedback, or None if no pose.
        """
        angles = get_pushup_angles(landmarks)
        if angles is None:
            self.current_form_status = "No pose detected"
            return self._build_result(angles)

        # Average left and right sides
        elbow_angle = (angles['left_elbow_angle'] + angles['right_elbow_angle']) / 2
        hip_angle = (angles['left_hip_angle'] + angles['right_hip_angle']) / 2
        shoulder_angle = (angles['left_shoulder_angle'] + angles['right_shoulder_angle']) / 2

        # State machine transitions
        prev_state = self.state

        if self.state == RepState.UP:
            if elbow_angle < self.ELBOW_UP_THRESHOLD:
                self.state = RepState.GOING_DOWN
                self._rep_start_time = time.time()
                self._min_elbow_angle = elbow_angle
                self._min_hip_angle = hip_angle
                self.current_form_status = "Going down..."

        elif self.state == RepState.GOING_DOWN:
            self._min_elbow_angle = min(self._min_elbow_angle, elbow_angle)
            self._min_hip_angle = min(self._min_hip_angle, hip_angle)

            if elbow_angle <= self.ELBOW_DOWN_THRESHOLD:
                self.state = RepState.DOWN
                self.current_form_status = "At bottom — push up!"
            elif elbow_angle > self.ELBOW_UP_THRESHOLD:
                # Went back up without going deep enough — still count partial
                self.state = RepState.GOING_UP
                self._max_extension_angle = elbow_angle

        elif self.state == RepState.DOWN:
            self._min_elbow_angle = min(self._min_elbow_angle, elbow_angle)
            self._min_hip_angle = min(self._min_hip_angle, hip_angle)

            if elbow_angle > self.ELBOW_DOWN_THRESHOLD:
                self.state = RepState.GOING_UP
                self._max_extension_angle = elbow_angle
                self.current_form_status = "Pushing up..."

        elif self.state == RepState.GOING_UP:
            self._max_extension_angle = max(self._max_extension_angle, elbow_angle)

            if elbow_angle >= self.ELBOW_UP_THRESHOLD:
                # Rep completed
                self._complete_rep(elbow_angle, hip_angle)
                self.state = RepState.UP

        # Live form checks
        self._live_form_check(elbow_angle, hip_angle)

        return self._build_result(angles)

    def _live_form_check(self, elbow_angle, hip_angle):
        """Update live form status based on current angles."""
        issues = []
        if hip_angle < self.HIP_PARTIAL_MIN:
            issues.append("⚠ Hips sagging — keep body straight!")
        elif hip_angle < self.HIP_CORRECT_MIN:
            issues.append("💡 Slight hip sag — tighten core")

        if self.state in (RepState.GOING_DOWN, RepState.DOWN):
            if hip_angle >= self.HIP_CORRECT_MIN and elbow_angle <= self.ELBOW_CORRECT_MAX:
                self.current_form_status = "✅ Great form!"

        if issues:
            self.current_form_status = " | ".join(issues)

    def _complete_rep(self, final_elbow, final_hip):
        """Score a completed repetition and generate feedback."""
        rep_time = time.time() - self._rep_start_time if self._rep_start_time else 0
        self._rep_times.append(rep_time)

        feedback = []
        scores = []

        # 1) Depth check (elbow at bottom)
        min_elbow = self._min_elbow_angle
        if min_elbow <= self.ELBOW_CORRECT_MAX:
            scores.append(2)
            feedback.append(f"✅ Great depth — elbows at {min_elbow:.0f}°")
        elif min_elbow <= self.ELBOW_PARTIAL_MAX:
            scores.append(1)
            feedback.append(f"⚠ Lower more — elbows only reached {min_elbow:.0f}° (aim for ≤{self.ELBOW_CORRECT_MAX}°)")
        else:
            scores.append(0)
            feedback.append(f"❌ Insufficient depth — elbows at {min_elbow:.0f}° (need ≤{self.ELBOW_PARTIAL_MAX}°)")

        # 2) Hip alignment check
        min_hip = self._min_hip_angle
        if min_hip >= self.HIP_CORRECT_MIN:
            scores.append(2)
            feedback.append(f"✅ Excellent body alignment — hips at {min_hip:.0f}°")
        elif min_hip >= self.HIP_PARTIAL_MIN:
            scores.append(1)
            feedback.append(f"⚠ Slight hip sag — {min_hip:.0f}° (aim for ≥{self.HIP_CORRECT_MIN}°)")
        else:
            scores.append(0)
            feedback.append(f"❌ Hips sagging — {min_hip:.0f}° (keep body straight ≥{self.HIP_PARTIAL_MIN}°)")

        # 3) Full extension check
        max_ext = self._max_extension_angle
        if max_ext >= self.EXTENSION_CORRECT_MIN:
            scores.append(2)
            feedback.append(f"✅ Full arm extension — {max_ext:.0f}°")
        elif max_ext >= self.EXTENSION_PARTIAL_MIN:
            scores.append(1)
            feedback.append(f"⚠ Extend arms more — {max_ext:.0f}° (aim for ≥{self.EXTENSION_CORRECT_MIN}°)")
        else:
            scores.append(0)
            feedback.append(f"❌ Incomplete extension — {max_ext:.0f}° (need ≥{self.EXTENSION_PARTIAL_MIN}°)")

        # Overall verdict
        total_score = sum(scores)
        if total_score >= 5:
            verdict = FormVerdict.CORRECT
            self.correct_reps += 1
        elif total_score >= 3:
            verdict = FormVerdict.PARTIAL
            self.partial_reps += 1
        else:
            verdict = FormVerdict.INCORRECT
            self.incorrect_reps += 1

        self.total_reps += 1

        rep_data = {
            'rep_number': self.total_reps,
            'verdict': verdict,
            'min_elbow_angle': min_elbow,
            'min_hip_angle': min_hip,
            'max_extension_angle': max_ext,
            'rep_time': round(rep_time, 2),
            'feedback': feedback,
            'score': total_score,
        }

        self.rep_history.append(rep_data)
        self.current_feedback = feedback
        self.current_form_status = f"Rep {self.total_reps}: {verdict}"

        # Reset per-rep trackers
        self._min_elbow_angle = 180
        self._min_hip_angle = 180
        self._max_extension_angle = 0
        self._rep_start_time = None

    def _build_result(self, angles):
        """Build result dict for GUI consumption."""
        avg_speed = 0.0
        if self._rep_times:
            avg_speed = round(sum(self._rep_times) / len(self._rep_times), 2)

        return {
            'state': self.state,
            'total_reps': self.total_reps,
            'correct_reps': self.correct_reps,
            'partial_reps': self.partial_reps,
            'incorrect_reps': self.incorrect_reps,
            'avg_rep_speed': avg_speed,
            'current_feedback': list(self.current_feedback),
            'form_status': self.current_form_status,
            'angles': angles,
            'rep_history': self.rep_history,
        }

    def get_session_summary(self):
        """Return a summary dict for logging."""
        total_time = sum(self._rep_times) if self._rep_times else 0
        return {
            'total_reps': self.total_reps,
            'correct_reps': self.correct_reps,
            'partial_reps': self.partial_reps,
            'incorrect_reps': self.incorrect_reps,
            'avg_speed': round(total_time / max(1, len(self._rep_times)), 2),
            'duration': round(total_time, 2),
            'rep_history': self.rep_history,
        }
