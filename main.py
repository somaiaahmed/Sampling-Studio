import sys
import numpy as np
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from scipy.fft import fft, fftfreq  #for fast fourier transform operations
from scipy.interpolate import interp1d
from signal_mixer import SignalMixer


class SignalSamplingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.f_max = 0  # Initialize f_max
        self.initUI()
        self.mixer = SignalMixer() 
        self.time = []
        self.mixer.update_signal.connect(self.update_original_signal)  # Connect the signal
        self.generate_signal()  # Set f_max

    def initUI(self):
        self.setWindowTitle("Signal Sampling and Recovery")
        self.setGeometry(100, 100, 1200, 800)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.original_plot = pg.PlotWidget(title="Original Signal")
        self.reconstructed_plot = pg.PlotWidget(title="Reconstructed Signal")
        self.error_plot = pg.PlotWidget(title="Error (Original - Reconstructed)")
        self.frequency_plot = pg.PlotWidget(title="Frequency Domain")

        # Put graphs into grid layout
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.addWidget(self.original_plot, 0, 0)
        grid_layout.addWidget(self.reconstructed_plot, 0, 1)
        grid_layout.addWidget(self.error_plot, 1, 0)
        grid_layout.addWidget(self.frequency_plot, 1, 1)
        layout.addLayout(grid_layout)

        control_panel = QtWidgets.QHBoxLayout()
        self.sampling_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sampling_slider.setMinimum(1)
        self.sampling_slider.setValue(1)
        self.sampling_slider.valueChanged.connect(self.update_sampling)

        self.sampling_label = QtWidgets.QLabel("Sampling Frequency: 10")  # As we've set the default to be 10
        control_panel.addWidget(self.sampling_slider)
        control_panel.addWidget(self.sampling_label)
        layout.addLayout(control_panel)

        mix_button = QtWidgets.QPushButton("Open Signal Mixer")
        mix_button.clicked.connect(self.open_mixer)
        layout.addWidget(mix_button)

    def open_mixer(self):
        self.mixer.show()

    def generate_signal(self):
        self.time = np.linspace(0, 1, 100)
        if self.mixer.signals:
            self.signal = self.mixer.compose_signal(self.time)
        else:    
            f1 = 5  # Frequency of the first sine wave
            f2 = 15  # Frequency of the second sine wave
            self.signal = np.sin(2 * np.pi * f1 * self.time) + 0.5 * np.sin(2 * np.pi * f2 * self.time)

        # Store the maximum frequency
        self.f_max = max(f1, f2) if not self.mixer.signals else max(f[0] for f in self.mixer.signals)        
        self.sampling_slider.setMaximum(4 * self.f_max)

        self.update_plots()

    def update_original_signal(self):
        """Update the original signal based on the mixer contents."""
        self.signal = self.mixer.compose_signal(self.time)  # Use compose_signal with the time array
        self.update_plots()  # Update plots with new signal

    def update_sampling(self):
        sampling_freq = self.sampling_slider.value()
        self.sampling_label.setText(f"Sampling Frequency: {sampling_freq}")  # Updating slider label with slider value as Fs changes
        self.sample_and_reconstruct(sampling_freq)

    def sample_and_reconstruct(self, sampling_freq):
        sample_points = np.linspace(0, len(self.time) - 1, sampling_freq).astype(int)
        sampled_time = self.time[sample_points]
        sampled_signal = self.signal[sample_points]

        if len(sampled_time) < 4:
            interpolation_kind = 'linear' 
        else:
            interpolation_kind = 'cubic'

        interpolator = interp1d(sampled_time, sampled_signal, kind=interpolation_kind, fill_value="extrapolate")
        reconstructed_signal = interpolator(self.time)

        self.update_plots(sampled_time, sampled_signal, reconstructed_signal)

    def update_plots(self, sampled_time=None, sampled_signal=None, reconstructed_signal=None):
        self.original_plot.clear()
        self.reconstructed_plot.clear()
        self.error_plot.clear()
        self.frequency_plot.clear()

        # Update plot for original signal
        self.original_plot.plot(self.time, self.signal, pen='b', name="Original Signal")
        if sampled_time is not None and sampled_signal is not None:
            self.original_plot.plot(sampled_time, sampled_signal, pen=None, symbol='o', symbolBrush='r')

        # Update plot for reconstructed signal
        if reconstructed_signal is not None:
            self.reconstructed_plot.plot(self.time, reconstructed_signal, pen='g')

            # Calculating error and updating its plot
            error = self.signal - reconstructed_signal
            self.error_plot.plot(self.time, error, pen='r')

        # Update plot for frequency domain signal
        freqs = fftfreq(len(self.time), self.time[1] - self.time[0])
        fft_original = np.abs(fft(self.signal))

        # Correctly scale the FFT for real signals
        fft_original[1:] *= 2  # Double the amplitudes for positive frequencies, except DC component
        fft_original /= len(self.time)  # Normalize by the length of the time vector

        self.frequency_plot.plot(freqs[:len(freqs)//2], fft_original[:len(freqs)//2], pen='b')

        # Set same viewing range for original, reconstructed, and error plots
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

    def closeEvent(self, event):
        self.mixer.close()  # Close the SignalMixer window
        event.accept()  # Accept the close event

    def main(self):
        self.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SignalSamplingApp()
    window.main() 
    sys.exit(app.exec_())
