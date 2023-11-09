import pymapmanager as pymapmanager
import pymapmanager.interface
import pandas as pd
import pytest
from PyQt5 import QtCore

from pytestqt.qtbot import QtBot # NOTE: needed to install pytestqt
from pymapmanager._logger import logger


def makeDF():
    df = pd.DataFrame()
    df["A"] = [10,20,30]
    df["B"] = [11,22,33]
    df["C"] = [111,222,334]
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
    def __init__(self):

        self.rowIdx = None

    def setSignalValues(self, rowIdx):
        logger.info(f'setting rowIdx: {rowIdx}')
        self.rowIdx = rowIdx

    def getSignalValues(self):
        return self.rowIdx

def test_signals(scatterPlotWidget):    
    """
        testing to ensure that scatter plot receives and uses df value correctly
    """
    # logger.info(f'')
    rowIdxList = [0]

    # Select Point
    scatterPlotWidget.selectHighlighterPoints(rowIdxList)

    # Get Values within Highlighter
    xVals, yVals =scatterPlotWidget.getHighlighter().get_xyVal()
    assert xVals == [10]
    assert yVals == [111]
    logger.info(f'xyVals: {scatterPlotWidget.getHighlighter().get_xyVal()}')

    # Get index from Signal sent out of highlighter
    # scatterPlotWidget.selectPointsFromHighlighter()
    sigVal = signalValues()
    scatterPlotWidget.signalAnnotationSelection2.connect(sigVal.setSignalValues)

    # need to manually select points
    rowIndexes = sigVal.getSignalValues()
    logger.info(f'rowIndex: {rowIndexes}')
    assert rowIndexes == [0]

# use pytest -s to show print/logging output

if __name__ == '__main__':
    # test_searchWidget()
    logger.info(f'test_scatterPlotWindow finished !!!')