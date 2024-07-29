from collections import deque
from datetime import time

import numpy as np


class MidiAnalyzer:
    def __init__(self):
        self.notes = deque(maxlen=20)
        self.timestamps = deque(maxlen=20)
        self.velocities = deque(maxlen=20)
        self.active_notes = set()

    def add_note(self, note, velocity):
        self.notes.append(note)
        self.velocities.append(velocity)
        self.active_notes.add(note)

    def remove_note(self, note):
        self.active_notes.discard(note)

    def get_active_notes(self):
        return list(self.active_notes)

    def add_note(self, note, velocity):
        self.notes.append(note)
        self.velocities.append(velocity)

    def get_current_chord(self):
        current_notes = set(self.notes)
        if len(current_notes) >= 3:
            return len(current_notes)  # Return the number of unique notes as a simple measure
        return 0

    def get_playing_intensity(self):
        if self.velocities:
            return sum(self.velocities) / len(self.velocities) / 127.0
        return 0


    def get_pitch_range(self):
        if self.notes:
            return (max(self.notes) - min(self.notes)) / 127.0
        return 0