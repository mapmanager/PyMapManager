
from qtpy import QtGui, QtCore, QtWidgets

# import pymapmanager.annotations

from pymapmanager.interface2.stackWidgets.base.mmWidget2 import mmWidget2
from pymapmanager.interface2.core.search_widget import myQTableView

from pymapmanager._logger import logger

class SearchWidget(mmWidget2):

    _widgetName = 'Search Widget'

    def __init__(self, stackWidget):
        """Widget to display a search of point annotations.
        """
        super().__init__(stackWidget)

        self._annotations = stackWidget.getStack().getPointAnnotations()

        self._buildUI()

    def _buildUI(self):
        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)

        df = self._annotations.getDataFrame()
        self.myTableView = myQTableView(df, name='SearchWidget')

        vLayout.addWidget(self.myTableView)


        