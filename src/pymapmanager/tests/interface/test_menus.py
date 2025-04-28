import pytest

from qtpy import QtWidgets, QtCore

from mapmanagercore.data import getTiffChannel_1
from pymapmanager.interface import PyMapManagerApp
from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

def _get_all_actions(menu):
    """Recursevly get all action in a menu and its submenus.
    """
    actions = []
    for action in menu.actions():
        # logger.error(f'action:{action}')
        if isinstance(action, QtWidgets.QAction) and action.isSeparator():
            continue
        actions.append(action)
        # if isinstance(action, QtWidgets.QMenu):
        if action.menu():
            # menuTitle = action.menu().title()
            # logger.info(f'  recurse on menuTitle:{menuTitle}')
            actions.extend(_get_all_actions(action.menu()))
    return actions

def test_menu_action(qtbot, qapp):
    """Go through all menus, find all nested actions and call action->trigger()
    """
    # this function is calling menu to set log level !!!
    logger.setLevel('INFO')
    
    # need to open stack widget, app has no menus
    mmapPath = getTiffChannel_1()
    stackWidgetWindow = qapp.loadStackWidget(mmapPath)

    # menu_bar = stackWidgetWindow.menuBar()
    mainMenus = stackWidgetWindow._mainMenu

    for name, menu in mainMenus._menuDict.items():
        menuTitle = menu.title()
        logger.info(f'=== Testing action name:{name} menuTitle:{menuTitle}')

        menu.aboutToShow.emit()
        
        if name == 'Plugins':
            logger.info(f'skipping "Plugins"')
            continue
        
        actions = _get_all_actions(menu)

        # logger.info(f'found {len(actions)} actions')
        for action in actions:
            _actionText = action.text()
            logger.info(f'  trigger menuTitle:{menuTitle} _actionText:"{_actionText}"')
            if _actionText in ['Tiff File Ch1',
                               'Tiff File Ch2',
                               'mmap with spines and segments'
                               ]:
                continue

            if not action.isEnabled():
                logger.info(f'    -->> _actionText:{_actionText} is not enabled')
            else:
                action.trigger()
