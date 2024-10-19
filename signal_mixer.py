import os
import random
from matplotlib import pyplot as plt
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from signal_construct import Signal



class SignalMixer(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()  # Define a signal to emit when updating

    def __init__(self):
        super().__init__()
        self.signals = []  # List to hold tuples of (frequency, amplitude)
        self.initUI()
        self.max_length = 0  # Initialize max_length to 0


    def initUI(self):
        self.setWindowTitle("Signal Mixer")
        self.setGeometry(200, 200, 400, 300)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.frequency_input = QtWidgets.QDoubleSpinBox()
        self.frequency_input.setRange(0, 100)  # Frequency range
        self.frequency_input.setDecimals(2)
        self.frequency_input.setValue(5)  # Default frequency

        self.amplitude_input = QtWidgets.QDoubleSpinBox()
        self.amplitude_input.setRange(0, 10)  # Amplitude range
        self.amplitude_input.setDecimals(2)
        self.amplitude_input.setValue(1)  # Default amplitude

        # SNR Slider
        self.snr_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.snr_slider.setRange(0, 100)  # SNR range in dB
        self.snr_slider.setValue(20)  # Default SNR level
        self.snr_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.snr_slider.setTickInterval(10)

        self.snr_label = QtWidgets.QLabel("SNR Level: 20 dB")
        # Connect SNR slider to update label
        self.snr_slider.valueChanged.connect(self.update_snr_label)

        add_button = QtWidgets.QPushButton("Add Signal")
        add_button.clicked.connect(self.add_signal)

        remove_button = QtWidgets.QPushButton("Remove Last Signal")
        remove_button.clicked.connect(self.remove_signal)

        update_button = QtWidgets.QPushButton("Update Original Signal")
        update_button.clicked.connect(self.emit_update_signal)  # Connect to signal emission

        import_button = QtWidgets.QPushButton("Import Signals from File")
        import_button.clicked.connect(self.import_signal_file)  # Connect to import function


        self.signal_list = QtWidgets.QListWidget()

        layout.addWidget(QtWidgets.QLabel("Frequency (Hz):"))
        layout.addWidget(self.frequency_input)
        layout.addWidget(QtWidgets.QLabel("Amplitude:"))
        layout.addWidget(self.amplitude_input)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addWidget(update_button)  # Add the update button
        layout.addWidget(import_button)   # Add the import button
        layout.addWidget(QtWidgets.QLabel("Select SNR (dB):"))
        layout.addWidget(self.snr_slider)
        layout.addWidget(self.snr_label)
        layout.addWidget(self.signal_list)

    def update_snr_label(self):
        snr_value = self.snr_slider.value()
        self.snr_label.setText(f"SNR Level: {snr_value} dB")

    def add_signal(self):
        frequency = self.frequency_input.value()
        amplitude = self.amplitude_input.value()
        self.signals.append((frequency, amplitude))
        self.update_signal_list()

    def remove_signal(self):
        if self.signals:
            self.signals.pop()
            self.update_signal_list()

    def update_signal_list(self):
        self.signal_list.clear()
        for signal in self.signals:
            if isinstance(signal, Signal):
                # For imported Signal objects, display the title and length
                self.signal_list.addItem(f"Title: {signal.title}, Length: {len(signal.data)} samples")
            else:
                # Assuming it's a tuple (frequency, amplitude) for composed signals
                frequency, amplitude = signal
                self.signal_list.addItem(f"Frequency: {frequency} Hz, Amplitude: {amplitude}")


    def emit_update_signal(self):
        self.update_signal.emit()  # Emit the signal to notify the main app

    def compose_signal(self, time):
        """Compose the mixed signal based on the current signals."""
        mixed_signal = np.zeros_like(time)
        for signal in self.signals:
            if isinstance(signal, Signal):
                # If the signal is an instance of Signal, use its data
                mixed_signal += signal.data  # Assumes signal.data is a numpy array of the same length as time
            elif isinstance(signal, tuple) and len(signal) == 2:
                # Assuming it's a tuple (frequency, amplitude)
                frequency, amplitude = signal
                mixed_signal += amplitude * np.sin(2 * np.pi * frequency * time)
            else:
                # Handle unexpected signal formats if necessary
                raise ValueError("Unsupported signal format: {}".format(signal))

        # Add noise based on the selected SNR
        snr_db = self.snr_slider.value()  # Get the selected SNR level
        return self.add_noise(mixed_signal, snr_db)
    
    def add_noise(self, signal, snr_db):
        """Add additive noise to the signal based on the specified SNR level."""
        snr_linear = 10 ** (snr_db / 10.0)
        signal_power = np.mean(signal ** 2)
        noise_power = signal_power / snr_linear
        noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)
        return signal + noise
        
    def import_signal_file(self):
        file_name, _ = QFileDialog.getOpenFileName()
        sampling_rate = 1
        if file_name:
            extension = os.path.splitext(file_name)[1].lower()
            if extension == '.csv':
                with open(file_name, mode='r') as file:
                    # Read the sampling rate from the first line
                    sampling_rate = float(file.readline().strip())
                    signal_data = np.genfromtxt(file, delimiter=',')
            elif extension == '.txt':
                signal_data = np.loadtxt(file_name)
            elif extension == '.bin':
                with open(file_name, 'rb') as f:
                    signal_data = np.fromfile(f, dtype=np.float32)
            else:
                self.show_error_message("Unsupported file format.")
                return
        else:
            return

        if signal_data.ndim == 1:
            new_signal = Signal(
                signal_data=signal_data,
                color=self.generate_random_light_color(),
                title=os.path.splitext(os.path.basename(file_name))[0],
                f_sample=sampling_rate
            )

            # Append the newly created Signal instance to the signals list
            self.signals.append(new_signal)
            self.update_signal_list()  # Update the display with the new signal
            self.max_length = max(self.max_length, len(signal_data))
            
            # Update the original graph with the newly imported signal
            self.emit_update_signal()  # Emit signal to update the graph
            
        else:
            self.show_error_message("Unsupported signal dimension: " + str(signal_data.ndim))

        
    def show_error_message(self, message):
        # Display an error message to the user
        QMessageBox.critical(self, "Error", message)

    @staticmethod
    def generate_random_light_color():
        # Generate RGB values that are in a range that avoids dark colors
        r = random.randint(128, 255)
        g = random.randint(128, 255)
        b = random.randint(128, 255)
        return (r, g, b)

    # Add this method to your SignalMixer class
    def plot_signal(self, signal):
        """Plot the given signal using Matplotlib."""
        plt.figure(figsize=(10, 5))  # Create a new figure
        plt.plot(signal.time_axis, signal.data, color=signal.color, label=signal.title)
        plt.title(signal.title)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.grid()
        plt.show()