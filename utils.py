from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog
from PyQt5 import QtGui, QtWidgets
from pyqtgraph import PlotWidget, QtCore
import os
import numpy as np
import random
from signal import Signal


class Utils:
# Button Style
    button_style_sheet = """
    QPushButton {
        background-color: #d3d3d3;  
        color: black;
        font-size: 14px;
        padding: 2px;
        font-weight: bold;
        border-radius: 10px;
        width:20px;
        height:20px;
        border: 2px solid #28a745; 
        border-width: 3px; 
    }
    QPushButton:hover {
        background-color: #5a6268;  
        border: 2px solid #ffffff;  
    }
    QPushButton:pressed {
        background-color: #495057;   
    }
    """

    # Slider Style
    slider_style_sheet = """
    QSlider {
        background-color: #343a40;  
        padding :0px;
    }
    QSlider::groove:horizontal {
        border: 1px solid #495057;  
        height: 8px;
        background: #212529;  
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #28a745;  
        border: 2px solid #495057;  
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }
    QSlider::handle:horizontal:hover {
        background: #218838; 
        border: 2px solid #495057;

    }
    QSlider::sub-page:horizontal {
        background: #28a745; 
        border-radius: 4px;
    }
    QSlider::add-page:horizontal {
        background: #212529;  
        border-radius: 4px;
    }
    """

    # Window Style
    window_style_sheet = "background-color: #343a40;"

    # CheckBox Style
    checkBox_style_sheet = """
    QCheckBox {
        color: #cfd8dc;  
        font-size: 14px;
        padding: 5px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 2px solid #495057;  
        background-color: #495057; 
    }
    QCheckBox::indicator:checked {
        background-color: #28a745;  
        border: 2px solid #495057;  
    }
    QCheckBox::indicator:hover {
        border: 2px solid #28a745;  
    }
    """

    # LineEdit Style
    lineEdit_style_sheet = """
    QLineEdit {
        color: white;
        font-size: 16px;
        padding: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
        border: 2px solid #495057; 
        border-radius: 10px;
        background-color: #212529;  
    }
    """

    # Label Style
    label_style_sheet = """
    QLabel {
        color: white;
        font-size: 14px;
        padding-bottom: 5px;
    }
    """

    # Tab Style
    tab_style_sheet = """
    QTabBar::tab {
        color: black;  /* Bold black text */
        font-weight: bold;  /* Making the text bold */
        background-color: #495057;  /* Darker gray for normal state */
        padding: 10px;  /* Adding some padding for better appearance */
        border: 1px solid #343a40;  /* Border color, slightly darker gray */
        border-radius: 10px;
    }
    QTabBar::tab:selected {
        background: #28a745;  /* Green for selected tab */
        color: black;  /* Ensure text remains black when selected */
    }
    QTabBar::tab:hover {
        background: #6c757d;  /* Light gray on hover */
        color: black;  /* Keep text black on hover */
    }
    """

    # ComboBox Style
    comboBox_style_sheet = """
    QComboBox {
        color: white;
        font-size: 16px;
        padding: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
        border: 2px solid #495057;  
        border-radius: 10px;
        background-color: #212529; 
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #212529;  
        color: white;
    }
    QComboBox QAbstractItemView::item {
        background-color: #212529;  
        color: white;
    }
    QComboBox::item:selected {
        background-color: #495057;  
        color: white;
    }
    """
  
    @staticmethod
    def generate_square_wave(points):
        t = np.linspace(0, points/100, points)
        return (t < 0.5).astype(int)

    @staticmethod
    def generate_cosine_wave(points):
        t = np.linspace(0, points/100, points)
        return (np.cos(2*np.pi*5*t))

    @staticmethod
    def generate_sine_wave(points):
        t = np.linspace(0, points/100, points)
        return (np.sin(2*np.pi*5*t))

    @staticmethod
    def create_button(text, method, icon_name='', stylesheet=button_style_sheet, set_enabled=True):
        button = QtWidgets.QPushButton(text)

        button.setStyleSheet(stylesheet)
        # Set size policy to allow stretching
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Fixed)

        # Optional icon for the button
        if icon_name:
            base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(
                base_path, 'assets', 'button_icons', icon_name + '.png')
            icon = QtGui.QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(30, 30))  # Enlarge the icon size

        else:
            button.setText(text)
        # Connect the button to the method
        button.clicked.connect(method)
        button.setEnabled(set_enabled)

        return button

    @staticmethod
    def update_button(button, text, icon_name):
        button.setText(text)
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(
            base_path, 'assets', 'button_icons', icon_name + '.png')
        icon = QtGui.QIcon(icon_path)
        button.setIcon(icon)
        return button

    @staticmethod
    def show_error_message(message):
        # Create a message for error
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Error")
        msg_box.setWindowIcon(QtGui.QIcon("assets\\Pulse.png"))
        msg_box.exec_()

    @staticmethod
    def show_info_message(message, glue=False):
        # create message for information with 2 options
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(message)
        msg_box.setWindowTitle("Information")
        msg_box.setWindowIcon(QtGui.QIcon("assets\\Pulse.png"))
        if glue:
            # Add custom buttons for glue
            reset_button = msg_box.addButton("Reset", QMessageBox.ActionRole)
            continue_button = msg_box.addButton(
                "Continue", QMessageBox.AcceptRole)
            # Execute message box
            msg_box.exec_()
            # know which button was clicked
            if msg_box.clickedButton() == reset_button:
                return "reset"
            else:
                return "continue"

    @staticmethod
    def show_warning_message(message):
        # Create a QMessageBox for warning
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Warning")
        msg_box.setWindowIcon(QtGui.QIcon("assets\\Pulse.png"))
        msg_box.exec_()

    @staticmethod
    # browsing local signal files, returning signal data as np array
    def import_signal_file(plot):
        file_name, _ = QFileDialog.getOpenFileName()
        sampling_rate = 1
        if file_name:
            extension = os.path.splitext(file_name)[1].lower()
            if extension == '.csv':
                with open(file_name, mode='r') as file:
                    # Read the sampling rate from the first line
                    sampling_rate = float(file.readline().strip())

                    # Load the remaining data into a NumPy array
                    signal_data = np.genfromtxt(file, delimiter=',')

                # Optionally, you can return or use the sampling rate as needed
                print("Sampling Rate:", sampling_rate)
            elif extension == '.txt':
                # Assuming space-separated signal data in TXT file
                signal_data = np.loadtxt(file_name)
            elif extension == '.bin':
                with open(file_name, 'rb') as f:
                    # Load binary data assuming it's float32 by default
                    signal_data = np.fromfile(f, dtype=np.dtype)
            else:
                Utils.show_error_message("Unsupported file format.")
                return
        else:
            return

        if signal_data.ndim == 1:
            new_signal = Signal(
                signal_data=signal_data,
                color=Utils.generate_random_light_color(),
                title=os.path.splitext(os.path.basename(file_name))[0],
                f_sample=sampling_rate
            )

            # Append the newly created Signal instance to the signals list
            plot.signals.append(new_signal)
            plot.max_length = max(plot.max_length, len(signal_data))
            plot.update_max_time(np.linspace(
                0, plot.max_length / sampling_rate, plot.max_length))
            plot.plot_signals()

        else:
            Utils.show_error_message(
                "Unsupported signal dimension." + str(signal_data.ndim))

    @staticmethod
    def generate_random_light_color():
        # Generate RGB values that are in a range that avoids dark colors
        r = random.randint(128, 255)
        g = random.randint(128, 255)
        b = random.randint(128, 255)
        return (r, g, b)
