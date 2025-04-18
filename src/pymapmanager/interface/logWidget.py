from qtpy import QtWidgets

from pymapmanager._logger import logger, getLoggerFilePath

class PyMapManagerLog(QtWidgets.QMainWindow):
    """Plugin to display sanpy.log
    """

    def __init__(self):
        """
        Args:
            ba (bAnalysis): Not required
        """
        super().__init__(None)

        # layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QPlainTextEdit()
        widget.setReadOnly(True)
        # layout.addWidget(widget)

        # load sanpy.log
        logFilePath = getLoggerFilePath()
        logger.info(f'opening log file {logFilePath}')
        with open(logFilePath, "r") as f:
            lines = f.readlines()
        text = ""
        for line in lines:
            text += line  # line already has CR

        # add text to widget
        widget.document().setPlainText(text)

        # logger.info(f"logFilePath: {logFilePath}")

        self.setWindowTitle('MapManager Log')

        # self.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()
