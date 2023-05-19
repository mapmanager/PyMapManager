import sys

from qtpy import QtCore, QtWidgets, QtGui

import pymapmanager
from pymapmanager._logger import logger

class segmentListWidget(QtWidgets.QWidget):
    """A (hypothetical) list of segments with an 'Edit Segments' checkbox
    """
    signalEditSegment = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()

        self.sm = None

        _vLayout = QtWidgets.QVBoxLayout()

        self._editSegmentCheckbox = QtWidgets.QCheckBox('Edit Segments')
        self._editSegmentCheckbox.stateChanged.connect(self._on_segment_edit_checkbox)
        _vLayout.addWidget(self._editSegmentCheckbox)

        self.setLayout(_vLayout)
        
    def _on_segment_edit_checkbox(self, state : int):
        state = state > 0
        logger.info(f'state: {state}')
        self.signalEditSegment.emit(state)

    def _installStateMachine(self, sm):
        self.sm = sm
        
        # set interface based on state
        self.sm.baseState.assignProperty(self._editSegmentCheckbox, "enabled", True)
        self.sm.selectSpine_state.assignProperty(self._editSegmentCheckbox, "enabled", False)
        self.sm.moveSpine_state.assignProperty(self._editSegmentCheckbox, "enabled", False)
        self.sm.manualConnectSpine_state.assignProperty(self._editSegmentCheckbox, "enabled", False)

        # Add state transitions in response to checkbox signal
        self.sm.baseState.addTransition(self.signalEditSegment, self.sm.editSegment_state)
        self.sm.editSegment_state.addTransition(self.signalEditSegment, self.sm.baseState)


