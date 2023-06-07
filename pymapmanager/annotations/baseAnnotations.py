"""
We will derive (point, line) annotations from this
"""

from email import header
import enum
import errno
import os
import time
import traceback
from pprint import pprint

from typing import List, Union, Optional  # , Callable, Iterator

import numpy as np
import pandas as pd

import pymapmanager.annotations

from pymapmanager._logger import logger

class AddAnnotationEvent():
    """Added annotations are proposed as just (z,y,x) points
    
    The parent stack window decides the pointType based on the state of the window
    
    We have two different point types enumes, one for pointAnnotation and one for line annotations
        pymapamanger.annotations.pointAnnotation.pointTypes
        pymapamanger.annotations.lineAnnotations.linePointTypes
    """
    def __init__(self, z : float, y : float, x : float, pointType = None):
        self._dict = {
            'x': x,
            'y': y,
            'z': z,
            'pointType': pointType,
            'annotationObject': None,
            'addedRowIdx': None,
        }      

    def getZYXDictForm(self):
        dict = {
            'x': self._dict['x'],
            'y': self._dict['y'],
            'z': self._dict['z'],
        }
        return dict
    
    def getZYX(self):
        return self._dict['z'], self._dict['y'], self._dict['x']
    
    def setPointType(self, pointType):
        """
        Args:
            pointType is a enum from one of
                pymapamanger.annotations.pointAnnotation.pointTypes
                pymapamanger.annotations.lineAnnotations.linePointTypes
        """
        self._dict['pointType'] = pointType

    def getPointType(self):
        return self._dict['pointType']
    
    def setAddedRow(self, addedRow : int):
        self._dict['addedRowIdx'] = addedRow

    def getAddedRow(self):
        return self._dict['addedRowIdx']

class SelectionEvent():
    """Created and emited on an annotation selection.
    """
    def __init__(self,
                 annotation : "baseAnnotations" = None,
                 rowIdx : List[int] = None,
                 isEsc : bool = False,
                 isAlt : bool = False,
                 isShift : bool = False,
                 lineIdx : List[int] = None,
                 ):
        
        if isinstance(rowIdx, int):
            rowIdx = [rowIdx]
        
        self._selDict = {
            'annotationObject': annotation,
            'rowIdx': rowIdx,
            'isEsc': isEsc,
            'isAlt': isAlt,
            'isShift': isShift,
            'lineIdx': lineIdx
        }

    def __str__(self):
        _str = '\n'  # f"  {self.type}" + '\n'
        for k,v in self._selDict.items():
            if k == 'annotationObject':
                v = type(v)
            _str += f'  {k}: {v}' + '\n'
        return _str

    def isPointSelection(self):
        return self.type == pymapmanager.annotations.pointAnnotations
    
    def isLineSelection(self):
        # annotationType = self._selDict['annotationObject']
        logger.info(f'--->> check type {self.type}')
        # logger.info(f'--->> controlled type {pymapmanager.annotations.lineAnnotations}')
        # return annotationType == pymapmanager.annotations.lineAnnotations

        # Altered on 4/19 because self.type would return <class 'type'>
        # rather than  <class 'pymapmanager.annotations.lineAnnotations.lineAnnotations'>
        return self.type == pymapmanager.annotations.lineAnnotations
    

    def linePointSelected(self):
        """
        isLineSelection is throwing error
        self.type would return <class 'type'>
        rather than  <class 'pymapmanager.annotations.lineAnnotations.lineAnnotations'>

        This class was made as a possible fix
        """
        annotationType = self._selDict['annotationObject']
        return annotationType== pymapmanager.annotations.lineAnnotations
    
    @property
    def type(self):
        # temp = type(self._selDict['annotationObject'])
        # logger.info(f'--->> IT WORKS {temp}')

        return type(self._selDict['annotationObject'])
    
    @property
    def annotationObject(self) -> "pymapmanager.annotations.baseAnnotations":
        return self._selDict['annotationObject']
    
    def getLineIdx(self) -> Optional[List[int]]:
        """Get list of selected rows, can be None.

        For line selection, will be segmentID
        """
        return self._selDict['lineIdx']
    
    def getRows(self) -> Optional[List[int]]:
        """Get list of selected rows, can be None.

        For line selection, will be segmentID
        """
        return self._selDict['rowIdx']

    def getColumnValues(self, colStr):
        """Get column values for selected annotations.
        """
        _values = self.annotationObject.getValues(colStr, self.getRows())
        return _values
    
    @property
    def isEsc(self):
        return self._selDict['isEsc']

    @property
    def isAlt(self):
        return self._selDict['isAlt']

    @property
    def isShift(self):
        return self._selDict['isShift']

