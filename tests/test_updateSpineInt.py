
import pymapmanager as pmm

def test_spineUpdate():
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath)

    # Testing calculation of brightest Index
    newZYXValues = None
    spineIdx = 102
    la = myStack.getLineAnnotations()

    segmentID = myStack.getPointAnnotations().getValue("segmentID", spineIdx)
    zyxLineSegment = la.get_zyx_list(segmentID)
    imageChannel = 2
    # imageSlice = 31

    imageSlice = myStack.getPointAnnotations().getValue("z", spineIdx)
    # imgSliceData = myStack.getImageSlice(imageSlice, imageChannel)

    upslices = 1
    downSlices = 1
    imgSliceData = myStack.getMaxProjectSlice(imageSlice, imageChannel, upslices, downSlices)

    myStack.getPointAnnotations().updateSpineInt(newZYXValues,
                                                spineIdx,
                                                zyxLineSegment,
                                                imageChannel,
                                                imgSliceData,
                                                la
                                                )
    
    brightestIdx = myStack.getPointAnnotations().getValue("brightestIndex", spineIdx)
    assert brightestIdx == 274
    
    # Testing when Spine is moved
    newZYXValues = {"x": 600, 
                    "y": 150, 
                    "z": 31}
    
    myStack.getPointAnnotations().updateSpineInt(newZYXValues,
                                                spineIdx,
                                                zyxLineSegment,
                                                imageChannel,
                                                imgSliceData,
                                                la
                                                )
    
     # Testing when Spine is manually connected (brightest Index is manually picked)
    brightestIndex = 151
    myStack.getPointAnnotations().updateSpineInt(newZYXValues,
                                            spineIdx,
                                            zyxLineSegment,
                                            imageChannel,
                                            imgSliceData,
                                            la,
                                            brightestIndex = brightestIndex
                                            )

if __name__ == '__main__':
    test_spineUpdate()