import sys
import secrets
import sqlite3
import json
import pickle
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFormLayout, QLineEdit, QGridLayout, QCheckBox, QHBoxLayout, QSpacerItem

settings = {}
settings["colDisplayStart"] = 0
settings["colDisplayNum"] = 14
settings["themesDisplayed"] = []

DATA_DB_PATH = 'data.db'

def initDB():
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS themes (themeId INT PRIMARY KEY, name TXT, startCol INT, endCol INT)")
    cur.execute("CREATE TABLE IF NOT EXISTS columns (colId INT PRIMARY KEY, nameTop TXT, nameBottom TXT, themeData TXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS state (name TXT PRIMARY KEY, value BLOB)")
    con.commit()
    con.close()

def loadSettings():
    global settings
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT value FROM state WHERE name = ?;', ["settings"])
    settingsFetched = cur.fetchone()[0]
    con.close()
    if settingsFetched is not None:
        settings = pickle.loads(settingsFetched)
    else:
        pass

def saveSettings():
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('INSERT INTO state (name, value) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value=excluded.value;', ["settings", pickle.dumps(settings)])
    con.commit()
    con.close()

def saveThemeChanges(themeId, themeName=None, startCol=None, endCol=None):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('INSERT OR IGNORE INTO themes (themeId) VALUES (?);', [themeId])
    if themeName is not None:
        cur.execute('INSERT INTO themes (themeId, name) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET name=excluded.name;', [themeId, themeName])
    if startCol is not None:
        cur.execute('INSERT INTO themes (themeId, startCol) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET startCol=excluded.startCol;', [themeId, startCol])
    if endCol is not None:
        cur.execute('INSERT INTO themes (themeId, endCol) VALUES (?, ?) ON CONFLICT(themeId) DO UPDATE SET endCol=excluded.endCol;', [themeId, endCol])
    con.commit()
    con.close()

def loadTheme(themeId):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT * FROM themes WHERE themeId = ?;', [themeId])
    theme = cur.fetchone()
    con.close()
    return theme

def saveColChanges(colId, nameTop=None, nameBottom=None, box=None):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('INSERT OR IGNORE INTO columns (colId) VALUES (?);', [colId])
    if nameTop is not None:
        cur.execute('INSERT INTO columns (colId, nameTop) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET nameTop=excluded.nameTop;', [colId, nameTop])
    if nameBottom is not None:
        cur.execute('INSERT INTO columns (colId, nameBottom) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET nameBottom=excluded.nameBottom;', [colId, nameBottom])
    if box is not None:
        cur.execute('SELECT themeData FROM columns WHERE colId = ?;', [colId])
        jsonTxt = cur.fetchone()[0]
        if jsonTxt is not None:
            themeDataDict = json.loads(jsonTxt)
        else:
            themeDataDict = {}
        themeDataDict[ str(box['themeId']) ] = box['value']
        jsonTxt = json.dumps(themeDataDict)
        cur.execute('INSERT INTO columns (colId, themeData) VALUES (?, ?) ON CONFLICT(colId) DO UPDATE SET themeData=excluded.themeData;', [colId, jsonTxt])
    con.commit()
    con.close()

def loadCol(colId):
    con = sqlite3.connect(DATA_DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT * FROM columns WHERE colId = ?;', [colId])
    col = cur.fetchone()
    con.close()
    if col is not None:
        if col[3] is not None:
            themeDataDict = json.loads(col[3])
        else:
            themeDataDict = {}
        return (col[1],col[2],themeDataDict)
    else:
        return ("","",{})

class Box(QCheckBox):

    def __init__(self, themeId, colId):
        super().__init__()
        self.setTristate(True)
        columnThemeData = loadCol(colId)[2]
        if str(themeId) not in columnThemeData.keys():
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(columnThemeData[str(themeId)])
        self.stateChanged.connect(self.storeNewState)
        self._colId = colId
        self._themeId = themeId

    def setCol(self, colId):
        self._colId = colId

    def storeNewState(self):
        box = {}
        box['themeId'] = self._themeId
        box['value'] = self.checkState()
        saveColChanges(self._colId, box=box)

class ThemeRow(QWidget):

    def __init__(self, themeName, themeId = -1):
        global settings
        super().__init__()

        if themeId == -1:
            self._themeId = secrets.randbelow(99999)
        else:
            self._themeId = themeId

        layout = QHBoxLayout()
        self.setLayout(layout)

        themeWidth = 156
        self._themeName = QLineEdit(themeName)
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
        if themeId == -1:
            saveThemeChanges(self._themeId,  themeName=themeName)
            settings["themesDisplayed"].append(self._themeId)
            saveSettings()
        else:
            theme = loadTheme(themeId)
            self._themeName.clear()
            self._themeName.setText(theme[1])

    def updateThemeRowName(self):
        newName = self._themeName.text()
        saveThemeChanges(self._themeId, themeName=newName)

class ColNameBox(QLineEdit):

    def __init__(self, colId, position):
        super().__init__()
        self._colId = colId
        self._position = position #T Top / B Bottom

        colWidth = 64
        self.setMaximumWidth(colWidth)
        self.setMinimumWidth(colWidth)

        if self._position == 'T':
            self.setText(loadCol(colId)[0])
        else:
            self.setText(loadCol(colId)[1])

        self.editingFinished.connect(self.updateColName)

    def updateColName(self):
        newName = self.text()
        if self._position == 'T':
            saveColChanges(self._colId, nameTop=newName)
        else:
            saveColChanges(self._colId, nameBottom=newName)

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

        loadSettings()

        if len(settings["themesDisplayed"]) == 0:
            for itemNum in range(7):
                self.addRow()
        else:
            for themeId in settings["themesDisplayed"]:
                self.addRow(themeId=themeId)

        saveSettings()

    def addRow(self, location=-1, themeId=-1):
        if location == -1:
            row = self._flo.rowCount()
            self._flo.addRow("", ThemeRow(f"Item {row-1}",themeId=themeId))
        else:
            row = location + 2
            self._flo.insertRow(row, "", ThemeRow(f"Item {row-1}",themeId=themeId))

    def rmRow(self, location=-1):
        if location == -1:
            row = self._flo.rowCount() - 1
        else:
            row = location + 2
        self._flo.removeRow(row)

app = QApplication(sys.argv)

initDB()

window = MainWindow()
window.show()
app.exec()
