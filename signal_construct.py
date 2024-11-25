import numpy as np
from PyQt5 import QtWidgets


class Signal():

    def __init__(self, signal_data, title='signal', f_sample=100):
        self.data = signal_data
        self.title = title
        self.f_sample = f_sample
        self.time_axis = np.linspace(0, len(signal_data) / self.f_sample, len(signal_data)) #length of signal_data / f_sample to get duration &spacing points

    def __lt__(self, other):
        return len(self.data) < len(other.data)

    def __repr__(self):
        return str(self.data)
    
