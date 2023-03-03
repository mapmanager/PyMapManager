import math
import numpy as np

import pymapmanager as pmm

def getOffsets(n, d):
    """Get an nxn grid/square of points where each point is seperated by d pixels.

        Centered on (0,0)

    Args:
        n: Shape of the square to return
        d: distance (in pixels) between each nxn point.

    Returns:
        list of list of [y,x]
    """
    start = -math.floor(n/2) * d
    stop = (math.floor(n/2)+1) * d
    aRange = np.arange(start, stop, step=d)

    offsetList = []
    for x in aRange:
        for y in aRange:
            offsetList.append([y,x])
    return offsetList

def _loadStackAndGetSpine(rowIdx):
    """Load a stack and grab a spine.

    Note: This is the kind of little utility function
        I might write when debugging this code

    Args:
        rowIdx (int): the row index into our stacks point annotations
            this should be a spine roi

    Return:
        A dict with keys
            imgSlice: 2d np array of image the spine is in
            x (int): x coord of spine
            y (int): y coor of spine
            z (int): z (slice) coord of spine
    """
    
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(stackPath, defaultChannel=2, loadImageData=True)

    pa = myStack.getPointAnnotations()

    # get one row from point annotations (as dict)
    spineDict = pa.getRows_v2(rowIdx, asDict=True)

    _x = spineDict['x']
    _y = spineDict['y']
    _z = spineDict['z']

    # x and y are float, for our little test, convert to int
    _x = int(_x)
    _y = int(_y)

    # grab the image corresponding to the z-plane of the spine
    oneImage = myStack.getImageSlice(imageSlice=_z, channel=2)

    theDict = {
        'imgSlice': oneImage,
        'x': _x,
        'y': _y,
        'z': _z,  # not used
    }

    return theDict

def run():
    # I chose spine 110 arbitrarily
    rowIdx = 110

    myLittleDict = _loadStackAndGetSpine(rowIdx)
    imgSlice = myLittleDict['imgSlice']
    xSpine = myLittleDict['x']
    ySpine = myLittleDict['y']

    # this is the image we will interogate for the sum of our mask
    print(f'imgSlice: {imgSlice.shape} mean:{np.mean(imgSlice)} sum:{np.sum(imgSlice)}')

    # make up a simple 2d mask, in practice this is spine/segment mask
    # the mask we are making here is an X centered on spine (xSpine,ySpine)
    myMask = np.zeros((imgSlice.shape), dtype=np.uint8)
    myMask[ySpine, xSpine] = 1
    myMask[ySpine-1, xSpine-1] = 1
    myMask[ySpine-1, xSpine+1] = 1
    myMask[ySpine+1, xSpine+1] = 1
    myMask[ySpine+1, xSpine-1] = 1

    # these are parameters the user can specify
    n = 5  # number of points in square grid
    d = 10  # distance (pixels) between each point in the grid
    
    # get a grid of offsets, wrt (0,0)
    offsetList = getOffsets(n, d)

    print('offsetList:', offsetList)

    # myMaskCoord is ndarray with shape (4,2) ???
    myMaskCoord = np.argwhere(myMask==1)
    print ('myMaskCoord:', type(myMaskCoord), myMaskCoord.shape)
    print('  ', myMaskCoord)

    # move the spine/dendrite mask to a number of candidate positions
    # and find the minimum intensity position
    minSumInt = 2**16  # we are looking for a min so start really big
    minOffset = None
    for _idx, currentOffset in enumerate(offsetList):
        print(_idx)
        print('  currentOffset:', currentOffset)

        currentMaskCoord = myMaskCoord + currentOffset
                
        # shape here is 4x2 (4 points by (y,x))
        print('  currentMaskCoord shape is:', currentMaskCoord.shape)
        print('    ', currentMaskCoord)

        # pull out the pixel intensities (from the image) using our list of coordinates
        # e.g. the candidate mask or the current mask coords
        
        # this was a mistake (in the lab)
        # maskedImage = oneImage[currentMaskCoord]

        # NOTE: this needs to be [list(y), list(x)]
        # this is correct ( or at least a version that works here)
        yCoord = currentMaskCoord[:,0]
        xCoord = currentMaskCoord[:,1]
        print('  yCoord:', yCoord)
        print('  xCoord:', xCoord)
        pixelIntensitiesInMask = imgSlice[yCoord, xCoord]

        # pixelIntensitiesInMask loses the 2d dimensionality and is 1-D
        # it is a list of pixel intensities in the mask, fine for 
        # calculating intensity stats like (sum, mean, min, max, ...)
        print('  pixelIntensitiesInMask:', pixelIntensitiesInMask.shape)
        print('    ', pixelIntensitiesInMask)

        currSumInt = np.sum(pixelIntensitiesInMask)
        print('    currSumInt:', currSumInt)
        if currSumInt < minSumInt:
            minSumInt = currSumInt
            minOffset = currentOffset

    # we need to offset the spine/dendrite roi by this (dy,dx)
    # to get the minimum background intentisity
    print('ANSWER minOffset is:', minOffset)

    #
    # plot the image and each position
    import matplotlib.pyplot as plt
    plt.imshow(imgSlice)
    
    # I am always confused, did I get x/y wrong in _loadStackAndGetSpine()
    plt.plot(xSpine, ySpine, 'or')

    for _offset in offsetList:
        ySpine_offset = ySpine + _offset[0]
        xSpine_offset = xSpine + _offset[1]
        plt.plot(xSpine_offset, ySpine_offset, 'o')
    plt.show()

if __name__ == '__main__':
    run()
    
    # test if our little load function works
    #_loadStackAndGetSpine()