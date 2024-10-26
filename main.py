import sys
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from scipy.fft import fft, fftfreq  
from scipy.interpolate import interp1d, CubicSpline, lagrange
from signal_mixer import SignalMixer


class SignalSamplingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.interp_method = None
        self.f_max = 0  
        self.sampling_rate = 2

        self.initUI()
        self.mixer = SignalMixer() 
        self.max_time_axis = 1
        self.time = np.linspace(0, self.max_time_axis, 1000)
        self.mixer.update_signal.connect(self.update_original_signal)  
        self.generate_signal()  
        self.sample_and_reconstruct()  #initial sampling & reconstruction


    def initUI(self):
        self.setWindowTitle("Signal Sampling and Recovery")
        self.setGeometry(100, 100, 1200, 800)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.original_plot = pg.PlotWidget(title="Original Signal")
        self.reconstructed_plot = pg.PlotWidget(title="Reconstructed Signal")
        self.error_plot = pg.PlotWidget(title="Error (Original - Reconstructed)")
        self.frequency_plot = pg.PlotWidget(title="Frequency Domain")

        
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.addWidget(self.original_plot, 0, 0)
        grid_layout.addWidget(self.reconstructed_plot, 0, 1)
        grid_layout.addWidget(self.error_plot, 1, 0)
        grid_layout.addWidget(self.frequency_plot, 1, 1)
        layout.addLayout(grid_layout)

        #slider for sampling:
        control_panel = QtWidgets.QHBoxLayout()
        self.sampling_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sampling_slider.setMinimum(0)
        self.sampling_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sampling_slider.setTickInterval(1)  
        self.sampling_slider.setValue(self.sampling_rate)
        self.sampling_slider.valueChanged.connect(self.update_sampling)

        self.sampling_label = QtWidgets.QLabel(f"Sampling Frequency: {self.sampling_rate}")  
        control_panel.addWidget(self.sampling_slider)
        control_panel.addWidget(self.sampling_label)
        layout.addLayout(control_panel)

        #(dropdown list)
        self.reconstruction_method_comboBox = QComboBox(self)
        self.reconstruction_method_comboBox.addItems(["Whittaker-Shanon (sinc)", "Zero-Order Hold", "Linear", "Cubic Spline", "Lagrange"])
        self.reconstruction_method_comboBox.currentTextChanged.connect(self.update_reconstruction_method)
        
        layout.addWidget(self.reconstruction_method_comboBox)

        mix_button = QtWidgets.QPushButton("Open Signal Mixer")
        mix_button.clicked.connect(self.open_mixer)
        layout.addWidget(mix_button)

    def open_mixer(self):
        self.mixer.show()

    def generate_signal(self):
        if self.mixer.signals:
            self.signal = self.mixer.compose_signal(self.time)
        else:    
            f1 = 5  
            f2 = 15 
            self.signal = np.sin(2 * np.pi * f1 * self.time) + 0.5 * np.sin(2 * np.pi * f2 * self.time)
        
        self.f_max = max(f1, f2) if not self.mixer.signals else max(f[0] for f in self.mixer.signals)   
        self.update_sampling_slider()
     
        #self.sampling_slider.setMaximum(4 * self.f_max)

        self.update_plots()

    def update_original_signal(self):
        """Update the original signal based on the mixer contents."""
        self.signal = self.mixer.compose_signal(self.time)  
        self.f_max = max(f[0] for f in self.mixer.signals if isinstance(f, tuple))  # For tuple signals        
        self.update_sampling_slider()
        self.update_plots()  

    def update_sampling_slider(self):
        """Reconfigure the sampling slider based on the current f_max."""
        self.sampling_slider.setMaximum(4 * self.f_max)  # Set the slider maximum to 4 times f_max
        self.sampling_slider.setTickInterval(int(self.f_max))  # Update tick interval to f_max
        self.sampling_slider.setValue(min(self.sampling_rate, 4 * self.f_max))  # Adjust the current value to be within the new range
        self.sampling_label.setText(f"Sampling Frequency: {self.sampling_slider.value()}")  # Update the label

    def update_sampling(self):
        self.sampling_rate = self.sampling_slider.value()
        if self.sampling_rate < 2:
            self.sampling_rate = 2

        self.sampling_slider.setValue(self.sampling_rate)  # Reset the slider to 2
        self.sampling_label.setText(f"Sampling Frequency: {self.sampling_rate}")  
        self.sample_and_reconstruct()

    def update_reconstruction_method(self, text='Whittaker-Shanon (sinc)'):
        # defining interpolation methods
        # Whittaker-Shannon (Sinc) Interpolation
        def sinc_interp(x, s, t):
            """
            x: sample positions (sampling_t)
            s: sample values (sampled_signal)
            t: target positions (continuous time for reconstruction)
            """             
            T = x[1] - x[0]  
            return np.array([np.sum(s * np.sinc((t_i - x) / T)) for t_i in t])

        # Zero-order hold interpolation
        def zero_order_hold(x, s, t):
            s_interp = np.zeros_like(t)
            for i, t_i in enumerate(t):
                idx = np.searchsorted(x, t_i) - 1
                s_interp[i] = s[idx]
            return s_interp    

        # linear interpolation
        def linear_interp(x, s, t):
            return np.interp(t, x, s)

        # cubic spline interpolation
        def cubic_spline_interp(x, s, t):
            cs = CubicSpline(x, s)
            return cs(t)

        # lagrang interpolation
        def lagrange_interp(x, s, t):
            poly = lagrange(x, s)
            return poly(t)

        if text == 'Whittaker-Shanon (sinc)':
            self.interp_method = sinc_interp
        elif text == 'Zero-Order Hold':
            self.interp_method = zero_order_hold
        elif text == 'Linear':
            self.interp_method = linear_interp
        elif text == 'Cubic Spline':
            self.interp_method = cubic_spline_interp
        elif text == 'Lagrange':
            self.interp_method = lagrange_interp
        
        self.sample_and_reconstruct()


    def sample_and_reconstruct(self):
        if self.interp_method is None:
            self.update_reconstruction_method()

        sample_points = np.linspace(0, len(self.time) - 1, self.sampling_rate * self.max_time_axis).astype(int)
        sampled_time = self.time[sample_points]
        sampled_signal = self.signal[sample_points]

        reconstructed_signal = self.interp_method(sampled_time, sampled_signal, self.time)

        self.update_plots(sampled_time, sampled_signal, reconstructed_signal)

    def update_plots(self, sampled_time=None, sampled_signal=None, reconstructed_signal=None):
        self.original_plot.clear()
        self.reconstructed_plot.clear()
        self.error_plot.clear()
        self.frequency_plot.clear()

        
        self.original_plot.plot(self.time, self.signal, pen='y', name="Original Signal")
        if sampled_time is not None and sampled_signal is not None:  #x and y coordinates of the sampled points
            self.original_plot.plot(sampled_time, sampled_signal, pen=None, symbol='o', symbolBrush='r')

        
        if reconstructed_signal is not None:
            self.reconstructed_plot.plot(self.time, reconstructed_signal, pen='g')

            
            error = self.signal - reconstructed_signal
            text = f'Absolute Error: {round(np.sum(np.abs(error)), 2)}'
            text_item = pg.TextItem(text, anchor=(0, 5), color='w')
            self.error_plot.addItem(text_item, ignoreBounds=True)
            text_item.setPos(self.time[0], self.signal[0])  # Position the text
            self.error_plot.plot(self.time, error, pen='r')

            freqs = fftfreq(len(self.time), self.time[1] - self.time[0])
            fft_original = np.abs(fft(reconstructed_signal))

            fft_original[1:] *= 2  
            fft_original /= len(self.time)  
            # self.sampling_slider.setMaximum(4 * self.f_max)
            self.frequency_plot.plot(freqs[:len(freqs)//2], fft_original[:len(freqs)//2], pen=pg.mkPen('r', width=5))

        
        freqs = fftfreq(len(self.time), self.time[1] - self.time[0])
        fft_original = np.abs(fft(self.signal))
        
        fft_original[1:] *= 2  
        fft_original /= len(self.time)  
        # self.sampling_slider.setMaximum(4 * self.f_max)
        self.frequency_plot.plot(freqs[:len(freqs)//2], fft_original[:len(freqs)//2], pen='y')
        
        self.set_same_viewing_range()
    
    def set_same_viewing_range(self):
        x_min, x_max = min(self.time), max(self.time)
        y_min, y_max = min(self.signal), max(self.signal)

        self.original_plot.setXRange(x_min, x_max)
        self.reconstructed_plot.setXRange(x_min, x_max)
        self.error_plot.setXRange(x_min, x_max)

        self.original_plot.setYRange(y_min, y_max)
        self.reconstructed_plot.setYRange(y_min, y_max)
        self.error_plot.setYRange(y_min, y_max)

        self.frequency_plot.setXRange(0, 2 * self.f_max)  

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left and self.sampling_rate > 2:
            self.sampling_rate -= 1
            self.sample_and_reconstruct() 
        elif event.key() == Qt.Key_Right and self.sampling_rate < len(self.signal):
            self.sampling_rate += 1
            self.sample_and_reconstruct()     
        print('Sampling rate:', self.sampling_rate)   

    def closeEvent(self, event):
        self.mixer.close()  
        event.accept()  

    def main(self):
        self.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SignalSamplingApp()
    window.main() 
    sys.exit(app.exec_())
