"""
History View Module
Displays past workout sessions with stats and a progress chart.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

from core import logger


class HistoryView(tk.Frame):
    """Performance history view with table and charts."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0f0f1a', **kwargs)
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg='#1a1a2e', height=60)
        header.pack(fill='x', padx=0, pady=(0, 10))
        header.pack_propagate(False)

        tk.Label(
            header, text="📊  Performance History", font=("Segoe UI", 16, "bold"),
            fg='#00d2ff', bg='#1a1a2e'
        ).pack(side='left', padx=20, pady=15)

        refresh_btn = tk.Button(
            header, text="🔄 Refresh", font=("Segoe UI", 10, "bold"),
            bg='#333355', fg='#aaaacc', activebackground='#444466',
            relief='flat', cursor='hand2', command=self._refresh_data,
            bd=0
        )
        refresh_btn.pack(side='right', padx=20, pady=15)

        clear_btn = tk.Button(
            header, text="🗑  Clear All", font=("Segoe UI", 10, "bold"),
            bg='#ff4444', fg='white', activebackground='#cc3333',
            relief='flat', cursor='hand2', command=self._clear_history,
            bd=0
        )
        clear_btn.pack(side='right', padx=5, pady=15)

        # ── Summary stats ──
        summary_frame = tk.Frame(self, bg='#0f0f1a')
        summary_frame.pack(fill='x', padx=15, pady=(0, 10))

        self.summary_vars = {}
        summary_config = [
            ('total_sessions', 'Sessions', '#e94560'),
            ('lifetime_reps', 'Total Reps', '#00d2ff'),
            ('lifetime_correct', 'Correct', '#4ade80'),
            ('form_score', 'Form Score', '#a855f7'),
            ('avg_rep_speed', 'Avg Speed', '#ffc107'),
        ]

        for key, label, color in summary_config:
            card = tk.Frame(summary_frame, bg='#1a1a2e', highlightthickness=1,
                           highlightbackground='#2a2a4a')
            card.pack(side='left', fill='x', expand=True, padx=3)

            tk.Label(card, text=label, font=("Segoe UI", 9), fg='#8888aa',
                    bg='#1a1a2e').pack(pady=(8, 0))

            var = tk.StringVar(value='—')
            self.summary_vars[key] = var
            tk.Label(card, textvariable=var, font=("Segoe UI", 20, "bold"),
                    fg=color, bg='#1a1a2e').pack(pady=(0, 8))

        # ── Content: Table + Chart ──
        content = tk.Frame(self, bg='#0f0f1a')
        content.pack(fill='both', expand=True, padx=15, pady=(0, 10))

        # Table
        table_frame = tk.Frame(content, bg='#1a1a2e', highlightthickness=1,
                               highlightbackground='#2a2a4a')
        table_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        tk.Label(table_frame, text="Session Log", font=("Segoe UI", 11, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 5))

        # Style the treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.Treeview",
                        background='#1a1a2e',
                        foreground='#ccccee',
                        fieldbackground='#1a1a2e',
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Dark.Treeview.Heading",
                        background='#2a2a4a',
                        foreground='#e94560',
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0)
        style.map("Dark.Treeview",
                  background=[('selected', '#e94560')],
                  foreground=[('selected', 'white')])

        columns = ('date', 'total', 'correct', 'partial', 'incorrect', 'speed', 'duration')
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show='headings',
            style='Dark.Treeview', height=10
        )

        headers = {
            'date': ('Date', 130),
            'total': ('Total', 60),
            'correct': ('✅', 50),
            'partial': ('⚠', 50),
            'incorrect': ('❌', 50),
            'speed': ('Speed', 65),
            'duration': ('Time', 65),
        }
        for col, (heading, width) in headers.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side='right', fill='y', padx=(0, 5), pady=(0, 10))

        # Chart
        chart_frame = tk.Frame(content, bg='#1a1a2e', highlightthickness=1,
                               highlightbackground='#2a2a4a', width=400)
        chart_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        chart_frame.pack_propagate(False)

        tk.Label(chart_frame, text="Progress Chart", font=("Segoe UI", 11, "bold"),
                fg='#8888aa', bg='#1a1a2e').pack(anchor='w', padx=12, pady=(8, 0))

        self.chart_container = tk.Frame(chart_frame, bg='#1a1a2e')
        self.chart_container.pack(fill='both', expand=True, padx=5, pady=5)

        self.no_data_label = tk.Label(
            self.chart_container, text="No session data yet.\nComplete a workout to see progress!",
            font=("Segoe UI", 12), fg='#8888aa', bg='#1a1a2e', justify='center'
        )
        self.no_data_label.place(relx=0.5, rely=0.5, anchor='center')

    def _refresh_data(self):
        """Reload data from database."""
        # Summary stats
        stats = logger.get_stats_summary()
        self.summary_vars['total_sessions'].set(str(stats['total_sessions']))
        self.summary_vars['lifetime_reps'].set(str(stats['lifetime_reps']))
        self.summary_vars['lifetime_correct'].set(str(stats['lifetime_correct']))
        self.summary_vars['form_score'].set(f"{stats['form_score']}%")
        self.summary_vars['avg_rep_speed'].set(f"{stats['avg_rep_speed']:.1f}s")

        # Table
        for item in self.tree.get_children():
            self.tree.delete(item)

        history = logger.get_history()
        for row in history:
            self.tree.insert('', 'end', values=(
                row['date'],
                row['total_reps'],
                row['correct_reps'],
                row['partial_reps'],
                row['incorrect_reps'],
                f"{row['avg_speed']:.1f}s",
                f"{row['duration']:.0f}s",
            ))

        # Chart
        self._draw_chart(history)

    def _draw_chart(self, history):
        """Draw a progress chart."""
        # Clear existing chart
        for w in self.chart_container.winfo_children():
            w.destroy()

        if not history:
            self.no_data_label = tk.Label(
                self.chart_container,
                text="No session data yet.\nComplete a workout to see progress!",
                font=("Segoe UI", 12), fg='#8888aa', bg='#1a1a2e', justify='center'
            )
            self.no_data_label.place(relx=0.5, rely=0.5, anchor='center')
            return

        # Reverse so oldest first
        history = list(reversed(history))

        fig = Figure(figsize=(4, 3), dpi=100, facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f0f1a')

        dates = list(range(1, len(history) + 1))
        correct = [r['correct_reps'] for r in history]
        partial = [r['partial_reps'] for r in history]
        incorrect = [r['incorrect_reps'] for r in history]

        ax.bar(dates, correct, label='Correct', color='#4ade80', alpha=0.9)
        ax.bar(dates, partial, bottom=correct, label='Partial', color='#ffc107', alpha=0.9)
        bottoms = [c + p for c, p in zip(correct, partial)]
        ax.bar(dates, incorrect, bottom=bottoms, label='Incorrect', color='#ff4444', alpha=0.9)

        ax.set_xlabel('Session #', color='#8888aa', fontsize=9)
        ax.set_ylabel('Reps', color='#8888aa', fontsize=9)
        ax.tick_params(colors='#8888aa', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#2a2a4a')
        ax.spines['left'].set_color('#2a2a4a')

        legend = ax.legend(fontsize=8, facecolor='#1a1a2e', edgecolor='#2a2a4a',
                          labelcolor='#ccccee', loc='upper left')

        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _clear_history(self):
        """Clear all session history."""
        if messagebox.askyesno("Clear History", "Delete all workout history?"):
            logger.delete_all_history()
            self._refresh_data()

    def on_show(self):
        """Called when view becomes visible."""
        self._refresh_data()

    def on_hide(self):
        """Called when view is hidden."""
        pass
