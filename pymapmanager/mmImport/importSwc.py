import os
from pprint import pprint

import pandas as pd
import numpy as np

from pymapmanager.annotations.pointAnnotations import pointAnnotations
from pymapmanager.stack import stack

from pymapmanager._logger import logger

def _import_swc(path : str):
    sep = ' '
    dfLoaded = pd.read_csv(path, header=0, index_col=False, sep=sep)
    
    prev = dfLoaded['prev']
    prevDiff = np.diff(prev)
    
    prevDiff = np.insert(prevDiff, obj=0, values=1, axis=0)
    
    dfLoaded['prevDiff'] = prevDiff
    dfLoaded['segmentID'] = 0

    columns = ['x', 'y', 'z', 'xVoxel', 'yVoxel', 'zVoxel',
        'segmentID', 'roiType']

    df = pd.DataFrame(columns=columns)

    # newSegmentRows is True on a row that starts a new segment
    newSegmentRows = np.where(prevDiff != 1)  # returns a tuple
    newSegmentRows = newSegmentRows[0]
    print('newSegmentRows:', newSegmentRows.shape, newSegmentRows[0:10])

    lastSegmentRow = 0
    segmentID = 0
    for idx, newSegmentRow in enumerate(newSegmentRows):
        if idx == 0:
            continue

        #numPnts = newSegmentRow - lastSegmentRow + 1
        dfLoaded.loc[lastSegmentRow:newSegmentRow, 'segmentID'] = segmentID
        
        # increment
        segmentID += 1
        lastSegmentRow = newSegmentRow

    #print('clean up newSegmentRows:', newSegmentRows[-2], len(dfLoaded))
    dfLoaded.loc[newSegmentRows[-1]:len(dfLoaded), 'segmentID'] = segmentID

    pprint(dfLoaded)

    import matplotlib.pyplot as plt
    dfLoaded.plot(y='prevDiff', kind='line')
    dfLoaded.plot(y='segmentID', kind='line')
    plt.show()

    return None, dfLoaded

def _convertLines():
    # file to import
    pointPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_l.txt'
    swcPath = '/Users/cudmore/Sites/PyMapManager/data/example_tracing.swc'

    # user specified import function
    header, df = _import_swc(swcPath)

    # make native
    tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = stack(tifPath)

    la = myStack.getLineAnnotations()

    # header
    #for k,v in header.items():
    #    la.setHeaderVal(k, v)

    # data
    for column in df.columns:
        #la[column] = df[column]
        print('  setting column:', column)
        la.setColumn(column, df[column])

    # save
    la.save(forceSave=True)

if __name__ == '__main__':
    _convertLines()
