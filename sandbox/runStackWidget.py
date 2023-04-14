import sys

import pymapmanager.interface
from pymapmanager._logger import logger

def run():
    
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pymapmanager.stack(path=path, loadImageData=True)
    logger.info(f'myStack: {myStack}')
    
    # creat the main application
    app = pymapmanager.interface.PyMapManagerApp()
    
    # create a stack widget
    bsw = pymapmanager.interface.stackWidget(myStack=myStack)

    # snap to an image
    #bsw._imagePlotWidget.slot_setSlice(30)
    
    # select a point and zoom
    bsw.zoomToPointAnnotation(10, isAlt=True, select=True)

    # run the Qt event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
