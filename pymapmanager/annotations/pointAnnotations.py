"""
"""
#import os
import enum
import math
from pprint import pprint
from typing import List, Union

import pandas as pd
import numpy as np  # TODO (cudmore) only used for return signature?

import scipy
from scipy import ndimage

from pymapmanager.annotations import baseAnnotations
from pymapmanager.annotations import ColumnItem
from pymapmanager.annotations import comparisonTypes
# from pymapmanager.annotations import fileTypeClass

import pymapmanager.utils
import pymapmanager.annotations.mpSpineInt

from pymapmanager._logger import logger

class pointTypes(enum.Enum):
    """These Enum values are used to map to str (rather than directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    #pivotPnt = "pivotPnt"
    #pivotPnt = "globalPivotPnt"
    #linePnt = "linePnt"  # lineAnnotations

class pointAnnotations(baseAnnotations):
    """A list of point annotations

    Under the hood, this is a Pandas DataFrame
    one point per row with columns to specify parameters of each point.

    """

    # def __init__(self, path : Union[str, None] = None, analysisParams = None):
    # def __init__(self, stack, la = None, *args,**kwargs):
    def __init__(self, stack, la = None, path = None, analysisParams = None):
        # super().__init__(*args,**kwargs)
        super().__init__(path, analysisParams)

        # done in parent
        # self._analysisParams = kwargs['analysisParams']
        
        self._stack = stack
        self._lineAnnotations = la

        # TODO: put these items in a json file
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
            type = 'Int64',  # 'Int64' is pandas way to have an int with nan values
            units = '',
            humanname = 'connectionID',
            description = 'connectionID'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'brightestIndex',
            type = 'Int64',  # 'Int64' is pandas way to have an int with nan values
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

        # detection params for rois
        colItem = ColumnItem(
            name = 'extendHead',
            type = 'float',
            units = '',
            humanname = 'Extend Tail',
            description = ''
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'extendTail',
            type = 'float',
            units = '',
            humanname = 'Extend Head',
            description = ''
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'width',
            type = 'float',
            units = '',
            humanname = 'ROI Width',
            description = ''
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'radius',
            type = 'float',
            units = '',
            humanname = 'Segment Radius',
            description = ''
        )
        self.addColumn(colItem)

        # add a number of columns for ROI intensity analysis
        numChannels = self._stack.numChannels

        self._addIntColumns(numChannels=numChannels)

        # load from csv if it exists
        self.load()

    def setLineAnnotations(self, la):
        self._lineAnnotations = la
    
    def setStack(self, stack):
        self._stack = stack

    def _addIntColumns(self, numChannels=2):
        """Add (10 * num channels) columns to hold roi based intensity analysis.
        """
        roiList = ['spine', 'spineBackground', 'segment', 'segmentBackground']
        statNames = ['Sum', 'Min', 'Max', 'Mean', 'Std']
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
        """Helper function to get an intensity column name.
        
        Intensity columns are things like: sSum_ch1, bsSum_ch1

        See: _addIntColumns(), setIntValue(), getIntValue()
        """
        if roiStr == 'spine':
            colStrPrefix = 's'
        elif roiStr == 'spineBackground':
            colStrPrefix = 'sb'
        elif roiStr == 'segment':
            # d short for dendrite
            colStrPrefix = 'd' 
        elif roiStr == 'segmentBackground':
            colStrPrefix = 'db'
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

    def addSpine(self, x, y, z,
                 segmentID,
                 dfSegment):
        newRow = super().addAnnotation(x, y, z)

        self._df.loc[newRow, 'roiType'] = pointTypes.spineROI
        self._df.loc[newRow, 'segmentID'] = segmentID

        # calculate brightest index, rois, and intensity

    def addAnnotation(self,
                    x, y, z,
                    roiType : pointTypes,
                    segmentID : Union[int, None] = None,
                    ):
                    # *args,**kwargs):
        """Add an annotation of a particular roiType.
        
        Args:
            roiType:
            segmentID:
            imgData: image to use for finding brightest path and intensities
        """

        if roiType == pointTypes.spineROI and segmentID is None:
            logger.error(f'All spineROI require an int segmentID, got {segmentID}')
            return

        # newRow = super().addAnnotation(*args,**kwargs)
        newRow = super().addAnnotation(x, y, z)

        self._df.loc[newRow, 'roiType'] = roiType.value
        self._df.loc[newRow, 'segmentID'] = segmentID

        # self.analyzeSpine(newRow)

        # called by stackWidget on new spine roi
        # if roiType == pointTypes.spineROI:
        #      self.updateSpineInt(newRow, xyzLineSegment, channelNumber,imgData)

        return newRow

    def _old_updateSpineConnection(self, selectedLinePointIdx, spineIdx, zyxLineSegment, 
                              channelNumber : int, imgData : np.array, la):
        """ Update the backend for spine after it was manually connected
        
        """
        # _z = self.getValue('z', spineIdx)
        # _y = self.getValue('y', spineIdx)
        # _x = self.getValue('x', spineIdx)
        
        # 1) brightest index is manually selected
        brightestIndex = selectedLinePointIdx
        logger.info(f"brightestIndex:{brightestIndex}")
        
        self.updateSpineInt(newZYXValues = None, spineIdx=spineIdx,
                            zyxLineSegment= zyxLineSegment,
                            channelNumber=channelNumber,
                            imgData = imgData,
                            la = la,
                            brightestIndex = brightestIndex)
        
        # TODO: Update interface and image to display change

    def analyzeSpine_new(self,
                         rowIdx : int,
                         imgData,
                         zyxLine
                         ) -> int:
        """Make a new spine at pnt (x,y,z)
            find brightest index into segment
            make rois (spine, segment, spine background, segment background)
            calculate intensity
        
            On new, caller needs to set x,y,z,segmentID
            On move, caller needs to set new (x,y,z)
            On manual set connection, caller needs to set new brightest index

        Notes
        =====
        New version June 23
        """

        # imgData needs to be pulled from stack
        # upSlices = 1
        # downSlices = 1
        # imgSliceData = self.getStack().getMaxProjectSlice(_imageSlice, imageChannel, 
        #                                                   upSlices=upSlices, downSlices = downSlices)

        spineDict = self.getRows_v2(rowIdx, asDict=True)
        analysisDict = mpSpineInt.intAnalysisWorker(spineDict, zyxLine, imgData)
        
        # fill in all the values
        logger.info('intAnalysisWorker returned')
        print(analysisDict)

    def updateSpineInt(self, newZYXValues: None, spineIdx, zyxLineSegment, 
                       channelNumber : int, imgData : np.array, 
                       la: "pymapmanager.annotations.lineAnnotations", brightestIndex: int = None):
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
            newZYXValues: is None for when a new Spine is created. When moving Spine it need actual values to replace the old data
            Either None or A dict(z,y,x)
            spineIdx (int) the row index into the pandas dataframe we are updating
            zyxLineSegment (List(z,y,x)): A list of (z,y,x) point we want to connect to (via brightest index)
            channelNumber (int) the channel number we are connecting to, needed to get the correct column name with _ch<channelNumber>
            imgData (np.ndarray) the actual image data to search in
            la: lineAnnotations
        """
        # logger.info('This is setting lots of columns in our backend with all intensity measurements')
        # logger.info(f'  imgData.shape {imgData.shape}')

        # logger.info(f"spineIdx:{spineIdx}")
        if(newZYXValues is None):
            _z = self.getValue('z', spineIdx)
            _y = self.getValue('y', spineIdx)
            _x = self.getValue('x', spineIdx)
        else:
            _z = newZYXValues['z']
            _y = newZYXValues['y']
            _x = newZYXValues['x']
            self.setValue('z', spineIdx, _z)
            self.setValue('y', spineIdx, _y)
            self.setValue('x', spineIdx, _x)

        # Send signal to update table widget and refresh interface image
        # _myPointListWidget

        # logger.info(f"x coordinate value :{_x}")
        # logger.info(f"y coordinate value :{_y}")
        # logger.info(f"z coordinate value :{_z}")

        segmentID = self.getValue('segmentID', spineIdx)
        chStr = str(channelNumber)
        
        # 1) find brightest path to line segment
        #brightestIndex = self.reconnectToSegment(spineIdx, xyzLineSegment, imgData)
        if (brightestIndex is None):
            # calculateSingleBrightestIndex(self, channel: int, spineRowIdx: int, lineAnnotation, img):
            # brightestIndex = self._calculateSingleBrightestIndex(channel = channelNumber, spineRowIdx = spineIdx
            #                                                  , zyxLineSegment = zyxLineSegment, img = imgData)
            brightestIndex = self.calculateSingleBrightestIndex(channel = channelNumber, spineRowIdx = spineIdx
                                                             , lineAnnotation = la, img = imgData)
            
            logger.info(f"newly calculated brightestIndex is :{brightestIndex}")

        logger.info(f"brightestIndex:{brightestIndex}")

        # 1.1) set the backend value
        self.setValue('brightestIndex', spineIdx, brightestIndex)

        # 2) calculate spine roi (spine rectangle - segment polygon) ... complicated

        # TODO (Cudmore) no need for this, just use
        # xBrightestLine = la.getValue('x', brightestIndex)
        # and get rid of zyxLineSegment parameter
        startRow, _  = la._segmentStartRow(segmentID)
        # Adjust my startrow of the segment to get proper index location
        xBrightestLine = zyxLineSegment[brightestIndex-startRow][2]
        yBrightestLine = zyxLineSegment[brightestIndex-startRow][1]
        zBrightestLine = zyxLineSegment[brightestIndex-startRow][0]
        
        # Only update BrightestPoint if none was provided
        if (brightestIndex is None):
            self.setValue('xLine', spineIdx, xBrightestLine)
            self.setValue('yLine', spineIdx, yBrightestLine)
            self.setValue('zLine', spineIdx, zBrightestLine)
        
        logger.info(f"xBrightestLine:{xBrightestLine}")
        logger.info(f"yBrightestLine:{yBrightestLine}")
        
        # Analysis Parameters
        width = self._analysisParams.getCurrentValue("width")
        extendHead = self._analysisParams.getCurrentValue("extendHead")
        extendTail = self._analysisParams.getCurrentValue("extendTail")
        radius = self._analysisParams.getCurrentValue("radius")

        logger.info(f"width:{width}")
        logger.info(f"extendHead:{extendHead}")
        logger.info(f"extendTail:{extendTail}")

        spineRectROI = pymapmanager.utils.calculateRectangleROIcoords(xPlotSpines = _x, yPlotSpines = _y,
                                                                      xPlotLines = xBrightestLine,
                                                                      yPlotLines = yBrightestLine,
                                                                      width = width,
                                                                      extendHead = extendHead,
                                                                      extendTail = extendTail)
        # logger.info(f"spineRectROI:{spineRectROI}")
        # radius = 5
        
        forFinalMask = True
        lineSegmentROI = pymapmanager.utils.calculateLineROIcoords(lineIndex = brightestIndex,
                                                                   radius = radius,
                                                                   lineAnnotations = la,
                                                                   forFinalMask = forFinalMask)
        # logger.info(f"lineSegmentROI:{lineSegmentROI}")

        finalSpineROIMask = pymapmanager.utils.calculateFinalMask(rectanglePoly = spineRectROI, 
                                                                  linePoly = lineSegmentROI)
                                                                
        # logger.info(f"finalSpineROIMask:{finalSpineROIMask}")

        # 3) calculate dict for spine with keys ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as columns in our pandas dataframe

        # TODO: change setbackgroundINT to accept argument finalSpineROIMask and use it in this function
        # get dict with spine intensity measurements
        spineIntDict = pymapmanager.utils._getIntensityFromMask(finalSpineROIMask, imgData)
        # logger.info(f"spineIntDict:{spineIntDict}")

        if spineIntDict is None:
            logger.error(f'error retrieving int stats for finalSpineROIMask with imgData shape: {imgData.shape}')
        else:
            self.setIntValue(spineIdx, 'spine', channelNumber, spineIntDict)


        # debugSpineIntDict = self.setIntValue(spineIdx, 'spine', channelNumber, spineIntDict)
        # print("spineIntDict", spineIntDict)

        # 4) translate the roi in a grid to find dimmest position
        #   calculate dict with background ('Sum', 'Min', 'Max', 'Mean', ....)
        #   and store as column in our pandas dataframe

        # mask, distance, numPts, originalSpinePoint, img
        distance = 7
        numPts = 7
        originalSpinePoint = [int(_y), int(_x)]
        # print("finalSpineROIMask", finalSpineROIMask.shape)

        # Pass in full combined mask to calculate offset
        segmentMask = pymapmanager.utils.convertCoordsToMask(lineSegmentROI)
        spineMask = pymapmanager.utils.convertCoordsToMask(spineRectROI)
        # When finding lowest intensity we use the full mask
        combinedMasks = segmentMask + spineMask
        combinedMasks[combinedMasks == 2] = 1

        backgroundRoiOffset = pymapmanager.utils.calculateLowestIntensityOffset(mask = combinedMasks, distance = distance
                                                                            , numPts = numPts
                                                                            , originalSpinePoint = originalSpinePoint, img=imgData)  

        self.setValue('xBackgroundOffset', spineIdx, backgroundRoiOffset[0])
        self.setValue('yBackgroundOffset', spineIdx, backgroundRoiOffset[1])

        print("spineIdx", spineIdx)
        backgroundMask = pymapmanager.utils.calculateBackgroundMask(finalSpineROIMask, backgroundRoiOffset)

        # TODO: Check if backgroundMask is out of bounds (of 1024x1024)
        # Change position of lowest intensity if that is the case.

        spineBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(backgroundMask, imgData)

        if spineBackgroundIntDict is None:
            logger.error(f'error retrieving int stats for backgroundMask with imgData shape: {imgData.shape}')
        else:
            self.setIntValue(spineIdx, 'spineBackground', channelNumber, spineBackgroundIntDict)

        # Segment
        segmentIntDict = pymapmanager.utils._getIntensityFromMask(segmentMask, imgData)
        self.setIntValue(spineIdx, 'segment', channelNumber, segmentIntDict)

        segmentBackgroundMask = pymapmanager.utils.calculateBackgroundMask(segmentMask, backgroundRoiOffset)
        segmentBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(segmentBackgroundMask, imgData)
        self.setIntValue(spineIdx, 'segmentBackground', channelNumber, segmentBackgroundIntDict)



    def _old_reconnectToSegment(self, rowIdx : int):
        """Connect a point to brightest path to a line segment.

        Only spineROI are connected like this

        TODO: Not implemented
        
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
    
    def getRoiTypes(self):
        """Get all unique roi types
        
        Args:
     
        """
        
        # if not isinstance(col, list):
        #     col = [col]
        
        dfPoints = self.getDataFrame()
        roiTypes = dfPoints.roiType.unique()
        return roiTypes
    
    # def getUniqueSegmentID(self):
    #     """Get all unique SegmentID
        
    #     Args:
     
    #     """
        
    #     # if not isinstance(col, list):
    #     #     col = [col]
        
    #     dfPoints = self.getDataFrame()
    #     segmentID = dfPoints.segmentID.unique()
    #     return segmentID
    
    def getfilteredValues(self, colName, roiType, segmentID) -> pd.DataFrame:
        """ Get all values according to colName, roitype and segmentID

        Args:
            segmentID: integer or All for entire segment ID list
            roiType: pointAnnotation roi type
            colName: one column name within dataframe
        """

        compareValues = [roiType.value]
        if not isinstance(colName, list):
            colName = [colName]

        if segmentID == "All":
            segmentID = self.getSegmentList()
            values = self.getRoiType_col(col = colName, roiType = roiType)
        else:
            segmentID = int(segmentID)
            # dfPoints = dfPoints[dfPoints['segmentID'] == segmentID]
            compareValues.append(segmentID)
            values = self.getValuesWithCondition(colName,
                    compareColNames=['roiType', 'segmentID'],
                    comparisons=[comparisonTypes.equal, comparisonTypes.equal],
                    compareValues=compareValues)
    
        # print("compareValues", compareValues)


        return values
        # return dfPoints

    def getSegmentSpines(self, segmentID : int) -> pd.DataFrame:
        """Get all spines connected to one segment.
        """
        dfPoints = self.getDataFrame()
        dfSpines = dfPoints[dfPoints['roiType'] == 'spineROI']
        dfSpines = dfSpines[dfSpines['segmentID']==segmentID]
        return dfSpines

    def _old_getSegmentControlPnts(self, segmentID : int) -> pd.DataFrame:
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
        # import pymapmanager
        # print("spineRowIdx", spineRowIdx)

        segmentID = self.getValue("segmentID", spineRowIdx)
        segmentID = int(segmentID)
        # print("segmentID", segmentID)
        logger.info(f"segmentID:{segmentID} spineRowIDX:{spineRowIdx}")
       
        segmentZYX = lineAnnotation.getZYXlist(segmentID, ['linePnt'])
        # print("segmentZYX", segmentZYX)
        # segmentZYX2 = lineAnnotation.get_zyx_list(spineRowIdx)
        # print("segmentZYX2", segmentZYX2)

        # # Pull out into list z y x 
        x = self.getValue("x", spineRowIdx)
        y = self.getValue("y", spineRowIdx)
        z = self.getValue("z", spineRowIdx)

        startRow, _  = lineAnnotation._segmentStartRow(segmentID)

        numPts = self._analysisParams.getCurrentValue("numPts")

        # print("numPts", numPts)
        # print("type numPts", type(numPts))
        # Check to see if this val is correct before storing into dataframe
        brightestIndex = pymapmanager.utils._findBrightestIndex(x, y, z, segmentZYX, img, numPnts = numPts)

        brightestIndex = brightestIndex + startRow
        # Store into backend
        # backendIdx
        self.setValue("brightestIndex", spineRowIdx, brightestIndex)

        return brightestIndex
    
    # TODO: remove channel
    def calculateBrightestIndexes(self, 
                stack : "pymapmanager.pymapmanager.stack",       
                segmentID : Union[int, List[int], None],
                channel: int,
                upValue = 1,
                downValue = 1):
        """
            Function to calculate brightest indexes within one segment or multiple segments and 
            saves them into the back end
        """
        lineAnnotation = stack.getLineAnnotations()
        pointAnnotation = stack.getPointAnnotations()
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
            # print("index", index)
            currentDF = segmentSpineDFs[index]
            # print("currentDF", currentDF)
            # Looping through all spines connected to one segment
            for idx, val in enumerate(currentDF["index"]):
                # print("Val", val)
                # val = current index
                spineZval = pointAnnotation.getValue("z", val)
                # img = stack.getImageChannel(channel=channel)
                
                # logger.info('DEBUG')
                # logger.info(f'  spineZval:{spineZval}')
                # logger.info(f'  channel:{channel}')
                # logger.info(f'  upValue:{upValue}')
                # logger.info(f'  downValue:{downValue}')
                
                img = stack.getMaxProjectSlice(spineZval, channel, upValue, downValue)
                self.calculateSingleBrightestIndex(channel, val, lineAnnotation, img)
                # print("stored", idx)


    def calculateJaggedPolygon(self, lineAnnotations, _selectedRow, _channel, img):
        """ Return coordinates of polygon connecting spine to line within AnnotationPlotWidget.py.
        This will be used to plot whenever we click a new spine on the interface
        """
        segmentID = self.getValue('segmentID', _selectedRow)
        zyxList = lineAnnotations.get_zyx_list(segmentID)

        # Later on retrieve this from the backend
        # startRow, _  = lineAnnotations._segmentStartRow(segmentID)
        # brightestIndex = self._calculateSingleBrightestIndex(_channel, int(_selectedRow), zyxList, img)
        # brightestIndex += startRow

        brightestIndex = self.getValue('brightestIndex', _selectedRow)
        brightestIndex = int(brightestIndex)

        logger.info(f"_selectedRow: {_selectedRow} segmentID: {segmentID} brightestIndex: {brightestIndex}")

        segmentDF = lineAnnotations.getSegmentPlot(None, ['linePnt'])
        xLine = segmentDF["x"].tolist()
        yLine = segmentDF["y"].tolist()
        xBrightestLine = []
        yBrightestLine = []
        xBrightestLine.append(xLine[brightestIndex])
        yBrightestLine.append(yLine[brightestIndex])

        _xSpine = self.getValue('x', _selectedRow)
        _ySpine = self.getValue('y', _selectedRow)

        # Analysis Parameters
        width = self._analysisParams.getCurrentValue("width")
        extendHead = self._analysisParams.getCurrentValue("extendHead")
        extendTail = self._analysisParams.getCurrentValue("extendTail")
        radius = self._analysisParams.getCurrentValue("radius")

        logger.info(f"width:{width}")
        logger.info(f"extendHead:{extendHead}")
        logger.info(f"extendTail:{extendTail}")

        spinePolyCoords = pymapmanager.utils.calculateRectangleROIcoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine
                                                                         , width, extendHead, extendTail)
        forFinalMask = True
        # radius = 5
        linePolyCoords = pymapmanager.utils.calculateLineROIcoords(brightestIndex, radius, lineAnnotations, forFinalMask)
        finalMaskPoly = pymapmanager.utils.calculateFinalMask(spinePolyCoords,linePolyCoords)
        # print("finalMaskPoly", finalMaskPoly)
        # coordsOfMask = np.column_stack(np.where(finalMaskPoly > 0))
        # # print("coordsOfMask", coordsOfMask)

        struct = scipy.ndimage.generate_binary_structure(2, 2)
        # Get points surrounding the altered combined mask
        dialatedMask = scipy.ndimage.binary_dilation(finalMaskPoly, structure = struct, iterations = 1)

        labelArray, numLabels = ndimage.label(dialatedMask)
        # print("numLabels", numLabels)
        # Separate mask into labeled regions and acquire the labeled region that contains original spine point
        currentLabel = pymapmanager.utils.checkLabel(dialatedMask, _xSpine, _ySpine)

        coordsOfMask = np.argwhere(labelArray == currentLabel)
        # print("type of coordsOfMask", type(coordsOfMask))

        # Check for left/ right points within mask
        segmentROIpointsWithinMask = pymapmanager.utils.getSegmentROIPoints(coordsOfMask, linePolyCoords)
        # logger.info(f"segmentROIpointsWithinMask: {segmentROIpointsWithinMask}")

        topTwoRectCoords = pymapmanager.utils.calculateTopTwoRectCoords(xBrightestLine[0], yBrightestLine[0], _xSpine, _ySpine, 
                                                                        width, extendHead)
        finalSetOfCoords = segmentROIpointsWithinMask.tolist()
        # logger.info(f"finalSetOfCoords before top two rect: {finalSetOfCoords}")

        finalSetOfCoords.insert(0,topTwoRectCoords[1])
        finalSetOfCoords.append(topTwoRectCoords[0])
        finalSetOfCoords.append(topTwoRectCoords[1])
        finalSetOfCoords = np.array(finalSetOfCoords)
        # logger.info(f"finalSetOfCoords: {finalSetOfCoords}")

        # return finalSetOfCoords
        # finalMaskPolyCoords = np.column_stack(np.where(finalMaskPoly > 0))
        return finalSetOfCoords
        # return coordsOfMask

    # def OLD_def calculateSegmentPolygon(self, spineRowIndex, lineAnnotations, radius, forFinalMask):
    def calculateSegmentPolygon(self, spineRowIndex, lineAnnotations, forFinalMask):
        """ 
        Used to calculated the segmentPolygon when given a spine row index

        """

        brightestIndex = self.getValue('brightestIndex', spineRowIndex)
        brightestIndex = int(brightestIndex)
        radius = self._analysisParams.getCurrentValue("radius")

        segmentPolygon = pymapmanager.utils.calculateLineROIcoords(brightestIndex, radius, lineAnnotations, forFinalMask)

        return segmentPolygon


    def OLD_setSingleSpineOffsetDictValues(self, spineRowIdx: int, lineAnnotation, channelNumber, myStack):
        """
            Args:
                stack: the stack that we are using to acquire all the data
                channel: current channel used for image analysis
                spineRowIdx: Row index of the current spine
                zyxLineSegment: List of z,y,x for each coordinate for in the specific line segment that we are looking at. 

            For one spine, calculates and storee the spine, spinebackground, segment, segmentBackground 
            as dictionary values in the backend.
            Also store the offset values needed to get the spine/segment background values.

        """
        segmentID = self.getValue("segmentID", spineRowIdx)
        segmentID = int(segmentID)
        logger.info(f"segmentID {segmentID} spineRowIDX{spineRowIdx}")
        segmentZYX = lineAnnotation.getZYXlist(segmentID, ['linePnt'])

        # # Pull out into list z y x 
        x = self.getValue("x", spineRowIdx)
        y = self.getValue("y", spineRowIdx)
        z = self.getValue("z", spineRowIdx)

        imageSlice = myStack.getPointAnnotations().getValue("z", spineRowIdx)
        upslices = 1
        downSlices = 1
        img = myStack.getMaxProjectSlice(imageSlice, channelNumber, upslices, downSlices)

        # Store into backend
        # backendIdx
        # self.setValue("brightestIndex", spineRowIdx, brightestIndex)

        # Get brightest index from back end
        brightestIndex = int(self.getValue("brightestIndex", spineRowIdx))

        _debug = False
        if _debug:
            logger.info(f"[segmentID]{segmentID}")
            logger.info(f"[spineRowIdx]{spineRowIdx}")
            logger.info(f"[brightestIndex]{brightestIndex}")
            # logger.info(f"[segmentZYX]{segmentZYX}")
            # logger.info(f"segmentZYX[brightestIndex]{segmentZYX[brightestIndex]}")
        
        # segmentZYX doesn't account for index of the original dataframe
        # Subtract by the initial index of the segment to get the correct value in the list
        startRow, _  = lineAnnotation._segmentStartRow(segmentID)

        xBrightestLine = segmentZYX[brightestIndex-startRow][2]
        yBrightestLine = segmentZYX[brightestIndex-startRow][1]
        zBrightestLine = segmentZYX[brightestIndex-startRow][0]
        # self.setValue('xLine', spineRowIdx, xBrightestLine)
        # self.setValue('yLine', spineRowIdx, yBrightestLine)
        # self.setValue('zLine', spineRowIdx, zBrightestLine)
        
        if _debug:
            logger.info(f"xBrightestLine:{xBrightestLine}")
            logger.info(f"yBrightestLine:{yBrightestLine}")

        spineRectROI = pymapmanager.utils.calculateRectangleROIcoords(xPlotSpines = x, yPlotSpines = y,
                                                                      xPlotLines = xBrightestLine,
                                                                      yPlotLines = yBrightestLine)

        radius = 5
        forFinalMask = True
        lineSegmentROI = pymapmanager.utils.calculateLineROIcoords(lineIndex = brightestIndex,
                                                                   radius = radius,
                                                                   lineAnnotations = lineAnnotation,
                                                                   forFinalMask = forFinalMask)

        # TODO: write a function to calculate finalSpineROIMask given spineRowIdx and lineAnnotation
        finalSpineROIMask = pymapmanager.utils.calculateFinalMask(rectanglePoly = spineRectROI, 
                                                                  linePoly = lineSegmentROI)

        # get dict with spine intensity measurements
        spineIntDict = pymapmanager.utils._getIntensityFromMask(finalSpineROIMask, img)

        if spineIntDict is None:
            logger.error(f'error retrieving int stats for finalSpineROIMask with img shape: {img.shape}')
        else:
            self.setIntValue(spineRowIdx, 'spine', channelNumber, spineIntDict)
    
        # print("spineIntDict", spineIntDict)

        distance = 7
        numPts = 7
        originalSpinePoint = [int(y), int(x)]
        # print("finalSpineROIMask", finalSpineROIMask.shape)
        # Pass in full combined mask to calculate offset
        
        segmentMask = pymapmanager.utils.convertCoordsToMask(lineSegmentROI)
        spineMask = pymapmanager.utils.convertCoordsToMask(spineRectROI)
        # When finding lowest intensity we use the full mask
        combinedMasks = segmentMask + spineMask
        combinedMasks[combinedMasks == 2] = 1
        
        backgroundRoiOffset = pymapmanager.utils.calculateLowestIntensityOffset(mask = combinedMasks, distance = distance
                                                                            , numPts = numPts
                                                                            , originalSpinePoint = originalSpinePoint, img=img)  
        logger.info(f"segmentID:{segmentID} spineRowIdx:{spineRowIdx} backgroundRoiOffset:{backgroundRoiOffset}")
        self.setValue('xBackgroundOffset', spineRowIdx, backgroundRoiOffset[0])
        self.setValue('yBackgroundOffset', spineRowIdx, backgroundRoiOffset[1])

        backgroundMask = pymapmanager.utils.calculateBackgroundMask(finalSpineROIMask, backgroundRoiOffset)
        spineBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(backgroundMask, img)
        
        if spineBackgroundIntDict is None:
            logger.error(f'error retrieving int stats for spineBackgroundIntDict with img shape: {img.shape}')
        else:
            self.setIntValue(spineRowIdx, 'spineBackground', channelNumber, spineBackgroundIntDict)

        # Segment
        segmentIntDict = pymapmanager.utils._getIntensityFromMask(segmentMask, img)
        if segmentIntDict is None:
            logger.error(f'error retrieving int stats for segmentMask with img shape: {img.shape}')
        else:
            self.setIntValue(spineRowIdx, 'segment', channelNumber, segmentIntDict)

        segmentBackgroundMask = pymapmanager.utils.calculateBackgroundMask(segmentMask, backgroundRoiOffset)
        segmentBackgroundIntDict = pymapmanager.utils._getIntensityFromMask(segmentBackgroundMask, img)
        if segmentBackgroundIntDict is None:
            logger.error(f'error retrieving int stats for segmentBackgroundIntDict with img shape: {img.shape}')
        else:
            self.setIntValue(spineRowIdx, 'segmentBackground', channelNumber, segmentBackgroundIntDict)

    # TODO: remove channel
    # rename to setAllSpineOffsetDictValues
    def OLD_setBackGroundMaskOffsets(self, 
                segmentID : Union[int, List[int], None],
                lineAnnotation,
                channelNumber,
                stack):
        """
            Function that calls setSingleSpineOffsetDictValues for all spines in given segment(s)
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

        upSlices = 1
        downSlices = 1
        imgChannel = 2
        # Loop through all segments in the given list
        for index in range(len(segmentID)):
            print("index", index)
            currentDF = segmentSpineDFs[index]
            # Looping through all spines connected to one segment
            for idx, val in enumerate(currentDF["index"]):
                self.OLD_setSingleSpineOffsetDictValues(val, lineAnnotation, channelNumber, stack)
                # _imageSlice = self.getValue("z", val)
                # imgData = stack.getMaxProjectSlice(_imageSlice, imgChannel, 
                #                                     upSlices=upSlices, downSlices = downSlices)
                
                # zyxLineSegment = lineAnnotation.get_zyx_list(index)
                # self.updateSpineInt(newZYXValues = None, spineIdx = val, 
                #                     zyxLineSegment = zyxLineSegment, channelNumber = imgChannel,
                #                     imgData = imgData, la = lineAnnotation,
                #                     brightestIndex = None)
                # if(val == 83):
                #     return

    def updateAllSpineAnalysis(self, segmentID, lineAnnotation, imgChannel, stack):
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

        # TODO: Change these values to values from analysis Param Dict
        upSlices = 1
        downSlices = 1
        # Loop through all segments in the given list
        for segmentIndex in range(len(segmentID)):
            # print("index", segmentIndex)
            currentDF = segmentSpineDFs[segmentIndex]
            # Looping through all spines connected to one segment
            for idx, spineRowIdx in enumerate(currentDF["index"]):
                # val = spineRowIdx
                # self.setSingleSpineOffsetDictValues(val, lineAnnotation, channelNumber, stack)
                # currentSlice = the z that the point is in
                _imageSlice = self.getValue("z", spineRowIdx)
                imgData = stack.getMaxProjectSlice(_imageSlice, imgChannel, 
                                                    upSlices=upSlices, downSlices = downSlices)
                
                zyxLineSegment = lineAnnotation.get_zyx_list(segmentIndex)
                self.updateSpineInt(newZYXValues = None, spineIdx = spineRowIdx, 
                                    zyxLineSegment = zyxLineSegment, channelNumber = imgChannel,
                                    imgData = imgData, la = lineAnnotation,
                                    brightestIndex = None)
                
                # if(val == 83):
            #     return

        


if __name__ == '__main__':
    pass