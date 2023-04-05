"""
"""
#import os
import enum
import math
from pprint import pprint
from typing import List, Union

import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import comparisonTypes
from pymapmanager.annotations import fileTypeClass

import pymapmanager.utils

from pymapmanager._logger import logger

class pointTypes(enum.Enum):
    """
    These Enum values are used to map to str (rather than directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    #pivotPnt = "pivotPnt"
    #pivotPnt = "globalPivotPnt"
    #linePnt = "linePnt"  # lineAnnotations

class pointAnnotations(baseAnnotations):
    """
    A list of annotations (a database)
    """
    
    #filePostfixStr = '_db2.txt'
    userColumns = ['cPnt']  # TODO: Add more

    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
 
        colItem = ColumnItem(
            name = 'roiType',
            type = str,
            units = '',
            humanname = 'ROI Type',
            description = ''
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'segmentID',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'Segment ID',
            description = 'Segment ID'
        )
        self.addColumn(colItem)

        # Add column for connection index
        colItem = ColumnItem(
            name = 'connectionID',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'connectionID',
            description = 'connectionID'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'brightestIndex',
            type = 'Int64',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'brightestIndex',
            description = 'brightestIndex'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'xLine',
            type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'xLine',
            description = 'X coordinate of the brightest point within the line that the spine is connected to'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'yLine',
            type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'yLine',
            description = 'Y coordinate of the brightest point within the line that the spine is connected to'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'zLine',
            type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'zLine',
            description = 'Z coordinate of the brightest point within the line that the spine is connected to'
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'xBackgroundOffset',
            type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'xBackgroundOffset',
            description = ''
        )
        
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'yBackgroundOffset',
            type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
            units = '',
            humanname = 'yBackgroundOffset',
            description = ''
        )
        
        self.addColumn(colItem)


        # feb 2023 with Johnson on zoom
        self._addIntColumns()

        self.load()

    def load(self):
        super().load()

    def _addIntColumns(self):
        """Add (10 * num channels) columns to hold roi based intensity analysis.
        """
        roiList = ['spine', 'spineBackground']
        statNames = ['Sum', 'Min', 'Max', 'Mean', 'Std']
        numChannels = 2 # fix this, get it from backend stack
        for roiStr in roiList:
            for statName in statNames:
                for channelNumber  in range(numChannels):
                    channelNumber += 1  # 1 based
                    # for example 'sSum_ch1'
                    #currColStr = roi + stat + channelStr
                    currColStr = self._getIntColName(roiStr, statName, channelNumber)
                    colItem = ColumnItem(
                        name = currColStr,
                        type = 'float',  # 'Int64' is pandas way to have an int64 with nan values
                        units = '',
                        humanname = '',
                        description = ''
                    )
                    self.addColumn(colItem)

    def _getIntColName(self, roiStr, statStr, channel : int):
        """Helper function to get an intensity stat column name.
        
        Intensity columns are things like: sSum_ch1, bsSum_ch1

        See: _addIntColumns(), setIntValue(), getIntValue()
        """
        if roiStr == 'spine':
            colStrPrefix = 's'
        elif roiStr == 'spineBackground':
            colStrPrefix = 'sb'
        else:
            logger.error(f'did not understand roiStr "{roiStr}"')
            return
        colNameStr = colStrPrefix + statStr + '_ch' + str(channel)
        return colNameStr
    
    def getIntValue(self, rowIdx : int, roiStr : str, channel : int) -> dict:
        """Get a dictionary of intensity values for one spine.
        
        Args:
            rowIdx: Row index to get
            roiStr: From ['spine', 'spineBackground']
            channel: Channel number 1,2,3,...
        """
        retDict = {}
        intStatList = ['Sum', 'Min', 'Max', 'Mean', 'Std']
        for intStatStr in intStatList:
            colStr = self._getIntColName(roiStr, intStatStr, channel)
            val = self.getValue(colStr, rowIdx)
            retDict[intStatStr] = val
        return retDict

    def setIntValue(self, rowIdx : int, roiStr : str, channel : int, statDict : dict):
        """Set a number of columns with intensity analysis values from a dict.

        Args:
            rowIdx: Row index to set
            roiStr: From ['spine', 'spineBackground']
            channel: Channel number 1,2,3,...
            statDict: Dict with keys of 'sum', 'mean', 'min', ...
        """

        for statKeyStr,statValue in statDict.items():
            colNameStr = self._getIntColName(roiStr, statKeyStr, channel)
            if not self.columns.columnIsValid(colNameStr):
                logger.error(f'Column "{colNameStr}" does not exist')
                continue
            self.setValue(colNameStr, rowIdx, statValue)

    def addAnnotation(self,
                    roiType : pointTypes,
                    segmentID : Union[int, None] = None,
                    *args,**kwargs):
        """
        Add an annotation of a particular roiType.
        
        Args:
            roiType:
            segmentID:
            imgData: image to use for finding brightes path and intensities
        """

        if roiType == pointTypes.spineROI and segmentID is None:
            logger.error(f'All spineROI require an int segmentID, got {segmentID}')
            return

        newRow = super().addAnnotation(*args,**kwargs)

        self._df.loc[newRow, 'roiType'] = roiType.value
        self._df.loc[newRow, 'segmentID'] = segmentID

        # called by stackWidget on new spine roi
        # if roiType == pointTypes.spineROI:
        #      self.updateSpineInt(newRow, xyzLineSegment, channelNumber,imgData)

        return newRow

    def updateSpineInt(self, spineIdx, zyxLineSegment, channelNumber : int, imgData : np.array, la):
        """Update all spine intensity measurements for:
            (1) a spine mask roi
            (2) minimal background roi (from a grid of candidates).

        Update all intensity measures for a given spine including:
            brightestIdx: brightest path from spine xyz to segment line
            all colmns for spine intensity (sSum, sMin, sMax, ...)
            all columns for spine background intensity (bsSum, bsMin, bsMax, ...)

        This get called on
            - new spine
            - user moves spine
            - user modifies the segment zyx tracing

        We need to know a lot of extra information
            - zyxLineSegment: coordinates of the segment we are connecting to (brightes path)
            - channelNumber: int
            - imgData: the raw image data to search

        Args:
            spineIdx (int) the row index into the pandas dataframe we are updating
            zyxLineSegment (List(z,y,x)): A list of (z,y,x) point we want to connect to (via brightest index)
            channelNumber (int) the channel number we are connecting to, needed to get the correct column name with _ch<channelNumber>
            imgData (np.ndarray) the actual image data to search in
            la: lineAnnotations
        """
        logger.info('This is setting lots of columns in our backend with all intensity measurements')
        logger.info(f'  imgData.shape {imgData.shape}')

        logger.info(f"spineIdx:{spineIdx}")
        _z = self.getValue('z', spineIdx)
        _x = self.getValue('x', spineIdx)
        _y = self.getValue('y', spineIdx)
        segmentID = self.getValue('segmentID', spineIdx)
        chStr = str(channelNumber)
        
        # 1) find brightest path to line segment
        #brightestIndex = self.reconnectToSegment(spineIdx, xyzLineSegment, imgData)
        brightestIndex = self._calculateSingleBrightestIndex(channel = channelNumber, spineRowIdx = spineIdx
                                                             , zyxLineSegment = zyxLineSegment, img = imgData)

        logger.info(f"brightestIndex:{brightestIndex}")

        # 1.1) set the backend value
        self.setValue('brightestIndex', spineIdx, brightestIndex)

        # 2) calculate spine roi (spine rectangle - segment polygon) ... complicated

        # xPlotLines, yPlotLines, xPlotSpines, yPlotSpines
        # pass in line annotations to index at brightestIndex?

        xBrightestLine = zyxLineSegment[brightestIndex][2]
        yBrightestLine = zyxLineSegment[brightestIndex][1]
        zBrightestLine = zyxLineSegment[brightestIndex][0]
        self.setValue('xLine', spineIdx, xBrightestLine)
        self.setValue('yLine', spineIdx, yBrightestLine)
        self.setValue('zLine', spineIdx, zBrightestLine)
        logger.info(f"xBrightestLine:{xBrightestLine}")
        logger.info(f"yBrightestLine:{yBrightestLine}")

        spineRectROI = pymapmanager.utils.calculateRectangleROIcoords(xPlotSpines = _x, yPlotSpines = _y,
                                                                      xPlotLines = xBrightestLine,
                                                                      yPlotLines = yBrightestLine)

        logger.info(f"spineRectROI:{spineRectROI}")

        radius = 3
        lineSegmentROI = pymapmanager.utils.calculateLineROIcoords(lineIndex = brightestIndex,
                                                                   radius = radius,
                                                                   lineAnnotations = la)

        logger.info(f"lineSegmentROI:{lineSegmentROI}")

        finalSpineROIMask = pymapmanager.utils.calculateFinalMask(rectanglePoly = spineRectROI, 
                                                                  linePoly = lineSegmentROI)
                                                                
        logger.info(f"finalSpineROIMask:{finalSpineROIMask}")

        # 3) calculate dict for spine with keys ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as columns in our pandas dataframe
        # this is fake, replace with real code
        # spineRoiMask = np.empty_like(imgData, dtype=np.uint8)  # TODO actually calulate spineRoiMask
        # spineRoiMask[:][:] = 0
        # spineRoiMask[_y][_x] = 1
        
        # get dict with spine intensity measurements
        spineIntDict = pymapmanager.utils._getIntensityFromMask(finalSpineROIMask, imgData)

        logger.info(f"spineIntDict:{spineIntDict}")

        self.setIntValue(spineIdx, 'spine', channelNumber, spineIntDict)


        # debugSpineIntDict = self.setIntValue(spineIdx, 'spine', channelNumber, spineIntDict)
        print("spineIntDict", spineIntDict)

        # 4) translate the roi in a grid to find dimmest position
        #   calculate dict with background ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as column in our pandas dataframe

        # this is fake, replace with real code
        # _xOffset = 10
        # _yOffset = 20
        # backgroundRoiMask = np.empty_like(imgData)  # TODO actually calulate backgroundRoiMask
        # backgroundRoiMask[:][:] = 0
        # logger.info(f'  backgroundRoiMask:{backgroundRoiMask.shape}')
        # backgroundRoiMask[_y + _yOffset][_x + _xOffset] = 1
        
        # mask, distance, numPts, originalSpinePoint, img
        distance = 2
        numPts = 3
        originalSpinePoint = [int(_y), int(_x)]
        print("finalSpineROIMask", finalSpineROIMask.shape)
        backgroundRoiOffset = pymapmanager.utils.calculateLowestIntensityOffset(mask = finalSpineROIMask, distance = distance
                                                                            , numPts = numPts
                                                                            , originalSpinePoint = originalSpinePoint, img=imgData)  

        self.setValue('xBackgroundOffset', spineIdx, backgroundRoiOffset[0])
        self.setValue('yBackgroundOffset', spineIdx, backgroundRoiOffset[1])

        backgroundMask = pymapmanager.utils.calculateBackgroundMask(finalSpineROIMask, backgroundRoiOffset)

        # TODO: offset original mask to get BackgroundROIMASK
        # Alternately calculate values of points within mask rather than using actual mask
        # backgroundRoiMask = finalSpineROIMask                                    
        #print("backgroundRoiMask", backgroundRoiMask.shape)

        #logger.info(f"backgroundRoiMask.shape:{backgroundRoiMask.shape}")

        # get dict with background intensity measurements
        # backgroundRoiAsList = np.argwhere(finalSpineROIMask==1)
        # backgroundRoiAsList += backgroundRoiOffset # for each point in lhs, add the pone point on the rhs

        spineBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(backgroundMask, imgData)
        
        self.setIntValue(spineIdx, 'spineBackground', channelNumber, spineBackgroundIntDict)

        # debugBackgroundSpineIntDict = self.setIntValue(spineIdx, 'spineBackground', channelNumber, spineBackgroundIntDict)
        # print("debugBackgroundSpineIntDict", debugBackgroundSpineIntDict)

        #
        # DEBUG
        #
        # retreive the value and print the dict
        # see: tests/test_point_annotations.test_int_columns()
        # logger.info('!!! we just added a spine, here are the value of the spine intensity:')
        # debugSpineIntDict = self.getIntValue(spineIdx, 'spine', channelNumber)
        # print(debugSpineIntDict)
        # logger.info('  and the background (I made these up)')
        # debugBackgroundSpineIntDict = self.getIntValue(spineIdx, 'spineBackground', channelNumber)
        # print(debugBackgroundSpineIntDict)

        # Figure out how to display the rectangle region on the interface.
        # Order the coordinates in the right order to plot
        #   - improve on the shape of the polygon

    def reconnectToSegment(self, rowIdx : int):
        """
        Connect a point to brightest path to a line segment.

        Only spineROI are connected like this

        Args:
            rowIdx: The row in the table
        
        Returns:
            cPnt: Connection point on lineAnnotations or None if not connected
        """
        
        # TODO: (cudmore) search for brightest path to segmentID (in line annotation)
        # this becomes the "connection point" (cPnt)

        # TODO: (cudmore) the stack class should do this

        #return cPnt

    def getRoiType_xyz(self, roiType : pointTypes):
        """Get (x,y,z) of one roiType.
        """
        #logger.info(f'{roiType.value}')
        xyz = self.getValuesWithCondition(['z', 'y', 'x'],
                    compareColNames='roiType',
                    comparisons=comparisonTypes.equal,
                    compareValues=roiType.value)
        return xyz

    def getTypeAndSegmentColumn(self, col, roiType: pointTypes,
                                    segmentID : int):
        if not isinstance(col, list):
            col = [col]
        
        xyz = self.getValuesWithCondition(col,
                    compareColNames=['roiType', 'segmentID'],
                    comparisons=[comparisonTypes.equal, comparisonTypes.equal],
                    compareValues=[roiType.value, segmentID])
        return xyz
    
    def getRoiType_col(self, col : Union[List[str], str], roiType : pointTypes):
        """Get values in column(s) for one roi type
        
        Args:
            col: the column to get values from
            roitType: the roi type to get from
        """
        
        if not isinstance(col, list):
            col = [col]
        
        xyz = self.getValuesWithCondition(col,
                    compareColNames='roiType',
                    comparisons=comparisonTypes.equal,
                    compareValues=roiType.value)
        return xyz

    def getSegmentSpines(self, segmentID : int) -> pd.DataFrame:
        """Get all spines connected to one segment.
        """
        dfPoints = self.getDataFrame()
        dfSpines = dfPoints[dfPoints['roiType'] == 'spineROI']
        dfSpines = dfSpines[dfSpines['segmentID']==segmentID]
        return dfSpines

    def getSegmentControlPnts(self, segmentID : int) -> pd.DataFrame:
        """Get all controlPnt connected to one segment.
        """
        dfPoints = self.getDataFrame()
        dfPoints = dfPoints[dfPoints['roiType'] == 'controlPnt']
        dfPoints = dfPoints[dfPoints['segmentID']==segmentID]
        return dfPoints

    def _isValid(self):
        """Check that all annotations are valid.
        
        For example:
            spineROI requires (segmentID, brightestIdx)
            controlPnt requires (segmentID)
        """
        isTrue = True
        for idx, row in self._df.iterrows():
            if row['roiType'] == 'spineROI':
                if row['segmentID'] >= 0:
                    pass
                else:
                    logger.error(f"row {idx} spineROI does not have a segmentID, found {row['segmentID']}")
                    isTrue = False
                if row['brightestIndex'] >= 0:
                    pass
                else:
                    logger.warning(f"row {idx} spineROI does not have a brightestIndex, found {row['brightestIndex']}. Need to use util._findBrightestIndex()")
                    #isTrue = False
        
        return isTrue
    
    # Call this when creating a new spine
    # OLD: def _calculateSingleBrightestIndex(self, channel: int, spineRowIdx: int, lineAnnotation, img):
    def _calculateSingleBrightestIndex(self, channel: int, spineRowIdx: int, zyxLineSegment, img):
        """
            Args:
                stack: the stack that we are using to acquire all the data
                channel: current channel used for image analysis
                spineRowIdx: Row index of the current spine
                zyxLineSegment: List of z,y,x for each coordinate for in the specific line segment that we are looking at. 

            Return:
                Brightest index of a line point for one spine point
        """
        import pymapmanager
        # lineAnnotation = stack.getLineAnnotations()
        # img = stack.getImageChannel(channel = channel)
        # segmentID = self.getValue("segmentID", spineRowIdx)
        # print(type(segmentID), segmentID)
     
        # call backend function within lineAnnotations
        # segmentZYX = lineAnnotation.getZYXlist(int(segmentID), ['linePnt'])

        # # Pull out into list z y x 
        x = self.getValue("x", spineRowIdx)
        y = self.getValue("y", spineRowIdx)
        z = self.getValue("y", spineRowIdx)

        # Bug:
        # segmentZYX = lineAnnotation.getSegment_xyz(segmentID)
        # print("segmentZYX: ", type(segmentZYX))
        # print("segmentZYX[0]: ", segmentZYX[0])
        # import sys
        # sys.exit(0)
        # call utility function
        # Check to see if this val is correct before storing into dataframe
        brightestIndex = pymapmanager.utils._findBrightestIndex(x, y, z, zyxLineSegment, img)

        # Store into backend
        # backendIdx
        self.setValue("brightestIndex", spineRowIdx, brightestIndex)

        return brightestIndex

    # def calculateBrightestIndexes(self, stack, channel: int, 
    #                 segmentID : Union[int, List[int], None],
    #                 lineAnnotation,
    #                 img):

    def calculateSingleBrightestIndex(self, channel: int, spineRowIdx: int, lineAnnotation, img):
        """
            Args:
                stack: the stack that we are using to acquire all the data
                channel: current channel used for image analysis
                spineRowIdx: Row index of the current spine
                zyxLineSegment: List of z,y,x for each coordinate for in the specific line segment that we are looking at. 

            Return:
                Brightest index of a line point for one spine point
        """
        import pymapmanager
        print("spineRowIdx", spineRowIdx)

        segmentID = self.getValue("segmentID", spineRowIdx)
        segmentZYX = lineAnnotation.getZYXlist(int(segmentID), ['linePnt'])
        # print("segmentZYX", segmentZYX)
        # segmentZYX2 = lineAnnotation.get_zyx_list(spineRowIdx)
        # print("segmentZYX2", segmentZYX2)

        # # Pull out into list z y x 
        x = self.getValue("x", spineRowIdx)
        y = self.getValue("y", spineRowIdx)
        z = self.getValue("y", spineRowIdx)

        # Check to see if this val is correct before storing into dataframe
        brightestIndex = pymapmanager.utils._findBrightestIndex(x, y, z, segmentZYX, img)

        # Store into backend
        # backendIdx
        self.setValue("brightestIndex", spineRowIdx, brightestIndex)

        return brightestIndex
    
    # TODO: remove channel
    def calculateBrightestIndexes(self, channel: int, 
                segmentID : Union[int, List[int], None],
                lineAnnotation,
                img):
        """
            Function to calculate brightest indexes within one segment or multiple segments and 
            saves them into the back end
        """
        # lineAnnotation = stack.getLineAnnotations()
        # img = stack.getImageChannel(channel = channel)
        if segmentID is None:
            # grab all segment IDs into a list
            segmentID = lineAnnotation.getSegmentList()
            # print("segmentID", segmentID)

        elif (isinstance(segmentID, int)):
            newIDlist = []
            newIDlist.append(segmentID)
            segmentID = newIDlist

        segmentSpineDFs = []

        # List of all segmentID dataframes 
        for id in segmentID:
            segmentSpineDFs.append(self.getSegmentSpines(id))

        # print("segmentSpineDFs", segmentSpineDFs)

        # Loop through all segments in the given list
        for index in range(len(segmentID)):
            currentDF = segmentSpineDFs[index]
            # print("currentDF", currentDF)
            # Looping through all spines connected to one segment
            for idx, val in enumerate(currentDF["index"]):
                # print("Val", val)
                # val = current index
                self.calculateSingleBrightestIndex(channel, val, lineAnnotation, img)
                print("stored", idx)


    def calculateJaggedPolygon(self, lineAnnotations, _selectedRow, _channel, img):
        """ Return coordinates of polygon connecting spine to line within AnnotationPlotWidget.py.
        This will be used to plot whenever we click a new spine on the interface
        """
        segmentID = self.getValue('segmentID', _selectedRow)
        zyxList = lineAnnotations.get_zyx_list(segmentID)

        # Later on retrieve this from the backend

        brightestIndex = self._calculateSingleBrightestIndex(_channel, int(_selectedRow), zyxList, img)
     
        segmentDF = lineAnnotations.getSegmentPlot(None, ['linePnt'])
        xLine = segmentDF["x"].tolist()
        yLine = segmentDF["y"].tolist()
        xBrightestLine = []
        yBrightestLine = []
        xBrightestLine.append(xLine[brightestIndex])
        yBrightestLine.append(yLine[brightestIndex])

        _xSpine = self.getValue('x', _selectedRow)
        _ySpine = self.getValue('y', _selectedRow)

        spinePolyCoords = pymapmanager.utils.calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine)
        linePolyCoords = pymapmanager.utils.calculateLineROIcoords(brightestIndex, 5, lineAnnotations)
        finalMaskPoly = pymapmanager.utils.calculateFinalMask(spinePolyCoords,linePolyCoords)
        # print("finalMaskPoly", finalMaskPoly)
        # coordsOfMask = np.column_stack(np.where(finalMaskPoly > 0))

        # # print("coordsOfMask", coordsOfMask)
        import scipy
        from scipy import ndimage
        # print(combinedMasks)
        struct = scipy.ndimage.generate_binary_structure(2, 2)
        # Get points surrounding the altered combined mask
        dialatedMask = scipy.ndimage.binary_dilation(finalMaskPoly, structure = struct, iterations = 1)

        labelArray, numLabels = ndimage.label(dialatedMask)
        currentLabel = pymapmanager.utils.checkLabel(dialatedMask, _xSpine, _ySpine)

        # coordsOfMaskOutline = np.column_stack(np.where(outlineMask > 0))

        coordsOfMask = np.argwhere(labelArray == currentLabel)
        print("type of coordsOfMask", type(coordsOfMask))
        # Check for left/ right points within mask
        segmentROIpointsWithinMask = pymapmanager.utils.getSegmentROIPoints(coordsOfMask, linePolyCoords)

        topTwoRectCoords = pymapmanager.utils.calculateTopTwoRectCoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine)
        finalSetOfCoords = segmentROIpointsWithinMask.tolist()
        finalSetOfCoords.insert(0,topTwoRectCoords[1])
        finalSetOfCoords.append(topTwoRectCoords[0])
        finalSetOfCoords.append(topTwoRectCoords[1])
        finalSetOfCoords =  np.array(finalSetOfCoords)
        # print("segmentROIpointsWithinMask", segmentROIpointsWithinMask)

        # # Remove the inner mask (combined mask) to get the outline
        # outlineMask = dialatedMask - finalMaskPoly
        # # Loop through to create list of coordinates for the polygon
        # # print(outlineMask)

        # labelArray, numLabels = ndimage.label(outlineMask)
        # currentLabel = pymapmanager.utils.checkLabel(outlineMask, _xSpine, _ySpine)

        # # coordsOfMaskOutline = np.column_stack(np.where(outlineMask > 0))

        # coordsOfMaskOutline = np.argwhere(labelArray == currentLabel)
        # # coordsOfMaskOutline = np.argwhere(labelArray == currentLabel)
        # coordsOfMaskOutline = pymapmanager.utils.rotational_sort(coordsOfMaskOutline, (int(_ySpine), int(_xSpine)), True)
        # # print("coordsOfMaskOutline", coordsOfMaskOutline)

        # coordsOfMask = np.column_stack(np.where(dialatedMask > 0))
        # print("coordsOfMask", coordsOfMask)
        return finalSetOfCoords
        # return finalMaskPolyCoords
            
            

    # function to set brightest index in column
        # add for one spine when a new one is added
        # loop to do it for all spines within a segment / for multiple segments
    # 2nd function to return 4 coords to rectangle 
    # Both take in lineannotations
    #  _function used internally for one spine

if __name__ == '__main__':
    pass