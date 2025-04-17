
from functools import partial
from qtpy import QtGui, QtWidgets, QtCore
from pymapmanager._logger import logger

# from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from pymapmanager.interface2.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType, pmmEvent
# from pymapmanager.interface2.stackWidgets.event.spineEvent import DeleteSpineEvent, EditSpinePropertyEvent
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QPoint

# from pymapmanager.interface2.openFirstWindow import DragAndDropWidget

class ChannelEditor(mmWidget2):
    _widgetName = 'Channel Editor'

    def __init__(self, stackWidget):
        """Widget to edit/ rearrange channels in each time point
        """
        super().__init__(stackWidget)
        self.stackWidget = stackWidget
        self.totalChannelsShown = 0
        self.refreshGUI()

    def getGridLayout(self):
        return self.finalLayout

    def _buildGUI(self):

        self.gridLayout = QtWidgets.QGridLayout()
        # numberOfChannels = self.stackWidget.getStack().numChannels
        # dictOfChannelPaths = self.stackWidget.getStack().getChannelDict()
        # listOfChannelIdx = self.stackWidget.getStack().getChannelKeys()
        # self._listOfChannelIdx = listOfChannelIdx
        
        _shape = self.stackWidget.getStack().shape
        zSlice = _shape[0]
        xVal = _shape[2]
        yVal = _shape[1]
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
        
        # Display channel list based on what is shown rather than the actual index in the backend
        # for channelIdx in range(maxNumChannels): # max number of channels designated by user
        for channelKey in self.stackWidget.getStack().getChannelKeys():
            # For channels that are already loaded/ imported
            # if channelIdx in listOfChannelIdx:
            if 1:
                # logger.info(f"channel index in loop {channelKey}")
                self.totalChannelsShown += 1
                try:
                    channelPath = dictOfChannelPaths[channelKey]
                except:
                    logger.error(f'xxx abb missing `dictOfChannelPaths`')
                    channelPath = " "

                # abb actualIndex and channelRowNum are redundant -> removed
                # Offset by 1,  channel idx being 0 based
                # actualIndex = channelKey # index within backend  # abb removed
                # channelRowNum = str(channelKey + 1)  
                # channelRowNum = channelKey  # abb removed
                # Offset by 1, accounting for initial column name 
                # self.gridLayout.addWidget(QtWidgets.QLabel(channelRowNum), channelKey + 1, 0)
                # self.gridLayout.addWidget(DraggableWidget(channelPath, channelKey + 1, 1, self, name = "widget " + 
                #                     str(channelRowNum), stackWidget = self.stackWidget,
                #                     channelKey = channelKey), channelKey + 1, 1)

                # Diplaying channel as seen in the row rather than actual index in backend
                self.gridLayout.addWidget(QtWidgets.QLabel(str(self.totalChannelsShown)), self.totalChannelsShown, 0)

                self.gridLayout.addWidget(DraggableWidget(channelPath, self.totalChannelsShown, 1, self, name = "widget " + 
                                                str(channelKey), stackWidget = self.stackWidget,
                                                channelIdx = channelKey), self.totalChannelsShown, 1)
                
                                                # ), channelKey + 1, 1)

                # if channelIdx > 0: # For now have a restriction on deleting first channel
                if 1:
                    deleteButton = QtWidgets.QPushButton('')
                    # self.gridLayout.addWidget(deleteButton, channelIdx + 1, 2)
                    self.gridLayout.addWidget(deleteButton, self.totalChannelsShown, 2)

                    # Set a trashcan icon (using standard icon set)
                    pixmapi = getattr(QtWidgets.QStyle, "SP_TrashIcon")
                    icon = self.style().standardIcon(pixmapi)
                    deleteButton.setIcon(icon)
                    deleteButton.clicked.connect(partial(self.on_button_click, channelKey))
                
                # lastChannelIdx = channelIdx
    
        # abb removed
        # if self.totalChannelsShown != maxNumChannels:
        if 1:
            self.gridLayout.addWidget(ImportChannelWidget(channelIdx = channelKey + 1, parent= self), 
                                                        self.totalChannelsShown + 1, 1)
            # else:
            #     channelRowNum = channelIdx + 1
            #     self.gridLayout.addWidget(QtWidgets.QLabel(str(channelRowNum)), channelRowNum, 0)
            #     self.gridLayout.addWidget(ContainerWidget(ImportChannelWidget(channelIdx = channelIdx, parent= self), 
            #                                               color = "maroon", padding = "1px"), 
            #                                               channelRowNum, 1)

        self.finalLayout = self.gridLayout

        return self.finalLayout 

    def importChannel(self, channelIdx, tifFile = None):
        """Open a file dialog and update the label with the file path."""
        self._stackWidget.loadInNewChannel(path = tifFile, channel = channelIdx)
        self.refreshGUI()

    def on_button_click(self, channelIdx):
        print("Button clicked!, ", channelIdx)

        self.stackWidget.deleteChannel(channelIdx)

        # check to see if there are any channels after this channel 
        # channelIdx is the actual channel in the backend (0 based)
        # TotalChannelsShown is 1 based
        # subtract 1 to make it 0 based
        if channelIdx < self.totalChannelsShown - 1:
            # decrement actual channel indexes of channels after
            # this way all the indexes correspond within the GUI (e.g. color channel indexing)
            # abb todo: get channel keys from map timepoint
            for actualIndex in self._listOfChannelIdx:
                # logger.info(f"actual Idx {actualIndex}")
                if channelIdx <  actualIndex:
                    # logger.info(f"moving actual index {actualIndex} to {actualIndex - 1}")
                    self._stackWidget.moveChannel(actualIndex, actualIndex - 1)
                    
        self.refreshGUI()

    def refreshGUI(self):
        self.totalChannelsShown = 0
        finalLayout = self._buildGUI()
        self._makeCentralWidget(finalLayout)

    def importedNewChannelEvent(self, event):
        self.refreshGUI()

