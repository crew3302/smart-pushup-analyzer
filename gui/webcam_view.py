"""
Webcam View Module
Live webcam feed with real-time push-up form analysis.
"""

import tkinter as tk
from tkinter import font as tkfont
import cv2
from PIL import Image, ImageTk
import threading
import time

from core.pose_estimator import PoseEstimator
from core.form_analyzer import FormAnalyzer
from core import logger


class WebcamView(tk.Frame):
    """Live webcam push-up analysis view."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0f0f1a', **kwargs)
        self.parent = parent
        self.pose_estimator = None
        self.form_analyzer = FormAnalyzer()
        self.cap = None
        self.running = False
        self._after_id = None

        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg='#1a1a2e', height=60)
        header.pack(fill='x', padx=0, pady=(0, 10))
        header.pack_propagate(False)

        tk.Label(
            header, text="📹  Live Webcam Analysis", font=("Segoe UI", 16, "bold"),
            fg='#e94560', bg='#1a1a2e'
        ).pack(side='left', padx=20, pady=15)

        # ── Main content area ──
        content = tk.Frame(self, bg='#0f0f1a')
        content.pack(fill='both', expand=True, padx=15, pady=0)

        # Left: Video feed
        self.video_frame = tk.Frame(content, bg='#16213e', bd=0, highlightthickness=2,
                                    highlightbackground='#e94560')
        self.video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.video_frame.pack_propagate(False)
        self.video_frame.configure(width=640, height=480)

        self.video_label = tk.Label(self.video_frame, bg='#16213e')
        self.video_label.pack(fill='both', expand=True, padx=5, pady=5)

        # Placeholder text
        self.placeholder_label = tk.Label(
            self.video_frame, text="Click 'Start' to begin webcam analysis",
            font=("Segoe UI", 14), fg='#8888aa', bg='#16213e'
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor='center')

        # Right: Stats & Feedback panel
        right_panel = tk.Frame(content, bg='#0f0f1a', width=320)
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.pack_propagate(False)

        # Stats cards
        stats_frame = tk.Frame(right_panel, bg='#0f0f1a')
        stats_frame.pack(fill='x', pady=(0, 10))

        self.stat_vars = {}
        stats_config = [
            ('total_reps', 'Total Reps', '#e94560'),
            ('correct_reps', 'Correct', '#00d2ff'),
            ('partial_reps', 'Partial', '#ffc107'),
            ('incorrect_reps', 'Incorrect', '#ff4444'),
            ('avg_speed', 'Avg Speed', '#a855f7'),
        ]

        for i, (key, label, color) in enumerate(stats_config):
            card = tk.Frame(stats_frame, bg='#1a1a2e', bd=0, highlightthickness=1,
                           highlightbackground='#2a2a4a')
            card.pack(fill='x', pady=3)

            tk.Label(card, text=label, font=("Segoe UI", 10), fg='#8888aa',
                    bg='#1a1a2e').pack(side='left', padx=12, pady=8)

            var = tk.StringVar(value='0')
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, font=("Segoe UI", 18, "bold"),
                    fg=color, bg='#1a1a2e').pack(side='right', padx=12, pady=8)

        # Form status
        status_frame = tk.Frame(right_panel, bg='#1a1a2e', highlightthickness=1,
                                highlightbackground='#2a2a4a')
        status_frame.pack(fill='x', pady=(10, 5))

        tk.Label(status_frame, text="Form Status", font=("Segoe UI", 10, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 12),
                fg='#00d2ff', bg='#1a1a2e', wraplength=280, justify='left').pack(
            anchor='w', padx=12, pady=(2, 8))

        # Feedback area
        feedback_frame = tk.Frame(right_panel, bg='#1a1a2e', highlightthickness=1,
                                  highlightbackground='#2a2a4a')
        feedback_frame.pack(fill='both', expand=True, pady=(5, 10))

        tk.Label(feedback_frame, text="Latest Feedback", font=("Segoe UI", 10, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 0))

        self.feedback_text = tk.Text(
            feedback_frame, bg='#1a1a2e', fg='#ccccee', font=("Segoe UI", 10),
            wrap='word', relief='flat', state='disabled', height=8,
            insertbackground='#e94560', selectbackground='#e94560'
        )
        self.feedback_text.pack(fill='both', expand=True, padx=10, pady=(5, 10))

        # ── Bottom controls ──
        controls = tk.Frame(self, bg='#0f0f1a', height=60)
        controls.pack(fill='x', padx=15, pady=10)

        btn_style = {
            'font': ("Segoe UI", 12, "bold"),
            'relief': 'flat',
            'cursor': 'hand2',
            'width': 12,
            'height': 1,
            'bd': 0,
        }

        self.start_btn = tk.Button(
            controls, text="▶  Start", bg='#e94560', fg='white',
            activebackground='#c73350', command=self._start, **btn_style
        )
        self.start_btn.pack(side='left', padx=(0, 10))

        self.stop_btn = tk.Button(
            controls, text="⏹  Stop", bg='#333355', fg='#aaaacc',
            activebackground='#444466', command=self._stop, state='disabled',
            **btn_style
        )
        self.stop_btn.pack(side='left', padx=(0, 10))

        self.reset_btn = tk.Button(
            controls, text="🔄 Reset", bg='#333355', fg='#aaaacc',
            activebackground='#444466', command=self._reset,
            **btn_style
        )
        self.reset_btn.pack(side='left')

    def _start(self):
        """Start webcam capture and analysis."""
        if self.running:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_var.set("❌ Cannot open webcam!")
            return

        self.pose_estimator = PoseEstimator()
        self.running = True
        self.placeholder_label.place_forget()

        self.start_btn.configure(state='disabled', bg='#333355')
        self.stop_btn.configure(state='normal', bg='#e94560')

        self._update_frame()

    def _stop(self):
        """Stop webcam capture."""
        self.running = False
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        if self.cap and self.cap.isOpened():
            self.cap.release()

        if self.pose_estimator:
            self.pose_estimator.release()
            self.pose_estimator = None

        self.start_btn.configure(state='normal', bg='#e94560')
        self.stop_btn.configure(state='disabled', bg='#333355')
        self.status_var.set("Stopped")

        # Auto-save session if any reps were recorded
        self._auto_save_session()

    def _reset(self):
        """Reset the form analyzer."""
        self.form_analyzer.reset()
        self._update_stats({
            'total_reps': 0, 'correct_reps': 0,
            'partial_reps': 0, 'incorrect_reps': 0,
            'avg_rep_speed': 0, 'form_status': 'Ready',
            'current_feedback': [],
        })

    def _auto_save_session(self):
        """Automatically save the session if reps were recorded."""
        summary = self.form_analyzer.get_session_summary()
        if summary['total_reps'] > 0:
            logger.save_session(
                summary['total_reps'], summary['correct_reps'],
                summary['partial_reps'], summary['incorrect_reps'],
                summary['avg_speed'], summary['duration'],
            )
            self.status_var.set(f"✅ Session saved — {summary['total_reps']} reps logged")

    def _update_frame(self):
        """Read frame from webcam, analyze, and display."""
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.status_var.set("❌ Lost webcam feed")
            self._stop()
            return

        frame = cv2.flip(frame, 1)  # Mirror

        # Process pose
        annotated, landmarks = self.pose_estimator.process_frame(frame)

        # Analyze form
        result = self.form_analyzer.update(landmarks)
        self._update_stats(result)

        # Display frame
        self._display_frame(annotated)

        # Schedule next frame (~30 FPS)
        self._after_id = self.after(33, self._update_frame)

    def _display_frame(self, frame):
        """Convert and display an OpenCV frame in the Tkinter label."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize to fit the video frame container
        self.update_idletasks()
        label_w = self.video_frame.winfo_width() - 14  # account for padding + border
        label_h = self.video_frame.winfo_height() - 14
        if label_w < 100:
            label_w = 640
        if label_h < 100:
            label_h = 480

        h, w = frame_rgb.shape[:2]
        scale = min(label_w / w, label_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w > 0 and new_h > 0:
            frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))

        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def _update_stats(self, result):
        """Update stats display from analysis result."""
        if result is None:
            return

        self.stat_vars['total_reps'].set(str(result.get('total_reps', 0)))
        self.stat_vars['correct_reps'].set(str(result.get('correct_reps', 0)))
        self.stat_vars['partial_reps'].set(str(result.get('partial_reps', 0)))
        self.stat_vars['incorrect_reps'].set(str(result.get('incorrect_reps', 0)))
        self.stat_vars['avg_speed'].set(f"{result.get('avg_rep_speed', 0):.1f}s")

        self.status_var.set(result.get('form_status', ''))

        # Update feedback text
        feedback = result.get('current_feedback', [])
        if feedback:
            self.feedback_text.configure(state='normal')
            self.feedback_text.delete('1.0', 'end')
            for line in feedback:
                self.feedback_text.insert('end', line + '\n\n')
            self.feedback_text.configure(state='disabled')

    def on_hide(self):
        """Called when view is hidden — stop webcam."""
        self._stop()

    def on_show(self):
        """Called when view becomes visible."""
        pass
