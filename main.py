import sys
import os
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5 import QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph import PlotWidget, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QScrollBar
from utils import Utils
from statistics_window import StatisticsWindow
from interpolation_window import InterpolationWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from signal import Signal
from signal_plot_widget import SignalPlotWidget
from polar import PolarPlotWidget
from realtime_plot import RealTimePlot
import pandas as pd


class SignalApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.signal_to_be_moved = None

        self.original_x_range = self.first_graph.plot_widget.viewRange()[0]  # get initial x range
        self.original_y_range = self.first_graph.plot_widget.viewRange()[1]  # get initial y range
        self.original_x_range = self.second_graph.plot_widget.viewRange()[0]  # get initial x range
        self.original_y_range = self.second_graph.plot_widget.viewRange()[1]  # get initial y range

        SignalPlotWidget.user_interacting = False  #flag for mouse panning
        self.control_pressed = False

        self.first_graph.plot_signals()
        self.source_graph = None



    def initUI(self):
        self.setWindowTitle("Multi-Channel Signal Viewer")  
        self.setWindowIcon(QtGui.QIcon("assets\\Pulse.png")) 
        self.setStyleSheet(Utils.window_style_sheet)

        self.tab_widget = QtWidgets.QTabWidget()

        #adding tabs
        self.tab_widget.addTab(self.main_tab(), "Main")
        self.tab_widget.addTab(self.Polar_tab(), "Polar")
        self.tab_widget.addTab(self.real_time_tab(), "Real-Time")
        self.tab_widget.setStyleSheet(Utils.tab_style_sheet)

        #setting layout of main window to hold tab widget
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)
        self.setLayout(self.main_layout)

        #cnnecting mouse events for selecting/moving signals
        self.first_graph.plot_widget.scene().sigMouseClicked.connect(
            self.on_signal_clicked_first_graph)
        self.second_graph.plot_widget.scene().sigMouseClicked.connect(
            self.on_signal_clicked_second_graph)



    def main_tab(self):
        main_tab = QtWidgets.QWidget()

        main_layout = QtWidgets.QVBoxLayout(main_tab)


        #creating plotting widgets
        self.first_graph = SignalPlotWidget(name='Graph One', signals=[Signal(Utils.generate_sine_wave(100), 'r')])
        self.second_graph = SignalPlotWidget(name='Graph Two', signals=[Signal(Utils.generate_cosine_wave(100), 'r')])

        #setting some buttons
        self.swap_button = Utils.create_button("", self.swap_signals, "swap")
        self.glue_button = Utils.create_button("Glue", self.glue_signals)
        self.link_button = Utils.create_button("", self.toggle_link, "link")

        main_layout.addSpacing(5)
        main_layout.addLayout(self.first_graph.graph_layout)
        main_layout.addSpacing(5)

        #adding the "horizontal" button layout of signal 1 to the main "vertical" layout
        main_layout.addLayout(self.first_graph.button_layout)
        self.first_graph.button_layout.addSpacing(80)
        main_layout.addSpacing(15)

        main_layout.addLayout(self.second_graph.graph_layout)
        main_layout.addSpacing(5)

        #adding the "horizontal" button layout of signal 2 to the main "vertical" layout
        main_layout.addLayout(self.second_graph.button_layout)
        self.second_graph.button_layout.addSpacing(80)
        main_layout.addSpacing(15)

        buttons_layout_3 = QtWidgets.QHBoxLayout()
        buttons_layout_3.addStretch()
        buttons_layout_3.addStretch()
        buttons_layout_3.addStretch()
        buttons_layout_3.addStretch()
        buttons_layout_3.addStretch()
        buttons_layout_3.addStretch()

        buttons_layout_3.addWidget(self.swap_button)
        buttons_layout_3.addWidget(self.link_button)
        buttons_layout_3.addWidget(self.glue_button)

        main_layout.addLayout(buttons_layout_3)

        return main_tab



    def Polar_tab(self):
        polar_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(polar_tab)

        #creating instance of PolarPlotWidget for Matplotlib graph
        self.polar_plot_widget = PolarPlotWidget()
        layout.addWidget(self.polar_plot_widget)

        button_layout = QtWidgets.QHBoxLayout()

        button_layout.addSpacing(200)
        button_layout.addStretch()

        self.polar_play_button = Utils.create_button("", self.polar_plot_widget.play_animation, "play")
        button_layout.addWidget(self.polar_play_button)

        self.polar_pause_button = Utils.create_button("", self.polar_plot_widget.pause_animation, "pause")
        button_layout.addWidget(self.polar_pause_button)

        button_layout.addSpacing(200)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        return polar_tab



    def real_time_tab(self):
        #creating instance of RealTimePlot for real-time graph
        #self.real_time_plot = RealTimePlot()
        #return self.real_time_plot
        pass



    def toggle_link(self):
        SignalPlotWidget.is_linked = not SignalPlotWidget.is_linked
        #sync play state if linked
        if SignalPlotWidget.is_linked:
            #sync visibility of checkboxes
            self.second_graph.show_hide_checkbox.setChecked(self.first_graph.show_hide_checkbox.isChecked())
            self.link_button = Utils.update_button(self.link_button, "", "unlink")
            #dedicated to the case where one of the signals is already playing before linking the 2 graphs together
            if self.first_graph.is_playing:
                self.second_graph.play_pause_signal()
            elif self.second_graph.is_playing:
                self.first_graph.play_pause_signal()

            #determine lower speed and set both sliders to it
            lower_speed_index = min(self.first_graph.speed_slider.value(), self.second_graph.speed_slider.value())
            self.first_graph.speed_slider.setValue(lower_speed_index)
            self.second_graph.speed_slider.setValue(lower_speed_index)
            new_timer_interval = SignalPlotWidget.speed_mapping[lower_speed_index]

            if self.first_graph.timer is not None:
                self.first_graph.timer.setInterval(new_timer_interval)
            if self.second_graph.timer is not None:
                self.second_graph.timer.setInterval(new_timer_interval)
            self.first_graph.link_viewports()

        else:
            self.link_button = Utils.update_button(self.link_button, "", "link")
            self.first_graph.unlink_viewports()

        #ensure consistent signal speeds
        if SignalPlotWidget.is_linked:
            if self.first_graph.timer is not None and self.second_graph.timer is not None:
                if self.first_graph.timer.interval() != self.second_graph.timer.interval():
                    self.second_graph.timer.setInterval(self.first_graph.timer.interval())  #sync intervals



    def swap_signals(self):
        self.first_graph.signals, self.second_graph.signals = self.second_graph.signals, self.first_graph.signals

        #swappin text of  title input boxes
        title_text_1 = self.first_graph.title_input.text()
        title_text_2 = self.second_graph.title_input.text()
        self.first_graph.title_input.setText(title_text_2)
        self.second_graph.title_input.setText(title_text_1)

        #swapping state of visibility checkboxes
        self.first_graph.show_hide_checkbox1_stat = self.first_graph.show_hide_checkbox.isChecked()
        self.second_graph.show_hide_checkbox2_stat = self.second_graph.show_hide_checkbox.isChecked()
        self.first_graph.show_hide_checkbox.setChecked(self.second_graph.show_hide_checkbox2_stat)
        self.second_graph.show_hide_checkbox.setChecked(self.first_graph.show_hide_checkbox1_stat)

        #ensure visibility reflects swapped states
        self.first_graph.toggle_signal(Qt.Checked if self.second_graph.show_hide_checkbox2_stat else Qt.Unchecked)
        self.second_graph.toggle_signal(Qt.Checked if self.first_graph.show_hide_checkbox1_stat else Qt.Unchecked)

        self.first_graph.selected_signal, self.second_graph.selected_signal = self.second_graph.selected_signal, self.first_graph.selected_signal
        self.first_graph.plot_signals()



    def glue_signals(self):
        if self.first_graph.selected_signal and self.second_graph.selected_signal:
            self.interpolation_window = InterpolationWindow(
                self.first_graph.selected_signal, self.second_graph.selected_signal)  #generating Intepolation Window
            self.interpolation_window.show()  # showing Interpolation Window
        else:
            Utils.show_error_message("Each graph must have a selected signal")

    def on_signal_clicked_first_graph(self, event):
        # if self.control_pressed:
        self.on_signal_clicked(event, self.first_graph)

    def on_signal_clicked_second_graph(self, event):
        # if self.control_pressed:
        self.on_signal_clicked(event, self.second_graph)

    def on_signal_clicked(self, event, source_graph):

        self.signal_to_be_moved = source_graph.selected_signal
        self.source_graph = source_graph
        print(self.source_graph.name)
        if self.control_pressed:
            self.grabMouse()  #grab mouse to track where release happens

    def mouseReleaseEvent(self, event):
        #check if mouse release occurred on different graph
        if self.signal_to_be_moved:
            release_pos = event.pos()  #get release position in widget
            target_graph = None

            #determine if mouse release is on 2nd graph
            if self.second_graph.plot_widget.geometry().contains(release_pos):
                target_graph = self.second_graph
            elif self.first_graph.plot_widget.geometry().contains(release_pos):
                target_graph = self.first_graph
            
            #move signal from source graph to target graph
            if target_graph and target_graph != self.source_graph:
                if len(self.source_graph.signals) > 1:
                    self.source_graph.signals.remove(self.signal_to_be_moved)
                    target_graph.signals.append(self.signal_to_be_moved)
                    # target_graph.selected_signal = self.signal_to_be_moved
                    
                    target_graph.update_graph()
                    self.source_graph.update_graph()
                    # target_graph.plot_signals()
                else:
                    print("Empty graph")
            #clear selected signal and source graph
            self.signal_to_be_moved = None
            self.source_graph = None

        self.releaseMouse()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            if not self.control_pressed:
                self.control_pressed = True
                print("clicked")
        if event.key() == Qt.Key_Alt and self.source_graph:
            print("pressed")
            if len(self.source_graph.signals) > 1:
                self.source_graph.signals.remove(self.source_graph.selected_signal)
                self.source_graph.update_graph()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            if self.control_pressed:
                self.control_pressed = False
                print("released")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = SignalApp()
    ex.resize(900, 700)
    ex.show()
    sys.exit(app.exec_())