class fileTypeClass(enum.Enum):
    mapmanager_igor = 'mapmanager_igor'

class comparisonTypes(enum.Enum):
    equal = 'equal'
    lessthan = 'lessthan'
    greaterthan = 'greaterthan'
    lessthanequal = 'lessthanequal'
    greaterthanequal = 'greaterthanequal'

class ColumnItem():
    """Class to hold one columns.
    """
    def __init__(self,
            name : str,
            type = None,
            units : str = '',
            humanname : str = '',
            description : str = ''):
        self._dict = {
            'name': name,
            'type': type,
            'units': units,
            'humanname': humanname,
            'description': description,
        }
    
    def getName(self):
        """Get the name of the column.
        """
        return self._dict['name']

    def getType(self) -> type:
        """Get the name of the column.
        """
        return self._dict['type']

    def getValue(self, key):
        """Get value from column.
        """
        try:
            return self._dict[key]
        except (KeyError) as e:
            logger.error(e)
            return None

class Columns():
    """A list of ColumnItem.
    """
    def __init__(self):
        self._colList = []

    def getTypeDict(self):
        """Get a dictionary mapping column name to column type.
        
        Used in pandas read_csv dtype parameter.
        """
        typeDict = {}
        for colItem in self:
            typeDict[colItem.getName()] = colItem.getType()
        return typeDict

    def getColumnNames(self):
        """Get a list of all column names.
        """
        return [item.getName() for item in self._colList]
    
    def addColumn(self, colItem : ColumnItem):
        """Add a new column.
        
        Don't add if column `name` already exists.
        
        Returns:
            (bool) True if added, False otherwise.
        """
        name = colItem.getName()
        if name in self.getColumnNames():
            logger.warning(f'not adding column "{name}", already a Columns')
            return
        self._colList.append(colItem)
        return True

    def numColumns(self):
        return len(self._colList)

    def columnIsValid(self, columnNames : Union[str, List[str]]) -> bool:
        """Convenience function to check that column name(s) exist.
        """
        if not isinstance(columnNames, list):
            columnNames = [columnNames]

        _columnNames = self.getColumnNames()
        for columnName in columnNames:
            if not columnName in _columnNames:
                return False
        return True

    def __iter__(self):
        """As iterator, returns ColumnItem.
        """
        self._iterIdx = 0
        return self

    def __next__(self):
        if self._iterIdx < self.numColumns():
            x = self._colList[self._iterIdx]
            self._iterIdx += 1
            return x
        else:
            raise StopIteration

class annotationType(enum.Enum):
    """Used to determine the type of annotation.
    
    Used when we delete a point from a view (list, image scatter, scatter, etc)
    """
    point = 'point'
    line = 'line'
    segment = 'segment'

