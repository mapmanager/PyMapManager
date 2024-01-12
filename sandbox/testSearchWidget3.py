import sys

import pymapmanager.mmMap

import pymapmanager.interface
from pymapmanager._logger import logger

def run():
    
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    
    # load one stack
    stack = pymapmanager.stack(path=path, loadImageData=True)
    logger.info(f'myStack: {stack}')

    stack.createPaUUID()
    # creat the main application
    app = pymapmanager.interface.PyMapManagerApp()

    # create a stack widget
    bsw = pymapmanager.interface.stackWidget(stack=stack)
    bsw.toggleView(state=False, name = "Selection Info")
    bsw.show()

    # select a point and zoom
    bsw.zoomToPointAnnotation(99, isAlt=True, select=True)

    # run the Qt event loop
    sys.exit(app.exec_())

def newClass():
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    
    # load one stack
    stack = pymapmanager.stack(path=path, loadImageData=True)
    logger.info(f'myStack: {stack}')

    stack.createPaUUID()

    pa = stack.getPointAnnotations()
    paDf = pa.getDataFrame()

    logger.info(f"paDF: {paDf}")
    # run 


if __name__ == '__main__':
    run()
    # newClass()
