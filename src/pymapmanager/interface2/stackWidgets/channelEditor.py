
from functools import partial
from qtpy import QtGui, QtWidgets, QtCore
from pymapmanager._logger import logger

# from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent
from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent, EditSpinePropertyEvent
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QPoint

class ChannelEditor(mmWidget2):
    _widgetName = 'Channel Editor'

    def __init__(self, stackWidget):
        """Widget to edit/ rearrange channels in each time point
        """
        super().__init__(stackWidget)
        self.stackWidget = stackWidget
        self.refreshGUI()

    def getGridLayout(self):
        return self.finalLayout

    def _buildGUI(self):

        self.gridLayout = QtWidgets.QGridLayout()
        numberOfChannels = self.stackWidget.getStack().numChannels
        dictOfChannelPaths = self.stackWidget.getStack().getChannelDict()
        listOfChannelIdx = self.stackWidget.getStack().getChannelList()
        

        stackerHeader = self.stackWidget.getStack().header
        zSlice = stackerHeader["numSlices"]
        xVal = stackerHeader["xPixels"]
        yVal = stackerHeader["yPixels"]
        sizeWidget = QtWidgets.QLabel(f"Size: ({xVal}, {yVal}),  Slices: {zSlice}")


        # Labeled Columns
        self.gridLayout.addWidget(QtWidgets.QLabel("Channel"), 0, 0)

        qHLayout1 = QtWidgets.QHBoxLayout()
        qHLayout1.addWidget(QtWidgets.QLabel("Image Name"))
        qHLayout1.addStretch(1)
        qHLayout1.setSpacing(5)
        qHLayout1.addWidget(sizeWidget)

        self.gridLayout.addLayout(qHLayout1, 0, 1)
        # self.gridLayout.addWidget(QtWidgets.QLabel("Image Name"), 0, 1)
        # self.gridLayout.addWidget(xySizeWidget, 0, 1)
        
        # channelIdx in range(self.stackWidget.getStack().maxNumChannels)
        maxNumChannels = self.stackWidget.getStack().maxNumChannels

        for channelIdx in range(maxNumChannels):
            # For channels that are already loaded/ imported
            if channelIdx in listOfChannelIdx:
                try:
                    channelPath = dictOfChannelPaths[channelIdx]
                except:
                    channelPath = " "

                # Offsetby 1,  channel idx being 0 based
                channelRowNum = str(channelIdx + 1)  
                # Offset by 1, accounting for initial column name 
                self.gridLayout.addWidget(QtWidgets.QLabel(channelRowNum), channelIdx + 1, 0)

                self.gridLayout.addWidget(DraggableWidget(channelPath, channelIdx + 1, 1, self, name = "widget " + 
                                                str(channelRowNum), stackWidget = self.stackWidget,
                                                channelIdx = channelIdx
                                                ), channelIdx + 1, 1)

                if channelIdx > 0: # For now have a restriction on deleting first channel
                    deleteButton = QtWidgets.QPushButton('')
                    self.gridLayout.addWidget(deleteButton, channelIdx + 1, 2)

                    # Set a trashcan icon (using standard icon set)
                    pixmapi = getattr(QtWidgets.QStyle, "SP_TrashIcon")
                    icon = self.style().standardIcon(pixmapi)
                    deleteButton.setIcon(icon)
                    deleteButton.clicked.connect(partial(self.on_button_click, channelIdx))

            else:
                channelRowNum = channelIdx + 1
                self.gridLayout.addWidget(QtWidgets.QLabel(str(channelRowNum)), channelRowNum, 0)
                self.gridLayout.addWidget(ContainerWidget(ImportChannelWidget(channelIdx = channelIdx, parent= self), 
                                                          color = "maroon", padding = "1px"), 
                                                          channelRowNum, 1)

        self.finalLayout = self.gridLayout

        return self.finalLayout 

    def importChannel(self, channelIdx):
        """Open a file dialog and update the label with the file path."""
        self._stackWidget.loadInNewChannel(channel = channelIdx)

    def on_button_click(self, channelIdx):
        print("Button clicked!, ", channelIdx)

        self.stackWidget.deleteChannel(channelIdx)

        self.refreshGUI()

    def refreshGUI(self):

        finalLayout = self._buildGUI()
        self._makeCentralWidget(finalLayout)

    def importedNewChannelEvent(self, event):
        self.refreshGUI()

