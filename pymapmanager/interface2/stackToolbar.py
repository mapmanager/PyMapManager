from qtpy import QtGui, QtCore, QtWidgets

import pymapmanager.stack

from pymapmanager._logger import logger

class StackToolBar(QtWidgets.QToolBar):
    """ToolBar at the top of a stackWidget.
    
    Manager channels and sliding z.
    """
    signalChannelChange = QtCore.Signal(object)  # int : channel number
    signalSlidingZChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}
    signalRadiusChanged = QtCore.Signal(object)  # dict : {checked, upDownSlices}

    def __init__(self,
					myStack :pymapmanager.stack,
					displayOptionsDict : dict, parent=None):
        super().__init__(parent)

        self._myStack : pymapmanager.stack = myStack
        self._displayOptionsDict = displayOptionsDict

        # list of channel strings 1,2,3,...
        self._channelList = [str(x+1) for x in range(self._myStack.numChannels+1)]

        iconsFolderPath = ''  # TODO: get from canvas.util'

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

    def _setStack(self, theStack : pymapmanager.stack):
        """Set the state of the interface based on a stack.
        
        Args:
            theStack (pymapmanager.stack): The stack to dislpay in the widget
        """
        self._myStack = theStack
        
        numChannels = self._myStack.numChannels

        # toogle toolbar actions
        for action in self._actionList:
            actionName = action.statusTip()  # like '1', '2', '3', 'rgb'
            action.setVisible(True)
            if actionName == '1' and numChannels == 1:
                action.setVisible(False)
            if actionName == '2' and numChannels < 2:
                action.setVisible(False)
            if actionName == '3' and numChannels < 3:
                action.setVisible(False)
            if actionName == 'rgb' and numChannels < 2:
                action.setVisible(False)

        self.slidingUpDown.setMaximum(self._myStack.numSlices)

    def _on_channel_callback(self, checked, index):
        """
        this REQUIRES a list of actions, self.tooList
        """
        logger.info(f'checked:{checked} index:{index}')
        
        action = self._actionList[index]
        actionName = action.statusTip()
        isChecked = action.isChecked()
        logger.info(f'  index:{index} actionName:"{actionName}" isChecked:{isChecked}')

        if actionName in self._channelList:
            # channel 1,2,3
            channel = int(actionName)
        else:
            # rgb
            channel = actionName

        # getting sloppy
        self.slot_setChannel(channel)

        self.signalChannelChange.emit(channel)  # channel can be 'rgb'

    def _on_slidingz_checkbox(self, state):
        checked = state == 2
        upDownSlices = self.slidingUpDown.value()
        
        self.slidingUpDown.setEnabled(state)

        d = {
            'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def _on_radius_value_changed(self, value):
        """
        """
        logger.info(f'Recalculate left/right given new radius {value}')
        # call function to recaculate ALL left xy, right xy given a new radius


    def _on_slidingz_value_changed(self, value):
        checked = self.slidingCheckbox.isChecked()
        upDownSlices = value
        d = {
            'checked': checked,
            'upDownSlices': upDownSlices,
        }
        self.signalSlidingZChanged.emit(d)

    def slot_setChannel(self, channel):
        """Turn on button for slected channel.
        
        These are a disjoint list, only one can be active. Others automatically disable.
        """
        logger.info(f'bTopToolbar channel:{channel}')
        if channel == 'rgb':
            channelIdx = 3
        else:
            channelIdx = channel - 1

        # turn off sliding z
        slidingEnabled = channel != 'rgb'
        logger.info(f'  slidingEnabled:{slidingEnabled}')
        self.slidingUpDown.setEnabled(slidingEnabled)
        self.slidingCheckbox.setEnabled(slidingEnabled)
        #self.colorPopup.setEnabled(slidingEnabled)

        action = self._actionList[channelIdx]
        action.setChecked(True)

    def _buildUI(self):
        _defaultChannel = self._displayOptionsDict['windowState']['defaultChannel']

        # make ['1', '2', '3', 'rgb'] disjoint selections
        channelActionGroup = QtWidgets.QActionGroup(self)

        self._actionList = []
        _channelList = ['1', '2', '3', 'rgb']
        toolIndex = 0
        for toolName in _channelList:
            iconPath = ''  # use toolName to get from canvas.util
            theIcon = QtGui.QIcon(iconPath)

            # see: https://stackoverflow.com/questions/45511056/pyqt-how-to-make-a-toolbar-button-appeared-as-pressed
            theAction = QtWidgets.QAction(theIcon, toolName)
            theAction.setCheckable(True)
            if toolName == str(_defaultChannel):
                theAction.setChecked(True)
            theAction.setStatusTip(toolName) # USED BY CALLBACK, do not change
            if toolName in ['1', '2', '3']:
                # do not set shortcut, handled by main stack widget
                #theAction.setShortcut('1')# or 'Ctrl+r' or '&r' for alt+r
                theAction.setToolTip(f'View Channel {toolName} [{toolName}]')
            elif toolName == 'rgb':
                theAction.setToolTip('View RGB')

            theAction.triggered.connect(lambda checked, index=toolIndex: self._on_channel_callback(checked, index))

            # add action
            self._actionList.append(theAction)
            self.addAction(theAction)
            channelActionGroup.addAction(theAction)

            #logger.info('TODO: implement slot_setStack(theStack) to show/hide based on channels')
            # if toolIndex==1:
                # theAction.setVisible(False)

            toolIndex += 1
        #
        self.slidingCheckbox = QtWidgets.QCheckBox('Sliding Z')
        self.slidingCheckbox.stateChanged.connect(self._on_slidingz_checkbox)
        self.addWidget(self.slidingCheckbox)

        slidingUpDownLabel = QtWidgets.QLabel('+/-')
        self.slidingUpDown = QtWidgets.QSpinBox()
        self.slidingUpDown.setMaximum(self._myStack.numSlices)
        self.slidingUpDown.setValue(3)
        self.slidingUpDown.setEnabled(False)
        self.slidingUpDown.valueChanged.connect(self._on_slidingz_value_changed)
        self.addWidget(slidingUpDownLabel)
        self.addWidget(self.slidingUpDown)

        # add radius
        radiusLabel = QtWidgets.QLabel('radius')
        self._radiusSpinBox = QtWidgets.QSpinBox()
        self._radiusSpinBox.setMaximum(10)
        self._radiusSpinBox.setValue(3)
        self._radiusSpinBox.setEnabled(True)
        self._radiusSpinBox.valueChanged.connect(self._on_radius_value_changed)
        self.addWidget(radiusLabel)
        self.addWidget(self._radiusSpinBox)

        # colorList = ['Gray', 'Gray Inverted', 'Green', 'Red', 'Blue']
        # self.colorPopup = QtWidgets.QComboBox()
        # self.colorPopup.addItems(colorList)
        # self.addWidget(self.colorPopup)

    def _on_radius_value_changed(self, value):
        """
            Value to change the radius of the left/ right points. When changed the points also change.
        """
        logger.info(f'Recalculate left/right given new radius {value}')
        # call function to recaculate ALL left xy, right xy given a new radius
        # la = self._myStack.getLineAnnotations()
        # segmentID = None
        # radius = value
        # la.calculateAndStoreRadiusLines(segmentID = segmentID, radius = radius)

        # send signal to backend to refresh 
        # AnnotationPlotWidget that displays the radius line points
        self.signalRadiusChanged.emit(value)
        # signalRadiusChanged