class ImportChannelWidget(QtWidgets.QWidget):
    def __init__(self,
                 channelIdx,
                 parent: ChannelEditor = None):
        super().__init__()
        # channelRowNum = row
        self.setAcceptDrops(True)
        self.channelIdx = channelIdx
        self.parent = parent
        finalLayout = self._buildLayout()
        self.setLayout(finalLayout)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        # self.setMinimumHeight(200)
    
    def _buildLayout(self):
        hLayout = QtWidgets.QHBoxLayout()

        # missingChannelLabel = QtWidgets.QLabel('Missing Channel', self)
        openFileButton = QtWidgets.QPushButton('Open File')
        pixmapi = getattr(QtWidgets.QStyle, "SP_FileDialogToParent")
        icon = self.style().standardIcon(pixmapi)
        openFileButton.setIcon(icon)
        # openFileButton.clicked.connect(partial(self.importChannel, self.channelIdx))  # Connect the button click to the importFile method
        openFileButton.clicked.connect(self.onButtonPress)
        openFileButton.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        openFileButton.setMinimumHeight(60)
    
        hLayout.addWidget(openFileButton)
        # hLayout.setSpacing(0)

        return hLayout

    def onButtonPress(self):
        """ Call stackwidget to open file directory and load in new channel"""
        self.parent.importChannel(self.channelIdx)

    def importChannel(self, channelIdx, tifFile = None):
        """ Call stackwidget to open file directory and load in new channel"""
        self.parent.importChannel(channelIdx, tifFile)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for tifFile in files:
            # print(f)
            logger.info(f"loading file {tifFile}")

            # abb
            # self._app.loadStackWidget(tifFile)

            # abj
            self.importChannel(self.channelIdx, tifFile)

# class old_ImportChannelWidget(QtWidgets.QWidget):
#     def __init__(self, channelIdx, parent = None):
#         super().__init__()
#         # channelRowNum = row
#         self.channelIdx = channelIdx
#         self.parent = parent
#         finallayout = self._buildLayout()
#         self.setLayout(finallayout)
    
#     def _buildLayout(self):
#         hLayout = QtWidgets.QHBoxLayout()

#         missingChannelLabel = QtWidgets.QLabel('Missing Channel', self)
#         openFileButton = QtWidgets.QPushButton('Open File')
#         pixmapi = getattr(QtWidgets.QStyle, "SP_FileDialogToParent")
#         icon = self.style().standardIcon(pixmapi)
#         openFileButton.setIcon(icon)
#         openFileButton.clicked.connect(partial(self.importChannel, self.channelIdx))  # Connect the button click to the importFile method
        
#         openFileButton.setStyleSheet("""
#             QPushButton {
#                 background-color: darkgrey;  /* Background color */
#                 color: black;                 /* Text color */
#                 border: 1px maroon;      /* Border color */
#                 padding: 30px;                /* Padding inside the button */
#                 border-radius: 5px;    
#             }
#             QPushButton:hover {
#                 background-color: grey;  /* Background color when mouse hovers */
#             }
#         """)

