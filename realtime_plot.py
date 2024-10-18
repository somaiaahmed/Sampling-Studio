from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QMainWindow, QPushButton
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import sys
from selenium.webdriver.chrome.options import Options
from utils import Utils


class RealTimePlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.series_lat = QLineSeries()
        self.series_lon = QLineSeries()
        self.series_lat.setName("Latitude")
        self.series_lon.setName("Longitude")
        self.data = {'time': [], 'latitude': [], 'longitude': []}
        self.start_time = datetime.now()

        self.initUI()
        # !!! IMPORTANT !!!
        # those options are for the driver to run on wsl , if you are running on windows you can remove them
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")  # Needed for certain environments
        # Overcome limited resource problems
        options.add_argument("--disable-dev-shm-usage")
        ################################################
        self.driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=options)

        self.driver.get('https://www.orbtrack.org/#/?satName=ISS%20(ZARYA)')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(500)  # update every 500 ms

    def initUI(self):
        self.layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()


        # Labels
        self.lat_label = QLabel('Latitude: ')
        self.lon_label = QLabel('Longitude: ')
        self.time_label = QLabel('Time: ')
        self.lat_label.setStyleSheet(Utils.label_style_sheet)
        self.lon_label.setStyleSheet(Utils.label_style_sheet)
        self.time_label.setStyleSheet(Utils.label_style_sheet)
        self.layout.addWidget(self.lat_label)
        self.layout.addWidget(self.lon_label)
        self.layout.addWidget(self.time_label)

        # Latitude chart setup
        self.chart_lat = QChart()
        self.chart_lat.addSeries(self.series_lat)
        self.chart_lat.legend().setAlignment(Qt.AlignBottom)
        self.chart_lat.setTitle("Real-time ISS Latitude")
        self.chart_lat.setAnimationOptions(QChart.SeriesAnimations)

        # Longitude chart setup
        self.chart_lon = QChart()
        self.chart_lon.addSeries(self.series_lon)
        self.chart_lon.legend().setAlignment(Qt.AlignBottom)
        self.chart_lon.setTitle("Real-time ISS Longitude")
        self.chart_lon.setAnimationOptions(QChart.SeriesAnimations)

        # Axis setup
        self.axis_x_lat = QDateTimeAxis()
        # self.axis_x.setTickCount(10)
        self.axis_x_lat.setFormat("hh:mm:ss")
        self.axis_x_lat.setTitleText("Time (HH:MM:SS)")

        self.axis_x_lon = QDateTimeAxis()
        # self.axis_x.setTickCount(10)
        self.axis_x_lon.setFormat("hh:mm:ss")
        self.axis_x_lon.setTitleText("Time (HH:MM:SS)")

        self.axis_y_lat = QValueAxis()
        self.axis_y_lat.setLabelFormat("%.2f")
        self.axis_y_lat.setTitleText("Latitude")

        self.axis_y_lon = QValueAxis()
        self.axis_y_lon.setLabelFormat("%.2f")
        self.axis_y_lon.setTitleText("Longitude")

        self.chart_lat.addAxis(self.axis_x_lat, Qt.AlignBottom)
        self.chart_lat.addAxis(self.axis_y_lat, Qt.AlignLeft)
        self.series_lat.attachAxis(self.axis_x_lat)
        self.series_lat.attachAxis(self.axis_y_lat)

        self.chart_lon.addAxis(self.axis_x_lon, Qt.AlignBottom)
        self.chart_lon.addAxis(self.axis_y_lon, Qt.AlignLeft)
        self.series_lon.attachAxis(self.axis_x_lon)
        self.series_lon.attachAxis(self.axis_y_lon)

        self.chart_view_lat = QChartView(self.chart_lat)
        self.chart_view_lat.setRenderHint(QPainter.Antialiasing)
        self.chart_view_lat.setRubberBand(QChartView.RectangleRubberBand)
        self.chart_lat.axisY(self.series_lat).setRange(-20, 80)

        self.chart_view_lon = QChartView(self.chart_lon)
        self.chart_view_lon.setRenderHint(QPainter.Antialiasing)
        self.chart_view_lon.setRubberBand(QChartView.RectangleRubberBand)
        self.chart_lon.axisY(self.series_lon).setRange(-120, 30)

        self.layout.addWidget(self.chart_view_lat)
        self.layout.addWidget(self.chart_view_lon)

        # Play/Pause button
        self.play_pause_button = Utils.create_button("", self.toggle_timer, "pause")
        # self.play_pause_button.clicked.connect(self.toggle_timer)
        self.button_layout.addSpacing(120)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.play_pause_button)
        self.button_layout.addSpacing(120)
        self.button_layout.addStretch()
        self.layout.addLayout(self.button_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle('Real-time ISS Location')
        self.show()

    def update_data(self):
        try:
            latitude = self.driver.find_element(
                By.ID, 'satLat').text.replace('°', '').strip()
            longitude = self.driver.find_element(
                By.ID, 'satLon').text.replace('°', '').strip()
            time_str = self.driver.find_element(By.ID, 'satUTC').text.strip()

            self.lat_label.setText(f'Latitude: {latitude}')
            self.lon_label.setText(f'Longitude: {longitude}')
            self.time_label.setText(f'Time: {time_str}')

            # Clean and convert strings to floats
            if latitude == '.':
                latitude = 0.0
            else:
                latitude = float(latitude.replace(',', '.'))

            if longitude == '.':
                longitude = 0.0
            else:
                longitude = float(longitude.replace(',', '.'))

            # Calculate elapsed time
            current_time = datetime.now()
            self.data['time'].append(current_time)
            self.data['latitude'].append(latitude)
            self.data['longitude'].append(longitude)

            # Update series
            self.series_lat.append(
                int(current_time.timestamp() * 1000), latitude)
            self.series_lon.append(
                int(current_time.timestamp() * 1000), longitude)

            self.axis_x_lat.setMin(QDateTime.fromMSecsSinceEpoch(
                int(self.data['time'][0].timestamp() * 1000)))
            self.axis_x_lat.setMax(QDateTime.fromMSecsSinceEpoch(
                int(self.data['time'][-1].timestamp() * 1000)))

            self.axis_x_lon.setMin(QDateTime.fromMSecsSinceEpoch(
                int(self.data['time'][0].timestamp() * 1000)))
            self.axis_x_lon.setMax(QDateTime.fromMSecsSinceEpoch(
                int(self.data['time'][-1].timestamp() * 1000)))

            # Force refresh the chart
            self.chart_view_lat.update()
            self.chart_view_lon.update()
            self.chart_view_lat.repaint()
            self.chart_view_lon.repaint()

        except ValueError as e:
            print(f"ValueError: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def toggle_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_pause_button = Utils.update_button(
                self.play_pause_button, "", "play")
        else:
            self.timer.start(500)
            self.play_pause_button = Utils.update_button(
                self.play_pause_button, "", "pause")

    def closeEvent(self, event):
        self.driver.quit()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RealTimePlot()
    sys.exit(app.exec_())
