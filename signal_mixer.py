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
        self.time = np.linspace(0, 1, 1000)  # Time array for plotting (adjust as needed)
        self.mixed_signal = np.zeros_like(self.time)  # Initialize mixed signal

    def initUI(self):
        self.setWindowTitle("Signal Mixer")
        self.setGeometry(200, 200, 400, 300)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.frequency_input = QtWidgets.QSpinBox()
        self.frequency_input.setRange(0, 100)  # Frequency range
        #self.frequency_input.setDecimals(2)
        self.frequency_input.setValue(5)  # Default frequency

        self.amplitude_input = QtWidgets.QSpinBox()
        self.amplitude_input.setRange(0, 10)  # phase range
        #self.amplitude_input.setDecimals(2)
        self.amplitude_input.setValue(1)  # Default phase

        self.phase_input = QtWidgets.QSpinBox()
        self.phase_input.setRange(-180, 180)  # Amplitude range
        #self.phase_input.setDecimals(2)
        self.phase_input.setValue(0)  # Default amplitude

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

        remove_button = QtWidgets.QPushButton("Remove Signal")
        remove_button.clicked.connect(self.remove_signal)

        import_button = QtWidgets.QPushButton("Import Signals from File")
        import_button.clicked.connect(self.import_signal_file)  # Connect to import function


        self.signal_list = QtWidgets.QListWidget()

        layout.addWidget(QtWidgets.QLabel("Frequency (Hz):"))
        layout.addWidget(self.frequency_input)
        layout.addWidget(QtWidgets.QLabel("Amplitude:"))
        layout.addWidget(self.amplitude_input)
        layout.addWidget(QtWidgets.QLabel("Phase:"))
        layout.addWidget(self.phase_input)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)
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
        phase = self.phase_input.value()
        self.signals.append((frequency, amplitude, phase))
        self.update_signal_list()
        self.emit_update_signal()  # Emit the signal to update the graph

    def remove_signal(self):
        selected_item = self.signal_list.currentItem()  # Get the currently selected item
        if selected_item:
            index = self.signal_list.row(selected_item)  # Get the index of the selected item
            if index < len(self.signals):  # Check if the index is valid
                self.signals.pop(index)  # Remove the selected signal
                self.update_signal_list()  # Update the display
                self.emit_update_signal()  # Emit the signal to update the graph

    def update_signal_list(self):
        self.signal_list.clear()
        for signal in self.signals:
            if isinstance(signal, Signal):
                # For imported Signal objects, display the title and length
                self.signal_list.addItem(f"Title: {signal.title}, Length: {len(signal.data)} samples")
            else:
                # Assuming it's a tuple (frequency, amplitude) for composed signals
                frequency, amplitude, phase = signal
                self.signal_list.addItem(f"Frequency: {frequency} Hz, Amplitude: {amplitude}, Phase: {phase}")


    def emit_update_signal(self):
        self.update_signal.emit()  # Emit the signal to notify the main app

    def compose_signal(self, time):
        """Compose the mixed signal based on the current signals."""
        mixed_signal = np.zeros_like(time, dtype=float)  # Initialize as float to avoid casting issues
        
        for signal in self.signals:
            if isinstance(signal, Signal):
                # If the signal is an instance of Signal, use its data
                # Ensure the signal data matches the length of the time array
                if len(signal.data) != len(time):
                    # Resize the signal data to match the time length
                    # You can choose to truncate or pad the signal data
                    signal_data = np.resize(signal.data, time.shape)  # Resize or manipulate as needed
                else:
                    signal_data = signal.data
                mixed_signal += signal_data  # Assumes signal.data is a numpy array of the same length as time
                
            elif isinstance(signal, tuple) and len(signal) == 3:
                # Assuming it's a tuple (frequency, amplitude)
                frequency, amplitude, phase = signal
                mixed_signal += amplitude * np.sin(2 * np.pi * frequency * time + phase * np.pi / 180)
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

