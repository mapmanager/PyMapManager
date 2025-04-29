from qtpy import QtWidgets

from pymapmanager.interface.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface.stackWidgets import stackWidget

from pymapmanager.interface.stackWidgets.analysisParamWidget2 import AnalysisParamWidget 
from pymapmanager.interface.stackWidgets.base.mmWidget2  import mmWidget2

# from pymapmanager._logger import logger

class MetaDataWidget(mmWidget2):
    _widgetName = 'Metadata Widget'
    def __init__(self, stackWidget: stackWidget):
        super().__init__(stackWidget)

        layout = QtWidgets.QVBoxLayout(self)

        self.tabWidget = QtWidgets.QTabWidget()
        layout.addWidget(self.tabWidget)

        # add tabs
        voxelMetadata = stackWidget.getStack().getMetadata().voxelMetadata
        self.voxelTab = EditDataClass(stackWidget, dataClass=voxelMetadata)

        experimentMetadata = stackWidget.getStack().getMetadata().experimentMetadata
        self.experimentTab = EditDataClass(stackWidget, dataClass=experimentMetadata)

        self.analysisParamsTab = AnalysisParamWidget(stackWidget)

        # self.tabWidget.addTab(self.geometryTab, self.geometryTab._widgetName)
        # self.tabWidget.addTab(self.displayTab, self.displayTab._widgetName)
        self.tabWidget.addTab(self.voxelTab, "Voxel")
        self.tabWidget.addTab(self.experimentTab, "Experiment")
        self.tabWidget.addTab( self.analysisParamsTab, "Analysis Parameters")

        self.setCentralWidget(self.tabWidget)