"""
Main Application Module
Tkinter-based GUI shell with sidebar navigation and dark theme.
"""

import tkinter as tk
from tkinter import font as tkfont

from gui.webcam_view import WebcamView
from gui.video_view import VideoView
from gui.history_view import HistoryView


class App(tk.Tk):
    """Main application window."""

    BG_DARK = '#0a0a14'
    BG_SIDEBAR = '#12122a'
    BG_ACTIVE = '#1e1e3f'
    ACCENT = '#e94560'
    TEXT_PRIMARY = '#eeeeff'
    TEXT_DIM = '#8888aa'

    def __init__(self):
        super().__init__()

        self.title("AI Push-Up Form Analyzer")
        self.geometry("1280x780")
        self.minsize(1000, 600)
        self.configure(bg=self.BG_DARK)

        # Custom fonts
        self.title_font = tkfont.Font(family='Segoe UI', size=20, weight='bold')
        self.nav_font = tkfont.Font(family='Segoe UI', size=12)
        self.nav_font_bold = tkfont.Font(family='Segoe UI', size=12, weight='bold')

        self._build_sidebar()
        self._build_content_area()
        self._init_views()

        # Start with webcam view
        self._switch_view('webcam')

    def _build_sidebar(self):
        """Create the navigation sidebar."""
        self.sidebar = tk.Frame(self, bg=self.BG_SIDEBAR, width=240)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # App title / brand
        brand_frame = tk.Frame(self.sidebar, bg=self.BG_SIDEBAR)
        brand_frame.pack(fill='x', pady=(25, 30))

        tk.Label(
            brand_frame, text="💪", font=("Segoe UI Emoji", 28),
            bg=self.BG_SIDEBAR
        ).pack()

        tk.Label(
            brand_frame, text="PushUp AI", font=self.title_font,
            fg=self.ACCENT, bg=self.BG_SIDEBAR
        ).pack()

        tk.Label(
            brand_frame, text="Form Analyzer", font=("Segoe UI", 10),
            fg=self.TEXT_DIM, bg=self.BG_SIDEBAR
        ).pack()

        # Separator
        sep = tk.Frame(self.sidebar, bg='#2a2a4a', height=1)
        sep.pack(fill='x', padx=20, pady=(0, 15))

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ('webcam', '📹', 'Live Webcam'),
            ('video', '🎬', 'Upload Video'),
            ('history', '📊', 'History'),
        ]

        for key, icon, label in nav_items:
            btn_frame = tk.Frame(self.sidebar, bg=self.BG_SIDEBAR, cursor='hand2')
            btn_frame.pack(fill='x', padx=12, pady=3)

            btn_label = tk.Label(
                btn_frame, text=f"  {icon}  {label}",
                font=self.nav_font, fg=self.TEXT_DIM, bg=self.BG_SIDEBAR,
                anchor='w', padx=15, pady=12
            )
            btn_label.pack(fill='x')

            # Click binding
            for widget in (btn_frame, btn_label):
                widget.bind('<Button-1>', lambda e, k=key: self._switch_view(k))
                widget.bind('<Enter>', lambda e, f=btn_frame, l=btn_label, k=key:
                           self._on_hover(f, l, k, True))
                widget.bind('<Leave>', lambda e, f=btn_frame, l=btn_label, k=key:
                           self._on_hover(f, l, k, False))

            self.nav_buttons[key] = (btn_frame, btn_label)

        # Footer
        footer = tk.Frame(self.sidebar, bg=self.BG_SIDEBAR)
        footer.pack(side='bottom', fill='x', pady=15)

        tk.Label(
            footer, text="v1.0 • MediaPipe Pose",
            font=("Segoe UI", 8), fg='#555577', bg=self.BG_SIDEBAR
        ).pack()

    def _build_content_area(self):
        """Create the main content area."""
        self.content = tk.Frame(self, bg=self.BG_DARK)
        self.content.pack(side='right', fill='both', expand=True)

    def _init_views(self):
        """Initialize all view frames."""
        self.views = {}
        self.views['webcam'] = WebcamView(self.content)
        self.views['video'] = VideoView(self.content)
        self.views['history'] = HistoryView(self.content)
        self.current_view = None

    def _switch_view(self, view_key):
        """Switch to a different view."""
        if self.current_view == view_key:
            return

        # Hide current view
        if self.current_view and self.current_view in self.views:
            self.views[self.current_view].pack_forget()
            self.views[self.current_view].on_hide()

        # Show new view
        self.views[view_key].pack(fill='both', expand=True)
        self.views[view_key].on_show()
        self.current_view = view_key

        # Update nav button styles
        for key, (frame, label) in self.nav_buttons.items():
            if key == view_key:
                frame.configure(bg=self.BG_ACTIVE)
                label.configure(bg=self.BG_ACTIVE, fg=self.ACCENT,
                              font=self.nav_font_bold)
            else:
                frame.configure(bg=self.BG_SIDEBAR)
                label.configure(bg=self.BG_SIDEBAR, fg=self.TEXT_DIM,
                              font=self.nav_font)

    def _on_hover(self, frame, label, key, entering):
        """Handle navigation hover effect."""
        if key == self.current_view:
            return

        if entering:
            frame.configure(bg='#1a1a35')
            label.configure(bg='#1a1a35', fg=self.TEXT_PRIMARY)
        else:
            frame.configure(bg=self.BG_SIDEBAR)
            label.configure(bg=self.BG_SIDEBAR, fg=self.TEXT_DIM)

    def destroy(self):
        """Clean up resources before closing."""
        for view in self.views.values():
            if hasattr(view, 'on_hide'):
                view.on_hide()
        super().destroy()
