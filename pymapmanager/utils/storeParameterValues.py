import pymapmanager as pmm

def storeParameterValues(myStack, imageChannel):
    """
        Store all spineROI related analysis params for each spine point
    """
    pa = myStack.getPointAnnotations()
    la = myStack.getLineAnnotations()
    pa.storeParameterValues(None, la, imageChannel, myStack)


if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    imageChannel = 2
    storeParameterValues(myStack, imageChannel)
    pa = myStack.getPointAnnotations()
    pa.save(forceSave = True)