class MainWindow(QtWidgets.QMainWindow):
    signalSelectSpine = QtCore.Signal()
    signalCancelSpineSelection = QtCore.Signal()
    signalMoveSpine = QtCore.Signal(bool)
    signalManualConnectSpine = QtCore.Signal(bool)

    def __init__(self):
        super().__init__()

        self._buildUI()

        self.setupStateMachine()  # creates self.sm
        
        # tmp place for this, I want to pass state machine
        self._segmentListWidget._installStateMachine(self)

        self.show()

    def _buildUI(self):
        self._myCentralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self._myCentralWidget)

        _hLayout = QtWidgets.QHBoxLayout()

        # first v layout
        _vLayout = QtWidgets.QVBoxLayout()

        self._currentStateLabel = QtWidgets.QLabel('none')
        _vLayout.addWidget(self._currentStateLabel)

        self._selectSpineButton = QtWidgets.QPushButton("select spine")
        self._selectSpineButton.pressed.connect(self._on_select_spine)
        _vLayout.addWidget(self._selectSpineButton)

        self._cancelSpineSelectionButton = QtWidgets.QPushButton("cancel spine selection")
        self._cancelSpineSelectionButton.pressed.connect(self._on_cancel_spineSelection)
        _vLayout.addWidget(self._cancelSpineSelectionButton)

        _hLayout.addLayout(_vLayout)

        # second v layout
        _vLayout2 = QtWidgets.QVBoxLayout()

        # a segment list widget (with edit segment button)
        self._segmentListWidget = segmentListWidget()
        _vLayout2.addWidget(self._segmentListWidget)

        self._moveSpineCheckbox = QtWidgets.QCheckBox('Move Spine')
        self._moveSpineCheckbox.stateChanged.connect(self._on_move_spine_checkbox)
        _vLayout2.addWidget(self._moveSpineCheckbox)

        self._manualConnectCheckbox = QtWidgets.QCheckBox('Manual Connect Spine')
        self._manualConnectCheckbox.stateChanged.connect(self._on_manual_connect_spine_checkbox)
        _vLayout2.addWidget(self._manualConnectCheckbox)

        self._quitButton = QtWidgets.QPushButton('Quit')
        _vLayout2.addWidget(self._quitButton)

        _hLayout.addLayout(_vLayout2)

        # finalize
        self._myCentralWidget.setLayout(_hLayout)

    def _on_select_spine(self):
        logger.info("-->> emit signalSelectSpine")
        self.signalSelectSpine.emit()

    def _on_cancel_spineSelection(self):
        logger.info("-->> emit signalCancelSpineSelection")
        self.signalCancelSpineSelection.emit()

    def _on_move_spine_checkbox(self, state : int):
        state = state > 0
        logger.info(f'_on_move_spine_checkbox: {state}')
        self.signalMoveSpine.emit(state)

    def _on_manual_connect_spine_checkbox(self, state : int):
        state = state > 0
        logger.info(f'_on_manual_connect_spine_checkbox: {state}')
        self.signalManualConnectSpine.emit(state)


    def setupStateMachine(self):

        self.sm = QtCore.QStateMachine()

        self.parentState = QtCore.QState()

        # by constructing QState with a parent, the parent takes ownership
        # no need to have self.baseState, etc (but we need them in segmentListWidget)

        # base state
        self.baseState = QtCore.QState(self.parentState)
        self.baseState.assignProperty(self._currentStateLabel, "text", "In state baseState");
        self.baseState.assignProperty(self._selectSpineButton, "enabled", True)
        self.baseState.assignProperty(self._cancelSpineSelectionButton, "enabled", False)
        self.baseState.assignProperty(self._moveSpineCheckbox, "enabled", False)
        self.baseState.assignProperty(self._manualConnectCheckbox, "enabled", False)
        # self.sm.addState(self.baseState)

        # select spine state
        self.selectSpine_state = QtCore.QState(self.parentState)
        self.selectSpine_state.assignProperty(self._currentStateLabel, "text", "In state selectSpine_state");
        self.selectSpine_state.assignProperty(self._selectSpineButton, "enabled", False)
        self.selectSpine_state.assignProperty(self._cancelSpineSelectionButton, "enabled", True)
        self.selectSpine_state.assignProperty(self._moveSpineCheckbox, "enabled", True)
        self.selectSpine_state.assignProperty(self._manualConnectCheckbox, "enabled", True)
        # self.sm.addState(self.selectSpine_state)

        # edit segment state
        self.editSegment_state = QtCore.QState(self.parentState)
        self.editSegment_state.assignProperty(self._currentStateLabel, "text", "In state editSegment_state");
        self.editSegment_state.assignProperty(self._selectSpineButton, "enabled", False)
        self.editSegment_state.assignProperty(self._cancelSpineSelectionButton, "enabled", False)
        self.editSegment_state.assignProperty(self._moveSpineCheckbox, "enabled", False)
        self.editSegment_state.assignProperty(self._manualConnectCheckbox, "enabled", False)
        # self.sm.addState(self.editSegment_state)
        
        # move spine state
        self.moveSpine_state = QtCore.QState(self.parentState)
        self.moveSpine_state.assignProperty(self._currentStateLabel, "text", "In state moveSpine_state");
        self.moveSpine_state.assignProperty(self._selectSpineButton, "enabled", False)
        self.moveSpine_state.assignProperty(self._cancelSpineSelectionButton, "enabled", False)
        self.moveSpine_state.assignProperty(self._manualConnectCheckbox, "enabled", False)
        # self.sm.addState(self.moveSpine_state)

        # manually connect spine state
        self.manualConnectSpine_state = QtCore.QState(self.parentState)
        self.manualConnectSpine_state.assignProperty(self._currentStateLabel, "text", "In state manualConnectSpine_state");
        self.manualConnectSpine_state.assignProperty(self._selectSpineButton, "enabled", False)
        self.manualConnectSpine_state.assignProperty(self._cancelSpineSelectionButton, "enabled", False)
        self.manualConnectSpine_state.assignProperty(self._moveSpineCheckbox, "enabled", False)
        # self.sm.addState(self.manualConnectSpine_state)

        self.parentState.setInitialState(self.baseState)
        self.sm.addState(self.parentState)

        
        _finalState = QtCore.QFinalState()
        #_finalState.assignProperty(self._currentStateLabel, "text", "In state _finalState THE USER QUIT");
        self.sm.addState(_finalState)

        self.parentState.addTransition(self._quitButton.clicked, _finalState)

        # a child state could over-ride this so quit button would be ignored
        # would be better for that state to just disable the quit button
        self.manualConnectSpine_state.addTransition(self._quitButton.clicked, self.manualConnectSpine_state)

        self.sm.setInitialState(self.parentState)

        # connect quit
        self.sm.finished.connect(self._quit)

        #
        # state transitions
        #

        # 1) change states when a QWidget emits a signal
        #self.baseState.addTransition(self._selectSpineButton.pressed, self.selectSpine_state);
        # 2) change states on a custom signal
        self.baseState.addTransition(self.signalSelectSpine, self.selectSpine_state)
        # v2
        # self.baseState.addTransition(self.signalEditSegment, self.editSegment_state)
        
        self.selectSpine_state.addTransition(self.signalCancelSpineSelection, self.baseState)
        
        # TODO: how do we encode True/False for this ??? Maybe not neccessary?
        # in Qt documentation, this is a `guarded transition`.
        # move spine
        self.selectSpine_state.addTransition(self.signalMoveSpine, self.moveSpine_state)
        self.moveSpine_state.addTransition(self.signalMoveSpine, self.selectSpine_state)

        # manual connect
        self.selectSpine_state.addTransition(self.signalManualConnectSpine, self.manualConnectSpine_state)
        self.manualConnectSpine_state.addTransition(self.signalManualConnectSpine, self.selectSpine_state)

        #self.sm.setInitialState(self.baseState)
        
        self.sm.start()

    def _quit(self):
        """
        Need a way to transition back to previous state if user does not quit.
        
        print('user quit, show dialog to ask if they want to quit and then on ok, quit')
        """

        from qtpy.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to cquit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.close()
        else:
            pass
    
def run():
    app = QtWidgets.QApplication(sys.argv)
    
    smw = MainWindow()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()