import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QGridLayout, QCheckBox

class Box(QCheckBox):

    def __init__(self):
        super().__init__()
        self.setCheckState(Qt.Unchecked)


class ThemeName(QLineEdit):

    def __init__(self, inputText):
        super().__init__(inputText)
        self.setMaximumWidth(156)

class ColNameTop(QLineEdit):

    def __init__(self, inputText):
        super().__init__(inputText)
        self.setMaximumWidth(64)

class ColNameBottom(QLineEdit):

    def __init__(self, inputText):
        super().__init__(inputText)
        self.setMaximumWidth(64)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Theme System Journal")
        self._layout = QGridLayout()

        for i in range(1,8):
            self._layout.addWidget(ColNameTop(""), 0, i)

        for i in range(1,8):
            self._layout.addWidget(ColNameBottom(""), 1, i)

        for i in range(2,9):
            self.addRow()

        self.setLayout(self._layout)


    def addRow(self, location=-1):
        if location == -1:
            row = self._layout.rowCount()
            self._layout.addWidget(ThemeName(""), row, 0)
            for i in range(1,8):
                self._layout.addWidget(Box(), row, i, Qt.AlignHCenter)
        else:
            row = location

    def rmRow(self, location=-1):
        if location == -1:
            row = self._layout.rowCount() - 1
        else:
            pass

app = QApplication(sys.argv)

window = MainWindow()
window.show()
window.addRow()
window.addRow(location=4)
window.rmRow()
window.rmRow(location=5)

app.exec()
