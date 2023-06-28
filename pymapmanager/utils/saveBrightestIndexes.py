import pymapmanager as pmm
from pymapmanager.interface.stackWidget import stackWidget

from pymapmanager._logger import logger

def run(channel):
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(path=path)
    
    myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)

    # do this once and save into backend and file
    # myStack.createBrightestIndexes(channelNum = 2)
    pointAnnotations = myStack.getPointAnnotations()
    lineAnnotations = myStack.getLineAnnotations()
    segmentID = None
    pointAnnotations.calculateBrightestIndexes(myStack, segmentID, channel)
    myStack.save()

if __name__ == '__main__':
    channel = 2
    run(channel)