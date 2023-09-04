from qtpy import QtGui, QtCore, QtWidgets

class StatusToolbar(QtWidgets.QToolBar):
    """Status toolbar at bottom of stackWidget
    
    Display cursor x, y, pixel intensity, image slice.
    """
    def __init__(self,
                    numSlices,
                    parent=None):
        super().__init__('status', parent)
        self._numSlices = numSlices
        self.setWindowTitle('Status Toolbar')

        self.setFloatable(False)
        self.setMovable(False)
        
        self._buildUI()
    
    def slot_updateStatus(self, statusDict):
        """Update the status in response to mouse move.
        """
        try:
            xVal = statusDict['x']
            yVal = statusDict['y']
            intensity = statusDict['intensity']

            self.xVal.setText(str(xVal))  # we always report integer pixels
            self.yVal.setText(str(yVal)) 
            self.intensityVal.setText(str(intensity))  # intensity is always an integer (will not be true for analysis)
        except (KeyError) as e:
            # statusDict is from set slice
            pass

    def slot_setSlice(self, sliceNumber):
        """Update status in response to slice/image change.
        """
        # numSlices = self._myStack.numSlices
        newText = f'{sliceNumber}/{self._numSlices}'
        self.sliceLabel.setText(newText)

    def slot_setStatus(self, statusTxt : str):
        """Set status in toolbar.
        """
        self._lastStatus.setText(statusTxt)

    def _buildUI(self):
        _alignLeft = QtCore.Qt.AlignLeft
        _alignRight = QtCore.Qt.AlignRight

        _tmpWidget = QtWidgets.QWidget()

        hBoxLayout = QtWidgets.QHBoxLayout()

        # status of most recent action
        _statusLabel = QtWidgets.QLabel('Status:')
        self._lastStatus = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_statusLabel, alignment=_alignLeft)
        hBoxLayout.addWidget(self._lastStatus, alignment=_alignLeft)

        self.slot_setStatus('Ready')

        hBoxLayout.addStretch()  # to make everything align left

        # position of mouse
        _xLabel = QtWidgets.QLabel('x')
        self.xVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_xLabel, alignment=_alignRight)
        hBoxLayout.addWidget(self.xVal, alignment=_alignRight)

        _yLabel = QtWidgets.QLabel('y')
        self.yVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_yLabel, alignment=_alignRight)
        hBoxLayout.addWidget(self.yVal, alignment=_alignRight)

        _intensityLabel = QtWidgets.QLabel('Intensity')
        self.intensityVal = QtWidgets.QLabel('')
        hBoxLayout.addWidget(_intensityLabel, alignment=_alignRight)
        hBoxLayout.addWidget(self.intensityVal, alignment=_alignRight)

        #hBoxLayout.addStretch()  # to make everything align left

        sliceLabelStr = f'0/{self._numSlices}'
        self.sliceLabel = QtWidgets.QLabel(sliceLabelStr)
        hBoxLayout.addWidget(self.sliceLabel, alignment=_alignRight)

        #
        # as a widget
        #self.setLayout(hBoxLayout)
        
        # as a toolbar
        _tmpWidget.setLayout(hBoxLayout)
        self.addWidget(_tmpWidget)