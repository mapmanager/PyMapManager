
import json
import pymapmanager as pmm
from pymapmanager._logger import logger
import numpy as np

def exportAllSpineROI(path):
    """
    Export all spine ROI as json file.
    Paramaters
    ----------
    path : str
        Path to stack .tif
    Note
    ----
    This is an example of just the spine ROI.
        We might want to expand to include the segment ROI
        and eventually the background spine and segment roi.
    """
    stack = pmm.stack(path)
    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()
    channel = 2
    roiDict = {}

    downValue = 1
    upValue = 1
    
    for spineDF in pa:
        
        img = stack.getMaxProjectSlice(spineDF['z'], channel, upValue, downValue)

        # logger.info(f'spineRowIdx {spineRowIdx}')
        if spineDF['roiType'] == 'spineROI':
            # logger.info(f'spineRowIdx {spineRowIdx._get_value(0, 'index')}')
            spinePoly = pa.calculateJaggedPolygon(la, spineDF['index'], channel, img)

            # calculateSegmentPolygon(self, spineRowIndex, lineAnnotations, radius, forFinalMask):
            radius = 5
            forFinalMask = False
            # Note: lists are formatted in [x,y]
            segmentPoly = pa.calculateSegmentPolygon(spineDF['index'], la, radius, forFinalMask)

            bOffsetX = int(pa.getValue("xBackgroundOffset", spineDF['index']))
            bOffsetY = int(pa.getValue("yBackgroundOffset", spineDF['index']))

            # Y is X
            xSpineBackground = spinePoly[:,1] + bOffsetY
            xSpineBackground = xSpineBackground.tolist()
            ySpineBackground = spinePoly[:,0] + bOffsetX
            ySpineBackground = ySpineBackground.tolist()

            # Need to switch XY/LeftRight in the backend?
            xSegmentBackground = segmentPoly[:,0] + bOffsetY
            xSegmentBackground = xSegmentBackground.tolist()
            ySegmentBackground = segmentPoly[:,1] + bOffsetX
            ySegmentBackground = ySegmentBackground.tolist()

            # calculateJaggedPolygon(self, lineAnnotations, _selectedRow, _channel, img)
            # self._spinePolygon.setData(jaggedPolygon[:,1], jaggedPolygon[:,0])
            roiDict[int(spineDF['index'])] = {
                        'xSpine': spinePoly[:,1].tolist(),
                        'ySpine': spinePoly[:,0].tolist(),
                        'xSegment': segmentPoly[:,0].tolist(), 
                        'ySegment': segmentPoly[:,1].tolist(),
                        'xSpineBackground': xSpineBackground,
                        'ySpineBackground': ySpineBackground,
                        'xSegmentBackground': xSegmentBackground,
                        'ySegmentBackground': ySegmentBackground,
            }
            # jsonStr = json.dumps(spineRoiDict)
            # print(roiDict)
            # logger.info(f'spineRowIdx {spineRowIdx._get_value(0, 'index')}')
            # break

    with open("sample.json", "w") as outfile:
        json.dump(roiDict, outfile)

if __name__ == "__main__":
    stackPath = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    exportAllSpineROI(stackPath)
