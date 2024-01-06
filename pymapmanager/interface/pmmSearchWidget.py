from pymapmanager.interface.searchWidget2 import SearchController
from pymapmanager.interface.pmmWidget import PmmWidget
import pymapmanager
from pymapmanager._logger import logger

class PmmSearchWidget(PmmWidget):
    """
    """
    # signalSelectAnnotation2 = signal.
    def __init__(self, stack: pymapmanager.stack):
        super().__init__()
        self.stack = stack
        df = self.stack.getPointAnnotations().getDataFrame()
        self.mySeachWidget = SearchController(df)
        self.mySeachWidget.signalAnnotationSelection2.connect(self.slot_convertToAnnotationEvent)
        # self._blockSlots = False
        
    # TODO: hide PmmWidget in PmmSearchWidget
    # only show mySearchWidget
    def show(self):
        """
            Override show function
        """
        # Hides both pmmWidget and SearchWidget
        self.hide()
        # Only show SearchWidget
        self.mySeachWidget.show()

    def getDF(self):
        """
            Get the current point annotation dataframe
        """
        df = self.stack.getPointAnnotations().getDataFrame()
        return df

    # def slot_selectAnnotation2(self, selectionEvent):
    #     logger.info(f"pmmSearchWidget slot_selectAnnotation2")

    #     # Check for pa selection event
    #     if selectionEvent.isPointSelection:
    #         super().slot_selectAnnotation2(selectionEvent)

    def selectAction(self):        
        """ Updates selection within QTableView
        """
        # logger.info(f"searchWidget2 Select Action")
        selectionEvent = super().selectAction()
        # logger.info(f"selection event type {selectionEvent.type}") 
        # Ensure that it is a point selection and not line
        if selectionEvent.isPointSelection():
            rowIdxList = selectionEvent.getRows()
            logger.info(f"rowIdxList: {rowIdxList}")
            if len(rowIdxList) > 0:
                rowIdx = rowIdxList[0]
                self.mySeachWidget.selectRowInView(rowIdx)

    def slot_deletedRow(self, selectionEvent):
        """
            Update searchwidget on delete
        """
        # df = selectionEvent.getDF()
        df = self.getDF()
        self.mySeachWidget._deletedRow(df)

    def slot_addedRow(self, selectionEvent):
        """
            Update searchwidget on add
        """
        # df = selectionEvent.getDF()
        df = self.getDF()
        self.mySeachWidget._addedRow(df)

    def slot_updatedRow(self, selectionEvent):
        """
            Update searchwidget when a row's column(s) change
        """
        selectionIdx = selectionEvent.getRows()[0]
        logger.info(f"selectionIdx: {selectionIdx}")
        df = self.getDF()
        self.mySeachWidget._updatedRow(df, selectionIdx)

        # TODO: change Short fix
        # self.slot_convertToAnnotationEvent(selectionIdx, isAlt = False)
        # self.mySeachWidget.selectRowInView(selectionIdx)

    def slot_convertToAnnotationEvent(self, proxyRowIdx, isAlt):
        """ 
            Convert selected annotation to an event to be used in the rest of pymapmanager widgets
        """
        logger.info(f"slot_convertToAnnotationEvent")
        pa = self.stack.getPointAnnotations()
        _selectionEvent = pymapmanager.annotations.SelectionEvent(annotation=pa,
                                                        rowIdx=proxyRowIdx,
                                                        stack=self.stack,
                                                        isAlt=isAlt)
        # self.signalSelectAnnotation2.emit(_selectionEvent)

        # if _selectionEvent.type == pymapmanager.annotations.pointAnnotations:
        # Call Stack Widget function that signals other widgets
        # self.slot_selectAnnotation2(_selectionEvent)
        self.signalAnnotationSelection2.emit(_selectionEvent)
