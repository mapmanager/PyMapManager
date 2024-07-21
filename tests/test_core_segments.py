import pytest

import pandas as pd
import geopandas as gpd

from mapmanagercore import MapAnnotations, MultiImageLoader
from mapmanagercore.data import getTiffChannel_1, getLinesFile, getSingleTimepointMap

from pymapmanager.annotations.baseAnnotationsCore import LineAnnotationsCore

def _getEmptyMap():
    # add image channels to the loader
    loader = MultiImageLoader()
    loader.read(getTiffChannel_1(), channel=0)

    map = MapAnnotations(loader.build())
    tp = map.getTimePoint(0)

    return tp

def test_segment():

    # 1) load segments from and grab points
    linesFile = getLinesFile()
    df = pd.read_csv(linesFile)

    s = gpd.GeoSeries.from_wkt(df['segment'])
    # print(type(s.loc[0]))  # shapely.geometry.linestring.LineString
    for row in range(len(s)):
        print(f'length of loaded segment {row} is: {s.loc[row].length}')

    dfXyz = s.get_coordinates(include_z=True)
    dfSegment = dfXyz[dfXyz.index==0]

    # 2) make an empty map
    tp = _getEmptyMap()

    segmentID = tp.newSegment()

    n = len(dfSegment)
    print('adding points n:', n)
    for row in range(n):
        x = int(dfSegment['x'].iloc[row])
        y = int(dfSegment['y'].iloc[row])
        z = int(dfSegment['z'].iloc[row])
        
        _len0 = tp.appendSegmentPoint(segmentID, x, y, z)
        
    print('_len0:', _len0)

    tp.segments[:]

    print('tp.segments[:]')
    print(tp.segments[:])

    # s = gpd.GeoSeries.from_wkt(tp.segments[:]['segment'])
    print('segment length:', tp.segments[:]['segment'].loc[0].length)
    print('rough tracing length:', tp.segments[:]['roughTracing'].loc[0].length)

def test_qt_segments():
    """Load zarr, test core segment
     - add a segment
     - add a point
     - rebuild main df and summary df
    """
    from pymapmanager import stack
    
    zarrPath = getSingleTimepointMap()
    _stack = stack(zarrPath)
    print(_stack)

    segments = _stack.getLineAnnotations()

    segmentID = segments.newSegment()

    x = 100
    y = 100
    z = 20
    _len0 = segments.appendSegmentPoint(segmentID, x, y, z)
    
    x += 20
    y += 20
    z += 5
    _len0 = segments.appendSegmentPoint(segmentID, x, y, z)

    # see if 1 point segment works
    # new segment does not show up until it has 2x points
    segments._buildDataFrame()
    # segments._buildSummaryDf()

    print(segments.getDataFrame())
    print(segments.getSummaryDf())
    
if __name__ == '__main__':
    # test_segment()
    test_qt_segments()