import pandas as pd
import pytest
from PyQt5 import QtCore
from pytestqt.qtbot import QtBot # NOTE: needed to install pytestqt

import pymapmanager as pymapmanager
import pymapmanager.interface2
from pymapmanager._logger import logger
import pymapmanager.interface2.stackWidgets

def makeDF():
    df = pd.DataFrame()
    df["A"] = [10,20,30]
    df["B"] = [11,22,33]
    df["C"] = [111,222,334]
    return df

@pytest.fixture
def searchWidget(qtbot):
    df = makeDF()
    sc = pymapmanager.interface2.stackWidgets.SearchWidget(df = df)
    qtbot.addWidget(sc)
    return sc

def getProxy(searchWidget):
    myTableView = searchWidget.getMyQTableView()
    proxyModel = myTableView.getProxyModel()
    return proxyModel

def test_SmallerComparison(searchWidget):
    """
        proxyModel = myQSortFilterProxyModel
    """
    proxyModel = getProxy(searchWidget)

    proxyModel.slot_setComparisonValue("5")

    # Comparison: 10 > 5
    proxyModel.slot_setComparisonSymbol(">")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    logger.info(f'a: {a}')
    assert a == True

    # Comparison 10 < 5
    proxyModel.slot_setComparisonSymbol("<")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False

    # Comparison 10 <= 5
    proxyModel.slot_setComparisonSymbol("<=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False

    # Comparison 10 >= 5
    proxyModel.slot_setComparisonSymbol(">=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True    
    
    # Comparison 10 == 5
    proxyModel.slot_setComparisonSymbol("=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False    

    proxyModel.slot_setComparisonSymbol("None")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True  


def test_LargerComparison(searchWidget):
    """
        proxyModel = myQSortFilterProxyModel
    """
    proxyModel = getProxy(searchWidget)
    proxyModel.slot_setComparisonValue("20")

    # Comparison: 10 > 20
    proxyModel.slot_setComparisonSymbol(">")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    # logger.info(f'a: {a}')
    assert a == False

    # Comparison 10 < 20
    proxyModel.slot_setComparisonSymbol("<")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True

    # Comparison 10 <= 20
    proxyModel.slot_setComparisonSymbol("<=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True

    # Comparison 10 >= 20
    proxyModel.slot_setComparisonSymbol(">=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False    
    
    # Comparison 10 == 20
    proxyModel.slot_setComparisonSymbol("=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False    

    proxyModel.slot_setComparisonSymbol("None")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True  


def test_EqualComparison(searchWidget):
    """
        proxyModel = myQSortFilterProxyModel
    """
    proxyModel = getProxy(searchWidget)
    proxyModel.slot_setComparisonValue("10")

    # Comparison: 10 > 10
    proxyModel.slot_setComparisonSymbol(">")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    # logger.info(f'a: {a}')
    assert a == False

    # Comparison 10 < 10
    proxyModel.slot_setComparisonSymbol("<")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == False

    # Comparison 10 <= 10
    proxyModel.slot_setComparisonSymbol("<=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True

    # Comparison 10 >= 10
    proxyModel.slot_setComparisonSymbol(">=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True    
    
    # Comparison 10 == 10
    proxyModel.slot_setComparisonSymbol("=")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True  

    proxyModel.slot_setComparisonSymbol("None")
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex()) # args: row, PARENT
    assert a == True  

def test_EdgeCases(searchWidget):

    proxyModel = getProxy(searchWidget)
    # proxyModel.slot_setComparisonValue("10")

    # No Comparison Value set -> Should automatically NOT filter Row
    a = proxyModel.filterAcceptsRow(0, QtCore.QModelIndex())
    assert a == True  

    # Pattern but no comparison filter


# def test_searchWidget(qtbot):

#     df = makeDF()
#     sc = pymapmanager.interface.SearchController(df = df)
#     qtbot.addWidget(sc)

#     myTableView = sc.getMyQTableView()
#     proxyModel = myTableView.getProxyModel()


if __name__ == '__main__':
    # test_searchWidget()
    logger.info(f'test_searchWidget finished !!!')