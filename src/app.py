import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFormLayout, QLineEdit, QGridLayout, QCheckBox

class Boxes(QWidget):

    def __init__(self):
        super().__init__()
        grid = QGridLayout()
        self.setLayout(grid)

        for i in range(7):
            box = QCheckBox()
            box.setCheckState(Qt.Unchecked)
            grid.addWidget(box, 0,i)

class ThemeRow(QWidget):

    def __init__(self, inputText):
        super().__init__()
        grid = QGridLayout()
        self.setLayout(grid)

        self._themeName = QLineEdit(inputText)
        grid.addWidget(self._themeName, 0,0)

        self._boxes = Boxes()
        grid.addWidget(self._boxes, 0,1)




class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        themes = []

        for i in range(7):
            themes.append(ThemeRow(f"Item {i}"))

        self.setWindowTitle("Digital Theme System Journal")
        flo = QFormLayout()
        for itemNum in range(len(themes)):
            flo.addRow(f"{itemNum+1}: ", themes[itemNum])
        self.setLayout(flo)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
