"""
We will derive (point, line) annotations from this
"""

from email import header
import enum
import errno
from lib2to3.pgen2.pgen import DFAState  # for FileNotFoundError
import os
import time
from pprint import pprint

from typing import List, Union  # Callable, Iterator, Optional

import numpy as np
import pandas as pd

import pymapmanager.logger
logger = pymapmanager.logger.get_logger(__name__)

class fileTypeClass(enum.Enum):
    mapmanager_igor = 'mapmanager_igor'

class roiTypesClass(enum.Enum):
    """
    These Enum values are used to map to str literal (rather than directly using a str)
    """
    spineROI = "spineROI"  # pointAnnotations
    controlPnt = "controlPnt"
    pivotPnt = "pivotPnt"
    linePnt = "linePnt"  # lineAnnotations

class comparisonTypes(enum.Enum):
    equal = 'equal'
    lessthan = 'lessthan'
    greaterthan = 'greaterthan'
    lessthanequal = 'lessthanequal'
    greaterthanequal = 'greaterthanequal'

class baseAnnotations():
    
    #roiTypeEnum = roiTypesClass
    
    # TODO: (cudmore) moved this logic to pymapmanager.stack
    #filePostfixStr = ''  # derived must define, like ('_db2.txt' or '_l.txt')
    
    # todo: (cudmore) add self.addColumn() and all derived must use this
    # userColumns = []  # list of string specifying additional columns

    def __init__(self, path : Union[str, None] = None):
        """
        Args:
            path (str | None): Full path to a file (a csv file). If None then wait to create on save.
            fileType (fileTypeClass): File type to load
        """
        
        self._path = path
        #Full path to file we load/save. Can be None if we are new and have not saved.
        
        self._dataModified = False
        #To keep track if edits have been made and need to be save.
        
        self._header = self._getDefaultHeader()

        self._df = self._getDefaultDataFrame()

        self.load()

    def __iter__(self):
        """As iterator, returns pandas.core.series.Series
        """
        self._iterIdx = 0
        return self

    def __next__(self):
        if self._iterIdx < self.numAnnotations:
            x = self._df.iloc[self._iterIdx]
            self._iterIdx += 1
            return x
        else:
            raise StopIteration

    def __getitem__(self, item):
        return self._df[item]
    
    def __setitem__(self, item, value):
        self._df[item] = value

    @property
    def at(self):
        """Mimic pd.DataFrame self.at[row, col].
        """
        return self._df.at

    def unique(self, col : str):
        """Get unique values from a column.
        
        Args:
            col (Str):
        """
        return self._df[col].unique()

    @property
    def filePath(self) -> Union[str, None]:
        """Get the full file path we were loaded from.

        If None then we were not loaded from a file and we have not saved.
        """
        return self._path

    @property
    def columns(self):
        """Get column names.
        """
        return self._df.columns
    
    @property
    def numAnnotations(self):
        """Get the number of annotations.
        """
        if self._df is None:
            return 0
        else:
            return len(self._df)

    def getDataFrame(self) -> pd.DataFrame:
        """Get annotations as underlying `pd.DataFrame`.
        """
        return self._df

    def getRows(self,
                colStr : str,
                value,
                operator : comparisonTypes = comparisonTypes.equal) -> List[int]:
        """
        Get a list of rows corresponding to the values in a columns
        
        Args:
            colStr: The column to interogate
            value: The value to search for, type will depend on column type
            operator: Operator like (<, <, ==) to evaluate rows

        Returns:
            (List[int]) List of row indices.
        """
        if operator == comparisonTypes.equal:
            df  = self._df[ self._df[colStr] == value ]
        else:
            logger.error('NEED TO ADD OTHER COMPARISON TYPES')

        return df.index.tolist()

    def _reduceRows(self, 
                    compareColNames : Union[str, List[str]],
                    comparisons : Union[comparisonTypes, List[comparisonTypes]],
                    compareValues : Union[float, List[float]],
                    ):
        """Reduce the number of annotations based on values in specified columns.
        
        Args:
            compareColNames (str | list(str)):
            comparisons (comparisonTypes | list(comparisonTypes)):
            compareValues (???):
        """
        if not isinstance(compareColNames, list):
            compareColNames = [compareColNames]
        if not isinstance(comparisons, list):
            comparisons = [comparisons]
        if not isinstance(compareValues, list):
            compareValues = [compareValues]

        df = self._df

        for idx, compareColName in enumerate(compareColNames):
            comparison = comparisons[idx]
            compareValue = compareValues[idx]
            #print('compareColName:', compareColName, 'comparison:', comparison, 'compareValue:', compareValue)
            if comparison == comparisonTypes.equal:
                df = df[ df[compareColName]==compareValue ]
        
        #pprint(df)
        return df

    # def getValueFromRow()
    def getValuesWithCondition(self,
                    colName : Union[str, List[str]],
                    compareColName : Union[str, List[str]],
                    comparisons : Union[comparisonTypes, List[comparisonTypes]],
                    #compareValues = Union[float, List[float]],
                    compareValues,
                    ) -> Union[np.ndarray, None]:
        """Get values from a column that match another column value.

        Args:
            colName (str | List(str)): Column(s) to get values from
            compareColName (str | List(str)):
            comparisons (comparisonTypes | List(comparisonTypes)):
            compareValues (???): We don't know the type. Could be (float, int, bool) or other?
        """
        # TODO: check that lists are same length (compareColName, comparisons, compareValues)
        
        df = self._reduceRows(compareColName, comparisons, compareValues)
        values = df.loc[:,colName].values
        if values.shape[1]==1:
            values = values.flatten() # ensure 1D (for napari)
        return values

    def getValue(self, colName : str, rowIdx : int):
        """Get a single value from a row and column.
        """
        return self.getValues(colName, rowIdx)
        
    def getValues(self,
                    colName : Union[str, List[str]],
                    rowIdx : Union[int, List[int]] = None,
                    ) -> Union[np.ndarray, None]:
        """Get value(s) from a column or list of columns.

        Args:
            colName (str | List(str)): Column(s) to get values from
            rowIdx (int | list(int)): Rows to get values from

        Returns:
            Annotation values (np.ndarray)
        """
        #if rowIdx is not None and compareColName is not None:
        #    logger.error('can't specify both')
        #    # raise ...
        
        # TODO (cudmore) check that column exists and if not decide what to return.
        if not isinstance(colName, list):
            colName = [colName]

        if rowIdx is None:
            rowIdx = range(self.numAnnotations)  # get all rows
        elif not isinstance(rowIdx, list):
            rowIdx = [rowIdx]

        df = self._df
        
        try:
            # TODO (cudmore) can't mix compareColName (reduceRows) and rowIdx
            ret = df.loc[rowIdx, colName].values
            #logger.info(f'ret:{type(ret)} {ret.shape}')
            #if len(colName)==1:
            if ret.shape[1]==1:
                ret = ret.flatten() # ensure 1D (for napari)
            return ret
        #except(IndexError) as e:
        #    logger.error(f'Did not find rows: "{rowIdx}"')
        #    return None
        except(KeyError) as e:
            logger.error(f'Column {e}')
            return None
                
    def addAnnotation(self, 
                    x : int, y : int, z : int,
                    rowIdx : int = None) -> int:
        """
        Add a new annotation at pixel (x,y,z).
        
        Args:
            x (int): Pixel
            y (int):
            z (int):
            rowIdx (Union(int,None)): If specified then insert before the row index
                    otherwise, append

        Returns:
            (int) Added row (annotation) number.
        """
        
        if rowIdx is None:
            rowIdx = self.numAnnotations

        logger.info(f'{x},{y},{z},rowIdx:{rowIdx} numAnnotations:{self.numAnnotations}')

        # append a row of all None, not sure this is the best
        # we often need to ensure the type of each column remains heterogeneous
        # this may cause problem with str type columns (shown as type 'object' in pandas?)
        self._df.loc[rowIdx] = [None] * len(self._df.columns)

        self._df.loc[rowIdx, 'cSeconds'] = time.time()  # creation time
        self._df.loc[rowIdx, 'mSeconds'] = time.time()  # modification time

        # TODO (cudmore) import, I want (x,y,z) to be points/pixels
        # and (xVoxel, yVoxel, zVoxel) to be in real-world coordinates (usually micro-meter)
        self._df.loc[rowIdx, 'x'] = x
        self._df.loc[rowIdx, 'y'] = y
        self._df.loc[rowIdx, 'z'] = z

        # TODO: (cudmore) convert pixel to um. We need pymapmanager.stack header for this
        self._df.loc[rowIdx, 'xVoxel'] = x * self._header['voxelx']
        self._df.loc[rowIdx, 'yVoxel'] = y * self._header['voxely']
        self._df.loc[rowIdx, 'zVoxel'] = z * self._header['voxelz']

        self._resetIndex()
        
        #if segmentID is not None:
        #    self._df.loc[rowIdx, 'segmentID'] = segmentID

        self._dataModified = True

        return rowIdx

    def deleteAnnotation(self, rowIdx : Union[int, List[int]]) -> None:
        """
        Delete an annotation or list of annotations based on the row index.
        
        Args:
            rowIdx: Either a single row or a list of rows.
        """
        if not isinstance(rowIdx, list):
            rowIdx = [rowIdx]
        self._df.drop(labels=rowIdx, axis=0, inplace=True)
        self._resetIndex()

    def addColumn(self, colStr : str, values):
        """Add a column
        """
        if colStr in self.columns:
            logger.warning(f'Column alread exists "{colStr}"')
        self._df[colStr] = values  # TODO: keep track of column types ?

    def _resetIndex(self):
        """Reset pd.DataFrame row indexes. Needs to be done after inserting and deleting.
        """
        # Use the drop parameter to avoid the old index being added as a column
        self._df = self._df.reset_index(drop=True)
    
    def _getDefaultHeader(self):
        header = {
            'voxelx' : 1,  # um/pixel
            'voxely': 1,
            'voxelz': 1,
        }
        return header

    def setHeaderVal(self, key, value):
        """Set the value of a header key.
        """
        if not key in self._header.keys():
            logger.error(f'did not find "{key}" in header. Keys are {self._header.keys()}')
            return

        self._header[key] = value

    def _getDefaultDataFrame(self):
        """
        Get an empty default DataFrame with pre-defined columns.
        
        Returns:
            (pandas.DataFrame)

        Notes:
            - We need to work on defining this.
            - What columns are needed, what are their defaults, units, and their 'human readable' meanings.
            - Maybe have a dict (or similar) like this
                columnNames = {
                    'x': {
                        'defaultValue': None,
                        'type': float,
                        'units': 'um',
                        'humanname': 'X Pixel',
                        'description': 'The X-Coordinate of an annotation.',
                    },
                    'mSeconds': {
                        'defaultValue': None,
                        'type': int,
                        'units': 'seconds',
                        'humanname': 'Mod Seconds',
                        'description': 'Last modification time in linux epochs (seconds).',
                    }
            }
        """
        columns = ['roiType',
                    'x',  # points
                    'y',
                    'z',
                    'xVoxel',  # um
                    'yVoxel',
                    'zVoxel',
                    #'segmentID',
                    'channel',  # the image channel the annotation lives in
                    'cSeconds',  # creation time in linux epoch seconds
                    'mSeconds',  # modification time in linux epoch seconds
                    'note',  # user editable note
                ]

        # join/append userColumns defined in derived classes
        #columns = columns + self.userColumns

        df = pd.DataFrame(columns=columns)
        return df

    def importFile(self, path, fileType : fileTypeClass):
        # TODO: (cudmore) put in protected function
        if fileType == fileTypeClass.mapmanager_igor:
            logger.info(f'importing with _import_mapmanager_igor')
            logger.info(f'{path}')
            self._import_mapmanager_igor(path)
    
    def loadHeader(self):
        """Load header as dictionary.
        """
        
        logger.info(f'loading header from {self.filePath}')
        
        header = {}
        
        with open(self.filePath) as f:
            headerLine = f.readline().rstrip()

        items = headerLine.split(';')
        for item in items:
            if item:
                k,v = item.split('=')
                # TODO: (cudmore) we need to know the type, for now just float
                header[k] = float(v)
        
        logger.info('')
        pprint(header)

        self._header = header

        return header

    def load(self):
        """
        Load annotations from a file.
        """
        #TODO (cudmore) In future we need to load different annotation formats, not just our pymapmanager formats.
        
        if self.filePath is None:
            # no file yet
            return
            
        if not os.path.isfile(self.filePath):
            logger.warning(f'Did not find annotation file: {self.filePath}')
            #raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), self.filePath)
            return

        logger.info(f'loading file:{self.filePath}')
        
        self.loadHeader()
        
        self._df = pd.read_csv(self.filePath, header=1, index_col=False)
            
    def save(self, forceSave=False):
        """
        Save underlying pandas.DataFrame.

        Args:
            forceSave (bool): If true then save even if not dirty
        """
        if not self._dataModified and not forceSave:
            # if not dirty/modified, do not save
            #logger.info(f'not saving')
            return
            
        if len(self._df) == 0:
            # if no data, do not save
            return

        logger.info(f'saving {self.filePath}')
        
        # TODO: (cudmore) Fill this in
        headerStr = self._getHeaderStr()
        with open(self.filePath, 'w') as file:
            file.write(headerStr)

        with open(self.filePath, 'a') as file:
            self._df.to_csv(file, header=True, index=False)
        
    def _getHeaderStr(self):
        """Get header as string.
        
        ';' delimited list of key=value paurs
        """
        header = ''
        for k,v in self._header.items():
            header += f'{k}={v};'
        header += '\n'
        return header

