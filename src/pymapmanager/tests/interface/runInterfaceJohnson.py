"""Open a stack widget.
"""

import sys

# from qtpy import QtWidgets


from pymapmanager.interface.pyMapManagerApp import PyMapManagerApp
# from pymapmanager.interface import PyMapManagerApp
from pymapmanager.interface.stackWidgets.base.mmWidget2 import pmmEvent, pmmEventType
from pymapmanager.interface.stackWidgets.event.annotationEvent import UndoEvent
# abb 202504 removed
# from stackWidgets import stackWidget

from pymapmanager.interface.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                #    UndoSpineEvent,
                                                                   SelectSpine)

from pymapmanager._logger import logger

def _old_AddRandomColumns(df):
    import numpy as np  # remember, never do this in production code

    n = len(df)

    df['isBad'] = np.random.choice([True,False],size=n)
    print(df['isBad'])

    df['userType'] = np.random.randint(0, 10, size=n)


def run():
    app = PyMapManagerApp(sys.argv)

    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path ='\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\sandbox\\data\\rr30a_s0.mmap'
    # path = 'C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'
    # path = '\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'

    # abb turn off SettingWithCopyWarning
    import pandas as pd
    pd.options.mode.chained_assignment = None  # default='warn'

    # abb, macOS
    # you need to MANUALLY place this new mmap folder
    # on Windows and in python, will this kind of path work???
    # path = '../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'

    logger.error('abb Johnson needs to ensure this exists for 202504')
    logger.error(f"C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore-Data\\data\\202504\\single_timepoint_202504.mmap")

    # abb 202504, this is what you were loading
    path = 'C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore-Data\\data\\single_timepoint.mmap'
    
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u.mmap'


    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u_v3.mmap'
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/test2.mmap'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u.mmap'
    # import mapmanagercore

    # pooch path
    import mapmanagercore.data
    ## path = mapmanagercore.getSingleTimepointMap()
    # path = mapmanagercore.data.getSingleTimepointMap()

    print("path", path)
    sw2 = app.loadStackWidget(path)

    # from mapmanagercore.data import getSingleTimepointMap

    # path = getSingleTimepointMap()
    # print("path: ", path)
    # # sys.exit()
    # sw2 = app.loadStackWidget(path)

    
    # df = sw2.getStack().getPointAnnotations().getDataFrame()
    # df['userType'] = 1
    # sw2.getStack().getPointAnnotations().intializeIsBad()
    # sw2.getStack().getPointAnnotations().intializeUserType()
    # sw2.forceRefresh()
    # sw2.zoomToPointAnnotation(1, isAlt=True)

    sw2.zoomToPointAnnotation(5, isAlt=True)

    # sw2.runPlugin('Scatter Plot', inDock=False)
    
    # spineID = 75
    # deleteEvent = DeleteSpineEvent(sw2, spineID)
    # # deleteEvent = DeleteSpineEvent(sw2)
    # # deleteEvent.addDeleteSpine(spineID)
    # # sw2.deletedEvent(deleteEvent)
    # # sw2.emitEvent(deleteEvent, blockSlots=False)
    # sw2.slot_pmmEvent(deleteEvent)

    # undoEvent1 = deleteEvent
    # # Undo delete spine
    # undoDeleteEvent = UndoEvent(sw2, undoEvent1)
    # sw2.slot_pmmEvent(undoDeleteEvent)

    # _pmmEvent = pmmEvent(pmmEventType.delete, sw2)
    # _pmmEvent.setValue("pointSelection", [1])
    # sw2.emitEvent(_pmmEvent)
    # sw2.slot_pmmEvent(_pmmEvent)

    # sw2.deletedEvent()

    # sw2.runPlugin('Scatter Plot', inDock=True)

    sys.exit(app.exec_())

def runMultiTimepointMap():
    app = PyMapManagerApp(sys.argv)
    import mapmanagercore.data
    ## path = mapmanagercore.getSingleTimepointMap()
    path = mapmanagercore.data.get202504_map()

    print("path", path)
    sw2 = app.loadStackWidget(path)
    sys.exit(app.exec_())

def run_tif():
    app = PyMapManagerApp(sys.argv)
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.tif'
    path = 'C:/Users/johns/Documents/GitHub/MapManagerCore-Data/data/rr30a_s0u/t0/rr30a_s0_ch1.tif'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # # sw2 = app.loadTifFile(path)
    sw2 = app.loadStackWidget(path)
    sys.exit(app.exec_())


def run_2_tifs():
    app = PyMapManagerApp(sys.argv)
    path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.tif'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # # sw2 = app.loadTifFile(path)
    sw2 = app.loadStackWidget(path)


    path2 = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    sw2.loadInNewChannel(path2)

    # pluginID = sw2.runPlugin('Channel Editor', inDock=False)


    path3 = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    sw2.loadInNewChannel(path3)

    pluginID = sw2.runPlugin('Channel Editor', inDock=False)
 
    sys.exit(app.exec_())


def run3():
    app = PyMapManagerApp()
    path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u_newSpineAngle.mmap'

    sw2 = app.loadStackWidget(path)
    sw2.zoomToPointAnnotation(120, isAlt=True)
    sys.exit(app.exec_())

