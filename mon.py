import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap

class ImageLoader(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Test loading images
        self.up_pixmap = QPixmap('style/icons/Increment.png')
        self.down_pixmap = QPixmap('style/icons/Decrement.png')

        if self.up_pixmap.isNull():
            print("Could not load Increment image.")
        else:
            print("Increment image loaded successfully.")

        if self.down_pixmap.isNull():
            print("Could not load Decrement image.")
        else:
            print("Decrement image loaded successfully.")

        # Create labels to display the images
        self.up_label = QLabel()
        self.down_label = QLabel()

        if not self.up_pixmap.isNull():
            self.up_label.setPixmap(self.up_pixmap)
        if not self.down_pixmap.isNull():
            self.down_label.setPixmap(self.down_pixmap)

        layout.addWidget(self.up_label)
        layout.addWidget(self.down_label)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageLoader()
    window.setWindowTitle('Image Loader Test')
    window.resize(300, 200)
    window.show()
    sys.exit(app.exec_())
