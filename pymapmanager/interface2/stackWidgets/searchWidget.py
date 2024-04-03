
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

import pymapmanager.annotations

from .mmWidget2 import mmWidget2
# from .mmWidget2 import pmmEventType, pmmEvent, pmmStates

from pymapmanager.interface2.core.search_widget import myQTableView

class SearchWidget(mmWidget2):

    _widgetName = 'Search Widget'

    def __init__(self, stackWidget : "StackWidget"):
        """
        """
        super().__init__(stackWidget)

        self._annotations = stackWidget.getStack().getPointAnnotations()

        self._buildUI()

    def _buildUI(self):
        vLayout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(vLayout)

        df = self._annotations.getDataFrame()
        self.myTableView = myQTableView(df)

        vLayout.addWidget(self.myTableView)


        