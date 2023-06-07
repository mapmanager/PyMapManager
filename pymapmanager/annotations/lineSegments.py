import os
import uuid

from typing import List, Union, Optional  # , Callable, Iterator

import pandas as pd

import pymapmanager as pmm
from pymapmanager._logger import logger

def convertToNewFormat():
    """Conver line annotations from single fife (with many segments)
    to many flies with just one segment per file.
    """

    # load the previous file format
    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_s0_la.txt'
    la = pmm.annotations.lineAnnotations(path)

    for segmentID in range(la.numSegments):
        dfOneSegment = la.getSegment(segmentID)

        la2 = pmm.annotations.lineAnnotations2()
        #la2._uuid = _getNewUuid()
        la2._df = dfOneSegment
        savePath = f'/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0/rr30a_la_{la2.uuid}.txt'
        la2._path = savePath
        la2.save(forceSave=True)

def _getNewUuid():
    return "h" + str(uuid.uuid4()).replace("-", "_")

class lineSegments:
    """Class to hold a number of lineAnnotation line segments.
    """
    def __init__(self, path : Optional[str] = None):
        self._path = path  # folder path to load/save
        
        self._segments = {}  # keys are segment uuid

        self.load()

    @property
    def numSegments(self):
        return len(self._segments.keys())
    
    def getDataFrame(self):
        dictList = []
        for segment in self:
            dictList.append(segment.getSummaryDict())
        df = pd.DataFrame(dictList)
        return df
    
    def uuidFromIdx(self, segmentID):
        keyList = list(self._segments.keys())
        return keyList[segmentID]
    
    def appendNewSegment(self):
        newSegment = pmm.annotations.lineAnnotations2()
        self._segments[newSegment.uuid] = newSegment

    def deleteSegment(self, uuid):
        _deletedSegment = self._segments.pop('key', None)
        return _deletedSegment
    
    def appendAnnotation(self, uuid, x, y, z):
        self._segments[uuid].addAnnotation(x,y,z)
    
    def getSegmentPlot(self, segmentID, roiTypes, sliceNumber):
        uuid = self.uuidFromIdx(segmentID)
        return self._segments[uuid].getSegmentPlot(segmentID, roiTypes, sliceNumber)

    def load(self):
        """
        Parameters
        ----------
        path : str
            Folder to load individual segment files from.
            Each segment file has _la_ and ends in .txt
        """
        if self._path is None:
            return
        
        files = os.listdir(self._path)
        for file in files:
            if not file.endswith('.txt'):
                continue
            if not '_la_' in file:
                continue
            filePath = os.path.join(self._path, file)
            #print('filePath:', filePath)
            la = pmm.annotations.lineAnnotations2(filePath)
            self._segments[la.uuid] = la

    def save(self):
        if self._path is None:
            logger.info(f'Did not save lineSegments, no path specified.')
            return

    def getKeyList(self):
        """Get list of segments uuid keys.
        """
        return list(self._segments.keys())
    
    def __iter__(self):
        """Allow iteration with "for item in self"
        """
        self._iterIdx = -1
        return self

    def __next__(self):
        """Allow iteration with "for item in self"
        """
        self._iterIdx += 1
        if self._iterIdx >= self.numSegments:
            self._iterIdx = -1  # reset to initial value
            raise StopIteration
        else:
            keyList = self.getKeyList()
            key = keyList[self._iterIdx]
            return self._segments[key]

def test_load():
    loadFolderPath = f'/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0'
    ls = lineSegments(loadFolderPath)
    
    # for segment in ls:
    #     print(segment.getSummaryDict())

    df = ls.getDataFrame()
    print(df)

def test_new():
    ls = lineSegments()
    ls.appendNewSegment()
    logger.info(f'after appendNewSegment, numSegments: {ls.numSegments}')

    uuid = ls.uuidFromIdx(0)

    x = 1
    y = 4
    z = 4
    ls.appendAnnotation(uuid, x, y, z)
    x = 2
    y = 5
    z = 5
    ls.appendAnnotation(uuid, x, y, z)
    x = 3
    y = 6
    z = 5
    ls.appendAnnotation(uuid, x, y, z)

    segmentID = 0
    sliceNumber = 5
    df = ls.getSegmentPlot(segmentID, [pmm.annotations.linePointTypes.linePnt.value], sliceNumber)
    logger.info('df from getSegmentPlot')
    print(df)

if __name__ == '__main__':
    
    # do not call multiple times
    #convertToNewFormat()

    test_new()
    # test_load()
