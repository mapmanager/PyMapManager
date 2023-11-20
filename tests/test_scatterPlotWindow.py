import pymapmanager as pymapmanager
import pymapmanager.interface
import pandas as pd
import pytest
from PyQt5 import QtCore

from pytestqt.qtbot import QtBot # NOTE: needed to install pytestqt
from pymapmanager._logger import logger


def makeDF():
    df = pd.DataFrame()
    df["A"] = [10,20,30] # Currently this is selected as 1st column being analyzed
    df["B"] = [11,22,33]
    df["C"] = [111,222,333] # Currently this is selected as 2nd column being analyzed
    return df

@pytest.fixture
def scatterPlotWidget(qtbot):
    df = makeDF()
    sPW = pymapmanager.interface.ScatterPlotWindow2(inputtedDF = df, filterColumn=None, hueColumn=None)
    qtbot.addWidget(sPW)
    return sPW

# TODO: Check changing xy stats

# def test_signalSentOut(scatterPlotWidget):
#     """
#         testing to ensure that scatter plot Widget sends out correct (usable) values
#     """

#     # Programmatically select item in highlighted

#     scatterPlotWidget.selectPointsFromHighlighter()

class signalValues:

    signalAnnotationSelection2 = QtCore.Signal(object) 

    def __init__(self):

        self.rowIdx = None

    def setSignalValues(self, rowIdx):
        logger.info(f'setting rowIdx: {rowIdx}')
        self.rowIdx = rowIdx

    def getSignalValues(self):
        return self.rowIdx

# def setSignalValues(signalValues, rowIdx):
#     signalValues.setSignalValues(rowIdx)

# def setSignalValues(rowIdx):
#     logger.info(f'rowIdx: {rowIdx}')

def test_signals(scatterPlotWidget):    
    """
        testing to ensure that scatter plot receives and uses df value correctly
    """
    # logger.info(f'')
    rowIdxList = [0]
    
    # sigVal = signalValues()
    # scatterPlotWidget.signalAnnotationSelection2.connect(sigVal.setSignalValues)
    # scatterPlotWidget.signalAnnotationSelection2.connect(setSignalValues)

    # Select Point
    scatterPlotWidget.selectHighlighterPoints(rowIdxList)

    # Get Values within Highlighter
    xVals, yVals = scatterPlotWidget.getHighlighter().get_xyVal()
    logger.info(f'xyVals: {scatterPlotWidget.getHighlighter().get_xyVal()}')
    assert xVals == [10]
    assert yVals == [111]

    # Selecting multiple points
    rowIdxList = [0,1,2]
    scatterPlotWidget.selectHighlighterPoints(rowIdxList)
    xVals, yVals = scatterPlotWidget.getHighlighter().get_xyVal()
    logger.info(f'xyVals: {scatterPlotWidget.getHighlighter().get_xyVal()}')
    assert xVals == [10, 20, 30]
    assert yVals == [111, 222, 333]

    # Get index from Signal sent out of highlighter
    # scatterPlotWidget.selectPointsFromHighlighter()
    sigVal = signalValues()
    scatterPlotWidget.signalAnnotationSelection2.connect(sigVal.setSignalValues)
    # scatterPlotWidget.signalAnnotationSelection2.connect(setSignalValues)

    from unittest.mock import Mock

    event = Mock()

    # Test Single Spine Selection
    event.ind = [0] # select index 
    event.mouseevent.button = 1 # Make it a left click mouse event

    scatterPlotWidget.getHighlighter()._on_spine_pick_event3(event)

    rowIndexes = sigVal.getSignalValues()
    logger.info(f'rowIndex: {rowIndexes}')
    assert rowIndexes == [0]

    # Multiple Spines Selected
    runningIndex = []
    event.ind = [1] # select index S
    event.mouseevent.button = 1 # Make it a left click mouse event
    scatterPlotWidget.getHighlighter()._on_spine_pick_event3(event)
    rowIndexes = sigVal.getSignalValues()
    logger.info(f'rowIndexes: {rowIndexes}')
    runningIndex.append(rowIndexes[0])

    event.ind = [2] # select index S
    event.mouseevent.button = 1 # Make it a left click mouse event
    scatterPlotWidget.getHighlighter()._on_spine_pick_event3(event)
    rowIndexes = sigVal.getSignalValues()
    logger.info(f'rowIndexes: {rowIndexes}')
    runningIndex.append(rowIndexes[0])

    logger.info(f'multiple rowIndexes: {runningIndex}')
    assert runningIndex == [1,2]

    # Test Escape

    # Test Single select then drag Highlight

    # Test Drag Highlight then single select
    


# use pytest -s to show print/logging output

if __name__ == '__main__':
    # test_searchWidget()
    logger.info(f'test_scatterPlotWindow finished !!!')