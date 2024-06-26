import pytest

from qtpy import QtGui, QtWidgets  # QtCore

class myApp(QtWidgets.QApplication):
    def __init__(self, argv=[], deferFirstWindow=False):        
        super().__init__(argv)

@pytest.fixture(scope="session")
def qapp_cls():
    return myApp

def test_app(qtbot, qapp):
    print(f'qapp is:{qapp}')
