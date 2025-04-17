from pprint import pprint
from functools import partial

from qtpy import QtCore, QtWidgets

# from mapmanagercore.metadata._metadata3 import _metadataBase

from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2
from pymapmanager.interface2.stackWidgets import stackWidget2
from pymapmanager._logger import logger

class EditDataClass(mmWidget2):
    _widgetName = '__UNDEFINED__'

    def __init__(self,
                 stackWidget: stackWidget2,
                 ):
        """After init, must call setDataclass().
        """
        super().__init__(stackWidget)

        # self._dataclass: _metadataBase = None
        self._dataclass: "_metadataBase" = None
        """The dataclass we are editing."""

        self._dict: dict = None
        """The dict we edit (a copy)."""

        self.widgetDict = {}
        self.canApply = False

    def setDataclass(self, dataClass):
        self._dataclass = dataClass
        self._dict = self._dataclass.to_dict_with_metadata()
        
        self._buildGUI()

        self.postInitGui()

    def postInitGui(self):
        """Inherited classes can tweek the gui.
        """
        return
    
    def _buildGUI(self):
        # build main gui
        self.layout = QtWidgets.QVBoxLayout()
        self._makeCentralWidget(self.layout)

        windowLayout = self._builldLayout()
        self.layout.addLayout(windowLayout)

    def _controlUI(self) -> QtWidgets.QHBoxLayout:
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

        # Moves the buttons closer togethers
        hControlLayout.addStretch()
        return hControlLayout
    
    def _builldLayout(self) -> QtWidgets.QVBoxLayout:
        # key = name of parameter
        # val = columns within dictionary. Used column name to get value

        vLayout = QtWidgets.QVBoxLayout()
        vLayoutParams = QtWidgets.QGridLayout()

        hControlLayout = self._controlUI()
   
        vLayout.addLayout(hControlLayout)
        vLayout.addLayout(vLayoutParams)
        
        col = 0
        row = 0
        rowSpan = 1
        colSpan = 1

        for paramKey, val in self._dict.items():
                        
            col = 0

            currentValue = val["currentValue"]
            valueType = val["type"]

            # units = val["units"]
            description = val["description"]

            aLabel = QtWidgets.QLabel(paramKey)
            vLayoutParams.addWidget(aLabel, row, col, rowSpan, colSpan)
            col += 1

            # unitsLabel =  QtWidgets.QLabel(units)
            # vLayoutParams.addWidget(unitsLabel, row, col, rowSpan, colSpan)
            # col += 1

            # Different conditions for key type
            aWidget = None
            if valueType == "int":
                aWidget = QtWidgets.QSpinBox()
                aWidget.setRange(0, 2**16)  
                aWidget.setValue(currentValue)
                aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                aWidget.valueChanged.connect(partial(self.on_spin_box, paramKey))

                # TODO: limit by how many channels there actually are
                # if paramName == "channel":
                #     logger.info(f"channel current value {currentValue}")
                #     aWidget.setRange(1, 2)  

                #     # need to offset value for channel indexing in backend
                #     currentValue = val["currentValue"] + 1
                # else:
                #     aWidget.setRange(0, 2**16)  
            
            elif valueType == "float":
                aWidget = QtWidgets.QDoubleSpinBox()
                aWidget.setRange(0, +1e3)
                aWidget.setValue(currentValue)
                aWidget.setKeyboardTracking(False)  # don't trigger signal as user edits
                aWidget.valueChanged.connect(partial(self.on_spin_box, paramKey))

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
                    partial(self.on_bool_combo_box, paramKey)
            )
            elif valueType == "str":
                # text edit
                aWidget = QtWidgets.QLineEdit(currentValue)
                # aWidget.setReadOnly(True)  # for now our 1 edit widget is not editable
                aWidget.setAlignment(QtCore.Qt.AlignLeft)
                aWidget.editingFinished.connect(
                    partial(self.on_text_edit, paramKey)
                )
            else:
                logger.error(
                    f'Did not understand valueType:"{valueType}" for parameter:"{paramKey}"'
                )

            if aWidget is not None:
                # keep track of what we are displaying
                self.widgetDict[paramKey] = aWidget

                vLayoutParams.addWidget(aWidget, row, col, rowSpan, colSpan)

            col += 1
            
            descriptionLabel = QtWidgets.QLabel(description)
            vLayoutParams.addWidget(descriptionLabel, row, col, rowSpan, colSpan)
            row += 1

        return vLayout
    
    def on_bool_combo_box(self, paramName, value):
        logger.warning(f'TODO: paramName:{paramName} value:{value}')
            
    def on_text_edit(self, paramName):
        # get str from widget
        value = self.widgetDict[paramName].text()

        logger.info(f'value:{value} {type(value)}')
        
        self._dict[paramName]["currentValue"] = value
        self._enableButtons()

    def on_spin_box(self, paramName, value):
        """When QDoubldeSpinBox accepts None, value is -1e9
        """
        self._dict[paramName]["currentValue"] = value

        self._enableButtons()

    def _enableButtons(self):
        self.canApply = True
        self.applyButton.setEnabled(self.canApply)

    def on_button_click(self, buttonName):
        """
        Buttons:
            Set Default - Reset all current values to the original Default Values
            Apply - Confirms changes and applies the changed values in the backend
        """        
        if buttonName == "Set Defaults":
            # reset the dataclass
            self._dataclass.reset_to_defaults()
            # grab the dict again
            self._dict = self._dataclass.to_dict_with_metadata()

            self._refreshWidget()  # refresh with new values

        elif buttonName == "Apply":
            # Set stack _dataclass to local dict
            # tricky, we need the dataclass key:name
            # (not our full descriptive _dict)
            tmpDict = {}
            for k,v in self._dict.items():
                tmpDict[k] = v['currentValue']
            self._dataclass.updateDromDict(tmpDict)

            self.canApply = False
            self.applyButton.setEnabled(self.canApply)

        else:
            logger.warning(f'Button "{buttonName}" not understood.')

    def _refreshWidget(self):
        """ refresh widget when dataclass changes
        """

        for paramKey, val in self._dict.items():
            # key = paramName, ex: width
            # val = all values of that key, (currentValue, defaultValue, etc...) 

            aWidget = self.widgetDict[paramKey]
            currentValue = self._dict[paramKey]["defaultValue"] 
            
            if isinstance(aWidget,
                          (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                aWidget.setValue(currentValue)

            elif isinstance(aWidget, QtWidgets.QComboBox):
                # bool combobox
                aWidget.setCurrentText(str(currentValue))
            
            elif isinstance(aWidget, QtWidgets.QLineEdit):
                aWidget.setText(currentValue)
            
            else:
                logger.warning(
                    f'key "{paramKey}" has value "{currentValue}" but widget type "{type(aWidget)}" not understood.')
