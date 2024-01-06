from pymapmanager.interface.scatterPlotWindow2 import ScatterPlotWindow2
from pymapmanager.interface.pmmWidget import PmmWidget
import pymapmanager
from pymapmanager._logger import logger

class PmmScatterPlotWidget(PmmWidget):
    """
        PMM Wrapper class for scatter plot window
    """
    def __init__(self, stack: pymapmanager.stack):
        super().__init__()
        self.stack = stack
        df = self.stack.getPointAnnotations().getDataFrame()
        filterColumn = "roiType"
        hueColumn = "segmentID"
        self.myScatterPlotWindow = ScatterPlotWindow2(df, filterColumn, hueColumn)
        self.myScatterPlotWindow.signalAnnotationSelection2.connect(self.slot_convertToAnnotationEvent)

    def show(self):
        """
            Override show function
        """
        # Hides both pmmWidget and SearchWidget
        self.hide()
        # Only show SearchWidget
        self.myScatterPlotWindow.show()

    def slot_deletedRow(self, selectionEvent):
        """
            Update searchwidget on delete
        """
        # df = selectionEvent.getDF()
        df = self.getDF()
        self.myScatterPlotWindow._deletedRow(df)

    def slot_addedRow(self, selectionEvent):
        """
            Update searchwidget on add
        """
        # df = selectionEvent.getDF()
        df = self.getDF()
        self.myScatterPlotWindow._addedRow(df)

    def slot_updatedRow(self, selectionEvent):
        """
            Update searchwidget when a row's column(s) change
        """
        selectionIdx = selectionEvent.getRows()[0]
        # logger.info(f"selectionIdx: {selectionIdx}")
        df = self.getDF()
        self.myScatterPlotWindow._updatedRow(df)

    def selectAction(self):        
        """ Updates selection
        """
        # logger.info(f"searchWidget2 Select Action")
        selectionEvent = super().selectAction()

        if selectionEvent.isPointSelection():
            rowIdxList = selectionEvent.getRows()
            logger.info(f"rowIdxList: {rowIdxList}")
            # if len(rowIdxList) > 0:
                # rowIdx = rowIdxList[0]
            self.myScatterPlotWindow.selectHighlighterPoints(rowIdxList)


    def slot_convertToAnnotationEvent(self, proxyRowIdx):
        """ 
            Convert selected annotation to an event to be used in the rest of pymapmanager widgets
        """
        logger.info(f"slot_convertToAnnotationEvent")
        pa = self.stack.getPointAnnotations()
        _selectionEvent = pymapmanager.annotations.SelectionEvent(annotation=pa,
                                                        rowIdx=proxyRowIdx,
                                                        stack=self.stack,
                                                        )
        
        self.signalAnnotationSelection2.emit(_selectionEvent)

    
