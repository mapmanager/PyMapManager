import pdb
import pytest

import mapmanagercore.data

from pymapmanager.interface import PyMapManagerApp
from pymapmanager.interface.stackWidgets import stackWidget
from pymapmanager.interface.stackWidgets.event.spineEvent import AddSpineEvent, EditSpinePropertyEvent, DeleteSpineEvent, MoveSpineEvent
from pymapmanager.interface.stackWidgets.event.annotationEvent import UndoEvent, RedoEvent 
from pymapmanager._logger import logger

# this makes qapp be our PyMapManagerApp, it is derived from QApplication
@pytest.fixture(scope="session")
def qapp_cls():
    return PyMapManagerApp

@pytest.fixture
def stackWidgetObject(qtbot, qapp):
	# path = '../PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
    path = mapmanagercore.data.getSingleTimepointMap()
    sw = qapp.loadStackWidget(path)
    return sw

def pytest_configure():
    pytest.addedSpineID = None

def test_Undos(stackWidgetObject, qapp):
    logger.info(f'----------- Start of test_Undos -----------')
    logger.info(f'{stackWidgetObject}')
    
    assert stackWidgetObject is not None
    assert isinstance(stackWidgetObject, stackWidget)

    # pytest.set_trace()  # Enter debugger here
    # zoom to point for visual testing
    # stackWidgetObject.zoomToPointAnnotation(75, isAlt=True)
    
    # Store old spine coordinates before moving
    spineID = 6

    oldX = stackWidgetObject.getStack().getPointAnnotations().getValue('x', spineID)
    oldY = stackWidgetObject.getStack().getPointAnnotations().getValue('y', spineID)
    oldZ = stackWidgetObject.getStack().getPointAnnotations().getValue('z', spineID)

    # Move spine
    x = 557
    y = 222
    z = 31

    moveEvent = MoveSpineEvent(stackWidgetObject, spineID=spineID, x=x, y=y, z=z)
    # stackWidgetObject.moveAnnotationEvent(moveEvent)
    # stackWidgetObject.emitEvent(moveEvent) # this does not work
    stackWidgetObject.slot_pmmEvent(moveEvent) 

    # verify new position of spine
    # temp = stackWidgetObject.getStack().getPointAnnotations().getValues(['x','y','z'], spineID)
    verifyX = stackWidgetObject.getStack().getPointAnnotations().getValue('x', spineID)
    verifyY = stackWidgetObject.getStack().getPointAnnotations().getValue('y', spineID)
    verifyZ = stackWidgetObject.getStack().getPointAnnotations().getValue('z', spineID)

    assert verifyX == x
    assert verifyY == y
    assert verifyZ == z

    # Undo Move spine
    # _undoEvent = UndoEvent(stackWidgetObject, None)
    logger.info(f'----------- Undo Move Spine -----------')
    stackWidgetObject.emitUndoEvent()

    # Verify old position of spine after undoing move
    verifyOldX = stackWidgetObject.getStack().getPointAnnotations().getValue('x', spineID)
    verifyOldY = stackWidgetObject.getStack().getPointAnnotations().getValue('y', spineID)
    verifyOldZ = stackWidgetObject.getStack().getPointAnnotations().getValue('z', spineID)

    assert verifyOldX == oldX
    assert verifyOldY == oldY
    assert verifyOldZ == oldZ


    logger.info(f'----------- Add Spine -----------')
    # Add Spine
    x = 600
    y = 230
    z = 30
    addEvent = AddSpineEvent(stackWidgetObject, x, y, z)
    stackWidgetObject.slot_pmmEvent(addEvent)

    # Get new Spine ID
    spineID = addEvent.getSpines()[0]
    pytest.addedSpineID = spineID
    logger.info(f"newly added spine {spineID}")

    # Verify AddSpine
    spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    assert spineExists is True

    # Undo Add spine
        # _undoEvent = UndoEvent(stackWidgetObject, None)
        # stackWidgetObject.slot_pmmEvent(_undoEvent)
    logger.info(f'----------- Undo Add Spine -----------')
    stackWidgetObject.emitUndoEvent()

    # Verify Undo Add Spine
    spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    assert spineExists is False

    # TODO: Go back and test delete, undo and move for known bug
    spineID = 2
    
    # Delete Spine 2
    logger.info(f'----------- Delete Spine 2-----------')
    deleteEvent = DeleteSpineEvent(stackWidgetObject, spineID=spineID)
    stackWidgetObject.slot_pmmEvent(deleteEvent)

    # Verify Delete
    spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    assert spineExists is False

    logger.info(f'----------- Undo Delete Spine -----------')
    # Undo delete spine
    stackWidgetObject.emitUndoEvent()

    df = stackWidgetObject.getStack().getPointAnnotations().getDataFrame()
    logger.info(f"END of Undo Test, df {df}")

    # Verify Undo Delete
    spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    assert spineExists is True

    # paLength = stackWidgetObject.getStack().getPointAnnotations().__len__()
    # df = stackWidgetObject.getStack().getPointAnnotations().getDataFrame()
    # logger.info(f"END of Undo Test, df {df}")

# @pytest.mark.skip(reason="not currently testing")
def test_Redos(stackWidgetObject, qapp):

    assert stackWidgetObject is not None
    assert isinstance(stackWidgetObject, stackWidget)

    # Redo previous delete on spine 2
    stackWidgetObject.emitRedoEvent()

    spineID = 2
    # Verify Delete
    spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    assert spineExists is False

    # paLength = stackWidgetObject.getStack().getPointAnnotations().__len__()
    # logger.info(f"After redo delete {paLength}")

    # Redo Add Spine
    # TODO: fix backend issue with redo add bug
    # Bug: occurs when there is two redos in a row with add being the last redo
    # stackWidgetObject.emitRedoEvent()

    # logger.info(f"After redo add {paLength}")

    # # Verify Add
    # spineID = pytest.addedSpineID
    # spineExists = stackWidgetObject.getStack().getPointAnnotations().spineID_Exists(spineID)
    # assert spineExists is False


