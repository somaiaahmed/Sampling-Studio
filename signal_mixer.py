import os
import random
from matplotlib import pyplot as plt
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem

from signal_construct import Signal



class SignalMixer(QtWidgets.QWidget):
    update_signal = QtCore.pyqtSignal()  
    update_noise = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.signals = []  # list of tuples: (frequency, amplitude, phase)
        self.initUI()
        self.max_length = 0  
        self.time = np.linspace(0, 1, 1000) 
        self.mixed_signal = np.zeros_like(self.time)  

    def initUI(self):

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.frequency_input = QtWidgets.QSpinBox()
        self.frequency_input.setRange(0, 100) 
        self.frequency_input.setValue(5) 

        self.amplitude_input = QtWidgets.QSpinBox()
        self.amplitude_input.setRange(0, 10)  
        self.amplitude_input.setValue(1) 

        self.phase_input = QtWidgets.QSpinBox()
        self.phase_input.setRange(-180, 180) 
        self.phase_input.setValue(0)  

        #SNR slider :
        self.snr_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.snr_slider.setRange(0, 100) 
        self.snr_slider.setValue(100)  
        self.snr_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.snr_slider.setTickInterval(10)

        self.snr_label = QtWidgets.QLabel(f"SNR Level: {self.snr_slider.value()} dB")
        self.snr_slider.valueChanged.connect(self.update_snr_label)

        add_button = QtWidgets.QPushButton("Add Signal")
        add_button.clicked.connect(self.add_signal)

        add_component_button = QtWidgets.QPushButton("Add Component")
        add_component_button.clicked.connect(self.add_component)

        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.setObjectName("removeButton")
        remove_button.clicked.connect(self.remove_signal)

        import_button = QtWidgets.QPushButton("Import")
        import_button.clicked.connect(self.import_signal_file)

        self.export_button = QtWidgets.QPushButton("Export") 

        import_export_layout = QtWidgets.QHBoxLayout()
        import_export_layout.addWidget(import_button)
        import_export_layout.addWidget(self.export_button)


        self.signal_list = QTreeWidget()
        self.signal_list.setHeaderHidden(True)
        self.signal_list.clicked.connect(self.emit_update_signal)

        
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
        control_container_layout.addLayout(import_export_layout)
        
        control_container_layout.addWidget(QtWidgets.QLabel("Select SNR (dB):"))
        control_container_layout.addWidget(self.snr_slider)
        control_container_layout.addWidget(self.snr_label)

        control_container.setObjectName("control_container")

        layout.addWidget(control_container)
        
        with open("style/mixer.qss", "r") as f:
            self.setStyleSheet(f.read())

    def update_snr_label(self):
        self.snr_label.setText(f"SNR Level: {self.snr_slider.value()} dB")
        self.update_noise.emit()

    def add_signal(self):
        self.signals.append([])
        self.update_signal_list()
        self.emit_update_signal()

    def add_component(self, imported_signal=None):
        #if there's no signal it appends a new signal and put components into it 
        if not self.signals:
            self.add_signal()

        if isinstance(imported_signal, Signal):
            signal = imported_signal
        else:
            frequency = self.frequency_input.value()
            amplitude = self.amplitude_input.value()
            phase = self.phase_input.value()
            signal = (frequency, amplitude, phase)

        selected_item = self.signal_list.currentItem()
        if selected_item:
            parent = selected_item.parent()
            
            if parent:
                index = parent.indexOfChild(selected_item)
                parent.takeChild(index)
                #add a component to signals list by getting its parent index
                signal_index = self.signal_list.indexOfTopLevelItem(parent)
                if signal_index >= 0 and signal_index < len(self.signals):
                    self.signals[signal_index].append(signal)
            else:
                index = self.signal_list.indexOfTopLevelItem(selected_item)
                if index >= 0 and index < len(self.signals):
                    self.signals[index].append(signal)

        else:
            #if no item is selected, it appends comonents to last signal of tree
            self.signals[-1].append(signal)
        self.update_signal_list()
        self.emit_update_signal()

    def remove_signal(self):
        selected_item = self.signal_list.currentItem()
        if selected_item:
            parent = selected_item.parent()
            
            if parent:
                index = parent.indexOfChild(selected_item)
                parent.takeChild(index)
                #remove a component from signals list by getting its parent index
                signal_index = self.signal_list.indexOfTopLevelItem(parent)
                if signal_index >= 0 and signal_index < len(self.signals):
                    del self.signals[signal_index][index]
            else:
                #top level item (signal) --> default
                index = self.signal_list.indexOfTopLevelItem(selected_item)
                if index >= 0 and index < len(self.signals):
                    self.signals.pop(index)
                    self.signal_list.takeTopLevelItem(index)

            self.emit_update_signal()


    def update_signal_list(self):
        self.signal_list.clear()
        #loop throgh signals getting each index and its signal from enum
        for i, signal in enumerate(self.signals):
            #create tree widget for each signal 
            signal_item = QTreeWidgetItem([f"Signal {i+1}"])

            for component in signal:
                if isinstance(component, tuple) and len(component) == 3:
                    frequency, amplitude, phase = component
                    component_text = f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase}"
                    signal_item.addChild(QTreeWidgetItem([component_text]))
                elif isinstance(component, Signal):
                    #put signal item at top level of tree
                    signal_item.addChild(QTreeWidgetItem([f"{component.title}"]))
            self.signal_list.addTopLevelItem(signal_item)

    def emit_update_signal(self):
        self.update_signal.emit()  

    def compose_signal(self, time):
        # mixed signal from current signals
        mixed_signal = np.zeros_like(time)
        f_max = 2
        selected_item = self.signal_list.currentItem()
        if selected_item:
            parent = selected_item.parent()
            
            if parent:
                index = parent.indexOfChild(selected_item)
                
                signal_index = self.signal_list.indexOfTopLevelItem(parent)
                if signal_index >= 0 and signal_index < len(self.signals):
                    signal = self.signals[signal_index][index]
            else:                
                index = self.signal_list.indexOfTopLevelItem(selected_item)
                if index >= 0 and index < len(self.signals):
                    signal = self.signals[index]
                
        elif self.signals:
            signal = self.signals[-1]

        if isinstance(signal, list): 
            for component in signal:
                if isinstance(component, tuple) and len(component) == 3:
                    frequency, amplitude, phase = component
                    phase_rad = np.deg2rad(phase)
                    mixed_signal += amplitude * np.sin(2 * np.pi * frequency * time + phase_rad)
                    f_max = frequency if frequency > f_max else f_max
                elif isinstance(component, Signal):
                    if len(component.data) != len(mixed_signal):
                        component_data_resized = np.interp(
                            np.linspace(0, 1, len(mixed_signal)),
                            np.linspace(0, 1, len(component.data)),
                            component.data
                        )
                        mixed_signal += component_data_resized
                    else:
                        mixed_signal += component.data
                    f_max = int(component.f_sample) if int(component.f_sample) > f_max else f_max

                else:
                    raise ValueError("Unsupported component format: {}".format(component))
        elif isinstance(signal, tuple) and len(signal) == 3:
            frequency, amplitude, phase = signal
            phase_rad = np.deg2rad(phase)
            mixed_signal += amplitude * np.sin(2 * np.pi * frequency * time + phase_rad)
            f_max = frequency if frequency > f_max else f_max
        elif isinstance(signal, Signal):
            mixed_signal += signal.data 
            f_max = int(signal.f_sample) if int(signal.f_sample) > f_max else f_max
        else:
            raise ValueError("Unsupported signal format: {}".format(signal))

        return mixed_signal, f_max
    

    def import_signal_file(self):
        file_name, _ = QFileDialog.getOpenFileName()
        sampling_rate = 1
        if file_name:
            extension = os.path.splitext(file_name)[1].lower()
            if extension == '.csv':
                with open(file_name, mode='r') as file:
                    #read sampling rate from 1st line
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
                title=os.path.splitext(os.path.basename(file_name))[0],
                f_sample=sampling_rate
            )

            self.add_component(imported_signal=new_signal)
            self.max_length = max(self.max_length, len(signal_data))
            self.emit_update_signal() 
            
        else:
            self.show_error_message("Unsupported signal dimension: " + str(signal_data.ndim))

        
    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    @staticmethod
    def generate_random_light_color():
        r = random.randint(128, 255)
        g = random.randint(128, 255)
        b = random.randint(128, 255)
        return (r, g, b)
