import pymapmanager as pmm

def calculateAndStoreRadiusLines(path, segmentID, radius):
    """
        Calculates and Stores left/right points corresponding to each line point
    """
    myStack = pmm.stack(path)
    lineAnnotations = myStack.getLineAnnotations()
    lineAnnotations.calculateAndStoreRadiusLines(segmentID = segmentID, radius = radius)

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    lineAnnotations = myStack.getLineAnnotations()
    calculateAndStoreRadiusLines(stackPath, None, 3)
    lineAnnotations.save(forceSave = True)