from pythonosc import udp_client
import numpy as np
import time
import signal
import sys

client = udp_client.SimpleUDPClient("127.0.0.1", 4560)

def signal_handler(sig, frame):
    print("\nExiting cleanly...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Your note sending code
#my_notes = [60, 62, 64, 65, 67]

my_notes = np.load('heights.npy')

# Scale to MIDI range, then round
my_notes_scaled = np.interp(my_notes, 
                             (my_notes.min(), my_notes.max()), 
                             (60, 84))
my_notes = np.round(my_notes_scaled).astype(int)

print(my_notes)

for note in my_notes:
    print(f"Sending note {note}...")
    client.send_message("/play_note", int(note))
    time.sleep(0.2)

print("Done!")