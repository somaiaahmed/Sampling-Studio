import os
import random
from matplotlib import pyplot as plt
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem

from signal_construct import Signal



class SignalMixer(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()  # Define a signal to emit when updating
    update_noise = QtCore.pyqtSignal()
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
        self.amplitude_input.setRange(0, 10)  # pahse range
        self.amplitude_input.setDecimals(2)
        self.amplitude_input.setValue(1)  # Default pahse

        self.phase_input = QtWidgets.QDoubleSpinBox()
        self.phase_input.setRange(-180, 180)  # Amplitude range
        self.phase_input.setDecimals(2)
        self.phase_input.setValue(0)  # Default amplitude

        # SNR Slider
        self.snr_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.snr_slider.setRange(0, 100)  # SNR range in dB
        self.snr_slider.setValue(100)  # Default SNR level
        self.snr_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.snr_slider.setTickInterval(10)

        self.snr_label = QtWidgets.QLabel("SNR Level: 20 dB")
        # Connect SNR slider to update label
        self.snr_slider.valueChanged.connect(self.update_snr_label)

        add_button = QtWidgets.QPushButton("Add Signal")
        add_button.clicked.connect(self.add_signal)

        add_component_button = QtWidgets.QPushButton("Add Component")
        add_component_button.clicked.connect(self.add_component)


        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.setObjectName("removeButton")
        remove_button.clicked.connect(self.remove_signal)

        # update_button = QtWidgets.QPushButton("Update Original Signal")
        # update_button.clicked.connect(self.emit_update_signal)  # Connect to signal emission

        import_button = QtWidgets.QPushButton("Import Signals")
        import_button.clicked.connect(self.import_signal_file)  # Connect to import function


        self.signal_list = QTreeWidget()
        self.signal_list.setHeaderHidden(True)

        
        layout.addWidget(self.signal_list)

        control_container = QtWidgets.QGroupBox("")
        control_container_layout = QtWidgets.QVBoxLayout(control_container)

        control_container_layout.addWidget(QtWidgets.QLabel("Frequency (Hz):"))
        control_container_layout.addWidget(self.frequency_input)
        control_container_layout.addWidget(QtWidgets.QLabel("Amplitude:"))
        control_container_layout.addWidget(self.amplitude_input)
        control_container_layout.addWidget(QtWidgets.QLabel("Phase:"))
        control_container_layout.addWidget(self.phase_input)

        control_container_layout.addWidget(add_button)
        control_container_layout.addWidget(add_component_button)
        control_container_layout.addWidget(remove_button)
        # control_container_layout.addWidget(update_button)
        control_container_layout.addWidget(import_button)
        
        control_container_layout.addWidget(QtWidgets.QLabel("Select SNR (dB):"))
        control_container_layout.addWidget(self.snr_slider)
        control_container_layout.addWidget(self.snr_label)

        control_container.setObjectName("control_container")

        # Add the control_container to the main layout
        layout.addWidget(control_container)
        


        with open("style/mixer.qss", "r") as f:
            self.setStyleSheet(f.read())

    def update_snr_label(self):
        snr_value = self.snr_slider.value()
        self.snr_label.setText(f"SNR Level: {snr_value} dB")
        self.update_noise.emit()

    def add_signal(self):
        
        self.signals.append([])
        self.update_signal_list()
        self.emit_update_signal()

    def add_component(self):
        if not self.signals:
            self.add_signal()

        frequency = self.frequency_input.value()
        amplitude = self.amplitude_input.value()
        phase = self.phase_input.value()
        
        self.signals[-1].append((frequency, amplitude, phase))
        self.update_signal_list()
        self.emit_update_signal()

    def remove_signal(self):
        selected_item = self.signal_list.currentItem()
        if selected_item:
            parent = selected_item.parent()
            
            if parent:
                index = parent.indexOfChild(selected_item)
                parent.takeChild(index)
                # Remove component from signals list
                signal_index = self.signal_list.indexOfTopLevelItem(parent)
                if signal_index >= 0 and signal_index < len(self.signals):
                    del self.signals[signal_index][index]
            else:
                # Top level item (signal)
                index = self.signal_list.indexOfTopLevelItem(selected_item)
                if index >= 0 and index < len(self.signals):
                    self.signals.pop(index)
                    self.signal_list.takeTopLevelItem(index)

        self.emit_update_signal()


    def update_signal_list(self):
        self.signal_list.clear()
        for i, signal in enumerate(self.signals):
            signal_item = QTreeWidgetItem([f"Signal {i+1}"])
            
            for component in signal:
                frequency, amplitude, phase = component
                component_text = f"Frequency: {frequency} Hz, Amplitude: {amplitude}, Phase: {phase}"
                signal_item.addChild(QTreeWidgetItem([component_text]))

            # Add the signal item as a top-level item in the tree
            self.signal_list.addTopLevelItem(signal_item)


    def emit_update_signal(self):
        self.update_signal.emit()  # Emit the signal to notify the main app

    def compose_signal(self, time):
        """Compose the mixed signal based on the current signals."""
        mixed_signal = np.zeros_like(time)
        for signal in self.signals:
            if isinstance(signal, Signal):
                # If the signal is an instance of Signal, use its data
                mixed_signal += signal.data  # Assumes signal.data is a numpy array of the same length as time
            elif isinstance(signal, list):  # Check if the signal is a list of components
                for component in signal:
                    if isinstance(component, tuple) and len(component) == 3:
                        frequency, amplitude, phase = component
                        mixed_signal += amplitude * np.sin(2 * np.pi * frequency * time + phase * np.pi / 360)
                    else:
                        raise ValueError("Unsupported component format: {}".format(component))
            else:
                raise ValueError("Unsupported signal format: {}".format(signal))

        return mixed_signal

        
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
