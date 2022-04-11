"""
"""
import os
from typing import List, Union

import numpy as np
import pandas as pd

from pymapmanager.annotations import baseAnnotations
#from pymapmanager.annotations import roiTypesClass
from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import fileTypeClass

import pymapmanager.analysis

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class lineAnnotations(baseAnnotations):
    """
    A line annotation encapsulates a list of 3D points to represent a line tracing.

    There are multiple (possible) disjoint line segments, indicated by segmentID
    """
    
    #filePostfixStr = '_l.txt'
    #userColumns = []  # TODO: Add more

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)

    def load(self):
        super().load()

        # modify the type of some columns
        #df = self.getDataFrame()
        #if df is not None:
        #    df['segmentID'] = df['segmentID'].astype(int)

    def old__import_mapmanager_igor_header(self, path : str):
        """Load header from first line of file.
        
        Header is a ';' sperated list of key=value pairs.
        """
        header = {}
        
        # (voxelx,voxely,voxelz)) are in units 'um/pixel'
        acceptKeys = ['voxelx', 'voxely', 'voxelz']

        if not os.path.isfile(path):
            logger.warning(f'Did not find annotation file path: {path}')
            return None

        with open(path) as f:
            headerLine = f.readline().rstrip()

        items = headerLine.split(';')
        for item in items:
            if item:
                k,v = item.split('=')
                if k in acceptKeys:
                    # TODO: (cudmore) we need to know the type, for now just float
                    header[k] = float(v)
        
        #logger.info('')
        #pprint(header)

        return header
        
    def old_import_mapmanager_igor(self, path : str):
        #df = super()._import_mapmanager_igor(*args,**kwargs)

        header = self._import_mapmanager_igor_header(path)
        for k,v in header.items():
            self.setHeaderVal(k, v)

        df = pd.read_csv(path, header=1, index_col=False)

        # swap some columns
        x = df['x']  # um/pixel
        y = df['y']
        z = df['z']
        
        xPixel = x / self._header['voxelx']  # pixel
        yPixel = y / self._header['voxely']
        zPixel = z / self._header['voxelz']

        # set native dataframe
        self._df['x'] = xPixel
        self._df['y'] = yPixel
        self._df['z'] = zPixel

        self._df['xVoxel'] = x
        self._df['yVoxel'] = y
        self._df['zVoxel'] = z

        #self.addColumn('roiType', df['roiType'])
        self.addColumn('segmentID', df['segmentID'].values)

        #self._df['roiType'] = df['roiType']

        #self._df['roiType'] = df['roiType']
        #self._df['segmentID'] = df['parentID']
        
        #
        # specific to line annotations
        roiTypeStr = 'linePnt'
        self.addColumn('roiType', roiTypeStr)

        return df

    def getSegment_xyz(self, segmentID : Union[int, list[int]] = None) -> list:
        """Get a list of (z,y,x) values from segment(s).
        """
        if segmentID is None:
            segmentID = self.unique('segmentID')  # unique() does not work for float
        elif not isinstance(segmentID, list):
            segmentID = [segmentID]

        zyxList = []  # a list of segments, each segment is np.ndarray of (z,y,x)
        for oneSegmentID in segmentID:
            zyx = self.getValuesWithCondition(['z', 'y', 'x'],
                            compareColName='segmentID',
                            comparisons=comparisonTypes.equal,
                            compareValues=oneSegmentID)
            zyxList.append(zyx)

        return zyxList

    '''
    # experimenting with displaying line segments as napari `tracks` layer
    def getSegment_tracks(self, segmentID : Union[int, list[int]] = None) -> list:
        zyx = self.getSegment_xyz(segmentID)
        # [id, timepoint, z, y,x]
        zyxRet = []
        for idx, oneSegment in enumerate(zyx):
            #print('  ', idx, oneSegment.shape)
            beforeCol = 0
            value = 0  # time point
            axis = 1
            oneSegment = np.insert(oneSegment, beforeCol, value, axis=axis)
            
            # this allows each segment to have a different color
            # but, does not work, thinks all points in a segment is a 'track' of one point
            value = idx  # track id
            oneSegment = np.insert(oneSegment, beforeCol, value, axis=axis)
            #print('    ', idx, oneSegment.shape)

            #oneSegment[:,0] = idx  # np.arange(oneSegment.shape[0])  # track ID
            #oneSegment[:,1] = 0  # time-points

            zyxRet.append(oneSegment)
        
        zyxConcat = np.concatenate([x for x in zyxRet])
        
        # make every point a different track
        zyxConcat[:,0] = np.arange(zyxConcat.shape[0])

        return zyxConcat
    '''

    @property
    def numSegments(self):
        parentList = self._df['segmentID'].unique()
        return len(parentList)

    def _segmentStartRow(self, segmentID : int):
        """
        Get the first and last row of a given segment
        
        Args:
            segmentID: The segment to fetch
        """
        allRows = self.getRows('segmentID', segmentID, comparisonTypes.equal)
        if len(allRows)>0:
            return allRows[0], allRows[-1]
        else:
            # segment not found
            return None, None

    def addAnnotation(self, 
                    x : int, y : int, z : int,
                    segmentID : int,
                    rowIdx = None,
                    ) -> int:
        addedRow = super().addAnnotation(x, y, z, rowIdx=rowIdx)
        self.at[addedRow, 'segmentID'] = segmentID

    def addSegment(self, pointList : List[List[int]]):
        """
        Add a new segment from a list of [z,y,x] points.
        
        Args:
            pointList: List of (x,y,z) points.

        Notes:
            Assign each new point segmentID to pre-existing numSegments()

        Returns:
            (int) new segment id        
        """
        newSegmentID = self.numSegments
        logger.info(f'Adding segment with {len(pointList)} points with segmentID:{newSegmentID}')
        for point in pointList:
            x = point[2]
            y = point[1]
            z = point[0]
            #print('  ', x, y, z)
            self.addAnnotation(x, y, z, segmentID=newSegmentID)

        return newSegmentID

    def addToSegment(self, x, y, z, segmentID):
        """Add point(s) to a segment.
        """
        # find last row of segmentID and insert into df at (row+1)
        startRow, stopRow = self._segmentStartRow(segmentID)
        print('  addToSegment() startRow:', startRow, 'stopRow:', stopRow)
        if startRow is None or stopRow is None:
            logger.error(f'did not find segmentID:{segmentID}')
            return
        rowIdx = stopRow+1  # insert before this row
        self.addAnnotation(x,y,z,segmentID,rowIdx=rowIdx)

    def deleteFromSegment(self, points, segmentID):
        """Delete points from a segment.
        """
        pass

    def deleteSegment(self, segmentID : Union[int, List[int]]):
        """
        Delete an entire segment based on segmentID.
        
        Args:
            segmentID (int): A single segmentID or a list of segmentID to delete.
        
        TODO (cudmore) check that segmentID is in DataFrame, otherwise nothing is deleted.
        """
        
        if not isinstance(segmentID, list):
            segmentID = [segmentID]
        
        for segment in segmentID:
            theseRows = self.getRows('segmentID', segment, operator=comparisonTypes.equal)
            self.deleteAnnotation(theseRows)

    def calculateSegmentLength(self, segmentID : Union[int, List[int]] = None):
        """
        Calculate the length of segment(s) in um.
        
        Do this using euclidean distance between successive points
        
        Args:
            segmentID (list or None): If None then calculate for all segmentID

        Returns:
            (list, list) of 2d and 3d segment lengths

        TODO: (cudmore)
            - We need to store these lengths in the class and occassionally calculate again
                Like when a point is added, edited, or deleted
        """
        if segmentID is None:
            segmentID = range(self.numSegments)
        elif not isinstance(segmentID, list):
            segmentID = [segmentID]
        
        lengthList2D = []
        lengthList3D = []
        for segment in segmentID:
            # get list of 3D points (x,y,z)
            points = self.getSegment_xyz(segmentID=segment)
            
            length2D, length3D = pymapmanager.analysis.lineAnalysis.getLineLength(points)
            
            lengthList2D.append(length2D)
            lengthList3D.append(length3D)

        return lengthList2D, lengthList3D
        
