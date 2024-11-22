"""Open a stack widget.
"""

import sys

# from qtpy import QtWidgets

from pymapmanager.interface2 import PyMapManagerApp
from pymapmanager.interface2.stackWidgets.base.mmWidget2 import pmmEvent, pmmEventType
from stackWidgets import stackWidget2

from pymapmanager.interface2.stackWidgets.event.spineEvent import (AddSpineEvent,
                                                                   DeleteSpineEvent,
                                                                   MoveSpineEvent,
                                                                   UndoSpineEvent,
                                                                   SelectSpine)

def _old_AddRandomColumns(df):
    import numpy as np  # remember, never do this in production code

    n = len(df)

    df['isBad'] = np.random.choice([True,False],size=n)
    print(df['isBad'])

    df['userType'] = np.random.randint(0, 10, size=n)


def run():
    app = PyMapManagerApp()

    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path = '../PyMapManager-Data/core-map/one-timepoint/oneTimepoint.mmap'
    # path ='\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\sandbox\\data\\rr30a_s0.mmap'
    # path = 'C:\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'
    path = '\\Users\\johns\\Documents\\GitHub\\MapManagerCore\\data\\rr30a_s0u.mmap'
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u.mmap'


    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/rr30a_s0u_v3.mmap'
    # path = '/Users/johns/Documents/GitHub/MapManagerCore/data/test2.mmap'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # path = 'C:/Users/johns/Documents/TestMMCMaps/rr30a_s0u.mmap'
    # import mapmanagercore

    # pooch path
    import mapmanagercore.data
    ## path = mapmanagercore.getSingleTimepointMap()
    path = mapmanagercore.data.getSingleTimepointMap()

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

    sw2.zoomToPointAnnotation(1, isAlt=True)
    spineID = 1
    deleteEvent = DeleteSpineEvent(sw2, spineID)
    # deleteEvent = DeleteSpineEvent(sw2)
    # deleteEvent.addDeleteSpine(spineID)
    # sw2.deletedEvent(deleteEvent)
    # sw2.emitEvent(deleteEvent, blockSlots=False)
    sw2.slot_pmmEvent(deleteEvent)


    # _pmmEvent = pmmEvent(pmmEventType.delete, sw2)
    # _pmmEvent.setValue("pointSelection", [1])
    # sw2.emitEvent(_pmmEvent)
    # sw2.slot_pmmEvent(_pmmEvent)

    # sw2.deletedEvent()

    # sw2.runPlugin('Scatter Plot', inDock=True)

    sys.exit(app.exec_())

def run2_tif():
    app = PyMapManagerApp()
    path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.tif'
    # path = '/Users/johns/Documents/GitHub/PyMapManager-Data/one-timepoint/rr30a_s0_ch1.mmap'
    # # sw2 = app.loadTifFile(path)
    sw2 = app.loadStackWidget(path)
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
    app = PyMapManagerApp()
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

if __name__ == '__main__':
    run()
    # run2()
    # run3()
    # run4()
    # run5()
    # runFirstWindow()
    # testingOpenClose()
    # runPoochFileDirectly()
    # testingProgrammaticRunClose()
    # run2_tif()