class ImportChannelWidget(QtWidgets.QWidget):
    def __init__(self, channelIdx, parent = None):
        super().__init__()
        # channelRowNum = row
        self.channelIdx = channelIdx
        self.parent = parent
        finallayout = self._buildLayout()
        self.setLayout(finallayout)
    
    def _buildLayout(self):
        hLayout = QtWidgets.QHBoxLayout()

        missingChannelLabel = QtWidgets.QLabel('Missing Channel', self)
        openFileButton = QtWidgets.QPushButton('Open File')
        pixmapi = getattr(QtWidgets.QStyle, "SP_FileDialogToParent")
        icon = self.style().standardIcon(pixmapi)
        openFileButton.setIcon(icon)
        openFileButton.clicked.connect(partial(self.importChannel, self.channelIdx))  # Connect the button click to the importFile method
        
        openFileButton.setStyleSheet("""
            QPushButton {
                background-color: darkgrey;  /* Background color */
                color: black;                 /* Text color */
                border: 1px maroon;      /* Border color */
                padding: 30px;                /* Padding inside the button */
                border-radius: 5px;    
            }
            QPushButton:hover {
                background-color: grey;  /* Background color when mouse hovers */
            }
        """)

        openFileButton.setMinimumHeight(30)
        openFileButton.setMaximumWidth(120)

        missingChannelLabel.setStyleSheet("""
            QLabel {
                background-color: maroon;  /* Background color */
                color: white;                 /* Text color */
                border: 2px maroon;      /* Border color */
                border-radius: 5px;    
                padding: 30px;                /* Padding inside the Label */
            }
        """)

        hLayout.addWidget(missingChannelLabel)
        hLayout.addWidget(openFileButton)

        hLayout.setSpacing(0)

        return hLayout

    def importChannel(self, channelIdx):
        """ Call stackwidget to open file directory and load in new channel"""

        self.parent.importChannel(channelIdx = channelIdx)
        # self.parent.refreshGUI()

class ContainerWidget(QtWidgets.QWidget):
    def __init__(self, child, color, padding):
        super().__init__()
        """
            child - either a widget or layout of widgets to be placed in a decorated container
            color - color that the container holding the child will be
        """
        containerWidget = QtWidgets.QWidget(self)
        style = f"""
                QWidget {{
                    background-color: {color};  /* Background color */
                    border-radius: 5px;            /* Rounded corners */
                    padding: {padding};                  /* Padding around the widget */
                }}
            """

        containerWidget.setStyleSheet(style)

        finalLayout = QtWidgets.QHBoxLayout()
        if isinstance(child, QtWidgets.QWidget):
            finalLayout.addWidget(child)
        elif isinstance(child, QtWidgets.QLayout):
            logger.info(f"layout!!!!")
            finalLayout.addLayout(child)

        containerWidget.setLayout(finalLayout)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(containerWidget)
        self.setFixedSize(500, 80)

