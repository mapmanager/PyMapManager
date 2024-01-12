import sys

import pymapmanager.mmMap

import pymapmanager.interface
from pymapmanager._logger import logger

def run():
    
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    # loading from an incomplete map (missing int analysis for rois)
    # path = '..//PyMapManager-Data/maps/rr30a/rr30a_s1_ch2.tif'
    # path = '..//PyMapManager-Data/maps/rr30a/rr30a_s2_ch2.tif'
    #path = '..//PyMapManager-Data/maps/rr30a/rr30a_s3_ch2.tif'
    
    # load one stack
    stack = pymapmanager.stack(path=path, loadImageData=True)
    # pa = stack.getPointAnnotations()
    logger.info(f'myStack: {stack}')

    # Create UUID
    # pa.createUUID()
    # stack.getPointAnnotations().createUUID()
    stack.createPaUUID()

    # create the main application
    app = pymapmanager.interface.PyMapManagerApp()
    
    # create a stack widget
    bsw = pymapmanager.interface.stackWidget(stack=stack)
    bsw.toggleView(state=False, name = "Selection Info")
    bsw.show()
    
    # posRect = [100, 200, 800, 500]
    # bsw = app.openStack(path=path, posRect=posRect)

    # snap to an image
    #bsw._imagePlotWidget.slot_setSlice(30)
    
    # Show scatter plot window 2
    # bsw.showScatterPlot2(state = True)

    # Show search widget
    # bsw.showSearchWidget2(state = True)
        
    # select a point and zoom
    bsw.zoomToPointAnnotation(99, isAlt=True, select=True)

    # Select segment
    # Create new point

    # run the Qt event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
