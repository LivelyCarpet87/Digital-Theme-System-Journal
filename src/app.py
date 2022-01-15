import sys
import uuid
import sqlite3
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFormLayout, QLineEdit, QGridLayout, QCheckBox, QHBoxLayout, QSpacerItem

settings = {}
settings["colDisplayStart"] = 0
settings["colDisplayNum"] = 14
settings["rowsDisplayed"] = []

DATA_DB_PATH = 'data.db'

def initDB():
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS themes (themeId INT PRIMARY KEY, name TXT, startCol INT, endCol INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS columns (colId INT PRIMARY KEY, nameTop TXT, nameBottom TXT, themeData TXT)")
    con.commit()
    con.close()

def saveThemeChanges(themeId, themeName=None, startCol=None, endCol=None):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    if themeName is not None:
        cur.execute('INSERT INTO themes (themeId, name) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET obj=excluded.obj;', [themeId, themeName])
    if startCol is not None:
        cur.execute('INSERT INTO themes (themeId, startCol) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET obj=excluded.obj;', [themeId, startCol])
    if endCol is not None:
        cur.execute('INSERT INTO themes (themeId, endCol) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET obj=excluded.obj;', [themeId, endCol])
    con.commit()
    con.close()

def saveColChanges(colId, nameTop=None, nameBottom=None, box=None):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    if nameTop is not None:
        cur.execute('INSERT INTO columns (colId, nameTop) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET obj=excluded.obj;', [colId, nameTop])
    if nameBottom is not None:
        cur.execute('INSERT INTO columns (colId, nameBottom) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET obj=excluded.obj;', [colId, nameBottom])
    if box is not None:
        cur.execute('SELECT themeData FROM columns WHERE colId = ?;', [colId])
        jsonTxt = cur.fetchone()
        if res is not None:
            themeDataDict = json.loads(jsonTxt)
        else:
            themeDataDict = {}
        themeDataDict[ box['themeId'] ] = box['value']
        jsonTxt = json.dumps(themeDataDict)
        cur.execute('INSERT INTO columns (colId, themeData) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET obj=excluded.obj;', [colId, jsonTxt])
    con.commit()
    con.close()

class Box(QCheckBox):

    def __init__(self, themeId, col):
        super().__init__()
        self.setTristate(True)
        self.setCheckState(Qt.Unchecked)
        self.stateChanged.connect(self.storeNewState)
        self._col = col
        self._themeId = themeId

    def setCol(self, col):
        self._col = col

    def storeNewState(self):
        newState = self.checkState()

class ThemeRow(QWidget):

    def __init__(self, inputText, themeId = -1):
        super().__init__()

        if themeId == -1:
            self._themeId = uuid.uuid1().int
        else:
            self._themeId = themeId

        layout = QHBoxLayout()
        self.setLayout(layout)

        themeWidth = 156
        self._themeName = QLineEdit(inputText)
        self._themeName.setMaximumWidth(themeWidth)
        self._themeName.setMinimumWidth(themeWidth)
        layout.addWidget(self._themeName)
        self._themeName.editingFinished.connect(self.updateThemeRowName)

        self._boxes = []
        for i in range(settings["colDisplayStart"],
        settings["colDisplayStart"]+settings["colDisplayNum"]):
            box = Box(self._themeId, i)
            self._boxes.append(box)
            layout.addWidget(box)

    def updateThemeRowName(self):
        newName = self._themeName.text()

class ColNameBox(QLineEdit):

    def __init__(self, colId, position):
        super().__init__()
        self._colId = colId
        self._position = position #T Top / B Bottom

        colWidth = 64
        self.setMaximumWidth(colWidth)
        self.setMinimumWidth(colWidth)

        self.editingFinished.connect(self.updateColName)

    def updateColName(self):
        newName = self.text()

class ColNameRow(QWidget):

    def __init__(self, position):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        themeWidth = 156
        self._topRowSpacer = QSpacerItem(themeWidth, 12)
        layout.insertSpacerItem(0, self._topRowSpacer)

        self._cols = []

        for i in range(settings["colDisplayStart"],
        settings["colDisplayStart"]+settings["colDisplayNum"]):
            colNameBox = ColNameBox(i, position)
            layout.addWidget(colNameBox)
            self._cols.append(colNameBox)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Theme System Journal")
        self._flo = QFormLayout()
        self.setLayout(self._flo)
        self._flo.addRow("", ColNameRow("T"))
        self._flo.addRow("", ColNameRow("B"))

        for itemNum in range(7):
            self.addRow()

    def addRow(self, location=-1):
        if location == -1:
            row = self._flo.rowCount()
            self._flo.addRow("", ThemeRow(f"Item {row}"))
        else:
            row = location + 2
            self._flo.insertRow(row, "", ThemeRow(""))

    def rmRow(self, location=-1):
        if location == -1:
            row = self._flo.rowCount() - 1
        else:
            row = location + 2
        self._flo.removeRow(row)

app = QApplication(sys.argv)

window = MainWindow()
window.show()
window.addRow()
window.addRow(location=4)
window.rmRow()
window.rmRow(location=5)

app.exec()