def run4():
    app = PyMapManagerApp()
    path = 'C:/Users/johns/Documents/TestMMCMaps/ManualSave/firstTest.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u_newSpineAngle.mmap'

    sw2 = app.loadStackWidget(path)
    sw2.zoomToPointAnnotation(120, isAlt=True)
    sys.exit(app.exec_())

def run5():
    app = PyMapManagerApp()
    path = 'C:/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u_newSpineAngle.mmap'

    sw2 = app.loadStackWidget(path)
    sw2.zoomToPointAnnotation(120, isAlt=True)
    sys.exit(app.exec_())

def runPoochFileDirectly():
    app = PyMapManagerApp()
    path = r'C:\Users\johns\AppData\Local\pooch\pooch\Cache\cc845595cddcc942c8f9d3d717ffede4-rr30a_s0u.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u_newSpineAngle.mmap'

    sw2 = app.loadStackWidget(path)
    sw2.zoomToPointAnnotation(120, isAlt=True)
    sys.exit(app.exec_())

def runFirstWindow():
    app = PyMapManagerApp(sys.argv)
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u_newSpineAngle.mmap'
    sys.exit(app.exec_())

def testingOpenClose():

    # run plugin
    app = PyMapManagerApp()
    # pooch path
    import mapmanagercore.data
    ## path = mapmanagercore.getSingleTimepointMap()
    path = mapmanagercore.data.getSingleTimepointMap()

    print("path", path)
    sw2 = app.loadStackWidget(path)
    # sw2.runPlugin('Spine Info', inDock=False)

    # sw2.closePlugin('Spine Info')
    # sw2.runPlugin('Spine Info', inDock=False)
    # sw2.closePlugin('Spine Info', inDock=False)
    # sw2.runPlugin('Spine Info', inDock=True)
    # sw2.closePlugin('Spine Info', inDock=True)
    # sw2.runPlugin('Histogram', inDock=True)

    # sw2.runPlugin('Spine Info', inDock=False)
    # sw2.closePlugin(('Spine Info', 1))

    # sw2.runPlugin('Spine Info', inDock=False)
    # sw2.runPlugin('Spine Info', inDock=False)

    sw2.runPlugin('Spine Info', inDock=True)
    sw2.closePluginInDock('Spine Info')

    sw2.runPlugin('Spine Info', inDock=True)

    sys.exit(app.exec_())

def testingProgrammaticRunClose():

    # run plugin
    app = PyMapManagerApp()
    # pooch path
    import mapmanagercore.data
    ## path = mapmanagercore.getSingleTimepointMap()
    path = mapmanagercore.data.getSingleTimepointMap()

    print("path", path)
    sw2 = app.loadStackWidget(path)
    sw2.zoomToPointAnnotation(120, isAlt=True)
    pluginID = sw2.runPlugin('Spine Info', inDock=False)
    sw2.closePlugin(pluginID)

    # pluginID2 = sw2.runPlugin('Spine Info', inDock=True)
    # print("reeeee, ", pluginID2)
    # sw2.closePlugin(pluginID2)


    # sw2.runPlugin('Spine Info', inDock=False)
    # sw2.closePlugin('Spine Info', inDock=False)
 
    # sw2.runPlugin('Histogram', inDock=True)

    sys.exit(app.exec_())

def runThenLoad():
    app = PyMapManagerApp(sys.argv)
    import mapmanagercore.data
    path = mapmanagercore.data.getSingleTimepointMap()
    sw2 = app.loadStackWidget(path)

    path2 = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    sw2.loadInNewChannel(path2)
    
    path3 = 'C:/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.tif'
    sw2.loadInNewChannel(path3)

        
    # path4 = 'C:/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    # sw2.loadInNewChannel(path4)

    pluginID = sw2.runPlugin('Channel Editor', inDock=False)
 
    sys.exit(app.exec_())

def testAddDeleteRedoSegments():
    app = PyMapManagerApp(sys.argv)
    import mapmanagercore.data
    path = mapmanagercore.data.getSingleTimepointMap()
    sw2 = app.loadStackWidget(path)

    # path2 = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    # sw2.loadInNewChannel(path2)

    # Check (Enable) Edit Segment
    # on_edit_segment_checkbox._on_segment_edit_checkbox(state=1)
    _lineListWidget = sw2._getNamedWidget("Segment List").widget()
    print("_lineListWidget", _lineListWidget)
    _lineListWidget.enableEditSegments()
    
    # Add new segment

    # Add points

    # Delete Segment (press delete key)

    # undo delete

    # redo delete

    # pluginID = sw2.runPlugin('Channel Editor', inDock=False)
 
    sys.exit(app.exec_())


def testingGetValues():
    app = PyMapManagerApp(sys.argv)
    import mapmanagercore.data
    path = mapmanagercore.data.getSingleTimepointMap()
    sw2 = app.loadStackWidget(path)

    spineID = 2
    test = sw2.getStack().getPointAnnotations().getValues(colName = ['x', 'y', 'z'],rowIdx = spineID)
    print("testGetValues: ", test)

if __name__ == '__main__':
    # run()
    # testingGetValues()

    # TODO: fix merging for just tif, only works for zarr
    run_tif()
    # run_2_tifs()

    # runThenLoad()
    # runMultiTimepointMap()
    # run2()
    # run3()
    # run4()
    # run5()
    # runFirstWindow()
    # testingOpenClose()
    # runPoochFileDirectly()
    # testingProgrammaticRunClose()
    # run2_tif()

    # testAddDeleteRedoSegments()