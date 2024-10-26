import numpy as np
from PyQt5 import QtWidgets


class Signal():

    def __init__(self, signal_data, color='b', title='signal', is_hidden=False, f_sample=100):
        self.data = signal_data
        self.color = color
        self.title = title
        self.is_hidden = is_hidden
        self.frequency = self.calculate_frequency()  # Calculate frequency on initialization
        self.f_sample = f_sample
        self.time_axis = np.linspace(0, len(signal_data) / self.f_sample, len(signal_data))

    def calculate_frequency(self):
        # Implement frequency calculation based on signal_data
        # This is just a placeholder; you should define how to calculate the frequency based on your data
        return np.mean(np.abs(np.fft.rfft(self.data)))  # Example calculation

    def change_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()

    def __lt__(self, other):
        return len(self.data) < len(other.data)

    def __repr__(self):
        return str(self.data)
    