def run():
    logger.info('')
    
    # load a stack, line annotations use this as parent
    '''
    import pymapmanager.stack
    path = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
    stack = pymapmanager.stack.stack(path)
    print(stack)
    '''

    linePath = '../PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_s0_l.txt'
    linePath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_l.txt'

    la = lineAnnotations()   # line annotation directly from a parent stack
    la.importFile(linePath, fileType=fileTypeClass.mapmanager_igor)

    # could be test
    print('  todo: assert ... numAnnotations:', la.numAnnotations)
    xyzSegmentList  = la.getSegment_xyz()
    print('  todo: assert ... len(xyzSegmentList):', len(xyzSegmentList))  # unlike .tif image data, order is (x, y, slice)

    segLen = la.calculateSegmentLength()
    print('  todo: assert ... segLen:', segLen)

    # add a new segment from list of segment
    pointList = [
        [10, 10, 0],
        [20, 20, 0],
        [30, 30, 0],
        [40, 40, 0],
    ]
    newSegmentID = la.addSegment(pointList)  # add a new segment
    xyzSegmentList  = la.getSegment_xyz(segmentID=newSegmentID)
    print('  todo: assert ... after adding new segment len(xyzSegmentList):', len(xyzSegmentList))
    # unlike .tif image data, order is (x, y, slice)

    #print(la.getDataFrame())

    rows = la.getRows('segmentID', 1)  # get row indices where column 'segmentID' has value == 1
    print('  todo: assert ... rows corresponding to segmentID 1')
    print('    first:', rows[0], 'last:', rows[-1], 'num:', len(rows))

    # delete, seems to work
    print('  todo: assert ... before delete num segments:', la.numSegments)
    la.deleteSegment(1)
    print('  todo: assert ... after delete num segments:', la.numSegments)

    # add to segment
    segmentID = 0
    la.addToSegment(20, 30, 0, segmentID=segmentID)

    segmentID = 5
    la.addToSegment(40, 50, 0, segmentID=segmentID)

    # plot
    if 0 :
        import matplotlib.pyplot as plt
        xyz  = la.getPoints_xyz(asPixel=True)
        x = xyz[:,0]
        y = xyz[:,1]
        plt.plot(x, y, 'o')
        plt.show()

if __name__ == '__main__':
    run()