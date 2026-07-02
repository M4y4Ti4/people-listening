import cv2
import numpy as np
from pythonosc import udp_client

# OSC setup - sends to Sonic Pi
client = udp_client.SimpleUDPClient("127.0.0.1", 4560)

# HOG Person Detector setup
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

cap = cv2.VideoCapture(r"C:\Tracking\videos\cheesymelt.mp4")

# --- Settings ---
THRESHOLD_X = 370
MIN_HEIGHT = 50
MIN_WIDTH = 20

# Pitch range (MIDI notes)
PITCH_MIN, PITCH_MAX = 40, 80
Y_MIN, Y_MAX = 320, 420

# Duration range in seconds
DUR_MIN, DUR_MAX = 0.1, 1.0

# Track previous centroids for crossing detection
prev_centroids = {}

# --- Scale Definitions ---
# Each list contains the semitone intervals within an octave
SCALES = {
    "major":        [0, 2, 4, 5, 7, 9, 11],
    "minor":        [0, 2, 3, 5, 7, 8, 10],
    "pentatonic":   [0, 2, 4, 7, 9],
    "blues":        [0, 3, 5, 6, 7, 10],
    "dorian":       [0, 2, 3, 5, 7, 9, 10],
    "chromatic":    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

ROOT_NOTE = 60   # Middle C (C4) — change to suit your key
                 # 60=C, 61=C#, 62=D, 63=D#, 64=E, 65=F
                 # 66=F#, 67=G, 68=G#, 69=A, 70=A#, 71=B

SCALE = SCALES["pentatonic"]  # ✅ change this to try different scales

def snap_to_scale(pitch, root, scale):
    """Snaps a MIDI pitch to the nearest note in the given scale"""
    # Find which octave we're in
    octave = (pitch - root) // 12
    # Find position within octave
    position = (pitch - root) % 12
    
    # Find nearest scale degree
    nearest = min(scale, key=lambda s: abs(s - position))
    
    # Reconstruct the pitch
    return root + (octave * 12) + nearest

def map_value(value, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another, clamped to output range"""
    value = max(in_min, min(in_max, value))  # clamp input
    return out_min + (value - in_min) / (in_max - in_min) * (out_max - out_min)

def draw_dashed_line(frame, x, dash_length=20, gap_length=10, color=(0, 0, 255), thickness=2):
    """Draws a vertical dashed line at a given x coordinate"""
    frame_height = frame.shape[0]
    y = 0
    while y < frame_height:
        y_end = min(y + dash_length, frame_height)
        cv2.line(frame, (x, y), (x, y_end), color, thickness)
        y += dash_length + gap_length

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detect people using HOG
    boxes, weights = hog.detectMultiScale(
        frame,
        winStride=(8, 8),
        padding=(4, 4),
        scale=1.05
    )

    # Draw threshold line
    draw_dashed_line(frame, THRESHOLD_X)

    current_centroids = {}

    for i, (x, y, w, h) in enumerate(boxes):
        centroid_x = x + w // 2
        centroid_y = y + h // 2

        # Draw bounding box and centroid
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame, (centroid_x, centroid_y), 4, (255, 0, 0), -1)
        cv2.putText(frame, f"h:{h} w:{w}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        current_centroids[i] = centroid_x

        # --- Crossing Detection ---
        prev_x = prev_centroids.get(i, centroid_x)

        is_crossing = (prev_x < THRESHOLD_X <= centroid_x or   # left to right
                       prev_x > THRESHOLD_X >= centroid_x)     # right to left

        if is_crossing:
            rawpitch = int(map_value(h, 50, 300, PITCH_MIN, PITCH_MAX))
            pitch = snap_to_scale(pitch = rawpitch, root=ROOT_NOTE, scale=SCALE)
            duration = round(map_value(centroid_y, Y_MIN, Y_MAX, DUR_MAX, DUR_MIN), 2)
            print(f"✅ Crossing! pitch={pitch}, duration={duration}, y={centroid_y}")



            # Send to Sonic Pi via OSC
            client.send_message("/trigger/note", [pitch, duration])

    # Update previous centroids
    prev_centroids = current_centroids

    cv2.imshow("People Tracking", frame)

    if cv2.waitKey(40) == 27:  # ESC to quit
        break

cv2.destroyAllWindows()
cap.release()