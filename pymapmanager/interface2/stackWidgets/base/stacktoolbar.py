from functools import partial

from qtpy import QtGui, QtCore, QtWidgets

# from pymapmanager.stack import stack

from pymapmanager._logger import logger

class StackToolBar(QtWidgets.QToolBar):
    """ToolBar at the top of a stackWidget.
    
    Manager channels and sliding z.
    """
    signalChannelChange = QtCore.Signal(object)  # int : channel number
    signalSlidingZChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalRadiusChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalPlotCheckBoxChanged = QtCore.Signal(object)  # str: plot name being checked/ unchecked
    def __init__(self,
					myStack,
					displayOptionsDict : dict,
                    parent=None):
        """
        Parameters:
        myStack : pymapmanager.stack
        """
        super().__init__(parent)

        self._myStack = myStack
        self._displayOptionsDict = displayOptionsDict

        # list of channel strings 1,2,3,...
        self._channelList = [str(x+1) for x in range(self._myStack.numChannels+1)]

        # iconsFolderPath = ''  # TODO: get from canvas.util'

        self.setWindowTitle('Stack Toolbar')

        self.setFloatable(False)
        self.setMovable(False)

        #self.setOrientation(QtCore.Qt.Vertical);
        #self.setOrientation(QtCore.Qt.Horizontal);

        #myIconSize = 12 #32
        #self.setIconSize(QtCore.QSize(myIconSize,myIconSize))
        self.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )

        # myFontSize = 10
        # myFont = self.font();
        # myFont.setPointSize(myFontSize);
        # self.setFont(myFont)

        self._buildUI()

        # refresh interface
        self._setStack(self._myStack)

    def _setStack(self, theStack):
        """Set the state of the interface based on a stack.
        
        Parameters:
        theStack :pymapmanager.stack
            The stack to dislpay in the widget
        """
        self._myStack = theStack

        # all disabled and hidden
        for actionKey, actionWidget in self._actionDict.items():
            actionWidget.setDisabled(True)
            actionWidget.setVisible(False)

        for channelIdx in range(self._myStack.numChannels):
            self._actionDict[channelIdx].setDisabled(False)
            self._actionDict[channelIdx].setVisible(True)
        
        if self._myStack.numChannels > 1:
            self._actionDict['rgb'].setDisabled(False)
            self._actionDict['rgb'].setVisible(True)

        self.slidingUpDown.setMaximum(self._myStack.numSlices)

    def _on_channel_callback(self, toolNameStr : str, checked : bool):
        """
        this REQUIRES a list of actions, self.tooList
        """
        logger.info(f'checked:{checked} toolNameStr:{toolNameStr} {type(toolNameStr)}')
        
        if toolNameStr in ['1', '2', '3']:
            channelIdx = int(toolNameStr) - 1
        else:
            channelIdx = toolNameStr  # rgb
    
        logger.info(f'   -->> channelIdx:{channelIdx}')

        # action = self._actionList[index]
        # # actionName = action.statusTip()
        # actionName = action.text()  # like '1', '2', '3', 'rgb'
        # isChecked = action.isChecked()
        
        # logger.info(f'actionName:"{actionName}" isChecked:{isChecked} index:{index}')

        # if actionName in self._channelList:
        #     # channel 1,2,3
        #     channelNumber = int(actionName)
        #     channelIdx = channelNumber - 1
        # else:
        #     # rgb
        #     channelIdx = actionName

        # logger.info(f"actionName {actionName}")
        # logger.info(f"channel emit {channel}")

        # getting sloppy
        self.slot_setChannel(channelIdx)

        self.signalChannelChange.emit(channelIdx)  # channel can be 'rgb'

    def _old_on_slidingz_checkbox(self, state):
        checked = state == 2
        upDownSlices = self.slidingUpDown.value()
        
        self.slidingUpDown.setEnabled(state)

        d = {
            'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def _old__on_radius_value_changed(self, value):
        """
            Value to change the radius of the left/ right points.
            When changed the points also change.
        """
        logger.info(f'Recalculate left/right given new radius {value}')
        # send signal to backend to refresh 
        # AnnotationPlotWidget that displays the radius line points
        self.signalRadiusChanged.emit(value)

    # def _on_radius_value_changed(self, value):
    #     """
    #     """
    #     logger.info(f'Recalculate left/right given new radius {value}')

    #     # call function to recaculate ALL left xy, right xy given a new radius
    #     self.signalRadiusChanged.emit(value)

    def _on_slidingz_value_changed(self, value):
        # checked = self.slidingCheckbox.isChecked()
        upDownSlices = value
        d = {
            # 'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def slot_setChannel(self, channelIdx):
        """Turn on button for slected channel.
        
        These are a disjoint list, only one can be active. Others automatically disable.
        """
        logger.info(f'channelIdx:{channelIdx} {type(channelIdx)}')
        
        # turn off sliding z
        # slidingEnabled = channelIdx != 'rgb'
        # self.slidingCheckbox.setEnabled(slidingEnabled)
        # self.slidingUpDown.setEnabled(slidingEnabled)

        # activate one action in [1, 2, 3, rgb]
        self._actionDict[channelIdx].setChecked(True)

    def _buildUI(self):
        # see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
        _defaultChannel = self._displayOptionsDict['windowState']['defaultChannel']

        self._actionDict = {}

        # make ['1', '2', '3', 'rgb'] disjoint selections
        self.channelActionGroup = QtWidgets.QActionGroup(self)

        for channelIdx in range(self._myStack.maxNumChannels):
            iconPath = ''  # use toolName to get from canvas.util
            theIcon = QtGui.QIcon(iconPath)

            toolNameStr = str(channelIdx + 1)
            
            theAction = QtWidgets.QAction(theIcon, toolNameStr)
            theAction.setCheckable(True)
            if toolNameStr == str(_defaultChannel):
                theAction.setChecked(True)
            # do not set shortcut, handled by main stack widget
            #theAction.setShortcut('1')# or 'Ctrl+r' or '&r' for alt+r
            theAction.setToolTip(f'View Channel {toolNameStr}')

            theAction.triggered.connect(partial(self._on_channel_callback, toolNameStr))

            # add action
            self.addAction(theAction)
            self.channelActionGroup.addAction(theAction)
            self._actionDict[channelIdx] = theAction

        #
        toolNameStr = 'rgb'
        theAction = QtWidgets.QAction(theIcon, toolNameStr)
        theAction.setCheckable(True)
        theAction.setToolTip(f'View Channel {toolNameStr}')
        theAction.triggered.connect(partial(self._on_channel_callback, toolNameStr))
        # add action
        self.addAction(theAction)
        self.channelActionGroup.addAction(theAction)
        self._actionDict[toolNameStr] = theAction

        #
        # abb 20241119, we are always in sliding z, 0 will just be one image plane
        # self.slidingCheckbox = QtWidgets.QCheckBox('Sliding Z')
        # self.slidingCheckbox.stateChanged.connect(self._on_slidingz_checkbox)
        # self.addWidget(self.slidingCheckbox)

        self.slidingUpDownLabel = QtWidgets.QLabel('+/- Images')
        self.slidingUpDown = QtWidgets.QSpinBox()
        self.slidingUpDown.setMaximum(self._myStack.numSlices)
        self.slidingUpDown.setValue(0)
        self.slidingUpDown.setEnabled(True)  # 20241119, we are always in sliding z
        self.slidingUpDown.valueChanged.connect(self._on_slidingz_value_changed)
        self.addWidget(self.slidingUpDownLabel)
        self.addWidget(self.slidingUpDown)

        # Drop Box to hide different parts of plot
        plotMenuButton = QtWidgets.QPushButton("Plots")
        self.addWidget(plotMenuButton)
        plotMenu = QtWidgets.QMenu()

        plotMenuList = ["Annotations", "Spines", "Center Line", "Radius Lines", "Labels", "Image"]
        self.actionMenuDict = {}

        for plotName in plotMenuList:
            action = plotMenu.addAction(plotName)
            action.setCheckable(True)
            isChecked = True # set true by default
            # logger.info(f"userType {userType} isChecked {isChecked}")
            action.setChecked(isChecked)
            self.actionMenuDict[plotName] = action

        plotMenuButton.setMenu(plotMenu)
        # menu.triggered.connect(lambda action: print(action.text()))
        # plotMenu.triggered.connect(lambda action: self.plotMenuChange(action.text()))
        plotMenu.triggered.connect(lambda action: self.plotMenuChange(action))

        # colorList = ['Gray', 'Gray Inverted', 'Green', 'Red', 'Blue']
        # self.colorPopup = QtWidgets.QComboBox()
        # self.colorPopup.addItems(colorList)
        # self.addWidget(self.colorPopup)

        #self.setFocus()

    def labelBoxUpdate(self):
        """ Part of plot menu Change

        Logic for when spine box is changed to update label box
        """
        spinesAction = self.actionMenuDict["Spines"]
        spineChecked = spinesAction.isChecked()

        labelAction = self.actionMenuDict["Labels"]
        labelChecked = labelAction.isChecked()

        if not spineChecked and not labelChecked:
            #
            logger.info("entering edge case")
            # keep them both off 
            pass
        elif not spineChecked:
            labelAction.setChecked(False)
            self.signalPlotCheckBoxChanged.emit("UnRefreshed Labels")
        else:
            # check if label box is changed before setting checked
            if labelAction.isChecked():
                pass
            else:
                labelAction.setChecked(True)
                self.signalPlotCheckBoxChanged.emit("UnRefreshed Labels")
    
    def plotMenuChange(self, action):

        logger.info(f"plotMenuChange {action.text()}")

        if action.text() == "Annotations":
            # Disable Spines, Center Line, Radius Lines, Labels
            self.labelBoxUpdate()
        
        if action.text() == "Radius Lines":
            # self._radiusSpinBox.setEnabled(action.isChecked())
            # self.radiusLabel.setEnabled(action.isChecked())
            pass

        elif action.text() == "Image":
            self.channelActionGroup.setEnabled(action.isChecked())
        
        if action.text() == "Spines":
            self.labelBoxUpdate()
       
        plotName = action.text()
        self.signalPlotCheckBoxChanged.emit(plotName)
