import sys
from PyQt5.QtWidgets import QApplication, QWidget, QTableView, QMainWindow, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel


class myTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class mySearchWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.table = QTableView()

        # change to pandas dataframe
        data = [
            [4, 9, 2],
            [1, "hello", 0],
            [3, 5, 0],
            [3, 3, "what"],
            ["this", 8, 9],
            [3, 3, "whats"],
        ]

        self.model = myTableModel(data)  # pymapmanager pandasModel

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.setSearchColumns()
        self.setSortColumn()

        # configure search, can be in a seperate member function
        # to search different columns during runtime
        # self.proxy_model.setFilterKeyColumn(-1) # Search all columns.
        # self.proxy_model.sort(0, Qt.AscendingOrder)

        self.table.setModel(self.proxy_model)

        self.searchbar = QLineEdit()

        # You can choose the type of search by connecting to a different slot here.
        # see https://doc.qt.io/qt-5/qsortfilterproxymodel.html#public-slots
        # self.searchbar.textChanged.connect(self.proxy_model.setFilterFixedString)
        # self.searchbar.textChanged.connect(self.proxy_model.setFilterRegExp)
        self.searchbar.textChanged.connect(self.doSearch)

        # self.searchbar.textChanged.connect(self.proxy_model.setFilterWildcard)


        layout = QVBoxLayout()

        layout.addWidget(self.searchbar)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def doSearch(self, value : str):
        # we are gonna have different types of search
        self.proxy_model.setFilterRegularExpression(value)

    def setSearchColumns(self, searchCol : int = -1):
        self.proxy_model.setFilterKeyColumn(searchCol) # Search all columns.

    def setSortColumn(self, sortCol : int = 0):
        self.proxy_model.sort(sortCol, Qt.AscendingOrder)

app = QApplication(sys.argv)
window = mySearchWidget()

window.setSearchColumns(2)
window.setSortColumn(1)

window.show()
app.exec_()