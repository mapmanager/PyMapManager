from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager._logger import logger

class mmMapWidget(QtWidgets.QMainWindow):
    """Base class all map widgets are derived from.
    """
    def __init__(self, mapWidget : "pymapmanager.interface2.mapWidget.mapWidget"):
        super().__init__()

        self._mapWidget = mapWidget

    def _makeCentralWidget(self, layout):
        """To build a visual widget, call this function with a Qt layout like QVBoxLayout.
        """
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
    
    def getMap(self):
        return self._mapWidget._map

    def _addDockWidget(self, widget : "mmWidget2", position : str, name : str = '') -> QtWidgets.QDockWidget:
        """
        Parameters
        ----------
        widget : mmWidget2
            The mmWidget2 to add as a dock
        position : str
           One of ['left', 'top', right', 'bottom']
        name : str
            Name that appears in the dock
        """
        if position == 'left':
            position = QtCore.Qt.LeftDockWidgetArea
        elif position == 'top':
            position = QtCore.Qt.TopDockWidgetArea
        elif position == 'right':
            position = QtCore.Qt.RightDockWidgetArea
        elif position == 'bottom':
            position = QtCore.Qt.BottomDockWidgetArea
        else:
            logger.error(f'did not undertand position "{position}", defaulting to Left')
            position = QtCore.Qt.LeftDockWidgetArea

        dockWIdget = QtWidgets.QDockWidget(name)
        dockWIdget.setWidget(widget)
        dockWIdget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        dockWIdget.setFloating(False)
        self.addDockWidget(position, dockWIdget)
        return dockWIdget
    