#         openFileButton.setMinimumHeight(30)
#         openFileButton.setMaximumWidth(120)

#         missingChannelLabel.setStyleSheet("""
#             QLabel {
#                 background-color: maroon;  /* Background color */
#                 color: white;                 /* Text color */
#                 border: 2px maroon;      /* Border color */
#                 border-radius: 5px;    
#                 padding: 30px;                /* Padding inside the Label */
#             }
#         """)

#         hLayout.addWidget(missingChannelLabel)
#         hLayout.addWidget(openFileButton)

#         hLayout.setSpacing(0)

#         return hLayout

#     def importChannel(self, channelIdx):
#         """ Call stackwidget to open file directory and load in new channel"""

#         self.parent.importChannel(channelIdx = channelIdx)
#         # self.parent.refreshGUI()

# class ContainerWidget(QtWidgets.QWidget):
#     def __init__(self, child, color, padding):
#         super().__init__()
#         """
#             child - either a widget or layout of widgets to be placed in a decorated container
#             color - color that the container holding the child will be
#         """
#         containerWidget = QtWidgets.QWidget(self)
#         style = f"""
#                 QWidget {{
#                     background-color: {color};  /* Background color */
#                     border-radius: 5px;            /* Rounded corners */
#                     padding: {padding};                  /* Padding around the widget */
#                 }}
#             """

#         containerWidget.setStyleSheet(style)

#         finalLayout = QtWidgets.QHBoxLayout()
#         if isinstance(child, QtWidgets.QWidget):
#             finalLayout.addWidget(child)
#         elif isinstance(child, QtWidgets.QLayout):
#             logger.info(f"layout!!!!")
#             finalLayout.addLayout(child)

#         containerWidget.setLayout(finalLayout)
#         self.setLayout(QtWidgets.QHBoxLayout())
#         self.layout().addWidget(containerWidget)
#         self.setFixedSize(500, 80)

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
        # self.setFixedSize(500, 300)  # Set a fixed size for the widgets
        # self.setMinimumSize(500, 80)
        self.setAcceptDrops(True)  # Allow drag events

        # This will be used to store the original position of the widget
        self._drag_position = None
        self.mousePos = None # Parent mouse position
        # logger.info(f"text {text}")
        self._textWidget = QtWidgets.QLineEdit(text)
        self._textWidget.textChanged.connect(self.updateChannelName)

        # Have to make container widget a draggable widget for drag and drop to register
        self.containerWidget = QtWidgets.QWidget(self)
        self.containerWidget.setStyleSheet(self.getDefaultStyle())

        finalLayout = QtWidgets.QHBoxLayout(self.containerWidget)
        finalLayout.addWidget(self._textWidget)

        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.addWidget(self.containerWidget)
        self.setLayout(mainLayout)

        # self.setLayout(QtWidgets.QHBoxLayout())
        # self.layout().addWidget(self.containerWidget)

        # self.setFixedSize(500, 80)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.setMinimumSize(500, 80)
        self.setMaximumHeight(120)

    def getDefaultStyle(self):
        self.defaultStyle = f"""
                QWidget {{
                    background-color: "#2F2F2F" ;  /* Background color */
                    border-radius: 5px;            /* Rounded corners */
                    padding = "10px";              /* Padding around the widget */
                }}
                
        """
        return self.defaultStyle
                
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
            self.setCursor(QtCore.Qt.OpenHandCursor)

            # self.containerWidget.setStyleSheet("background-color: #2F2F2F; border-radius: 5px; padding: 10px; \
            #                 border: 1px solid lightBlue;")

            
            self.containerWidget.setStyleSheet("background-color: #2F2F2F; border-radius: 5px; padding: 10px; \
                    border: 1px solid lightBlue;")


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
            
            self.containerWidget.setStyleSheet(self.defaultStyle)
            self.setCursor(QtCore.Qt.ArrowCursor)
            self._drag_position = None
            event.accept()

            self.highlight_border = False
            self.containerWidget.setStyleSheet(self.defaultStyle)

    def paintEvent(self, event):
        """Override paintEvent to avoid unnecessary repaints."""
        if self._drag_position:
            super().paintEvent(event)  # Only trigger default paintEvent if not dragging
        else:
            # No paint event during dragging (prevents flickering)
            pass

    def resizeEvent(self, event):
        """Override resizeEvent to ensure no layout changes during resizing."""
        super().resizeEvent(event)  # Let the parent handle resizing

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
