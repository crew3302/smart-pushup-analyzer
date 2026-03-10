"""
Video Upload View Module
Analyze pre-recorded push-up videos.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import os
import threading

from core.pose_estimator import PoseEstimator
from core.form_analyzer import FormAnalyzer
from core import logger


class VideoView(tk.Frame):
    """Video upload and analysis view."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0f0f1a', **kwargs)
        self.parent = parent
        self.pose_estimator = None
        self.form_analyzer = FormAnalyzer()
        self.cap = None
        self.playing = False
        self.video_path = None
        self._after_id = None
        self.total_frames = 0
        self.current_frame_idx = 0

        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg='#1a1a2e', height=60)
        header.pack(fill='x', padx=0, pady=(0, 10))
        header.pack_propagate(False)

        tk.Label(
            header, text="🎬  Video Upload Analysis", font=("Segoe UI", 16, "bold"),
            fg='#a855f7', bg='#1a1a2e'
        ).pack(side='left', padx=20, pady=15)

        self.file_label = tk.Label(
            header, text="No file selected", font=("Segoe UI", 10),
            fg='#8888aa', bg='#1a1a2e'
        )
        self.file_label.pack(side='right', padx=20, pady=15)

        # ── Main content ──
        content = tk.Frame(self, bg='#0f0f1a')
        content.pack(fill='both', expand=True, padx=15, pady=0)

        # Left: Video display
        self.video_frame = tk.Frame(content, bg='#16213e', bd=0, highlightthickness=2,
                                    highlightbackground='#a855f7')
        self.video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.video_frame.pack_propagate(False)
        self.video_frame.configure(width=640, height=480)

        self.video_label = tk.Label(self.video_frame, bg='#16213e')
        self.video_label.pack(fill='both', expand=True, padx=5, pady=5)

        self.placeholder_label = tk.Label(
            self.video_frame, text="Click 'Browse' to select a push-up video",
            font=("Segoe UI", 14), fg='#8888aa', bg='#16213e'
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor='center')

        # Right: Stats & Summary panel
        right_panel = tk.Frame(content, bg='#0f0f1a', width=320)
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.pack_propagate(False)

        # Progress
        progress_frame = tk.Frame(right_panel, bg='#1a1a2e', highlightthickness=1,
                                  highlightbackground='#2a2a4a')
        progress_frame.pack(fill='x', pady=(0, 10))

        tk.Label(progress_frame, text="Progress", font=("Segoe UI", 10, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 0))

        self.progress_var = tk.StringVar(value="0%")
        tk.Label(progress_frame, textvariable=self.progress_var,
                font=("Segoe UI", 20, "bold"), fg='#a855f7',
                bg='#1a1a2e').pack(padx=12, pady=(2, 8))

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

        for key, label, color in stats_config:
            card = tk.Frame(stats_frame, bg='#1a1a2e', bd=0, highlightthickness=1,
                           highlightbackground='#2a2a4a')
            card.pack(fill='x', pady=3)

            tk.Label(card, text=label, font=("Segoe UI", 10), fg='#8888aa',
                    bg='#1a1a2e').pack(side='left', padx=12, pady=8)

            var = tk.StringVar(value='0')
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, font=("Segoe UI", 18, "bold"),
                    fg=color, bg='#1a1a2e').pack(side='right', padx=12, pady=8)

        # Form Status
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

        tk.Label(feedback_frame, text="Analysis Feedback", font=("Segoe UI", 10, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 0))

        self.feedback_text = tk.Text(
            feedback_frame, bg='#1a1a2e', fg='#ccccee', font=("Segoe UI", 10),
            wrap='word', relief='flat', state='disabled', height=8,
            insertbackground='#a855f7', selectbackground='#a855f7'
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

        self.browse_btn = tk.Button(
            controls, text="📂 Browse", bg='#a855f7', fg='white',
            activebackground='#9333ea', command=self._browse, **btn_style
        )
        self.browse_btn.pack(side='left', padx=(0, 10))

        self.play_btn = tk.Button(
            controls, text="▶  Play", bg='#333355', fg='#aaaacc',
            activebackground='#444466', command=self._play, state='disabled',
            **btn_style
        )
        self.play_btn.pack(side='left', padx=(0, 10))

        self.pause_btn = tk.Button(
            controls, text="⏸  Pause", bg='#333355', fg='#aaaacc',
            activebackground='#444466', command=self._pause, state='disabled',
            **btn_style
        )
        self.pause_btn.pack(side='left', padx=(0, 10))

        self.reset_btn = tk.Button(
            controls, text="🔄 Reset", bg='#333355', fg='#aaaacc',
            activebackground='#444466', command=self._reset,
            **btn_style
        )
        self.reset_btn.pack(side='left')

        self.save_video_btn = tk.Button(
            controls, text="🎥 Save Video", bg='#4ade80', fg='#0f0f1a',
            activebackground='#22c55e', command=self._save_video,
            **btn_style
        )
        self.save_video_btn.pack(side='right')

    def _browse(self):
        """Open file dialog to select a video."""
        path = filedialog.askopenfilename(
            title="Select Push-Up Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self.video_path = path
            self.file_label.configure(text=os.path.basename(path))
            self._load_video(path)

    def _load_video(self, path):
        """Load a video file for analysis."""
        self._stop_playback()

        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            self.status_var.set("❌ Cannot open video!")
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_idx = 0
        self.form_analyzer.reset()

        self.play_btn.configure(state='normal', bg='#a855f7')
        self.placeholder_label.place_forget()

        # Show first frame
        ret, frame = self.cap.read()
        if ret:
            self.pose_estimator = PoseEstimator()
            annotated, _ = self.pose_estimator.process_frame(frame)
            self._display_frame(annotated)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.status_var.set("Video loaded — click Play")

    def _play(self):
        """Start or resume video playback with analysis."""
        if self.playing or self.cap is None:
            return

        self.playing = True
        self.play_btn.configure(state='disabled', bg='#333355')
        self.pause_btn.configure(state='normal', bg='#a855f7')

        self._update_frame()

    def _pause(self):
        """Pause video playback."""
        self.playing = False
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        self.play_btn.configure(state='normal', bg='#a855f7')
        self.pause_btn.configure(state='disabled', bg='#333355')
        self.status_var.set("Paused")

    def _stop_playback(self):
        """Stop and release video."""
        self.playing = False
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

        if self.pose_estimator:
            self.pose_estimator.release()
            self.pose_estimator = None

    def _reset(self):
        """Reset analysis state."""
        self.form_analyzer.reset()
        self._update_stats_display({
            'total_reps': 0, 'correct_reps': 0,
            'partial_reps': 0, 'incorrect_reps': 0,
            'avg_rep_speed': 0, 'form_status': 'Ready',
            'current_feedback': [],
        })
        self.progress_var.set("0%")

        if self.video_path:
            self._load_video(self.video_path)

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

    def _save_video(self):
        """Save the processed video with pose overlay to a file."""
        if not self.video_path:
            self.status_var.set("❌ No video loaded!")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Processed Video",
            defaultextension=".mp4",
            initialfile="pushup_analyzed.mp4",
            filetypes=[
                ("MP4 Video", "*.mp4"),
                ("AVI Video", "*.avi"),
                ("All files", "*.*"),
            ]
        )
        if not save_path:
            return

        # Disable buttons during export
        self.save_video_btn.configure(state='disabled', bg='#333355', text='⏳ Exporting...')
        self.status_var.set("Exporting processed video...")

        # Run export in a background thread to keep GUI responsive
        thread = threading.Thread(target=self._export_video, args=(save_path,), daemon=True)
        thread.start()

    def _export_video(self, save_path):
        """Re-process the source video and write annotated frames with stats overlay."""
        try:
            src = cv2.VideoCapture(self.video_path)
            if not src.isOpened():
                self.after(0, lambda: self.status_var.set("❌ Cannot re-open source video!"))
                return

            fps = src.get(cv2.CAP_PROP_FPS) or 30
            width = int(src.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(src.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total = int(src.get(cv2.CAP_PROP_FRAME_COUNT))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

            estimator = PoseEstimator()
            analyzer = FormAnalyzer()
            frame_idx = 0

            while True:
                ret, frame = src.read()
                if not ret:
                    break

                annotated, landmarks = estimator.process_frame(frame)
                result = analyzer.update(landmarks)

                # Draw stats overlay on the frame
                self._draw_stats_overlay(annotated, result)

                out.write(annotated)

                frame_idx += 1
                if frame_idx % 10 == 0 and total > 0:
                    pct = int((frame_idx / total) * 100)
                    self.after(0, lambda p=pct: self.status_var.set(f"Exporting... {p}%"))

            estimator.release()
            src.release()
            out.release()

            self.after(0, lambda: self._on_export_done(save_path))

        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"❌ Export failed: {e}"))
            self.after(0, lambda: self.save_video_btn.configure(
                state='normal', bg='#4ade80', text='🎥 Save Video'))

    @staticmethod
    def _draw_stats_overlay(frame, result):
        """Draw rep count, correct reps, and form status on the video frame."""
        if result is None:
            return

        h, w = frame.shape[:2]

        # Semi-transparent dark background box at top-left
        overlay = frame.copy()
        box_w, box_h = 320, 140
        cv2.rectangle(overlay, (10, 10), (10 + box_w, 10 + box_h), (15, 15, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Border
        cv2.rectangle(frame, (10, 10), (10 + box_w, 10 + box_h), (233, 69, 96), 2)

        # Title
        cv2.putText(frame, "PushUp AI Analyzer", (20, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (233, 69, 96), 2)

        # Total Reps
        total = result.get('total_reps', 0)
        cv2.putText(frame, f"Total Reps: {total}", (20, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Correct Reps (green)
        correct = result.get('correct_reps', 0)
        cv2.putText(frame, f"Correct: {correct}", (20, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (128, 222, 74), 2)

        # Partial + Incorrect
        partial = result.get('partial_reps', 0)
        incorrect = result.get('incorrect_reps', 0)
        cv2.putText(frame, f"Partial: {partial}  |  Incorrect: {incorrect}", (20, 128),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (170, 170, 200), 1)

        # Form status at bottom-left
        status = result.get('form_status', '')
        if status:
            # Background for status bar
            status_overlay = frame.copy()
            cv2.rectangle(status_overlay, (10, h - 50), (w - 10, h - 10), (15, 15, 30), -1)
            cv2.addWeighted(status_overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, status, (20, h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 210, 255), 2)

    def _on_export_done(self, save_path):
        """Called when video export finishes."""
        self.save_video_btn.configure(state='normal', bg='#4ade80', text='🎥 Save Video')
        self.status_var.set(f"✅ Video saved!")
        messagebox.showinfo("Export Complete",
                           f"Processed video saved to:\n{save_path}")

    def _update_frame(self):
        """Read and analyze next video frame."""
        if not self.playing or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            # Video ended
            self.playing = False
            self.play_btn.configure(state='disabled', bg='#333355')
            self.pause_btn.configure(state='disabled', bg='#333355')
            self.status_var.set("✅ Analysis complete!")
            self._show_summary()
            self._auto_save_session()
            return

        self.current_frame_idx += 1

        # Process pose and analyze
        annotated, landmarks = self.pose_estimator.process_frame(frame)
        result = self.form_analyzer.update(landmarks)
        self._update_stats_display(result)
        self._display_frame(annotated)

        # Update progress
        if self.total_frames > 0:
            pct = int((self.current_frame_idx / self.total_frames) * 100)
            self.progress_var.set(f"{pct}%")

        # Get FPS from video for correct timing
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        delay = max(1, int(1000 / fps)) if fps > 0 else 33
        self._after_id = self.after(delay, self._update_frame)

    def _display_frame(self, frame):
        """Display a frame in the video label."""
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

    def _update_stats_display(self, result):
        """Update the stats panel."""
        if result is None:
            return

        self.stat_vars['total_reps'].set(str(result.get('total_reps', 0)))
        self.stat_vars['correct_reps'].set(str(result.get('correct_reps', 0)))
        self.stat_vars['partial_reps'].set(str(result.get('partial_reps', 0)))
        self.stat_vars['incorrect_reps'].set(str(result.get('incorrect_reps', 0)))
        self.stat_vars['avg_speed'].set(f"{result.get('avg_rep_speed', 0):.1f}s")

        self.status_var.set(result.get('form_status', ''))

        feedback = result.get('current_feedback', [])
        if feedback:
            self.feedback_text.configure(state='normal')
            self.feedback_text.delete('1.0', 'end')
            for line in feedback:
                self.feedback_text.insert('end', line + '\n\n')
            self.feedback_text.configure(state='disabled')

    def _show_summary(self):
        """Show final analysis summary in feedback area."""
        summary = self.form_analyzer.get_session_summary()
        self.feedback_text.configure(state='normal')
        self.feedback_text.delete('1.0', 'end')

        self.feedback_text.insert('end', "═══ ANALYSIS COMPLETE ═══\n\n")
        self.feedback_text.insert('end', f"Total Reps: {summary['total_reps']}\n")
        self.feedback_text.insert('end', f"✅ Correct: {summary['correct_reps']}\n")
        self.feedback_text.insert('end', f"⚠ Partial: {summary['partial_reps']}\n")
        self.feedback_text.insert('end', f"❌ Incorrect: {summary['incorrect_reps']}\n")
        self.feedback_text.insert('end', f"Avg Speed: {summary['avg_speed']:.1f}s/rep\n\n")

        # Per-rep breakdown
        for rep in summary.get('rep_history', []):
            self.feedback_text.insert('end', f"─── Rep {rep['rep_number']} ({rep['verdict']}) ───\n")
            for fb in rep.get('feedback', []):
                self.feedback_text.insert('end', f"  {fb}\n")
            self.feedback_text.insert('end', '\n')

        self.feedback_text.configure(state='disabled')

    def on_hide(self):
        """Called when view is hidden."""
        self._pause()

    def on_show(self):
        """Called when view becomes visible."""
        pass
