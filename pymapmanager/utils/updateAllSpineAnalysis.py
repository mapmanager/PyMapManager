import pymapmanager as pmm

def updateAllSpineAnalysis(myStack, imageChannel):
    """
        Calculates and Stores all the intensity values for all spines
    """
    pa = myStack.getPointAnnotations()
    la = myStack.getLineAnnotations()
    # imageChannel = 2
    # imageSlice = 31

    pa.updateAllSpineAnalysis(None, la, imageChannel, myStack)


if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    imageChannel = 2
    updateAllSpineAnalysis(myStack, imageChannel)
    pa = myStack.getPointAnnotations()
    pa.save(forceSave = True)