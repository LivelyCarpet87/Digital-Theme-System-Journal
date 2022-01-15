import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFormLayout, QLineEdit, QGridLayout, QCheckBox, QHBoxLayout

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
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._themeName = QLineEdit(inputText)
        self._themeName.setMaximumWidth(156)
        layout.addWidget(self._themeName)

        self._boxes = Boxes()
        layout.addWidget(self._boxes)




class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Theme System Journal")
        self._flo = QFormLayout()
        for itemNum in range(7):
            self._flo.addRow("", ThemeRow(f"Item {itemNum}"))

        self.setLayout(self._flo)

    def addRow(self, location=-1):
        if location == -1:
            itemNum = self._flo.rowCount()
            self._flo.addRow("", ThemeRow(f"Item {itemNum}"))
        else:
            self._flo.insertRow(location, "", ThemeRow(f"Item {location} Inserted"))

    def rmRow(self, location=-1):
        if location == -1:
            itemNum = self._flo.rowCount() - 1
            self._flo.removeRow(itemNum)
        else:
            self._flo.removeRow(location)

app = QApplication(sys.argv)

window = MainWindow()
window.show()
window.addRow()
window.addRow(location=4)
window.rmRow()
window.rmRow(location=5)

app.exec()
