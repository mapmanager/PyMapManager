from pymapmanager.interface.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface.stackWidgets import stackWidget
from pymapmanager._logger import logger, setLogLevel
from qtpy import QtGui, QtCore, QtWidgets

from pymapmanager.interface.pyMapManagerApp import PyMapManagerApp
from pymapmanager._logger import logger
from pymapmanager.interface.stackWidgets.experimentMetadata import ExperimentMetadata
from pymapmanager.interface.stackWidgets.voxelMetadata import VoxelMetadata 
from pymapmanager.interface.stackWidgets.analysisParamWidget2 import AnalysisParamWidget 

from pymapmanager.interface.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent

class MetaDataWidget(mmWidget2):
    _widgetName = 'Metadata Widget'
    def __init__(self, stackWidget: stackWidget):
        super().__init__(stackWidget)

        layout = QtWidgets.QVBoxLayout(self)

        self.tabWidget = QtWidgets.QTabWidget()
        layout.addWidget(self.tabWidget)

        # Instantiate and add tabs
        self.voxelTab = VoxelMetadata(stackWidget)
        self.experimentTab = ExperimentMetadata(stackWidget)
        self.analysisParamsTab = AnalysisParamWidget(stackWidget)

        # self.tabWidget.addTab(self.geometryTab, self.geometryTab._widgetName)
        # self.tabWidget.addTab(self.displayTab, self.displayTab._widgetName)
        self.tabWidget.addTab(self.voxelTab, "Voxel")
        self.tabWidget.addTab(self.experimentTab, "Experiment")
        self.tabWidget.addTab( self.analysisParamsTab, "Analysis Parameters")

        self.setCentralWidget(self.tabWidget)