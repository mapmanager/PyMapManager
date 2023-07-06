import pymapmanager as pmm

# StoreParameterValues
# UpdateAllspineAnalysis
# StoreROI
def storeROI(myStack, imageChannel):
    """
        Calculates and Stores all the intensity values for all spines
    """
    pa = myStack.getPointAnnotations()
    la = myStack.getLineAnnotations()
    # pa.updateAllSpineAnalysis(None, la, imageChannel, myStack)
    pa.storeROICoords(None, la)
    # def storeJaggedPolygon(self, lineAnnotations, _selectedRow, _channel, img):


if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)
    imageChannel = 2
    storeROI(myStack, imageChannel)
    pa = myStack.getPointAnnotations()
    pa.save(forceSave = True)