
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
        # self._paDf = stackWidget.getStack().getPointAnnotations().getDataFrame()
        # self._laDf = stackWidget.getStack().getLineAnnotations().getDataFrame()
        # self._summaryLaDf = stackWidget.getStack().getLineAnnotations().getSummaryDf()

        self.refreshGUI()

    def getGridLayout(self):
        return self.finalLayout

    def _buildGUI(self):

        self.finalLayout = QtWidgets.QGridLayout()

        numberOfChannels = self.stackWidget.getStack().numChannels
        listOfChannelPath = self.stackWidget.getStack().getChannelNames()
        logger.info(f'listOfChannelPath {listOfChannelPath}')
        
        # Labeled Columns
        self.finalLayout.addWidget(QtWidgets.QLabel("Channel"), 0, 0)
        self.finalLayout.addWidget(QtWidgets.QLabel("Image Name"), 0, 1)
        
        for channelIdx in range(numberOfChannels):
            # account for actual channel num
            try:
                channelPath = listOfChannelPath[channelIdx]
            except:
                channelPath = " "

            # Offsetby 1,  channel idx being 0 based
            channelRowNum = str(channelIdx + 1)  
            # Offset by 1, accounting for initial column name 
            self.finalLayout.addWidget(QtWidgets.QLabel(channelRowNum), channelIdx + 1, 0)
            self.finalLayout.addWidget(DraggableWidget(channelPath, channelIdx + 1, 1, self, name = "widget " + 
                                                       str(channelRowNum), stackWidget = self.stackWidget,
                                                       channelIdx = channelIdx
                                                       ), channelIdx + 1, 1)


        # TODO: add remove channel?
        # TODO: add logic to swap channel in backend
        return self.finalLayout 

    def refreshGUI(self):

        finalLayout = self._buildGUI()
        self._makeCentralWidget(finalLayout)

    def importedNewChannelEvent(self, event):
        self.refreshGUI()

class DraggableWidget(QtWidgets.QLineEdit):
    def __init__(self, text, row, column, parent=None, name = None, 
                 stackWidget = None, channelIdx = None):
        super().__init__(text=text, parent=parent)
        self.channelIdx = channelIdx
        self.widgetname = name
        self.rowNum = row
        self.columnNum = column
        self.parent = parent
        self.stackWidget = stackWidget
        self.setStyleSheet("background-color: black;")
        self.setFixedSize(500, 100)  # Set a fixed size for the widgets
        self.setAcceptDrops(True)  # Allow drag events

        # This will be used to store the original position of the widget
        self._drag_position = None
        self.mousePos = None # Parent mouse position

        self.textChanged.connect(self.updateChannelName)

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

    def mouseMoveEvent(self, event):
        """Move the widget as the mouse moves."""
        # logger.info(f"test 2")
        
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

                    # Check if the mouse position is inside the widget's bounds

                    # this widget is the first one being clicked!
                    # can i make it so it is the one underneath?
                    # logger.info(f" SELF self.widgetname  { self.widgetname }")
                    # logger.info(f" widget.widgetname  { widget.widgetname }")
                    # widgetPosX = widget_pos.x()
                    # mousePosX = mouse_pos.x()
                    # combo = widget_pos.x() + widget_rect.width()
                    # logger.info(f"widgetPosX {widgetPosX}  mousePosX {mousePosX} combo {combo}")

                    # widgetPosY = widget_pos.y()
                    # mousePosY = mouse_pos.y()
                    # combo2 = widget_pos.y() + widget_rect.height()
                    # logger.info(f"widgetPosY {widgetPosY}  mousePosY {mousePosY} combo2 {combo2}")
                    # logger.info(f"widget_rect.width {widget_rect.width()} widget_rect.height {widget_rect.height()}")

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


    # def mouseReleaseEvent(self, event):
    #     logger.info(f"test 3")
    #     """Handle the drop event by swapping positions."""
    #     if self._drag_position:
    #         logger.info(f"test 4")
    #         widgetUnderCursor =  self.parent.childAt(event.pos())
    #         logger.info(f"widgetUnderCursor {widgetUnderCursor}")
    #         if isinstance(widgetUnderCursor, DraggableWidget) and widgetUnderCursor != self:

    #             widget_rect = widget.rect()
    #             widget_pos = widget.mapTo(self.parent, widget_rect.topLeft())
            
    #             logger.info(f"test 5")
    #             # Swap positions with the widget under the cursor
    #             self.parent.getGridLayout().removeWidget(self)
    #             self.parent.getGridLayout().addWidget(self, widgetUnderCursor.getRow(), widgetUnderCursor.getColumn())

    #             self.parent.getGridLayout().removeWidget(widgetUnderCursor)
    #             self.parent.getGridLayout().addWidget(widgetUnderCursor, self.getRow(), self.getColumn())

    #             currentRow = self.getRow()
    #             currentCol = self.getColumn()

    #             switchRow = widgetUnderCursor.getRow()
    #             switchCol = widgetUnderCursor.getColumn()

    #             self.updateRowColumn(switchRow, switchCol)
    #             widgetUnderCursor.updateRowColumn(currentRow, currentCol)

    #         self._drag_position = None
    #         event.accept()
