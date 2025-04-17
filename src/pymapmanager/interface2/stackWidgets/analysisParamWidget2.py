from pymapmanager.interface2.stackWidgets.base.editDataclass import EditDataClass
from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2 import pyMapManagerApp2
from pymapmanager._logger import logger

class AnalysisParamWidget(EditDataClass):

    _widgetName = 'Analysis Parameters'

    def __init__(self,
                 stackWidget: stackWidget2,
                 pmmApp : pyMapManagerApp2 = None):

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