"""
Performance Logger Module
SQLite-based session history for push-up workouts.
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pushup_history.db')


def _get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the sessions table if it doesn't exist."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_reps INTEGER NOT NULL,
            correct_reps INTEGER NOT NULL,
            partial_reps INTEGER NOT NULL,
            incorrect_reps INTEGER NOT NULL,
            avg_speed REAL NOT NULL,
            duration REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def save_session(total_reps, correct_reps, partial_reps, incorrect_reps, avg_speed, duration):
    """Save a workout session to the database."""
    if total_reps == 0:
        return

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (date, total_reps, correct_reps, partial_reps, incorrect_reps, avg_speed, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_reps, correct_reps, partial_reps, incorrect_reps,
        round(avg_speed, 2), round(duration, 2),
    ))
    conn.commit()
    conn.close()


def get_history(limit=50):
    """Retrieve recent session history."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sessions ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_stats_summary():
    """Get aggregate stats across all sessions."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            COUNT(*) as total_sessions,
            COALESCE(SUM(total_reps), 0) as lifetime_reps,
            COALESCE(SUM(correct_reps), 0) as lifetime_correct,
            COALESCE(SUM(partial_reps), 0) as lifetime_partial,
            COALESCE(SUM(incorrect_reps), 0) as lifetime_incorrect,
            COALESCE(AVG(avg_speed), 0) as avg_rep_speed,
            COALESCE(SUM(duration), 0) as total_duration
        FROM sessions
    ''')
    row = cursor.fetchone()
    conn.close()

    if row:
        result = dict(row)
        total = result['lifetime_reps']
        result['form_score'] = round(
            (result['lifetime_correct'] / max(1, total)) * 100, 1
        )
        return result

    return {
        'total_sessions': 0,
        'lifetime_reps': 0,
        'lifetime_correct': 0,
        'lifetime_partial': 0,
        'lifetime_incorrect': 0,
        'avg_rep_speed': 0,
        'total_duration': 0,
        'form_score': 0,
    }


def delete_all_history():
    """Clear all session history."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions')
    conn.commit()
    conn.close()


# Initialize database on module import
init_db()