class baseAnnotations():
    def getAnnotationDict(self):
        theDict = {}
        for column in self._columns:
            theDict[column.getName()] = None
        return theDict

    def __init__(self, path : Union[str, None] = None):
        """Base class for annotations.

        Manage a pandas dataframe, one row per annotation with named columns.

        Args:
            path (str | None): Full path to a file (a csv file). If None then wait to create on save.
        """
        
        self._path = path
        #Full path to file we load/save. Can be None if we are new and have not saved.
        
        # default, empy DataFrame
        self._df = pd.DataFrame()

        self._dataModified = False
        #To keep track if edits have been made and need to be save.
        
        self._header = self._getDefaultHeader()

        # create Columns(), a list of ColumnItem()
        self._columns = Columns()

        # TODO (cudmore) Put all the parameters for these CoumnItem into a globally accessible dict
        # use this dict to create ColumnItem(dict['key']) and seld.addColumn()
        colItem = ColumnItem(
            name = 'x',
            type = int,
            units = 'Pixels',
            humanname = 'X Pixels',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'index',
            type = int,
            units = '',
            humanname = 'Row Index',
            description = 'Row Index'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'y',
            type = int,
            units = 'Pixels',
            humanname = 'Y Pixels',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'z',
            type = int,
            units = 'Pixels',
            humanname = 'Z Pixels',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'xVoxel',
            type = float,
            units = 'um',
            humanname = 'X Voxel (um)',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'yVoxel',
            type = float,
            units = 'um',
            humanname = 'Y Voxel (um)',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'zVoxel',
            type = float,
            units = 'um',
            humanname = 'Z Voxel (um)',
            description = 'xxx'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'channel',
            type = pd.Int64Dtype(),  # so we can have missing values
            units = '',
            humanname = 'Channel Number',
            description = 'xxx'
        )
        self.addColumn(colItem)

        # TODO (cudmore) add
        # bad:bool
        # type:enum
        # stackFile:str (filename of associated stack)

        # not sure if we keep these with each annotation (row)
        # or once in header, to export proper pd.dataframe, we might want to add this?
        # xVoxelSize
        # yVoxelSize
        # zVoxelSize

        colItem = ColumnItem(
            name = 'cSeconds',
            type = float,
            units = '',
            humanname = 'Creation time (s)',
            description = 'Creation time in linux epoch seconds'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'mSeconds',
            type = float,
            units = '',
            humanname = 'Modification time (s)',
            description = 'Modification time in linux epoch seconds'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'note',
            type = str,
            units = '',
            humanname = 'Note',
            description = 'User edited note'
        )
        self.addColumn(colItem)

        colItem = ColumnItem(
            name = 'isBad',
            type = bool,
            units = '',
            humanname = 'Bad',
            description = 'If user specifies annotation as bad'
        )
        self.addColumn(colItem)

        #
        # create dataframe with columnn names
        #columns = self._columns.getColumnNames()
        #self._df = pd.DataFrame(columns=columns)

        # classes that derive need to call this
        # self.load()

    @property
    def header(self) -> dict:
        """Get the file header dicitonary.
        """
        return self._header
    
    @property
    def columns(self) -> Columns:
        """Return the list of columns object.
        """
        return self._columns
        
    def __len__(self) -> int:
        """Return the number of annotations.
        """
        return len(self._df)
    
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

    @property
    def shape(self):
        return self._df.shape
    
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

    def saveAs(self, path : str):
        self._path = path
        self.save()

    # @property
    # def columns(self):
    #     """Get column names.
    #     """
    #     return self._columns
    
    def getSegmentPlot(self, segmentID : Union[int, List[int], None],
                        roiTypes : Union[List[str], None] = None, 
                        zSlice : Union[int, None] = None,
                        zPlusMinus : int = 0,
                        ) -> pd.DataFrame:
        """Get a pd.DataFrame to plot.

        Args:
            segmentID: A single segment (int), a list of segments [int], or None for all segments.
            roiTypes: List of annotation roitType or None for all roiType
            zSlice: The image slice (z) to limit returned annotations.
            zPlusMinus: Include annotations with z +/- this value
        """
        
        # reduce by roiType
        if isinstance(roiTypes, str):
            roiTypes = [roiTypes]
        if roiTypes is not None:
            df = self._df[self._df['roiType'].isin(roiTypes)]
        else:
            df = self._df

        # Reduce by [segmentID]
        if segmentID is None:
            segmentID = df['segmentID'].unique()
        elif isinstance(segmentID, list):
            pass
        elif isinstance(segmentID, int):
            segmentID = [segmentID]
        else:
            logger.error(f'did not understand segmentID:{segmentID} of {type(segmentID)}')
            return

        segmentID = [int(_segmentID) for _segmentID in segmentID]

        df = df[df['segmentID'].isin(segmentID)]

        # Reduce by Z
        if zSlice is not None:
            zMin = zSlice - zPlusMinus
            zMax = zSlice + zPlusMinus
            df = df[(df['z']>=zMin) & (df['z']<=zMax)]
        
        return df

    @property
    def numAnnotations(self):
        """Get the number of annotations.
        """
        if self._df is None:
            return 0
        else:
            return len(self._df)

    def getDataFrame(self) -> pd.DataFrame:
        """Get annotations as underlying `pandas.DataFrame`.
        """
        return self._df

    def rowColIs(self, rowIdx : int, colStr : str, value) -> bool:
        """Return true if row/col have value.
        """
        return self._df.at[rowIdx, colStr] == value

    def getRows_v2(self, rows : Union[List[int], int], asDict : bool = False) -> Union[pd.DataFrame,dict]:
        """Get rows from dataframe (all columns).
        
        Args:
            rows (int): rows to get
            asDict (bool): IF True then return dictionary, otherwise return DataFrame
        """
        if asDict:
            return self._df.loc[rows].to_dict()         
        else:
            return self._df.loc[rows]

    def getRows(self,
                colStr : str,
                value,
                operator : comparisonTypes = comparisonTypes.equal) -> List[int]:
        """Get a list of rows (int) corresponding to the values in a column
        
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

    def getValue(self, colName : str, rowIdx : int):
        """Get a single value from a row and column.
        
        Returns
            (scalar) type is defined by types in self.columns[colName]
        """
        _ret = self.getValues(colName, rowIdx)
        if _ret is not None:
            return _ret[0]

    def getValues(self,
                    colName : List[str],
                    rowIdx : Union[int, List[int], None] = None,
                    ) -> Union[np.ndarray, None]:
        """Get value(s) from a column or list of columns.

        Args:
            colName (str | List(str)): Column(s) to get values from
            rowIdx (int | list(int)): Rows to get values from

        Returns:
            Annotation values (np.ndarray)
        """

        # ensure it is a list
        if not isinstance(colName, list):
            colName = [colName]

        # check column names exist
        if not self.columns.columnIsValid(colName):
            logger.error(f'did not find column name "{colName}"')
            return
            
        if rowIdx is None:
            rowIdx = range(self.numAnnotations)  # get all rows
        elif not isinstance(rowIdx, list):
            rowIdx = [rowIdx]

        df = self._df
        
        try:
            # TODO (cudmore) can't mix compareColName (reduceRows) and rowIdx
            ret = df.loc[rowIdx, colName].to_numpy(na_value=np.nan)
            #logger.info(f'ret:{type(ret)} {ret.shape}')
            #if len(colName)==1:
            if ret.shape[1]==1:
                ret = ret.flatten() # ensure 1D (for napari)
            return ret
        #except (IndexError) as e:
        #    logger.error(f'Did not find rows: "{rowIdx}"')
        #    return None
        #except (IndexingError) as e:
        #    logger.error(f'IndexingError: {e}')
        except (KeyError) as e:
            logger.error(f'bad rowIdx(s) {rowIdx}, colName:{colName} range is 0...{len(self)-1}')
            #print(traceback.format_exc())
            return None

    def getValuesWithCondition(self,
                    colName : Union[str, List[str]],
                    compareColNames : Union[str, List[str]],
                    comparisons : Union[comparisonTypes, List[comparisonTypes]],
                    #compareValues = Union[float, List[float]],
                    compareValues,
                    ) -> Union[np.ndarray, None]:
        """Get values from column(s) that match another column(s) value.

        Args:
            colName (str | List(str)): Column(s) to get values from
            compareColNames (str | List(str)): Columns to compare to
            comparisons (comparisonTypes | List(comparisonTypes)): Type of comparisons
            compareValues (???): We don't know the type. Could be (float, int, bool) or other?
        """

        if not isinstance(compareColNames, list):
            compareColNames = [compareColNames]
        if not isinstance(comparisons, list):
            comparisons = [comparisons]
        if not isinstance(compareValues, list):
            compareValues = [compareValues]

        # TODO: check that lists are same length (compareColName, comparisons, compareValues)
        _lists = [compareColNames, comparisons, compareValues]
        if not all(len(_lists[0]) == len(l) for l in _lists[1:]):
            logger.error(f'all parameters need to be the same length')
            return None

        #df = self._old_reduceRows(compareColName, comparisons, compareValues)
        
        # iteratively reduce df
        df = self._df
        for idx, compareColName in enumerate(compareColNames):
            comparison = comparisons[idx]
            compareValue = compareValues[idx]
            #print('compareColName:', compareColName, 'comparison:', comparison, 'compareValue:', compareValue)
            if comparison == comparisonTypes.equal:
                df = df[ df[compareColName]==compareValue ]
            # TODO (cudmore) add other comparisonTypes, can we use (==, <=, !=, etc) for all possible types?

        # df['index'] = df.index
        # colName += 'index'

        values = df.loc[:,colName].values
        if values.shape[1]==1:
            values = values.flatten() # ensure 1D (for napari)
        return values

    def _setModTime(self, row):
        """Called everytime a value is modified in the backend

        Args:
            row (int)
        """
        self._dataModified = True
        self._df.loc[row, 'mSeconds'] = time.time()  # modification time

    def setValue(self, colName : str, row : int, value):
        """Set a single value in a row and column.
        
        Args:
            colName (str)
            row (int)
            value (???)
        """
        self._setModTime(row)

        if not self.columns.columnIsValid(colName):
            logger.warning(f'did not find "{colName}" in columns')
            return
        try:
            self._df.at[row, colName] = value
        except(IndexError) as e:
            logger.error(f'did not set value for col "{colName}" at row {row}')

    def setColumn(self, colName : str, values : list):
        """Set all values in one column.

        args:
            values: a list of some type like (str, int, float)
        """
        #if not colName in self.columns.getColumnNames():
        if len(values) != len(self._df):
            logger.warning(f'incorrect length of "{len(values)}", length expected "{len(self._df)}"')
            return

        if not self.columns.columnIsValid(colName):
            logger.warning(f'did not find "{colName}" in columns')
            return
        self._df[colName] = values
            
    def _getDefaultRow(self):
        """Get a list of values for a default row (for one annotations).
        
        TODO (Cudmore) maybe specify type of all ColumnItem using s string like ('int', 'float', etc)
                        not sure how to test the type of a name like `float`
                        type(float) resolves to <class 'type'>
        """
        row = [None] * self.columns.numColumns()
        for colIdx, columnItem in enumerate(self.columns):
            theType = columnItem.getType()
            theTypeStr = str(theType)
            #logger.info(f'theType "{theType}" is type() {type(theType)}')
            if theType == 'Int64':
                # 'Int64' is pandas way to have an int64 with nan values
                # TODO (cudmore) switch this to pd.Int64Dtype
                row[colIdx] = float('nan')
            #elif isinstance(theType, float):
            elif theType == 'float':
                row[colIdx] = float('nan')
            elif theTypeStr == "<class 'float'>":
                row[colIdx] = float('nan')
            #elif isinstance(theType, str):
            elif theTypeStr == "<class 'str'>":
                row[colIdx] = ''
            #elif isinstance(theType, int):
            elif theTypeStr == "<class 'int'>":
                # int always needs a values, caller is required to fill in
                pass
            else:
                className = self.__class__.__name__  # name of class, including inherited
                logger.warning(f'{className} did not understand {columnItem.getName()} with type "{theType}"')
        #print(row)
        #theRet = [None] * len(self._df.columns)
        return row


    def addAnnotation(self, 
                    x : int, y : int, z : int,
                    #channel : Union[int,None] = None,
                    #rowIdx : Union[int,None] = None) -> int:
    ) -> int:
        """Add a new annotation at pixel (x,y,z).
        
        Args:
            x (int): Pixel
            y (int):
            z (int):
            channel (int): Image channel number for the annotation
            rowIdx (Union(int,None)): If specified then insert before the row index
                    otherwise, append

        Returns:
            (int) Added row (annotation) number.
        """

        rowIdx = self.numAnnotations

        self._df.loc[rowIdx] = self._getDefaultRow()

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
        
        self._setModTime(rowIdx)

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

        self._dataModified = True

    def addColumn(self, columnItem : ColumnItem, values = None):
        """Add a column.

            This includes adding column to 'Columns' object and to back end pd.DataFrame.
        """

        colName = columnItem.getName()
        theType = columnItem.getType()

        # if already exists, do not add
        if self.columns.columnIsValid(colName):
            className = self.__class__.__name__  # name of class, including inherited
            logger.warning(f'class {className} did not add column "{colName}", it already exists.')

        # add to columns
        self.columns.addColumn(columnItem)

        # add to dataframe
        self._df[colName] = values  # TODO: keep track of column types ?

        # TODO (cudmor) this type conversion on columns IS NOT NECCESSARY !?!?!
        # convert column to proper type
        if theType is None:
            pass
        elif theType == 'Int64':
            # without this sillyness, we get error
            # TypeError: cannot safely cast non-equivalent float64 to int64
            self._df[colName] = np.floor(pd.to_numeric(self._df[colName], errors='coerce')).astype('Int64')
        else:
            self._df[colName].astype(theType)

    def _resetIndex(self):
        """Reset pd.DataFrame row indexes. Needs to be done after inserting and deleting.
        
        Also need to reset our "index" column.
        """
        # Use the drop parameter to avoid the old index being added as a column
        self._df = self._df.reset_index(drop=True)
    
        self._df['index'] = list(range(self.numAnnotations))

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

    def importFromFile(self, funcDef, path, finalizeImport=False):
        """Import from file path using function fundef.
        
        Args:
            funcDef (def) A function that accepts path as parameter and returns
                (dict) header dictionary
                (pd.DataFrame) dataframe of annotations.
        """
        # TODO (cudmore) check that funcDef exists      
        #       check parametersignature that there is one param and it is type str          
        # TODO (cudmore) check that path exists

        # TODO (cudmore) check that we got back header:dict and df:pd.DataFrame
        # TODO (cudmore) add try ... else to catch errors if return has wrong number of elements

        header, df = funcDef(path)

        if finalizeImport:
            self.importFromData(header, df)

        return header, df

    def importFromData(self, header, df):
        """Import annotations from a function in pymapmanager.mmImport
        
        Args:
            funDef (def) function that takes a path and return (header, df)
            path (str) Path to file for import
        """
        logger.info('')

        # TODO (cudmore) check that header is a dict
        # TODO (cudmore) check that df is a pd.DataFrame
        
        # header
        for k,v in header.items():
            self.setHeaderVal(k, v)

        # data
        for columnItem in df.columns:
            columnName = columnItem.getName()
            if not columnName in df.columns:
                className = self.__class__.__name__  # name of class, including inherited
                logger.warning(f'{className} did not find expected column "{columnName}"')
                continue
            self.setColumn(columnName, df[columnName])

    def loadHeader(self):
        """Load header as dictionary.

        Header is always first line in file.

        TODO (cudmore) Some files might not have a header
        """
        
        #logger.info(f'loading header from {self.filePath}')
        
        header = {}
        
        with open(self.filePath) as f:
            headerLine = f.readline().rstrip()

        items = headerLine.split(';')
        for item in items:
            if item:
                k,v = item.split('=')
                # TODO: (cudmore) we need to know the type, for now just float
                header[k] = v
        
        #logger.info('')
        #pprint(header)

        self._header = header

        return header

    def load(self):
        """Load annotations from a file.

        Annotations are always in a comma seperated file with a one line header.

        TODO (cudmore) We will always load our native format, rely on `mmImport` to coerce into native.
        """
        
        if self.filePath is None:
            # no file yet
            return False
            
        if not os.path.isfile(self.filePath):
            logger.warning(f'Did not find annotation file: {self.filePath}')
            #raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), self.filePath)
            return

        logger.info(f'loading file:{self.filePath}')
        
        self.loadHeader()  # load one line header
        
        # this gives errors, too complex
        # typeDict = self._columns.getTypeDict()  # map column name to type
        #dfLoaded = pd.read_csv(self.filePath, header=1, index_col=False, dtype=typeDict)

        numHeaderRows = 1
        dfLoaded = pd.read_csv(self.filePath, header=numHeaderRows, index_col=False)

        # if there is no 'index' column, make one. This is critical.
        if not 'index' in dfLoaded.columns:
            dfLoaded['index'] = [idx for idx in range(len(dfLoaded))]

        loadedColumns = dfLoaded.columns

        # actually assign expected columns from loaded
        for columnItem in self.columns:
            columnName = columnItem.getName()
            if not columnName in loadedColumns:
                className = self.__class__.__name__  # name of class, including inherited
                logger.warning(f'class {className} did not find expected column name "{columnName}"')
                continue

            self._df[columnName] = dfLoaded[columnName]  # this trashes our column types

        # TODO (cudmore) get rid of this column type checking
        # convert to proper type
        # for columnItems in self.columns:
        #     colName = columnItems.getName()
        #     theType = columnItems.getType()
        #     #logger.info(f'converting column "{colName}" to type:"{theType}"')
        #     if theType is None:
        #         pass
        #     elif theType == 'Int64':
        #         # without this sillyness, we get error
        #         # TypeError: cannot safely cast non-equivalent float64 to int64
        #         self._df[colName] = np.floor(pd.to_numeric(self._df[colName], errors='coerce')).astype('Int64')
        #     else:
        #         self._df[colName].astype(theType)

        # check if loaded df has unknown columns
        for loadedColumnName in loadedColumns:
            #if not loadedColumnName in self.columns.getColumnNames():
            if not self.columns.columnIsValid(loadedColumnName):
                className = self.__class__.__name__  # name of class, including inherited
                logger.warning(f'Loaded with unknown column name "{loadedColumnName}" in class "{className}"')
                # TODO (cudmore) consider adding to columns with type=None ???

        logger.info(f'  loaded df: rows: {len(self._df)} cols {len(self._df.columns)}')
        #pprint(self._df.head())

        return True
    
    def save(self, forceSave : bool = False):
        """Save underlying pandas.DataFrame.

        Args:
            forceSave: If true then save even if not dirty
        """
        if not self._dataModified and not forceSave:
            # if not modified, do not save
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
            self._df.to_csv(file, header=True, index=False, lineterminator = '\r')
        
    def _getHeaderStr(self):
        """Get header as string.
        
        ';' delimited list of key=value paurs
        """
        header = ''
        for k,v in self._header.items():
            header += f'{k}={v};'
        header += '\n'
        return header

if __name__ == '__main__':
    pass