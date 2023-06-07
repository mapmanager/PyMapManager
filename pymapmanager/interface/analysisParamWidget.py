from functools import partial
import math
from pymapmanager._logger import logger
from qtpy import QtGui, QtCore, QtWidgets
from pymapmanager import AnalysisParams
import pymapmanager

class AnalysisParamWidget(QtWidgets.QWidget):

    signalParameterChanged = QtCore.Signal(dict) # dict

    def __init__(self, analysisParams):
        """
            paramDict: detectionParamDict class
        """
        super().__init__(None)

        self.widgetDict = {}
        
        self._dict = analysisParams.getDict()
        self._buildGUI()

        self.show()

    def on_spin_box(self, paramName, value):
        """
        When QDoubldeSpinBox accepts None, value is -1e9
        """
        # logger.info(f'paramName:{paramName} value:"{value}" {type(value)}')
        # Set key value of local dictionary 
        # Send signal to update the global

        # self.setCurrentValue(key = paramName, value = value)

        _dict = {paramName: value}
        self.signalParameterChanged.emit(_dict)

    def _buildGUI(self):

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        windowLayout = self.buildAnalysisParamUI()
        self.layout.addLayout(windowLayout)
    
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
        for key, val in self._dict.items():

            col = 0

            # print(key)
            # print("v", val["type"])
            paramName = key
            currentValue = val["currentValue"]
            defaultValue = val["defaultValue"]
            valueType = val[
                "type"
            ]  # from ('int', 'float', 'boolean', 'string', detectionTypes_)
            units = val["units"]
            humanName = val["humanName"]
            description = val["description"]

            aLabel = QtWidgets.QLabel(paramName)
            vLayoutParams.addWidget(aLabel, row, col, rowSpan, colSpan)
            col += 1
            
            humanNameLabel =  QtWidgets.QLabel(humanName)
            vLayoutParams.addWidget(humanNameLabel, row, col, rowSpan, colSpan)
            col += 1
            
            unitsLabel =  QtWidgets.QLabel(units)
            vLayoutParams.addWidget(unitsLabel, row, col, rowSpan, colSpan)
            col += 1

            # Different conditions for key type
            aWidget = None
            if valueType == "int":
                aWidget = QtWidgets.QSpinBox()
                aWidget.setRange(
                    0, 2**16
                )  # minimum is used for setSpecialValueText()
                aWidget.setSpecialValueText(
                    "None"
                )  # displayed when widget is set to minimum
                if currentValue is None or math.isnan(currentValue):
                    aWidget.setValue(0)
                else:
                    aWidget.setValue(currentValue)
                aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                aWidget.valueChanged.connect(partial(self.on_spin_box, paramName))
            
            elif valueType == "float":
                aWidget = QtWidgets.QDoubleSpinBox()
                aWidget.setRange(
                    -1e9, +1e9
                )  # minimum is used for setSpecialValueText()
                aWidget.setSpecialValueText(
                    "None"
                )  # displayed when widget is set to minimum

                if currentValue is None or math.isnan(currentValue):
                    aWidget.setValue(-1e9)
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
                    "nameLabelWidget": humanNameLabel,
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

        return hControlLayout
    
    def on_button_click(self, buttonName):

        if buttonName == "Set Defaults":

            # for index, val in enumerate(self.widgetDict): 
            for key, val in self._dict.items():
                # key = paramName, ex: width
                # val = all values of that key, (currentValue, defaultValue, etc...)
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
                        f'key "{paramName}" has value "{currentValue}" but widget type "{type(aWidget)}" not understood.'
                    )

            # self.replot()

        else:
            logger.warning(f'Button "{buttonName}" not understood.')

if __name__ == '__main__':
    dp = AnalysisParams()

    import pymapmanager.interface
    app = pymapmanager.interface.PyMapManagerApp()
    dpWidget = AnalysisParamWidget(dp)

    import sys
    sys.exit(app.exec_())
    # print(dp._getDocs())