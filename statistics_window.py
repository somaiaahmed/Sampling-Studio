import numpy as np
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget

class StatisticsWindow(QtWidgets.QWidget):
    def __init__(self, signal, title, color, actual_signal):
        super().__init__()
        self.signal = signal
        self.title = title
        self.color = color
        self.actual_signal = actual_signal
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setStyleSheet("background-color: #042630;")
        
        layout = QtWidgets.QVBoxLayout()
        
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('#001414')
        self.plot_widget.plot(self.actual_signal.time_axis,self.signal, pen=self.color)
        self.plot_widget.setTitle(self.title)
        layout.addWidget(self.plot_widget)

        self.stats_labels = [
            ("Mean: ", self.calculate_mean),
            ("Standard Deviation: ", self.calculate_std),
            ("Duration: ", self.calculate_duration),
            ("Min: ", self.calculate_min),
            ("Max: ", self.calculate_max),
            ("Sampling Rate: ", self.calculate_sampling_rate)
        ]

        self.result_labels = []  

        for stat_name, method in self.stats_labels:
            h_layout = QtWidgets.QHBoxLayout()

            name_label = QtWidgets.QLabel(stat_name)
            name_label.setStyleSheet("""
                QLabel {
                    color: #adb4b4;  /* Light teal color */
                    font-size: 18px;  /* Larger font size for visibility */
                    font-weight: bold;  /* Make font bold */
                    padding: 5px;      /* Add padding for aesthetics */
                }
            """)

            value_label = QtWidgets.QLabel("Calculating...") 
            value_label.setStyleSheet("""
                QLabel {
                    color: #d0d6d6;  /* Light grey color */
                    font-size: 16px;  /* Slightly smaller font size for values */
                    font-weight: bold;  /* Make font bold */
                    margin-left: 10px;  /* Add space between name and value */
                }
            """)

            h_layout.addWidget(name_label)
            h_layout.addWidget(value_label)

            layout.addLayout(h_layout)

            self.result_labels.append(value_label)

        #back button
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #adb4b4;  /* Custom color */
                color: black;
                font-size: 16px;  /* Override the font size */
                font-weight: bold;  /* Make the font bold */
                padding: 12px;  /* Custom padding */
                width: 100px;  /* Set specific width */
                border-radius: 15px;  /* Custom border radius */
                border: 2px solid #4c7273;
            }
            QPushButton:hover {
                background-color: #4c7273;  /* Custom hover color */
                border-radius: 15px;  /* Custom border radius */
                border: 2px solid white;                       
            }
            QPushButton:pressed {
                background-color: #86b9b0;
            }
        """)
        self.back_button.clicked.connect(self.close)
        layout.addWidget(self.back_button)

        self.setLayout(layout)

        self.update_statistics()

    def update_statistics(self):
        """Calculate and update all statistics in the labels."""
        self.result_labels[0].setText(f"{self.calculate_mean():.2f}")
        self.result_labels[1].setText(f"{self.calculate_std():.2f}")
        self.result_labels[2].setText(f"{self.calculate_duration()} mS")
        self.result_labels[3].setText(f"{self.calculate_min():.2f}")
        self.result_labels[4].setText(f"{self.calculate_max():.2f}")
        self.result_labels[5].setText(f"{self.calculate_sampling_rate()} Hz")

    def calculate_mean(self):
        return np.mean(self.signal)

    def calculate_std(self):
        return np.std(self.signal)

    def calculate_duration(self):
        return len(self.signal)*1000/self.actual_signal.f_sample

    def calculate_min(self):
        return np.min(self.signal)

    def calculate_max(self):
        return np.max(self.signal)

    def calculate_sampling_rate(self):
        return self.actual_signal.f_sample
