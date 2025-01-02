import copy
from functools import partial
import math

from qtpy import QtCore, QtWidgets

import pymapmanager
from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent, pmmStates
from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager.interface2 import pyMapManagerApp2
from pymapmanager._logger import logger

class AnalysisParamWidget(mmWidget2):

    _widgetName = 'Analysis Parameters'

    signalSaveParameters = QtCore.Signal(dict) # dict
    signalReplotWidgetsWithNewParams = QtCore.Signal(dict) # dict

    def __init__(self, stackWidget: stackWidget2, pmmApp : pyMapManagerApp2 = None):
        """
            paramDict: detectionParamDict class

        """
        super().__init__(stackWidget)

        self.pmmApp = pmmApp
        self.widgetDict = {}
        # self.stackWidget = stackWidget
        self.canApply = False
        self.canSave = False

        if pmmApp is not None:
            # if stackWidget.isTifPath():
                # load and save from app

            # this essentially uses same analysis Params as stackWidget?
            self._analysisParameters = pmmApp.getAnalysisParams() 
            # self._analysisParameters = stackWidget.getAnalysisParams() 
            self.setWindowTitle('Analysis Parameters (Application)')
            # Get analysis Parameters from app that is save within user/documents
            
            # abb, this will be None if file does not exist
            _dict = pmmApp.getUserJsonData()
            logger.info(f"app _dict: {_dict}")

        else:
            # TODO: Disable if there is no current stack?
            self._analysisParameters = stackWidget.getAnalysisParams() 
            self.setWindowTitle('Analysis Parameters (Stack)')
            # Get analysis params from MapManagerCore Backend
            _dict = self._analysisParameters.getDict()

        # logger.info(f"self._dict {self._dict}")

        # deep copy to not alter original dict until we apply
        self._dict = copy.deepcopy(_dict)
        # self._dict = _dict
    
        # self.changedDict = {}
        self._buildGUI()

    def on_spin_box(self, paramName, value):
        """
        When QDoubldeSpinBox accepts None, value is -1e9
        """
        # Create a key value pair in changed value dictionary
        # self.changedDict[paramName] = value

        if paramName == "channel":
            # channel is offseted by 1 in calculation
            self._dict[paramName]["currentValue"] = value - 1
        else:
            # update dictionary directly
            self._dict[paramName]["currentValue"] = value

        self.enableButtons()

    def enableButtons(self):
        self.canApply = True
        self.canSave = True
        self.applyButton.setEnabled(self.canApply)
        self.saveButton.setEnabled(self.canSave)
        # logger.info(f"updated Dict {self._dict}")

    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        # self.setLayout(self.layout)
        windowLayout = self.buildAnalysisParamUI()
        self.layout.addLayout(windowLayout)
        self._makeCentralWidget(self.layout)
    
    def buildAnalysisParamUI(self):
        # key = name of parameter
        # val = columns within dictionary. Used column name to get value

        vLayout = QtWidgets.QVBoxLayout()
        vLayoutParams = QtWidgets.QGridLayout()

        hControlLayout = self.controlUI()
   
        vLayout.addLayout(hControlLayout)
        vLayout.addLayout(vLayoutParams)
        # self.stacked.addWidget(vLayout)
        
        col = 0
        row = 0
        rowSpan = 1
        colSpan = 1
        # logger.info(f"type of dict {type(self._dict)}")
        for key, val in self._dict.items():
            
            if key == "__version__":
                continue
            else:
                col = 0
                # print("key", key)
                # print("val", val)
                # print("v", val["type"])
                paramName = key
                currentValue = val["currentValue"]
                defaultValue = val["defaultValue"]
                # valueType = "int" # Currently all values are int. TODO: have a 'types' key in the backend
                # valueType = val[
                #     "type"
                # ]  # from ('int', 'float', 'boolean', 'string', detectionTypes_)
                try:
                    valueType = val[
                        "type"
                    ]  # from ('int', 'float', 'boolean', 'string', detectionTypes_)
                except (KeyError) as e:
                    logger.error(e)
                    logger.error(f'bad key:"{key}", available keys are:{val.keys()}')
                    continue
                    # normally we abort, but not for now...

                # units = val["units"]
                # humanName = val["humanName"]
                description = val["description"]

                aLabel = QtWidgets.QLabel(paramName)
                vLayoutParams.addWidget(aLabel, row, col, rowSpan, colSpan)
                col += 1
                
                # humanNameLabel =  QtWidgets.QLabel(humanName)
                # vLayoutParams.addWidget(humanNameLabel, row, col, rowSpan, colSpan)
                # col += 1
                
                # unitsLabel =  QtWidgets.QLabel(units)
                # vLayoutParams.addWidget(unitsLabel, row, col, rowSpan, colSpan)
                # col += 1

                # Different conditions for key type
                aWidget = None
                if valueType == "int":
                    aWidget = QtWidgets.QSpinBox()

                    # TODO: limit by how many channels there actually are
                    if paramName == "channel":
                        logger.info(f"channel current value {currentValue}")
                        aWidget.setRange(1, 2)  

                        # need to offset value for channel indexing in backend
                        currentValue = val["currentValue"] + 1
                    else:
                        aWidget.setRange(0, 2**16)  

                    # minimum is used for setSpecialValueText()
                    # aWidget.setSpecialValueText(
                    #     "None"
                    # )  # displayed when widget is set to minimum
                    if currentValue is None or math.isnan(currentValue):
                        aWidget.setValue(0)
                    else:
                        aWidget.setValue(currentValue)
                    aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                    aWidget.valueChanged.connect(partial(self.on_spin_box, paramName))
                
                elif valueType == "float":
                    aWidget = QtWidgets.QDoubleSpinBox()
                    aWidget.setRange(
                        0, +1e3
                    )  # minimum is used for setSpecialValueText()
                    # aWidget.setSpecialValueText(
                    #     "None"
                    # )  # displayed when widget is set to minimum

                    if currentValue is None or math.isnan(currentValue):
                        aWidget.setValue(0)
                    else:
                        aWidget.setValue(currentValue)
                    aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                    aWidget.valueChanged.connect(partial(self.on_spin_box, paramName))
                elif valueType == "list":
                    # text edit a list
                    pass
                elif valueType in ["bool", "boolean"]:
                    # popup of True/False
                    aWidget = QtWidgets.QComboBox()
                    aWidget.addItem("True")
                    aWidget.addItem("False")
                    aWidget.setCurrentText(str(currentValue))
                    aWidget.currentTextChanged.connect(
                        partial(self.on_bool_combo_box, paramName)
                )
                elif valueType == "string":
                    # text edit
                    aWidget = QtWidgets.QLineEdit(currentValue)
                    aWidget.setReadOnly(True)  # for now our 1 edit widget is not editable
                    aWidget.setAlignment(QtCore.Qt.AlignLeft)
                    aWidget.editingFinished.connect(
                        partial(self.on_text_edit, aWidget, paramName)
                    )
                else:
                    logger.error(
                        f'Did not understand valueType:"{valueType}" for parameter:"{paramName}"'
                    )

                if aWidget is not None:
                    # keep track of what we are displaying
                    # So that we can set to default
                    self.widgetDict[paramName] = {
                        "widget": aWidget,
                        # "nameLabelWidget": humanNameLabel,
                    }

                    vLayoutParams.addWidget(aWidget, row, col, rowSpan, colSpan)
                col += 1
                
                descriptionLabel = QtWidgets.QLabel(description)
                vLayoutParams.addWidget(descriptionLabel, row, col, rowSpan, colSpan)
                row += 1
        return vLayout
    
    def controlUI(self):
        # top controls
        hControlLayout = QtWidgets.QHBoxLayout()
        
        aName = "Set Defaults"
        aButton = QtWidgets.QPushButton(aName)
        aButton.clicked.connect(partial(self.on_button_click, aName))
        hControlLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

        applyButtonName = "Apply"
        self.applyButton = QtWidgets.QPushButton(applyButtonName)
        self.applyButton.clicked.connect(partial(self.on_button_click, applyButtonName))
        self.applyButton.setEnabled(self.canApply)
        hControlLayout.addWidget(self.applyButton, alignment=QtCore.Qt.AlignLeft)

        saveButtonName = "Save"
        self.saveButton = QtWidgets.QPushButton(saveButtonName)
        self.saveButton.clicked.connect(partial(self.on_button_click, saveButtonName))
        self.saveButton.setEnabled(self.canSave)
        hControlLayout.addWidget( self.saveButton, alignment=QtCore.Qt.AlignLeft)

        # Moves the buttons closer togethers
        hControlLayout.addStretch()
        return hControlLayout
    

    def refreshWidget(self):
        """ refresh Analysis Params Widget interface
        """

        # logger.info(f"replot self._dict {self._dict}")
        for key, val in self._dict.items():
            # key = paramName, ex: width
            # val = all values of that key, (currentValue, defaultValue, etc...) 
            if key == "__version__":
                continue
            else:
                paramName = key
                aWidget = self.widgetDict[paramName]["widget"]
                # print("key", key)
                # print("val", val)
                currentValue = self._dict[key]["defaultValue"] 
                if isinstance(aWidget, QtWidgets.QSpinBox):
                    try:
                        if currentValue is None or math.isnan(currentValue):
                            aWidget.setValue(0)
                        else:
                            aWidget.setValue(currentValue)
                    except TypeError as e:
                        logger.error(f"QSpinBox analysisParam:{paramName} ... {e}")
                elif isinstance(aWidget, QtWidgets.QDoubleSpinBox):
                    try:
                        if currentValue is None or math.isnan(currentValue):
                            aWidget.setValue(-1e9)
                        else:
                            aWidget.setValue(currentValue)
                    except TypeError as e:
                        logger.error(
                            f"QDoubleSpinBox analysisParam:{paramName} ... {e}"
                        )
                elif isinstance(aWidget, QtWidgets.QComboBox):
                    aWidget.setCurrentText(str(currentValue))
                elif isinstance(aWidget, QtWidgets.QLineEdit):
                    aWidget.setText(str(currentValue))
                else:
                    logger.warning(
                        f'key "{paramName}" has value "{currentValue}" but widget type "{type(aWidget)}" not understood.')

    def on_button_click(self, buttonName):
        """
        Buttons:
            Set Default - Reset all current values to the original Default Values
            Apply - Confirms changes and applies the changed values in the backend
                  - Only applys to that one particular spine
            Save - permanently saves dict changes to the backend (zarr directory file)

        
        """
        if buttonName == "Set Defaults":
            # call a function in mapmanagercore to set default
            # temp = self._analysisParameters.resetDefaults()
            # logger.info(f"temp {temp}")
            # self._dict = self._analysisParameters._getDefaults()
            _resetDict = self._analysisParameters.resetDefaults()
            self._dict = copy.deepcopy(_resetDict)
            # logger.info(f"self._dict {self._dict}")
            self.refreshWidget()

        elif buttonName == "Apply":

            #TODO: disable apply when all current changes have already been applied

            # Set dict in mapmanagercore backend
            self._analysisParameters.setDict(self._dict)
            appliedDict = self._analysisParameters.getDict()
            # Ensure that local dict is a deep copy of backend dict
            # Otherwise non applied changes are reflected immediately
            self._dict = copy.deepcopy(appliedDict)

            # refresh point and line annotations within stack/stackwidget
            # self.stackWidget.updateDFwithNewParams()

            self.canApply = False
            self.applyButton.setEnabled(self.canApply)

        elif buttonName == "Save":
            if self.pmmApp is None:
                # save to mmap directory file
                self._analysisParameters.save(externalDict = self._dict)
            else:
                # save to json file in user directory
                self.pmmApp.saveAnalysisParams(self._dict)

            self.canSave= False
            self.saveButton.setEnabled(self.canSave)

        else:
            logger.warning(f'Button "{buttonName}" not understood.')

    # Deprecated
    # def setRadiusEvent(self, event):
    #     """
    #     """
    #     # sliceNumber = event.getSliceNumber()
    #     logger.info("updating radius in analysis params")
    #     # update radius value
    #     displayOptions = self.stackWidget.getDisplayOptions()
    #     newRadius = displayOptions['lineDisplay']['radius']
    #     self.widgetDict["segmentRadius"].setValue(newRadius)

    #     self.enableButtons()
