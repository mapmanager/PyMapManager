"""
This is a common patttern we want to use in lots of places.

What I really want is a ...
"""

import pandas as pd
from pymapmanager._logger import logger

# TODO: separate to interface
class AnalysisParams():

    # signalParameterChanged = QtCore.Signal(dict) # dict

    def __init__(self):
        """A class to encapsulate common image analysis  parameters.
        
        This behaves like a dictionary where parameter names are keys
        """
        # super().__init__(None)
        self._dict = {}
        # self.widgetDict = {}
        # self.stacked = QtWidgets.QStackedWidget()

        self._defineAnalysisParams()

        # self._buildGUI()

        # self.show()

    def getCurrentValue(self, key):
        return self._dict[key]['currentValue'] 
    
    def getDict(self):
        return self._dict
    
    def _defineAnalysisParams(self):
        """Define all the analysis parameters.
        """

        # Spine Params
        key = "width"
        # currentValue = 3
        defaultValue = 3
        units = "pixels"
        description = "Width in pixels to calculate the spine ROI"
        humanName =  "Width of Spine ROI"
        # see = 'Creating a rect roi for a spine'
        type = "int"
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)

        key = "extendHead"
        # currentValue = 3
        defaultValue = 3
        units = "pixels"
        description = "Length in pixels by which to extend the spineROI forward"
        humanName =  "Front Length of Spine ROI"
        # see = 'Creating a rect roi for a spine'
        type = "int"
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)
        key = 'extendTail'
        # currentValue = 3
        defaultValue = 3
        type = "int"
        units = "pixels"
        description = 'Length in pixels by which to extend the spineROI backwards'
        humanName =  "Back Length of Spine ROI"
        # see = 'Creating a rect roi for a spine'
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)

        key = 'zPlusMinus'
        # currentValue = 3
        defaultValue = 3
        type = "int"
        units = "Layers"
        description = 'Used in Sliding-z-projection: for finding the brightest path from spine head to backbone (segment x/y/z)'
        humanName =  "Layers of Z being shown"
        # see = ''
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)

        key = 'numPts'
        # currentValue = 5
        defaultValue = 5
        type = "int"
        units = "pixels"
        description = 'Number of points to search forward/backward when finding brightest index'
        humanName =  "Points used for brightest Index calculation"
        # see = ''
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)

        # Line Params
        key = 'radius'
        # currentValue = 5
        defaultValue = 5
        type = "int"
        units = "pixels"
        description = 'Number of points (forward/backwards from the center brightest index) that is used to calculate the segment ROI'
        humanName =  "Amount to scale the size of the segment ROI"
        # see = ''
        self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
                                description=description, humanName=humanName, type=type)
        
        # key = 'totalPts'
        # # currentValue = 5
        # defaultValue = 5
        # type = "int"
        # units = "pixels"
        # description = 'Total Number of points to search forward/backward when displaying line/segment ROI'
        # humanName =  "Amount of points displayed in segment ROI"
        # # see = ''
        # self._addAnalysisParam(key=key, defaultValue=defaultValue, units=units, 
        #                         description=description, humanName=humanName, type=type)


    def _addAnalysisParam(self, key : str,
                        defaultValue,
                        units : str,
                        description : str,
                        humanName : str,
                        # see : str,
                        type):
        """Add a new analysis parameter key.
        
        Args:
            key : the name of the analysis parameter
            defaultValue : the default value for the analysis parameter
            description : human redable descition of what the analysis parameter does
            see : notes on what part of the code to look for usage
        
        Raises:
            KeyError: if the key already exists, it is not added
        """
        if self._paramExists(key):
            logger.error(f'key "{key}" already exists in dict ... not added')
            return
        
        #         key = "width"
        # currentValue = 3
        # defaultValue = 3
        # units = "pixels"
        # description = "Width in pixels to calculate the spine ROI"
        # humanName =  "Width of Spine ROI"
        _dict = {
            'currentValue': defaultValue,
            'defaultValue': defaultValue,
            'units' : units,
            'description' : description,
            'humanName' : humanName,
            # 'see': see,
            'type' : type
        }
        self._dict[key] = _dict

    def setCurrentValue(self, key : str, value):
        """Set a analysis parameter current value.
        """
        if not self._paramExists(key):
            logger.error(f'key "{key}" does not exists in dict ... not set')
            return

        self._dict[key]['currentValue'] = value

    def _paramExists(self, key):
        """Check if a analysis parameter exists.
        """
        return key in self._dict.keys()
    
    def __getitem__(self, key):
        """Allow [] indexing with ['key'].

        Returns:
            The current value for a given key
        """
        try:
            return self._dDict[key]['currentValue']
        except (KeyError) as e:
            logger.error(f'{e}')

    def _getDocs(self) -> str:
        """Make self documentation from our dict.
        
        Notes:
            This is not ideal, we really want each key as a row
            and all values like (currentValue, description) as columns
        
            - 5/23 Fixed with transpose
        """
        df = pd.DataFrame(self._dict).transpose()
        return df
    
    # def on_spin_box(self, paramName, value):
    #     """
    #     When QDoubldeSpinBox accepts None, value is -1e9
    #     """
    #     # logger.info(f'paramName:{paramName} value:"{value}" {type(value)}')
    #     # Set key value of local dictionary 
    #     # Send signal to update the global

    #     self.setCurrentValue(key = paramName, value = value)

    #     _dict = {paramName: value}
    #     self.signalParameterChanged.emit(_dict)
    
    # def _buildGUI(self):

    #     self.layout = QtWidgets.QVBoxLayout()
    #     self.setLayout(self.layout)
    #     windowLayout = self.buildAnalysisParamUI()
    #     self.layout.addLayout(windowLayout)
    
    # def buildAnalysisParamUI(self):
    #     # key = name of parameter
    #     # val = columns within dictionary. Used column name to get value

    #     vLayout = QtWidgets.QVBoxLayout()
    #     vLayoutParams = QtWidgets.QGridLayout()

    #     hControlLayout = self.controlUI()
   
    #     vLayout.addLayout(hControlLayout)
    #     vLayout.addLayout(vLayoutParams)
    #     # self.stacked.addWidget(vLayout)
        
    #     col = 0
    #     row = 0
    #     rowSpan = 1
    #     colSpan = 1
    #     for key, val in self._dict.items():

    #         col = 0

    #         # print(key)
    #         # print("v", val["type"])
    #         paramName = key
    #         currentValue = val["currentValue"]
    #         defaultValue = val["defaultValue"]
    #         valueType = val[
    #             "type"
    #         ]  # from ('int', 'float', 'boolean', 'string', detectionTypes_)
    #         units = val["units"]
    #         humanName = val["humanName"]
    #         description = val["description"]

    #         aLabel = QtWidgets.QLabel(paramName)
    #         vLayoutParams.addWidget(aLabel, row, col, rowSpan, colSpan)
    #         col += 1
            
    #         humanNameLabel =  QtWidgets.QLabel(humanName)
    #         vLayoutParams.addWidget(humanNameLabel, row, col, rowSpan, colSpan)
    #         col += 1
            
    #         unitsLabel =  QtWidgets.QLabel(units)
    #         vLayoutParams.addWidget(unitsLabel, row, col, rowSpan, colSpan)
    #         col += 1

    #         # Different conditions for key type
    #         aWidget = None
    #         if valueType == "int":
    #             aWidget = QtWidgets.QSpinBox()
    #             aWidget.setRange(
    #                 0, 2**16
    #             )  # minimum is used for setSpecialValueText()
    #             aWidget.setSpecialValueText(
    #                 "None"
    #             )  # displayed when widget is set to minimum
    #             if currentValue is None or math.isnan(currentValue):
    #                 aWidget.setValue(0)
    #             else:
    #                 aWidget.setValue(currentValue)
    #             aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
    #             aWidget.valueChanged.connect(partial(self.on_spin_box, paramName))
            
    #         elif valueType == "float":
    #             aWidget = QtWidgets.QDoubleSpinBox()
    #             aWidget.setRange(
    #                 -1e9, +1e9
    #             )  # minimum is used for setSpecialValueText()
    #             aWidget.setSpecialValueText(
    #                 "None"
    #             )  # displayed when widget is set to minimum

    #             if currentValue is None or math.isnan(currentValue):
    #                 aWidget.setValue(-1e9)
    #             else:
    #                 aWidget.setValue(currentValue)
    #             aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
    #             aWidget.valueChanged.connect(partial(self.on_spin_box, paramName))
    #         elif valueType == "list":
    #             # text edit a list
    #             pass
    #         elif valueType in ["bool", "boolean"]:
    #             # popup of True/False
    #             aWidget = QtWidgets.QComboBox()
    #             aWidget.addItem("True")
    #             aWidget.addItem("False")
    #             aWidget.setCurrentText(str(currentValue))
    #             aWidget.currentTextChanged.connect(
    #                 partial(self.on_bool_combo_box, paramName)
    #         )
    #         elif valueType == "string":
    #             # text edit
    #             aWidget = QtWidgets.QLineEdit(currentValue)
    #             aWidget.setReadOnly(True)  # for now our 1 edit widget is not editable
    #             aWidget.setAlignment(QtCore.Qt.AlignLeft)
    #             aWidget.editingFinished.connect(
    #                 partial(self.on_text_edit, aWidget, paramName)
    #             )
    #         else:
    #             logger.error(
    #                 f'Did not understand valueType:"{valueType}" for parameter:"{paramName}"'
    #             )

    #         if aWidget is not None:
    #             # keep track of what we are displaying
    #             # So that we can set to default
    #             self.widgetDict[paramName] = {
    #                 "widget": aWidget,
    #                 "nameLabelWidget": humanNameLabel,
    #             }

    #             vLayoutParams.addWidget(aWidget, row, col, rowSpan, colSpan)
    #         col += 1
            
    #         descriptionLabel = QtWidgets.QLabel(description)
    #         vLayoutParams.addWidget(descriptionLabel, row, col, rowSpan, colSpan)
    #         row += 1
    #     return vLayout
    
    # def controlUI(self):
    #     # top controls
    #     hControlLayout = QtWidgets.QHBoxLayout()
        
    #     aName = "Set Defaults"
    #     aButton = QtWidgets.QPushButton(aName)
    #     aButton.clicked.connect(partial(self.on_button_click, aName))
    #     hControlLayout.addWidget(aButton, alignment=QtCore.Qt.AlignLeft)

    #     return hControlLayout
    
    # def on_button_click(self, buttonName):

    #     if buttonName == "Set Defaults":

    #         # for index, val in enumerate(self.widgetDict): 
    #         for key, val in self._dict.items():
    #             # key = paramName, ex: width
    #             # val = all values of that key, (currentValue, defaultValue, etc...)
    #             paramName = key
    #             aWidget = self.widgetDict[paramName]["widget"]
    #             # print("key", key)
    #             # print("val", val)
    #             currentValue = self._dict[key]["defaultValue"] 
    #             if isinstance(aWidget, QtWidgets.QSpinBox):
    #                 try:
    #                     if currentValue is None or math.isnan(currentValue):
    #                         aWidget.setValue(0)
    #                     else:
    #                         aWidget.setValue(currentValue)
    #                 except TypeError as e:
    #                     logger.error(f"QSpinBox detectionParam:{paramName} ... {e}")
    #             elif isinstance(aWidget, QtWidgets.QDoubleSpinBox):
    #                 try:
    #                     if currentValue is None or math.isnan(currentValue):
    #                         aWidget.setValue(-1e9)
    #                     else:
    #                         aWidget.setValue(currentValue)
    #                 except TypeError as e:
    #                     logger.error(
    #                         f"QDoubleSpinBox detectionParam:{paramName} ... {e}"
    #                     )
    #             elif isinstance(aWidget, QtWidgets.QComboBox):
    #                 aWidget.setCurrentText(str(currentValue))
    #             elif isinstance(aWidget, QtWidgets.QLineEdit):
    #                 aWidget.setText(str(currentValue))
    #             else:
    #                 logger.warning(
    #                     f'key "{paramName}" has value "{currentValue}" but widget type "{type(aWidget)}" not understood.'
    #                 )

    #         # self.replot()

    #     else:
    #         logger.warning(f'Button "{buttonName}" not understood.')
# Create defaults and save button
# Save button will send the signals to backend for whatever changed

if __name__ == '__main__':
    dp = AnalysisParams()
    print(dp._getDocs())

    # dp.buildAnalysisParamUI()