class DraggableWidget(QtWidgets.QWidget):
    def __init__(self, text, row, column, parent=None, name = None, 
                 stackWidget = None, channelIdx = None):
        
        """ Draggable widget
        - shows and allows for editing of the name of the channel image
        - allows the user to drag and drop between other draggable widgets
        to swap positions

        Note: name was for testing purposes only
        
        """
        super().__init__(parent=parent)
        self.channelIdx = channelIdx
        self.widgetname = name
        self.rowNum = row
        self.columnNum = column
        self.parent = parent
        self.stackWidget = stackWidget
        # self.setStyleSheet("background-color: black;")
        self.setFixedSize(500, 300)  # Set a fixed size for the widgets
        self.setAcceptDrops(True)  # Allow drag events

        # This will be used to store the original position of the widget
        self._drag_position = None
        self.mousePos = None # Parent mouse position
        logger.info(f"text {text}")
        self._textWidget = QtWidgets.QLineEdit(text)
        self._textWidget.textChanged.connect(self.updateChannelName)

        # Have to make container widget a draggable widget for drag and drop to register
        self.containerWidget = QtWidgets.QWidget(self)
        self.defaultStyle = f"""
                QWidget {{
                    background-color: "#2F2F2F" ;  /* Background color */
                    border-radius: 5px;            /* Rounded corners */
                    padding = "10px";              /* Padding around the widget */
                }}
                
            """

        self.containerWidget.setStyleSheet(self.defaultStyle)
        finalLayout = QtWidgets.QHBoxLayout()
        finalLayout.addWidget(self._textWidget)

        self.containerWidget.setLayout(finalLayout)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.containerWidget)
        self.setFixedSize(500, 80)

    def getRow(self):
        return self.rowNum 
    
    def getColumn(self):
        return self.columnNum 
    
    def updateRowColumn(self, newRow, newColumn):
        self.rowNum = newRow
        self.columnNum = newColumn

    def mousePressEvent(self, event):
        """Store the initial position of the mouse."""
        logger.info(f"test")
        if event.button() == Qt.LeftButton:
            self._drag_position = event.pos()
            # self.mousePos = self._drag_position
            event.accept()

            self.highlight_border = True

    def mouseMoveEvent(self, event):
        """Move the widget as the mouse moves."""
        # logger.info(f"test 2")
        
        if event.buttons() & Qt.LeftButton:  # Check if the left button is held down
            if self._drag_position:
                # logger.info(f"test 2")
                # record mouse position relative to parent 
                child_pos = event.pos()
                self.mousePos = self.mapToParent(child_pos)
                # print("self.mousePos", self.mousePos)

                delta = event.pos() - self._drag_position
                self.move(self.pos() + delta)
                self.raise_()
                event.accept()

                if self.highlight_border:
                    self.containerWidget.setStyleSheet("background-color: #2F2F2F; border-radius: 5px; padding: 10px; \
                                       border: 1px solid lightBlue;")
                else:
                    self.containerWidget.setStyleSheet(self.defaultStyle)

    def mouseReleaseEvent(self, event):
        """Handle the drop event by swapping positions."""

        if self.mousePos is None: 
            return
        
        if self._drag_position:
            # Get the mouse position relative to the parent widget
            mouse_pos = self.mousePos 
            # Iterate through the child widgets in the parent layout
            layout = self.parent.getGridLayout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()

                # Check if the widget is a DraggableWidget and contains the mouse position
                if isinstance(widget, DraggableWidget) and widget != self:
                    widget_rect = widget.rect()
                    widget_pos = widget.mapTo(self.parent, widget_rect.topLeft())

                    if widget_pos.x() <= mouse_pos.x() <= widget_pos.x() + widget_rect.width() and \
                    widget_pos.y() <= mouse_pos.y() <= widget_pos.y() + widget_rect.height():
                        # Swap positions with the widget under the cursor
                        self.lock = True
                        self.swapDraggableWidget(widget)
                        break

                    else: # return back to origin position
                        logger.info(f"return back")
                        self.parent.getGridLayout().removeWidget(self)
                        self.parent.getGridLayout().addWidget(self, self.getRow(), self.getColumn())

            self._drag_position = None
            event.accept()

            self.highlight_border = False
            self.containerWidget.setStyleSheet(self.defaultStyle)

    def getChannelIdx(self):
        return self.channelIdx
    
    def swapDraggableWidget(self, widgetUnderCursor):
        if self.lock is False:
            return
        
        self.parent.getGridLayout().removeWidget(self)
        self.parent.getGridLayout().addWidget(self, widgetUnderCursor.getRow(), widgetUnderCursor.getColumn())

        self.parent.getGridLayout().removeWidget(widgetUnderCursor)
        self.parent.getGridLayout().addWidget(widgetUnderCursor, self.getRow(), self.getColumn())

        currentRow = self.getRow()
        currentCol = self.getColumn()

        # logger.info(f"currentRow {currentRow} currentCol {currentCol}")

        switchRow = widgetUnderCursor.getRow()
        switchCol = widgetUnderCursor.getColumn()

        # logger.info(f"switchRow {switchRow} switchCol {switchCol}")
        
        self.updateRowColumn(switchRow, switchCol)
        widgetUnderCursor.updateRowColumn(currentRow, currentCol)

        self.lock = False

        # add logic to swap in backend
        # already knows time point, srcChannel, destChannel 
        self.stackWidget.swapChannels(srcChannel = self.channelIdx, 
                                      destChannel = widgetUnderCursor.getChannelIdx())

    def updateChannelName(self, newChannelName: str = ""):
        self.stackWidget.updateChannel(newChannelName, channelIdx = self.getChannelIdx())
