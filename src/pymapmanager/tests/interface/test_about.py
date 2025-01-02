import pytest

from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

# @pytest.fixture
def test_about_dialog(qtbot, qapp):
    logger.info('')
    dlg = qapp._onAboutMenuAction()
    dlg.close()
    
# @pytest.fixture
def test_log_dialog(qtbot, qapp):
    logger.info('')
    dlg = qapp.openLogWindow()
    dlg.close()

