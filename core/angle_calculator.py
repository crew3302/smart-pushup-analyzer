"""
Angle Calculator Module
Computes joint angles from 2D/3D landmark coordinates.
"""

import numpy as np


def calculate_angle(point_a, point_b, point_c):
    """
    Calculate the angle at point_b formed by the line segments
    point_a -> point_b and point_c -> point_b.

    Args:
        point_a: tuple (x, y) or (x, y, z, vis)
        point_b: tuple (x, y) or (x, y, z, vis)
        point_c: tuple (x, y) or (x, y, z, vis)

    Returns:
        Angle in degrees (0–180).
    """
    a = np.array(point_a[:2], dtype=np.float64)
    b = np.array(point_b[:2], dtype=np.float64)
    c = np.array(point_c[:2], dtype=np.float64)

    ba = a - b
    bc = c - b

    dot = np.dot(ba, bc)
    mag_ba = np.linalg.norm(ba)
    mag_bc = np.linalg.norm(bc)

    if mag_ba == 0 or mag_bc == 0:
        return 0.0

    cos_angle = np.clip(dot / (mag_ba * mag_bc), -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))

    return round(angle, 1)


def get_pushup_angles(landmarks):
    """
    Compute the three critical push-up angles from landmarks dict.

    Returns:
        dict with keys: left_elbow_angle, right_elbow_angle,
                        left_hip_angle, right_hip_angle,
                        left_shoulder_angle, right_shoulder_angle
        or None if landmarks are insufficient.
    """
    if landmarks is None:
        return None

    required = [
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle',
    ]
    for key in required:
        if key not in landmarks:
            return None

    angles = {}

    # Elbow angles: shoulder -> elbow -> wrist
    angles['left_elbow_angle'] = calculate_angle(
        landmarks['left_shoulder'],
        landmarks['left_elbow'],
        landmarks['left_wrist'],
    )
    angles['right_elbow_angle'] = calculate_angle(
        landmarks['right_shoulder'],
        landmarks['right_elbow'],
        landmarks['right_wrist'],
    )

    # Hip angles: shoulder -> hip -> knee (body straightness)
    angles['left_hip_angle'] = calculate_angle(
        landmarks['left_shoulder'],
        landmarks['left_hip'],
        landmarks['left_knee'],
    )
    angles['right_hip_angle'] = calculate_angle(
        landmarks['right_shoulder'],
        landmarks['right_hip'],
        landmarks['right_knee'],
    )

    # Shoulder angles: elbow -> shoulder -> hip (arm extension)
    angles['left_shoulder_angle'] = calculate_angle(
        landmarks['left_elbow'],
        landmarks['left_shoulder'],
        landmarks['left_hip'],
    )
    angles['right_shoulder_angle'] = calculate_angle(
        landmarks['right_elbow'],
        landmarks['right_shoulder'],
        landmarks['right_hip'],
    )

    return angles
