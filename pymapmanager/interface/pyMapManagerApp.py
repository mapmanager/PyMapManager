import os

from qtpy import QtGui, QtCore, QtWidgets

import qdarktheme

# Enable HiDPI.
qdarktheme.enable_hi_dpi()

from pymapmanager._logger import logger
from pymapmanager.pmmUtils import getBundledDir

class PyMapManagerApp(QtWidgets.QApplication):
    def __init__(self, argv=['']):
        super().__init__(argv)

        qdarktheme.setup_theme()

        appIconPath = os.path.join(getBundledDir(), 'interface', 'icons', 'mapmanager-icon.png')
        logger.info(f'appIconPath:{appIconPath}')
        self.setWindowIcon(QtGui.QIcon(appIconPath))


        logger.info(f'Caller must run the event loop with "sys.exit(app.exec_())"')