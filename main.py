import sys
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QComboBox, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from scipy.fft import fft, fftfreq
from scipy.interpolate import interp1d, CubicSpline, lagrange
from signal_mixer import SignalMixer
from style.styling_methods import style_plot_widget
from signal_construct import Signal
from style.toggle import ToggleSwitch


class SignalSamplingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.interp_method = None
        self.f_max = 2
        self.sampling_rate = 2

        self.mixer = SignalMixer()
        self.initUI()

        self.max_time_axis = 10
        self.time = np.linspace(0, self.max_time_axis, 20000)
        self.signal = np.zeros_like(self.time)
        self.noise_signal = np.zeros_like(self.time)

        self.mixer.update_signal.connect(self.update_original_signal)
        self.mixer.update_noise.connect(self.sample_and_reconstruct)
        self.mixer.export_button.clicked.connect(self.export_signal)

    def initUI(self):
        self.setWindowTitle("Sampling Studio")
        self.setWindowIcon(QIcon("style/icons/logo.png"))
        self.setGeometry(100, 100, 1200, 800)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # creating our plots
        self.original_plot = pg.PlotWidget(title="Original Signal")
        self.reconstructed_plot = pg.PlotWidget(title="Reconstructed Signal")
        self.error_plot = pg.PlotWidget(
            title="Error (Original - Reconstructed)")
        self.frequency_plot = pg.PlotWidget(title="Frequency Domain")

        style_plot_widget(self.original_plot)
        style_plot_widget(self.reconstructed_plot)
        style_plot_widget(self.error_plot)
        style_plot_widget(self.frequency_plot)

        # creating grid layout for plots
        plot_grid = QtWidgets.QGridLayout()
        plot_grid.addWidget(self.original_plot, 0, 0)
        plot_grid.addWidget(self.reconstructed_plot, 1, 0)
        plot_grid.addWidget(self.error_plot, 2, 0)
        plot_grid.addWidget(self.frequency_plot, 3, 0)

        # horizontal layout for plots & mixer
        h_layout = QtWidgets.QHBoxLayout()
        right_panel_layout = QtWidgets.QVBoxLayout()

        right_panel_layout.addWidget(self.mixer)

        # slider for sampling:
        control_panel = QtWidgets.QVBoxLayout()
        toggle_layout = QtWidgets.QHBoxLayout()
        self.sampling_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        # self.sampling_slider.setMinimum(2)

        # reconstruction method combobox
        reconstruction_layout = QtWidgets.QHBoxLayout()
        self.reconstruction_method_label = QtWidgets.QLabel(
            "Reconstruction Method: ")
        reconstruction_layout.addWidget(self.reconstruction_method_label)
        self.reconstruction_method_comboBox = QtWidgets.QComboBox(self)
        self.reconstruction_method_comboBox.addItems(
            ["Whittaker-Shanon (sinc)", "Zero-Order Hold", "Linear", "Cubic Spline"])
        self.reconstruction_method_comboBox.currentTextChanged.connect(
            self.update_reconstruction_method)
        reconstruction_layout.addWidget(self.reconstruction_method_comboBox)
        control_panel.addLayout(reconstruction_layout)

        # layout.addLayout(control_panel)

        self.toggle = ToggleSwitch()
        self.toggle.setChecked(False)
        self.toggle.stateChanged.connect(self.update_sampling_slider)

        normalized_label = QtWidgets.QLabel("Normalized Mode")
        toggle_layout.addWidget(normalized_label)
        toggle_layout.addWidget(self.toggle)

        control_panel.addLayout(toggle_layout)

        self.sampling_slider.setValue(self.sampling_rate)
        self.sampling_slider.valueChanged.connect(self.update_sampling)
        self.sampling_slider.setObjectName("samplingSlider")

        self.sampling_label = QtWidgets.QLabel(
            f"Sampling Frequency: {self.sampling_rate} Hz")
        control_panel.addWidget(self.sampling_slider)
        control_panel.addWidget(self.sampling_label)

        control_panel_widget = QtWidgets.QWidget()
        control_panel_widget.setLayout(control_panel)
        control_panel_widget.setObjectName("controlPanel")

        right_panel_layout.addWidget(control_panel_widget)

        h_layout.addLayout(plot_grid, 4)
        h_layout.addLayout(right_panel_layout, 1)
        layout.addLayout(h_layout)

    def open_mixer(self):
        self.mixer.show()

    def update_original_signal(self):
        if not self.mixer.signals:
            # default is zero if no signals are present
            self.signal = np.zeros_like(self.time)
            self.original_plot.clear()
            self.f_max = 2
        else:
            self.signal, f_max = self.mixer.compose_signal(self.time)
            self.f_max = f_max

        self.update_sampling_slider()
        self.sample_and_reconstruct()

    def update_sampling_slider(self):
        # Set maximum value to 4 * f_max
        self.sampling_slider.setMaximum(4 * self.f_max)

        # ratio to fmax
        if self.toggle._checked:
            self.sampling_slider.setValue(self.sampling_rate)
            sampling_ratio = self.sampling_rate / self.f_max
            sampling_ratio = round(sampling_ratio, 2) 
            self.sampling_label.setText(
                f"Sampling Frequency: {sampling_ratio} max frequency")

        else:  # Normal mode
            self.sampling_slider.setValue(self.sampling_rate)

            self.sampling_label.setText(
                f"Sampling Frequency: {self.sampling_slider.value()} Hz")

    def update_sampling(self):

        self.sampling_rate = self.sampling_slider.value()

        if self.sampling_rate < 2:  # Enforce minimum value of 2
            self.sampling_rate = 2

        self.sampling_slider.setValue(self.sampling_rate)
        self.update_sampling_slider()

        self.sample_and_reconstruct()

    def update_reconstruction_method(self, text='Whittaker-Shanon (sinc)'):
        """
        1. sinc: for each target time (t_i), we sum contributions from all samples (s) weighted by sinc function based on 
          distance from each sample position (x). Good for bandlimited signals / signal is sampled above Nyquist rate
        """
        def sinc_interp(x, s, t):  # sinc(x) = sin(πx)/(πx) (Whittaker-Shannon)
            """
            x: sample positions (sampling_t)
            s: sample values (sampled_signal)
            t: target positions (continuous time for reconstruction)
            """
            T = x[1] - x[0]
            return np.array([np.sum(s * np.sinc((t_i - x) / T)) for t_i in t])

        """
        2. zero_order : for each target time (t_i), it finds index of  last sample <= t_i.. and uses its val. to hold
          constant until next sampling point. Simpole but might lead to significant distortion, especially for rapidly changing signals.
        """
        def zero_order_hold(x, s, t):  # maintain last sampled value until next sample is taken
            s_interp = np.zeros_like(t)
            for i, t_i in enumerate(t):
                idx = np.searchsorted(x, t_i) - 1
                s_interp[i] = s[idx]
            return s_interp

        """
        3. linear : for each target time (t_i), it uses np.interp function to perform linear interpolation between two nearest sample points.
          Has smoother transition than Zero but is still bad for non-linear signals.
        """
        def linear_interp(x, s, t):  # connect sample points linearly
            return np.interp(t, x, s)

        """
        4.cubic
        """
        def cubic_spline_interp(x, s, t):  # connects by cubic functions leading to smoother connection
            cs = CubicSpline(x, s)
            return cs(t)

        # """
        # 5.lagrange: good for small number of points, but can be hard to compute for large datasets and may lead to oscillations between points
        # """
        # def lagrange_interp(x, s, t):  # makes a polynomial through all sample points
        #     poly = lagrange(x, s)
        #     return poly(t)

        if text == 'Zero-Order Hold':
            self.interp_method = zero_order_hold
        elif text == 'Linear':
            self.interp_method = linear_interp
        elif text == 'Cubic Spline':
            self.interp_method = cubic_spline_interp
        # elif text == 'Lagrange':
        #     self.interp_method = lagrange_interp
        else:
            self.interp_method = sinc_interp

        self.sample_and_reconstruct()
    
    def sample_and_reconstruct(self):
        self.add_noise()
        if self.interp_method is None:
            self.update_reconstruction_method()

        noised_signal = (self.noise_signal + self.signal)

        # 1.excluding first and last point ==> good reconstruction at 2 * fmax
            # sample_points = np.linspace(0, len(self.time) - 1, (self.sampling_rate * self.max_time_axis)).astype(int)  # (start, stop, #samples)
            # sample_points = sample_points[1:-1]

        # good reconstruction at 2 * fmax + 1
        sample_points = np.arange(0, len(self.time) - 1, len(self.time)/(self.sampling_rate*self.max_time_axis)).astype(int)
        sampled_time = self.time[sample_points]
        sampled_signal = noised_signal[sample_points]

        reconstructed_signal = self.interp_method(sampled_time, sampled_signal, self.time)

        self.update_plots(sampled_time, sampled_signal, reconstructed_signal)

    def update_plots(self, sampled_time=None, sampled_signal=None, reconstructed_signal=None):
        self.original_plot.clear()
        self.reconstructed_plot.clear()
        self.error_plot.clear()
        self.frequency_plot.clear()

        noised_signal = self.noise_signal + self.signal

        self.original_plot.plot(self.time, noised_signal,
                                pen='#007AFF', name="Original Signal")
        if sampled_time is not None and sampled_signal is not None:
            self.original_plot.plot(
                sampled_time, sampled_signal, pen=None, symbol='o', symbolBrush='r')  # highlight sampled points

        self.reconstructed_plot.plot(
            self.time, reconstructed_signal, pen='#007AFF')  # reconstruct signal

        # calc. error graph (WITHOUT NOISE for constructed signals)
        # calc. error graph (WITHOUT NOISE for constructed signals)
        error = self.signal - reconstructed_signal
        text = f'error: {round(np.mean(np.abs(error)), 2)}'

        title = f"""
        <div style='text-align: center;font-family: "Segoe UI", sans-serif;'>
            <span style='font-size: 10pt;'>Error Graph</span><br>
            <span style='font-size: 8pt;'><b>{text}</b></span>
        </div>"""
        self.error_plot.setTitle(title)
        self.error_plot.plot(self.time, error, pen='#007AFF')

        # Repeat for the Noised Signal
        freqs = fftfreq(len(self.time), self.time[1] - self.time[0])

        fft_original = 2*np.abs(fft(self.signal))

        fft_original /= len(self.time)

        self.frequency_plot.plot(freqs, fft_original, pen=pg.mkPen('#007AFF', width=3))

        # overlap_factor = self.sampling_rate*(1/(0.05*self.f_max))
        self.frequency_plot.plot(
            freqs + self.sampling_rate + 0.2, fft_original, pen=pg.mkPen('r', width=2))
        self.frequency_plot.plot(
            freqs - self.sampling_rate - 0.2, fft_original, pen=pg.mkPen('r', width=2))

        self.set_same_viewing_range()
        self.frequency_plot.setXRange(-max(self.f_max, 20), max(self.f_max, 20))

    def add_noise(self):
        # convert SNR from dB to linear scale
        snr_linear = 10 ** (self.mixer.snr_slider.value() / 10.0)
        signal_power = np.mean(self.signal ** 2)  # calculate signal power
        # calculate noise power to achieve req. SNR
        noise_power = signal_power / snr_linear
        self.noise_signal = np.random.normal(
            0, np.sqrt(noise_power), self.signal.shape)  # generate Gaussian noise with: mean = 0 , calculated standard deviation

    def set_same_viewing_range(self):
        x_min, x_max = min(self.time), max(self.time)
        y_min, y_max = min(self.signal), max(self.signal)

        self.original_plot.setXRange(x_min, x_max)
        self.reconstructed_plot.setXRange(x_min, x_max)
        self.error_plot.setXRange(x_min, x_max)

        self.original_plot.setYRange(y_min, y_max)
        self.reconstructed_plot.setYRange(y_min, y_max)
        self.error_plot.setYRange(y_min, y_max)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left and self.sampling_rate > 2:
            self.sampling_rate -= 1
            self.sample_and_reconstruct()
        elif event.key() == Qt.Key_Right and self.sampling_rate < len(self.signal):
            self.sampling_rate += 1
            self.sample_and_reconstruct()

    def export_signal(self):
        # file dialog to save CSV file
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)

        if file_name:
            try:
                signal = np.insert(
                    self.signal + self.noise_signal, 0, self.f_max)
                np.savetxt(file_name, signal, delimiter=",")
                QMessageBox.information(
                    self, "Success", "File saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def closeEvent(self, event):
        self.mixer.close()
        event.accept()

    def main(self):
        self.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    with open("style/style.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = SignalSamplingApp()
    window.main()
    sys.exit(app.exec_())
