from functools import partial

from qtpy import QtGui, QtCore, QtWidgets

# from pymapmanager.interface.stackWidgets.base.mmWidget2 import pmmEvent
from pymapmanager.stack import stack

from pymapmanager._logger import logger
# from pymapmanager.interface.stackWidgets.base.mmWidget2 import pmmEvent

class StackToolBar(QtWidgets.QToolBar):
    """ToolBar at the top of a stackWidget.
    
    Manager channels and sliding z.
    """
    signalChannelChange = QtCore.Signal(object)  # int : channel number
    signalSlidingZChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalRadiusChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalPlotCheckBoxChanged = QtCore.Signal(object)  # str: plot name being checked/ unchecked
    def __init__(self,
					myStack: stack,
					displayOptionsDict : dict,
                    channelKey,  # the channel to init with
                    parent=None):
        """
        Parameters:
        myStack : pymapmanager.stack
        """
        super().__init__(parent)

        self._myStack:stack = myStack
        self._displayOptionsDict = displayOptionsDict

        self._currentChannel = channelKey

        self.setWindowTitle('Stack Toolbar')

        self.setFloatable(False)
        self.setMovable(False)

        self.setToolButtonStyle( QtCore.Qt.ToolButtonTextUnderIcon )

        # set in _setStack
        # self._buildUI()

        # refresh interface
        self._setStack(self._myStack)

    def _setStack(self, theStack: stack):
        """Set the state of the interface based on a stack.
        
        Parameters:
        -----------
        theStack :pymapmanager.stack
            The stack to dislpay in the widget
        """
        self._myStack = theStack

        # stack might have more or less channels than before
        self._buildUI()  # clear all actions and remake entire GUI

        # all disabled and hidden
        for actionKey, actionWidget in self._actionDict.items():
            actionWidget.setDisabled(True)
            actionWidget.setVisible(False)

        # for channelIdx in range(self._myStack.numChannels):
        for channelKey in self._myStack.getChannelKeys():
            # logger.info(f"channelIdx visible {channelIdx} ")
            self._actionDict[channelKey].setDisabled(False)
            self._actionDict[channelKey].setVisible(True)
        
        if self._myStack.numChannels > 1:
            self._actionDict['rgb'].setDisabled(False)
            self._actionDict['rgb'].setVisible(True)

        self.slidingUpDown.setMaximum(self._myStack.numSlices)

    def _on_channel_callback(self, toolNameStr : str, checked : bool):
        """
        this REQUIRES a list of actions, self.tooList
        """
        logger.info(f'toolNameStr:{toolNameStr} {type(toolNameStr)}')

        # toolNameInt = int(toolNameStr)
        
        if toolNameStr == 'rgb':
            pass
        else:
            # toolNameStr = int(toolNameStr)  # TODO: don't cast int() here, do it in signal slot
            pass

        self.slot_setChannel(toolNameStr)
        
        self.signalChannelChange.emit(toolNameStr)  # channel can be 'rgb'

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

    def slot_setChannel(self, channelKey):
        """Turn on button for selected channel.
        
        These are a disjoint list, only one can be active. Others automatically disable.
        """
        logger.info(f'channelIdx:{channelKey} {type(channelKey)}')

        # turn off sliding z
        # slidingEnabled = channelIdx != 'rgb'
        # self.slidingCheckbox.setEnabled(slidingEnabled)
        # self.slidingUpDown.setEnabled(slidingEnabled)

        # TODO: use stack metadata channels to determine type
        if channelKey == 'rgb':
            pass
        else:
            channelKey = int(channelKey)

        # logger.info(f'  is now {channelIdx} {type(channelIdx)}')

        # activate one action in [1, 2, 3, rgb]
        self._actionDict[channelKey].setChecked(True)

        self.setCurrentChannel(channelKey) # abj

        # self.signalChannelChange.emit(channelIdx)  # channel can be 'rgb'

    def _buildUI(self):
        # abb clear all actions, this is member of QToolbar (like menus)
        # used when we update stack after changing channels
        self.clear()
        
        # abb 202508 this is problematic as we do not know the type of channelKey
        # see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
        # _defaultChannel = self._displayOptionsDict['windowState']['defaultChannel']

        self._actionDict = {}

        # make ['1', '2', '3', 'rgb'] disjoint selections
        self.channelActionGroup = QtWidgets.QActionGroup(self)

        for channelKey in self._myStack.getChannelKeys():
            iconPath = ''  # use toolName to get from canvas.util
            theIcon = QtGui.QIcon(iconPath)

            toolNameStr = str(channelKey)  # dangerous but should usually work?

            theAction = QtWidgets.QAction(theIcon, toolNameStr)
            theAction.setCheckable(True)
            if toolNameStr == str(self.getCurrentChannel()):
                theAction.setChecked(True)
                # self.setCurrentChannel(_defaultChannel) # abj
            # do not set shortcut, handled by main stack widget
            #theAction.setShortcut('1')# or 'Ctrl+r' or '&r' for alt+r
            theAction.setToolTip(f'View Channel {toolNameStr}')
            theAction.triggered.connect(partial(self._on_channel_callback, toolNameStr))

            # add action
            self.addAction(theAction)
            self.channelActionGroup.addAction(theAction)
            self._actionDict[channelKey] = theAction

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
        # abj
        zPlusMinus = self._displayOptionsDict['windowState']['zPlusMinus']
        self.slidingUpDown.setValue(zPlusMinus)
        self.slidingUpDown.setEnabled(True)  # 20241119, we are always in sliding z
        self.slidingUpDown.valueChanged.connect(self._on_slidingz_value_changed)
        self.addWidget(self.slidingUpDownLabel)
        self.addWidget(self.slidingUpDown)

        # Drop Box to hide different parts of plot
        plotMenuButton = QtWidgets.QPushButton("Plots")
        self.addWidget(plotMenuButton)
        plotMenu = QtWidgets.QMenu()

        plotMenuList = ["Annotations", "Spines", "Labels", "Center Line", "Radius Lines", "Pivot Points", "Image"]
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

    def manuallyUpdatePlotBoxes(self, plotName, checked: bool = False):
        """
        """
        action = self.actionMenuDict[plotName]
        # self.plotMenuChange(action)
        action.setChecked(checked)
        self.plotMenuChange(action)

    def labelBoxUpdate(self):
        """ Part of plot menu Change

        Logic for when spine box is changed to update label box
        """
        spinesAction = self.actionMenuDict["Spines"]
        spineChecked = spinesAction.isChecked()

        labelAction = self.actionMenuDict["Labels"]
        labelChecked = labelAction.isChecked()

        if not spineChecked and not labelChecked:
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
    
    def checkAnnotations(self, check: bool = False):
        """ Uncheck and disable all annotations in the top tool bar
        """
        spinesAction = self.actionMenuDict["Spines"]
        # spineChecked = spinesAction.isChecked()
        spinesAction.setChecked(check)

        labelAction = self.actionMenuDict["Labels"]
        labelAction.setChecked(check)

        radiusLinesAction = self.actionMenuDict["Radius Lines"]
        radiusLinesAction.setChecked(check)

        centerLineAction = self.actionMenuDict["Center Line"]
        centerLineAction.setChecked(check)

        pivotPointsAction = self.actionMenuDict["Pivot Points"]
        pivotPointsAction.setChecked(check)

    def plotMenuChange(self, action):
        """ Emit a plot name after a given action (check box) is clicked

        Args:
            actions: holds the text() of plot that will be emitted to other widgets. This plot will be used to
            update those widgets accordingly
        """

        logger.info(f"plotMenuChange {action.text()}")

        if action.text() == "Annotations":
            # Disable Spines, Center Line, Radius Lines, Labels
            # check off their boxes
            annotationsAction = self.actionMenuDict["Annotations"]
            annotationCheck = annotationsAction.isChecked()
            logger.info(f"annotations check {annotationCheck}")
            self.checkAnnotations(annotationCheck)
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

    def setCurrentChannel(self, channelKey):
        """ set current channel selected
        """
        logger.info(f"setCurrentChannel {channelKey} {type(channelKey)}")
        self._currentChannel = channelKey

    def getCurrentChannel(self):
        """ Get current channel selected
        """
        return self._currentChannel
