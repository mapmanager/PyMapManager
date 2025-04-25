from pymapmanager.interface.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface.stackWidgets import stackWidget
from pymapmanager.interface import pyMapManagerApp
from pymapmanager._logger import logger

class AnalysisParamWidget(EditDataClass):

    # Name commented out to be used in meta data widget
    # _widgetName = 'Analysis Parameters'

    def __init__(self,
                 stackWidget: stackWidget,
                 pmmApp : pyMapManagerApp = None):

        super().__init__(stackWidget)

        self.pmmApp = pmmApp

        if pmmApp is not None:
            self.setWindowTitle('Analysis Parameters (Application)')
            # Get analysis Parameters from app that is saved in user/documents
            _analysisParameters = pmmApp.getAnalysisParams() 
            _dict = pmmApp.getUserJsonData()  # TODO not json, return dict
            # construct analysis params from loaded dict of key:value
            from mapmanagercore.metadata import AnalysisParams
            _analysisParameters = AnalysisParams(**_dict)
        else:
            self.setWindowTitle('Analysis Parameters (Stack)')
            _analysisParameters = stackWidget.getStack().getMetadata().analysisParameters

        self.setDataclass(_analysisParameters)

    def postInitGui(self):
        # turn off version
        self.widgetDict['version'].setEnabled(False)
        
        return
    
        # list of possible channel keys
        channelKeys = self.getStack().getMetadata().channelKeys

        from qtpy import QtCore, QtWidgets
        aComboBox = QtWidgets.QComboBox()
        aComboBox.addItems(channelKeys)  # requires List[str]
        self.widgetDict['brightestPathChannel'] = aComboBox