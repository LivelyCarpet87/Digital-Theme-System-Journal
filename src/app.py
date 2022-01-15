import sys
import secrets
import sqlite3
import json
import pickle
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFormLayout, QLineEdit, QGridLayout, QCheckBox, QHBoxLayout, QSpacerItem, QMenu, QAction

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
    res = cur.fetchone()
    settingsFetched = res[0] if res is not None else None
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
        self._colId = colId
        self._themeId = themeId
        self.stateChanged.connect(self.storeNewState)

        columnThemeData = loadCol(self._colId)[2]
        if str(self._themeId) not in columnThemeData.keys():
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(columnThemeData[str(self._themeId)])

    def setCol(self, colId):
        self._colId = colId
        columnThemeData = loadCol(self._colId)[2]
        if str(self._themeId) not in columnThemeData.keys():
            self.setCheckState(Qt.Unchecked)
        else:
            self.setCheckState(columnThemeData[str(self._themeId)])

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

        self.insertAboveAction = QAction(self)
        self.insertAboveAction.setText("Insert Theme Above")
        self.insertAboveAction.triggered.connect(self.insertAbove)
        self.insertBelowAction = QAction(self)
        self.insertBelowAction.setText("Insert Theme Below")
        self.insertBelowAction.triggered.connect(self.insertBelow)

        self.shiftUpAction = QAction(self)
        self.shiftUpAction.setText("Shift Theme Up")
        self.shiftUpAction.triggered.connect(self.shiftUp)
        self.shiftDownAction = QAction(self)
        self.shiftDownAction.setText("Shift Theme Down")
        self.shiftDownAction.triggered.connect(self.shiftDown)

        self.deleteThemeAction = QAction(self)
        self.deleteThemeAction.setText("Delete Theme")
        self.deleteThemeAction.triggered.connect(self.deleteTheme)

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

        self.optionsButton = QPushButton(self)
        self.optionsButton.setText("Options")          #text
        self.optionsButton.clicked.connect(self.optionsButtonPressed)
        layout.addWidget(self.optionsButton)

        self.statsButton = QPushButton(self)
        self.statsButton.setText("Stats")          #text
        self.statsButton.clicked.connect(self.statsButtonPressed)
        layout.addWidget(self.statsButton)

    def updateThemeRowName(self):
        newName = self._themeName.text()
        saveThemeChanges(self._themeId, themeName=newName)

    def refreshColumns(self):
        i = 0
        for box in self._boxes:
            box.setCol(settings["colDisplayStart"]+i)
            i += 1

    def optionsButtonPressed(self):
        self.createMenu(center=self.optionsButton).exec(self.optionsButton.mapToGlobal(QPoint(0,0)))

    def statsButtonPressed(self):
        pass

    def createMenu(self, center=None):
        if center == None:
            menu = QMenu()
        else:
            menu = QMenu(center)

        separator1 = QAction(self)
        separator1.setSeparator(True)
        separator2 = QAction(self)
        separator2.setSeparator(True)
        # Populating the menu with actions
        menu.addAction(self.insertAboveAction)
        menu.addAction(self.insertBelowAction)
        menu.addAction(separator1)
        menu.addAction(self.shiftUpAction)
        menu.addAction(self.shiftDownAction)
        menu.addAction(separator2)
        menu.addAction(self.deleteThemeAction)
        return menu

    def insertAbove(self):
        pass

    def insertBelow(self):
        pass

    def shiftUp(self):
        pass

    def shiftDown(self):
        pass

    def deleteTheme(self):
        pass

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

    def setCol(self, colId):
        self._colId = colId
        if self._position == 'T':
            self.setText(loadCol(colId)[0])
        else:
            self.setText(loadCol(colId)[1])

class ColNameRow(QWidget):

    def __init__(self, position):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._position = position

        themeWidth = 156
        self._topRowSpacer = QSpacerItem(themeWidth, 12)
        layout.insertSpacerItem(0, self._topRowSpacer)

        self._cols = []

        for i in range(settings["colDisplayStart"],
        settings["colDisplayStart"]+settings["colDisplayNum"]):
            colNameBox = ColNameBox(i, self._position)
            layout.addWidget(colNameBox)
            self._cols.append(colNameBox)

        if self._position == "T":
            self.backOneButton = QPushButton(self)
            self.backOneButton.setText("B1")
            self.backOneButton.clicked.connect(self.backOne)
            layout.addWidget(self.backOneButton)

            self.fowardOneButton = QPushButton(self)
            self.fowardOneButton.setText("F1")
            self.fowardOneButton.clicked.connect(self.fowardOne)
            layout.addWidget(self.fowardOneButton)
        else:
            self.backSevenButton = QPushButton(self)
            self.backSevenButton.setText("B7")
            self.backSevenButton.clicked.connect(self.backSeven)
            layout.addWidget(self.backSevenButton)

            self.fowardSevenButton = QPushButton(self)
            self.fowardSevenButton.setText("F7")
            self.fowardSevenButton.clicked.connect(self.fowardSeven)
            layout.addWidget(self.fowardSevenButton)

    def refreshColumns(self):
        i = 0
        for colNameBox in self._cols:
            colNameBox.setCol(settings["colDisplayStart"]+i)
            i += 1

    def fowardOne(self, event):
        global settings
        settings["colDisplayStart"] += 1
        saveSettings()
        window.refreshColumns()

    def backOne(self, event):
        global settings
        if settings["colDisplayStart"] > 0:
            settings["colDisplayStart"] -= 1
            saveSettings()
            window.refreshColumns()
        else:
            return

    def fowardSeven(self, event):
        global settings
        settings["colDisplayStart"] += 7
        saveSettings()
        window.refreshColumns()

    def backSeven(self, event):
        global settings
        if settings["colDisplayStart"] >= 7:
            settings["colDisplayStart"] -= 7
            saveSettings()
            window.refreshColumns()
        else:
            return

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Theme System Journal")
        self._flo = QFormLayout()
        self.setLayout(self._flo)
        self._themRows = []

        loadSettings()

        self._colNameRowTop = ColNameRow("T")
        self._flo.addRow("", self._colNameRowTop)
        self._colNameRowBottom = ColNameRow("B")
        self._flo.addRow("", self._colNameRowBottom)

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
            themeRow = ThemeRow(f"Item {row-1}",themeId=themeId)
            self._flo.addRow("", themeRow)
        else:
            row = location + 2
            themeRow = ThemeRow(f"Item {row-1}",themeId=themeId)
            self._flo.insertRow(row, "", themeRow)
        self._themRows.append(themeRow)

    def rmRow(self, location=-1):
        if location == -1:
            row = self._flo.rowCount() - 1
            self._themRows.pop(row -2)
        else:
            row = location + 2
            self._themRows.pop(location)
        self._flo.removeRow(row)

    def refreshColumns(self):
        self._colNameRowTop.refreshColumns()
        self._colNameRowBottom.refreshColumns()
        for row in self._themRows:
            row.refreshColumns()

app = QApplication(sys.argv)

initDB()

window = MainWindow()
window.show()
app.exec()
