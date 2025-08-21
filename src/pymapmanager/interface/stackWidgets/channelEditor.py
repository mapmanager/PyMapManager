import sys
import os
from pprint import pprint
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QLineEdit, 
    QPushButton, QColorDialog
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QMimeData
from PyQt5.QtGui import QPainter, QColor, QDrag, QPixmap

from mapmanagercore.imageImporter import acceptedExtensions

from pymapmanager.interface import PyMapManagerApp
from pymapmanager.interface.stackWidgets.stackWidget import stackWidget
from pymapmanager.interface.stackWidgets.base.mmWidget2  import mmWidget2, pmmEventType
from pymapmanager.interface.stackWidgets.event.channelEvent import ChannelEditType, EditChannelEvent

from pymapmanager._logger import logger


class DraggableChannel(QFrame):
    """
    Represents an individual channel row that can be clicked and dragged inside the list.
    
    Key Features:
    - Displays channel content in a horizontal layout
    - Handles mouse events to initiate drag-and-drop
    - Uses QDrag with custom QMimeData to store the source index
    - Changes appearance to semi-transparent while dragging
    - Allows editing of channel text via QLineEdit
    """
    
    # Signal emitted when channel text is edited
    channelKeyEdited = pyqtSignal(object, str)  # (channelKey, newValue)
    # Signal emitted when channel color is changed
    onSetColor = pyqtSignal(object, str)  # (channelKey, newColor) where newColor is hex like #FF0000
    # Signal emitted when channel is deleted
    onDeleteColor = pyqtSignal(object)  # (channelKey)
    
    def __init__(self, channelKey, text):
        super().__init__()
        self.channelKey = channelKey
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLineWidth(2)
        self.setAutoFillBackground(True)
        
        # Set up the layout with channel content
        layout = QHBoxLayout()
        
        # Text editor
        self.lineEdit = QLineEdit(text)
        self.lineEdit.setFrame(False)  # Remove border for cleaner look
        self.lineEdit.editingFinished.connect(self.onEditingFinished)
        layout.addWidget(self.lineEdit)
        
        # Color picker button
        self.colorButton = QPushButton()
        self.colorButton.setFixedSize(24, 24)
        self.colorButton.setStyleSheet("QPushButton { background-color: #FF0000; border: 1px solid #999; }")
        self.colorButton.clicked.connect(self.onColorButtonClicked)
        layout.addWidget(self.colorButton)
        
        # Trash button
        self.trashButton = QPushButton()
        self.trashButton.setFixedSize(24, 24)
        self.trashButton.setStyleSheet("QPushButton { background-color: #ffcccc; border: 1px solid #999; }")
        self.trashButton.clicked.connect(self.onTrashButtonClicked)
        
        # Set qtawesome trash icon
        try:
            import qtawesome as qta
            icon = qta.icon('mdi6.delete', color='#666666')
            self.trashButton.setIcon(icon)
        except ImportError:
            # Fallback to text if qtawesome is not available
            self.trashButton.setText("🗑")
        
        layout.addWidget(self.trashButton)
        
        self.setLayout(layout)
        
        # Drag state variables
        self.dragStartPos = None
        self.dragging = False

    def mousePressEvent(self, event):
        """Store the starting mouse position for drag detection."""
        if event.button() == Qt.LeftButton:
            self.dragStartPos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        If the mouse moves far enough, starts a drag.
        Creates a QDrag object containing the source index.
        Sets a pixmap of the widget so it "floats" under the cursor during drag.
        """
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if (event.pos() - self.dragStartPos).manhattanLength() < QApplication.startDragDistance():
            return

        # Check if dragging is enabled (more than one channel)
        channel_list = self.parentWidget()
        if channel_list and hasattr(channel_list, 'parent') and channel_list.parent():
            editor = channel_list.parent()
            if hasattr(editor, 'channelKeys') and len(editor.channelKeys) <= 1:
                return  # Disable dragging if only one channel

        if not self.dragging:
            self.startDrag(event.globalPos())

    def startDrag(self, globalPos):
        """Helper to configure and start the drag operation."""
        self.dragging = True
        
        # Create drag object
        drag = QDrag(self)
        
        # Create mime data with source index
        mimeData = QMimeData()
        # Get the DraggableChannelList container
        channel_list = self.parentWidget()
        sourceIndex = channel_list.layout.indexOf(self)
        mimeData.setText(str(sourceIndex))
        
        # Create pixmap of widget for visual feedback
        pixmap = self.grab()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 127))  # Semi-transparent
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setMimeData(mimeData)
        
        # Execute drag and handle result
        result = drag.exec_(Qt.MoveAction)
        
        # Reset dragging state
        self.dragging = False

    def onEditingFinished(self):
        """Handle when user finishes editing the channel text."""
        newValue = self.lineEdit.text()
        self.channelKeyEdited.emit(self.channelKey, newValue)

    def onColorButtonClicked(self):
        """Handle color picker button click."""
        color = QColorDialog.getColor()
        if color.isValid():
            hexColor = color.name()
            self.colorButton.setStyleSheet(f"QPushButton {{ background-color: {hexColor}; border: 1px solid #999; }}")
            self.onSetColor.emit(self.channelKey, hexColor)

    def onTrashButtonClicked(self):
        """Handle trash button click."""
        self.onDeleteColor.emit(self.channelKey)


class DraggableChannelList(QWidget):
    """
    Container widget holding all draggable channels in a QVBoxLayout.
    Handles drag enter, drag move, and drop events.
    
    Key Features:
    - Accepts drags only from DraggableChannel
    - Tracks the index where the dragged item will be inserted
    - Displays a placeholder gap in the layout during dragging
    - On drop: moves the widget to the new position and emits signal
    """
    
    # Signal emitted after a successful drop with (srcIndex, dstIndex)
    dragCompleted = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        # self.layout.setSpacing(2)
        
        # Drag state
        self._dropLineY = None  # Y position for drop line
        self.dragSourceIndex = None

    def dragEnterEvent(self, event):
        """Accepts drags with valid mime data."""
        if event.mimeData().hasText():
            try:
                self.dragSourceIndex = int(event.mimeData().text())
                event.acceptProposedAction()
            except ValueError:
                event.ignore()

    def dragMoveEvent(self, event):
        """
        Calculates target index from mouse position, updates drop line position.
        Shows where the item will be dropped.
        """
        if not event.mimeData().hasText():
            event.ignore()
            return
            
        # Calculate target index from mouse position
        localPos = event.pos()
        targetIndex = self.calculateDropIndex(localPos)
        
        # Calculate Y position for drop line
        self._dropLineY = self.calculateDropLineY(localPos)
        
        # Trigger repaint to show the line
        self.update()
            
        event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Reorders widgets in the layout.
        Emits the dragCompleted signal.
        """
        if not event.mimeData().hasText():
            event.ignore()
            return
            
        try:
            srcIndex = int(event.mimeData().text())
        except ValueError:
            event.ignore()
            return
            
        # Calculate final drop position
        localPos = event.pos()
        dstIndex = self.calculateDropIndex(localPos)
        
        # Clear drop line
        self._dropLineY = None
        self.update()
        
        # Emit signal with source and destination indices
        if srcIndex != dstIndex:
            self.dragCompleted.emit(srcIndex, dstIndex)
            
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """Clear drop line when drag leaves the widget."""
        self._dropLineY = None
        self.update()
        super().dragLeaveEvent(event)

    def calculateDropIndex(self, localPos):
        """Calculate the index where the item should be dropped based on mouse position."""
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.widget() is None:
                continue
            widget = item.widget()
            if localPos.y() < widget.y() + widget.height() // 2:
                return i
        return self.layout.count()

    def calculateDropLineY(self, localPos):
        """Calculate the Y position for the drop line based on mouse position."""
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item.widget() is None:
                continue
            widget = item.widget()
            if localPos.y() < widget.y() + widget.height() // 2:
                return widget.y()
        
        # If we get here, we're dropping after the last widget
        # Find the last actual widget (not stretch)
        for i in range(self.layout.count() - 1, -1, -1):
            item = self.layout.itemAt(i)
            if item.widget() is not None:
                return item.widget().y() + item.widget().height()
        
        # Fallback if no widgets found
        return 0

    def paintEvent(self, event):
        """Override paint event to draw the drop line when dragging."""
        super().paintEvent(event)
        
        # Draw drop line if we have a valid position
        if self._dropLineY is not None:
            painter = QPainter(self)
            painter.setPen(QColor("#2196F3"))  # Blue color
            painter.setBrush(QColor("#2196F3"))
            
            # Draw a horizontal line at the drop position
            line_height = 2
            painter.drawRect(0, self._dropLineY - line_height//2, self.width(), line_height)




class ChannelEditor2(mmWidget2):
    # Signal emitted when a channel is edited
    # channelEdited = pyqtSignal(str, str)  # (channelKey, newValue)
    # Signal emitted when a channel is moved
    # moveChannel = pyqtSignal(str, str)  # (channelKey, dstChannelKey) where dstChannelKey can be None for end
    # Signal emitted when a channel color is changed
    # channelColorChanged = pyqtSignal(str, str)  # (channelKey, newColor)
    # Signal emitted when a channel is deleted
    # channelDeleted = pyqtSignal(str)  # (channelKey)
    # Signal emitted when files are imported
    # filesImported = pyqtSignal(list)  # (list of file paths)
    
    _widgetName = 'Channel Editor'

    def __init__(self, stackWidget:stackWidget):
        super().__init__(stackWidget)
        self.setWindowTitle("Channel Editor")
        # Remove fixed geometry to allow auto-sizing
        # self.setGeometry(100, 100, 400, 300)
        
        # layout = QVBoxLayout(self)
        layout = QVBoxLayout()
        self._makeCentralWidget(layout)  # mmWidget2

        # Create top toolbar
        self.toolbar = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar)
        # toolbar_layout.setContentsMargins(5, 5, 5, 5)
        # toolbar_layout.setSpacing(10)
        
        # Add labels to toolbar
        # title_label = QLabel("Channel Manager")
        # title_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        # toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()  # Push remaining items to the right
        
        # status_label = QLabel("Ready")
        # status_label.setObjectName("status_label")
        # status_label.setStyleSheet("QLabel { color: #666; }")
        # toolbar_layout.addWidget(status_label)
        
        shapeTuple = self.getStackWidget().getStack().getMetadata().shape
        count_label = QLabel(f"Pixels:{shapeTuple}")
        count_label.setObjectName("count_label")
        count_label.setStyleSheet("QLabel { color: #666; }")
        toolbar_layout.addWidget(count_label)
        
        voxelTuple = self.getStackWidget().getStack().getMetadata().voxelMetadata.shape
        voxelLabel = QLabel(f"Voxels:{voxelTuple}")
        voxelLabel.setObjectName("voxelLabel")
        voxelLabel.setStyleSheet("QLabel { color: #666; }")
        toolbar_layout.addWidget(voxelLabel)

        # Add Import File button to top toolbar
        self.importButton = QPushButton("Import File")
        self.importButton.setAcceptDrops(True)
        self.importButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.importButton.clicked.connect(self.onImportButtonClicked)
        self.importButton.dragEnterEvent = self.onImportButtonDragEnter
        self.importButton.dragMoveEvent = self.onImportButtonDragMove
        self.importButton.dropEvent = self.onImportButtonDrop
        toolbar_layout.addWidget(self.importButton)
        
        # Add toolbar to main layout
        layout.addWidget(self.toolbar)
        
        # Create the draggable channel list
        self.channelList = DraggableChannelList()
        self.channelList.dragCompleted.connect(self.onDragCompleted)
        layout.addWidget(self.channelList)
        
        # Store the current data for reference
        self._current_data = self.getStackWidget().getStack().getMetadata().getChannelDataForWidget()
        
        # Add stretch to push channels to top
        self.channelList.layout.addStretch()
                
        # Build the GUI from the provided data
        self.rebuildFromData()

    # slot in response to channel edit (import, delete, move, name, color)
    def editChannelEvent(self, event: EditChannelEvent):
        logger.info('')
        self.rebuildFromData()

    def onChannelEdited(self, channelKey, newValue):
        """Handle channel text editing - emit higher-level signal."""
        logger.info(f"Channel edited: {channelKey} → {newValue}")
        # self.channelEdited.emit(channelKey, newValue)

        editChannelEvent = EditChannelEvent(
            eventType = pmmEventType.editChannel,
            mmWidget = self.getStackWidget(),
            editType = ChannelEditType.set_name,
            srcChannelKey = channelKey,
            newName = newValue
        )
        self.emitEvent(editChannelEvent)

    def onChannelColorChanged(self, channelKey, newColor):
        """Handle channel color change - emit higher-level signal."""
        logger.info(f"Channel color changed: {channelKey} → {newColor}")
        # self.channelColorChanged.emit(channelKey, newColor)
        editChannelEvent = EditChannelEvent(
            eventType = pmmEventType.editChannel,
            mmWidget = self.getStackWidget(),
            editType = ChannelEditType.set_channel_color,
            srcChannelKey = channelKey,
            newColorLUT = newColor
        )
        self.emitEvent(editChannelEvent)

    def onChannelDeleted(self, channelKey):
        """Handle channel deletion - emit signal for external handling."""
        logger.info(f"Channel deleted: {channelKey}")
        # self.channelDeleted.emit(channelKey)
        editChannelEvent = EditChannelEvent(
            eventType = pmmEventType.editChannel,
            mmWidget = self.getStackWidget(),
            editType = ChannelEditType.delete_channel,
            srcChannelKey = channelKey
        )
        self.emitEvent(editChannelEvent)

    def onDragCompleted(self, srcIndex, dstIndex):
        """Handle drag completion - emit signal for external handling."""
        logger.info(f"Drag completed: {srcIndex} → {dstIndex}")
        
        # Get channel keys from the ordered list
        channel_keys = list(self._current_data.keys())
        
        # Map indices to channel keys
        if 0 <= srcIndex < len(channel_keys):
            srcChannelKey = channel_keys[srcIndex]
        else:
            logger.error(f"Invalid source index: {srcIndex}")
            return
            
        # Determine destination channel key
        if dstIndex >= len(channel_keys):
            # Moving to the end of the list
            dstChannelKey = None
        elif 0 <= dstIndex < len(channel_keys):
            dstChannelKey = channel_keys[dstIndex]
        else:
            logger.error(f"Invalid destination index: {dstIndex}")
            return
        
        # Emit the moveChannel signal
        # self.moveChannel.emit(srcChannelKey, dstChannelKey)
        
        editChannelEvent = EditChannelEvent(
            eventType = pmmEventType.editChannel,
            mmWidget = self.getStackWidget(),
            editType = ChannelEditType.move_channel,
            srcChannelKey = srcChannelKey,
            dstChannelKey = dstChannelKey
        )
        self.emitEvent(editChannelEvent)

        print(f"Channel moved from position {srcIndex} to position {dstIndex}")
        print(f"Signal emitted: moveChannel({srcChannelKey}, {dstChannelKey})")

    def rebuildFromData(self, ):
        """Rebuild the GUI from external data. This is the main method for updating the view."""
        self._current_data = self.getStackWidget().getStack().getMetadata().getChannelDataForWidget()

        logger.info('self._current_data is now')
        pprint(self._current_data)

        channels_data = self._current_data
        
        # Clear existing widgets
        self._clearAllChannels()
        
        # logger.info('channels_data')
        # pprint(channels_data)

        # Add channels from data in order
        for key, channel_data in channels_data.items():
            logger.info(f'key: {key} channel_data: {channel_data}')
            
            label = channel_data["label"]
            color = channel_data.get("color")  # color will always be specified
            
            ch = DraggableChannel(key, label)
            ch.channelKeyEdited.connect(self.onChannelEdited)
            ch.onSetColor.connect(self.onChannelColorChanged)
            ch.onDeleteColor.connect(self.onChannelDeleted)
            ch.colorButton.setStyleSheet(f"QPushButton {{ background-color: {color}; border: 1px solid #999; }}")
            
            # Insert before the stretch widget
            self.channelList.layout.insertWidget(self.channelList.layout.count() - 1, ch)
        
        # Update button states
        self._updateTrashButtonStates()
        
        # Update toolbar
        self._updateToolbar()

    def _clearAllChannels(self):
        """Remove all channel widgets from the layout."""
        # Remove all widgets except the stretch
        widgets_to_remove = []
        for i in range(self.channelList.layout.count()):
            item = self.channelList.layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'channelKey'):
                widgets_to_remove.append(item.widget())
        
        for widget in widgets_to_remove:
            self.channelList.layout.removeWidget(widget)
            widget.deleteLater()

    def _updateTrashButtonStates(self):
        """Enable/disable trash buttons and drag functionality based on number of channels."""
        channelCount = len(self._current_data)
        
        # Find all DraggableChannel widgets and update their states
        for i in range(self.channelList.layout.count()):
            item = self.channelList.layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'trashButton'):
                # Disable trash button if only one channel remains
                item.widget().trashButton.setEnabled(channelCount > 1)
                
                # Store drag state for reference (can be used for visual feedback)
                item.widget().setProperty("draggingEnabled", channelCount > 1)

    # pretty good style using findChild
    def _updateToolbar(self):
        """Update toolbar labels with current information."""
        channelCount = len(self._current_data)
        
        # Update count label
        # count_label = self.toolbar.findChild(QLabel, "count_label")
        # if count_label:
        #     count_label.setText(f"Channels: {channelCount}")
        
        # Update status label
        # status_label = self.toolbar.findChild(QLabel, "status_label")
        # if status_label:
        #     if channelCount == 0:
        #         status_label.setText("No channels")
        #     elif channelCount == 1:
        #         status_label.setText("1 channel")
        #     else:
        #         status_label.setText(f"{channelCount} channels")

    def onImportButtonClicked(self):
        """Handle Import File button click."""
        # from PyQt5.QtWidgets import QFileDialog
        # files, _ = QFileDialog.getOpenFileNames(
        #     self, 
        #     "Select Files to Import", 
        #     "", 
        #     "All Files (*.*)"
        # )
        # self.filesImported.emit(files)
        editChannelEvent = EditChannelEvent(
            eventType = pmmEventType.editChannel,
            mmWidget = self.getStackWidget(),
            editType = ChannelEditType.import_new_channel,
            # importPath = tifFile
        )
        self.emitEvent(editChannelEvent)
 
    def onImportButtonDragEnter(self, event):
        """Handle drag enter event on import button."""
        
        if event.mimeData().hasUrls():
            # Check if any of the dragged files have accepted extensions
            accepted_exts = acceptedExtensions()
            has_valid_file = False
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    _, ext = os.path.splitext(file_path)
                    if ext in accepted_exts:
                        has_valid_file = True
                        break
            
            if has_valid_file:
                event.acceptProposedAction()
                self.importButton.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: 2px dashed #1976D2;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                """)
            else:
                event.ignore()
        else:
            event.ignore()

    def onImportButtonDragMove(self, event):
        """Handle drag move event on import button."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def onImportButtonDrop(self, event):
        """Handle drop event on import button."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
            # Extract file paths from URLs
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    file_paths.append(file_path)
            
            if file_paths:
                # self.filesImported.emit(file_paths)
                print(f"Files dropped: {file_paths}")
            
                editChannelEvent = EditChannelEvent(
                    eventType = pmmEventType.editChannel,
                    mmWidget = self.getStackWidget(),
                    editType = ChannelEditType.import_new_channel,
                    importPath = file_paths[0] # just the first file
                )
                self.emitEvent(editChannelEvent)

            # Reset button style
            self.importButton.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)

def run():
    app = PyMapManagerApp(sys.argv)

    # channels_data = {
    #     1: {"label": "Channel 1 - Red", "color": "#FF0000"},
    #     2: {"label": "Channel 2 - Green", "color": "#00FF00"}, 
    # }
    import pandas as pd
    pd.options.mode.chained_assignment = None  # default='warn'

    from mapmanagercore.data import get202504_map
    path = get202504_map()

    path = '/Users/cudmore/Desktop/single_timepoint_20250415.mmap'

    path = '/Users/cudmore/Sites/MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'

    print(f'path:{path}')

    stackWidget = app.loadStackWidget(path)
    if stackWidget is None:
        logger.error('did not load path')    
    else:
        logger.info('creating ChannelEditor2')
        w = ChannelEditor2(stackWidget)      
        w.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
    