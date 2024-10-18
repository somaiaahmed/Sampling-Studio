import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget
import pyqtgraph as pg
from pyqtgraph import PlotWidget
from PyQt5 import QtGui, QtWidgets
from utils import Utils
from pyqtgraph import PlotWidget, QtCore
from PyQt5.QtCore import Qt
from statistics_window import StatisticsWindow
from signal import Signal


class SignalPlotWidget():

    is_linked = False
    syncing = False
    user_interacting = False
    stopped_by_link = False
    graph_instances = []
    speed_mapping = {
        0: 200,  # x1/2 speed
        1: 100,  # Original speed
        2: 50,   # x2 speed
        3: 25    # x4 speed
    }

    def __init__(self, signals, is_playing=False, speed=1, window_range=(0, 30), timer=None, name='', preserve_zoom=False):
        super().__init__()
        self.signals = signals
        self.selected_signal = self.signals[0]
        self.is_playing = is_playing
        self.speed = speed
        self.window_range = window_range
        self.timer = timer
        self.name = name
        self.window_start, self.window_end = window_range
        self.preserve_zoom = preserve_zoom  

        self.max_length = len(max(self.signals).data)
        self.max_time_axis = np.linspace(0, self.max_length/100, self.max_length)
        self.other = None

        self.yMin = min(min(signal.data)
                        for signal in self.signals) if self.signals else self.yMin
        self.yMax = max(max(signal.data)
                        for signal in self.signals) if self.signals else self.yMax

        # graph layout
        self.graph_layout = QtWidgets.QHBoxLayout()
        self.graph_layout.addSpacing(10)

        # buttons layout
        self.controls_layout = QtWidgets.QVBoxLayout()

 
        self.plot_widget = PlotWidget()
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.setBackground('#001414')
        self.plot_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # event listeners for mouse panning
        self.plot_widget.scene().sigMouseClicked.connect(self.on_user_interaction_start)
        self.plot_widget.sigRangeChanged.connect(
            self.on_user_interaction_start)

        self.plot_widget.scene().sigMouseClicked.connect(self.on_signal_clicked)

        # show/hide checkBox
        self.show_hide_checkbox = QtWidgets.QCheckBox("Show/Hide")
        self.show_hide_checkbox.setStyleSheet(Utils.checkBox_style_sheet)
        self.show_hide_checkbox.setChecked(True)
        self.show_hide_checkbox.stateChanged.connect(self.toggle_signal)
        self.show_hide_checkbox.stateChanged.connect(self.sync_checkboxes)

        #input for sig.1 title
        self.title_input = QtWidgets.QLineEdit(self.selected_signal.title)
        self.title_input.setFixedWidth(150) 
        self.title_input.setStyleSheet(Utils.lineEdit_style_sheet)
        self.title_input.setAlignment(
            QtCore.Qt.AlignCenter)  
        self.title_input.textChanged.connect(self.update_signal_titles)

        # speed slider
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setMinimum(0)  
        self.speed_slider.setMaximum(3)  
        self.speed_slider.setValue(speed)   
        self.speed_slider.setTickInterval(1)  
        self.speed_slider.setFixedWidth(150) 

        #slider label
        self.speed_label = QtWidgets.QLabel("Signal speed control: ")
        self.speed_label.setStyleSheet(Utils.label_style_sheet)

        self.speed_layout = QtWidgets.QVBoxLayout()
        self.speed_layout.addStretch()
        self.speed_layout.addWidget(self.speed_label)
        self.speed_layout.addWidget(self.speed_slider)
        self.speed_slider.setStyleSheet(Utils.slider_style_sheet)
        self.speed_slider.valueChanged.connect(self.update_timer_speed)

        self.play_pause_button = Utils.create_button("", self.play_pause_signal, "play")
        self.button_layout = QtWidgets.QHBoxLayout()

        self.button_layout.addStretch()
        self.button_layout.addSpacing(100)

        self.button_layout.addWidget(self.play_pause_button)

        self.stop_signal_button = Utils.create_button(f"", self.stop_signal, "rewind")
        self.button_layout.addWidget(self.stop_signal_button)

        self.zoom_in_button = Utils.create_button(f"", self.zoom_in, "zoom_in")
        self.button_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = Utils.create_button(f"", self.zoom_out, "zoom_out")
        self.button_layout.addWidget(self.zoom_out_button)

        self.button_layout.addWidget(Utils.create_button(f"", lambda: (self.selected_signal.change_color(), self.plot_signals()), "color"))
        
        self.button_layout.addWidget(Utils.create_button(f"", self.show_statistics, "statistics"))
        self.button_layout.addWidget(Utils.create_button("", lambda: (Utils.import_signal_file(self), self.update_graph()), "import"))
        self.button_layout.addWidget(Utils.create_button(f"", self.delete_signal, icon_name="delete_1"))

        self.button_layout.addStretch() 
        self.button_layout.addStretch()  

        self.button_layout.addSpacing(110)


        self.graph_layout.addWidget(self.plot_widget)
        self.graph_layout.addSpacing(10)
        self.controls_layout.addWidget(self.title_input)
        self.controls_layout.addWidget(self.show_hide_checkbox)
        self.controls_layout.addLayout(self.speed_layout)
        self.graph_layout.addLayout(self.controls_layout)

        SignalPlotWidget.graph_instances.append(self)
        if len(SignalPlotWidget.graph_instances) == 2:
            self.other = SignalPlotWidget.graph_instances[0]
            self.other.other = self

    def update_graph(self):
        if self.signals:
            self.selected_signal = self.signals[-1]
            self.title_input.setText(self.selected_signal.title)
            self.max_length = len(max(self.signals).data)
            self.max_time_axis = np.linspace(0, self.max_length / 100, self.max_length)
            self.yMin = min(min(self.signals[-1].data), self.yMin)
            self.yMax = max(max(self.signals[-1].data), self.yMin)
        else:
            self.selected_signal = None
        self.plot_signals()

    def on_user_interaction_start(self):
        SignalPlotWidget.user_interacting = True

    def update_signal_titles(self):
        """ Updates the plot titles dynamically as the user changes the title inputs. """
        self.selected_signal.title = self.title_input.text()
        self.plot_widget.setTitle(self.selected_signal.title)

    def update_timer_speed(self):
        #current slider value in sig.1
        current_value = self.speed_slider.value()

        #change timer interval based on slider value
        new_timer_interval = SignalPlotWidget.speed_mapping[current_value]

        if self.timer is not None:
            self.timer.setInterval(new_timer_interval)

        #if linked, update other slider too
        if SignalPlotWidget.is_linked:
            self.other.speed_slider.setValue(current_value)

    def sync_checkboxes(self):
        if SignalPlotWidget.is_linked:
            self.other.show_hide_checkbox.setChecked(
                self.show_hide_checkbox.isChecked())

    def toggle_signal(self, state):
        if state == Qt.Checked:
            #plot signal only if checked
            self.plot_widget.clear()
            for signal in self.signals:
                if signal == self.selected_signal:
                    pen = pg.mkPen(color=signal.color, width=4)
                else:
                    pen = pg.mkPen(color=signal.color, width=1)
                self.plot_widget.plot(self.max_time_axis,
                                      signal.data, pen=pen)
            self.plot_widget.setYRange(-1, 1)
            self.plot_widget.setTitle(self.title_input.text())
        else:
            self.plot_widget.clear()  #clear plot if unchecked

    def update_plot(self, user_interacting):
        if self.is_playing and user_interacting:
            window_size = self.window_end - self.window_start  # how much is visible at once
            self.window_start = (self.window_start + 1) % (len(self.selected_signal.data) - window_size)  
            self.window_end = self.window_start + window_size
            self.plot_signals()


    def link_viewports(self):
        SignalPlotWidget.graph_instances[0].plot_widget.sigRangeChanged.connect(SignalPlotWidget.graph_instances[0].sync_range)
        SignalPlotWidget.graph_instances[1].plot_widget.sigRangeChanged.connect(SignalPlotWidget.graph_instances[1].sync_range)
        SignalPlotWidget.sync_viewports()

    def unlink_viewports(self):
        SignalPlotWidget.graph_instances[0].plot_widget.sigRangeChanged.disconnect(SignalPlotWidget.graph_instances[0].sync_range)
        SignalPlotWidget.graph_instances[1].plot_widget.sigRangeChanged.disconnect(SignalPlotWidget.graph_instances[1].sync_range)

    @staticmethod
    def sync_viewports():
        # Ensure both graphs have the same zoom and pan when linked
        # returns a list containing two elements: the x-range and y-range
        range1 = SignalPlotWidget.graph_instances[0].plot_widget.viewRange()
        # Padding = 0 is used to prevent signal shrinking by preventing buffer space
        SignalPlotWidget.graph_instances[1].plot_widget.setXRange(
            *range1[0], padding=0)
        # The asterisk in here unpacks the tuple so that setXRange() receives two args: start&end of range
        SignalPlotWidget.graph_instances[1].plot_widget.setYRange(
            *range1[1], padding=0)

    def sync_range(self):
        if SignalPlotWidget.syncing:
            return  # Prevent recursive syncing
        SignalPlotWidget.syncing = True

        range_ = self.plot_widget.viewRange()
        self.other.plot_widget.setXRange(*range_[0], padding=0)
        self.other.plot_widget.setYRange(*range_[1], padding=0)

        SignalPlotWidget.syncing = False

    def show_statistics(self):
        self.statistics_window = StatisticsWindow(
            self.selected_signal.data, self.selected_signal.title, self.selected_signal.color, self.selected_signal) 
        self.statistics_window.show()  

    def play_pause_signal(self):
        if not self.is_playing:
            self.is_playing = True
            self.play_pause_button = Utils.update_button(
                self.play_pause_button, "", "pause")
            if self.timer is None:
                self.timer = pg.QtCore.QTimer()
                self.timer.timeout.connect(lambda:
                                            (self.update_plot(SignalPlotWidget.user_interacting)))
                self.timer.start(100) 
            if SignalPlotWidget.is_linked and not self.other.is_playing:
                self.other.play_pause_signal()

        else:
            self.is_playing = False
            self.play_pause_button = Utils.update_button(
                self.play_pause_button, "", "play")
            if SignalPlotWidget.is_linked and self.other.is_playing:
                self.other.play_pause_signal()


    def plot_signals(self):
        self.plot_widget.clear()
        self.other.plot_widget.clear()
        if not self.preserve_zoom:
            self.original_x_range = self.plot_widget.viewRange()[0]
            self.original_y_range = self.plot_widget.viewRange()[1]

        if not self.preserve_zoom:
            self.original_x_range2 = self.other.plot_widget.viewRange()[0]
            self.original_y_range2 = self.other.plot_widget.viewRange()[1]

        #sync zoom and pan if linked
        if SignalPlotWidget.is_linked:
            SignalPlotWidget.sync_viewports()

        if self.show_hide_checkbox.isChecked():
            for signal in self.signals:
                if signal == self.selected_signal:
                    pen = pg.mkPen(color=signal.color, width=4)
                else:
                    pen = pg.mkPen(color=signal.color, width=1)
                self.plot_widget.plot(
                    signal.time_axis, signal.data, pen=pen)

            if SignalPlotWidget.user_interacting:
                current_time_window = self.max_time_axis[self.window_start:self.window_end]
                self.plot_widget.setXRange(
                    min(current_time_window), max(current_time_window), padding=0)

            if not self.preserve_zoom:
                global_min, global_max = self.get_global_min_and_max()
                self.plot_widget.setYRange(global_min, global_max)
            self.plot_widget.setTitle(self.title_input.text())

            # panning within limis
            self.plot_widget.setLimits(
                xMin=min(self.max_time_axis), xMax=max(self.max_time_axis), yMin=self.yMin, yMax=self.yMax)

        if self.other.show_hide_checkbox.isChecked():
            for signal in self.other.signals:
                if signal == self.other.selected_signal:
                    pen = pg.mkPen(color=signal.color, width=4)
                else:
                    pen = pg.mkPen(color=signal.color, width=1)

                self.other.plot_widget.plot(
                    signal.time_axis, signal.data, pen=pen)

            # case of user interaction
            if SignalPlotWidget.user_interacting:
                current_time_window = self.other.max_time_axis[
                    self.other.window_start:self.other.window_end]
                self.other.plot_widget.setXRange(
                    min(current_time_window), max(current_time_window), padding=0)

            # self.other.plot_widget.setYRange(-1, 1)
            self.other.plot_widget.setTitle(self.other.title_input.text())

            #panning within limis
            self.other.plot_widget.setLimits(
                xMin=min(self.other.max_time_axis), xMax=max(self.other.max_time_axis), yMin=self.other.yMin, yMax=self.other.yMax)

    def stop_signal(self):
        if self.show_hide_checkbox.isChecked():
            self.is_playing = not self.is_playing
            self.play_pause_signal()
            if SignalPlotWidget.is_linked and not SignalPlotWidget.stopped_by_link:
                SignalPlotWidget.stopped_by_link = True
                self.other.stop_signal()

        self.window_start = 0
        self.window_end = min(30, self.max_length)
        SignalPlotWidget.stopped_by_link = False
        self.plot_signals()

    def zoom_in(self):
        if isinstance(self.plot_widget, PlotWidget):
            x_range = self.plot_widget.viewRange()[0]
            y_range = self.plot_widget.viewRange()[1]

            zoom_factor_x = 0.16 
            zoom_factor_y = 0.105  

            new_x_range = (x_range[0] + (x_range[1] - x_range[0]) * zoom_factor_x, x_range[1] - (x_range[1] - x_range[0]) * zoom_factor_x)
            new_y_range = (y_range[0] + (y_range[1] - y_range[0]) * zoom_factor_y, y_range[1] - (y_range[1] - y_range[0]) * zoom_factor_y)

            self.plot_widget.setXRange(new_x_range[0], new_x_range[1], padding=0)
            self.plot_widget.setYRange(new_y_range[0], new_y_range[1], padding=0)

            if SignalPlotWidget.is_linked:
                self.other.plot_widget.setXRange(new_x_range[0], new_x_range[1], padding=0)
                self.other.plot_widget.setYRange(new_y_range[0], new_y_range[1], padding=0)
            self.preserve_zoom = True

    def zoom_out(self):
        if isinstance(self.plot_widget, PlotWidget):
            x_range = self.plot_widget.viewRange()[0]
            y_range = self.plot_widget.viewRange()[1]

            zoom_factor_x = 0.21  
            zoom_factor_y = 0.42  

            new_x_range = (x_range[0] - (x_range[1] - x_range[0]) * zoom_factor_x,x_range[1] + (x_range[1] - x_range[0]) * zoom_factor_x)
            new_y_range = (y_range[0] - (y_range[1] - y_range[0]) * zoom_factor_y,y_range[1] + (y_range[1] - y_range[0]) * zoom_factor_y)

            self.plot_widget.setXRange(new_x_range[0], new_x_range[1], padding=0)
            self.plot_widget.setYRange(new_y_range[0], new_y_range[1], padding=0)

            if SignalPlotWidget.is_linked:
                self.other.plot_widget.setXRange(new_x_range[0], new_x_range[1], padding=0)
                self.other.plot_widget.setYRange(new_y_range[0], new_y_range[1], padding=0)
            self.preserve_zoom = True

    def on_signal_clicked(self, event):
        # Get the mouse click position in plot coordinates
        pos = event.scenePos()  
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)

        x_mouse, y_mouse = mouse_point.x(), mouse_point.y()

        closest_signal = None
        min_distance = float('inf')  # infinity

        # Loop through each signal to find the closest one to the click
        for signal in self.signals:
            signal_data = signal.data
            x_data = self.max_time_axis
            y_data = signal_data
            index = (np.abs(x_data - x_mouse)).argmin()
            y_value_at_index = y_data[index]

            distance = np.sqrt(
                (x_mouse - x_data[index])**2 + (y_mouse - y_value_at_index)**2)

            # compare with previous distances
            if distance < min_distance:
                min_distance = distance
                closest_signal = signal

        if closest_signal:
            # Set the selected signal
            self.selected_signal = closest_signal
            self.title_input.setText(self.selected_signal.title)
            self.plot_signals()

    def update_max_time(self, new_max_time):
        self.max_time_axis = new_max_time

    def get_global_min_and_max(self):
        #minimum and maximum values from signal's data
        min_values = [np.min(signal.data) for signal in self.signals]
        max_values = [np.max(signal.data) for signal in self.signals]
        
        #global minimum and maximum values across all signals
        global_min = min(min_values)
        global_max = max(max_values)
        
        return global_min, global_max
    
    def delete_signal(self):
        if len(self.signals) > 1:
            self.signals.remove(self.selected_signal)
            self.update_graph()