def test_empty_init():
    #path = 'data/one-timepoint/rr30a_s0/rr30a_s0_db2.txt'
    #ba = baseAnnotations(path)
    ba = baseAnnotations()
    assert ba is not None
    return ba

def test_import():
    path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_db2.txt'
    ba = baseAnnotations()
    ba.importFile(path, fileType = fileTypeClass.mapmanager_igor)    
    return ba

def test_getValues(ba):

    # test_numAnnotations
    numAnnotations = ba.numAnnotations
    print('ba.numAnnotations:', ba.numAnnotations)
    assert numAnnotations == 287

    # test_getValues
    # because of optional params need 4x test (or more)
    colStr = 'x'
    values = ba.getValues(colStr)
    assert type(values) == np.ndarray
    assert values.shape == (287,)
    assert len(values) == 287

    colStr = ['x', 'y']
    values = ba.getValues(colStr)
    assert type(values) == np.ndarray
    assert values.shape == (287, 2)

    colStr = ['x']
    rowIdx = 10
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (1,)

    colStr = ['x']
    rowIdx = [10, 20, 30]
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (3,)

    colStr = ['x', 'y']
    rowIdx = [10, 20, 30]
    values = ba.getValues(colStr, rowIdx)
    assert values.shape == (3,2)

    if 0:
        colStr = ['x', 'y', 'does not exist']
        values = ba.getValues(colStr)
        assert values is None

    if 0:
        colStr = ['x', 'y', 'z']
        rowIdx = 500
        values = ba.getValues(colStr, rowIdx)
        assert values is None

    # test mixture of int and str return values
    #colStr = ['x', 'userName']
    #values = ba.getValues(colStr)
    # assert something

    colName = ['x', 'y']
    compareColName = 'roiType'
    comparisons = comparisonTypes.equal
    compareValues = 'spineROI'
    values = ba.getValuesWithCondition(colName, 
                    compareColName=compareColName,
                    comparisons=comparisons,
                    compareValues=compareValues)
    assert values.shape == (139,2)

    # test as iterable
    for a in ba:
        print(a)

if __name__ == '__main__':
    test_empty_init()
    ba = test_import()
    test_getValues(ba)