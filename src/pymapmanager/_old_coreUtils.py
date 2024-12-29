import time
import numpy as np
import pandas as pd

from mapmanagercore import MapAnnotations
from pymapmanager._logger import logger

def getPlotDict_mpl():
    """Get a new default plot dictionary.

    The plot dictionary is used to tell plot functions what to plot (e.g. ['xstat'] and ['ystat']).
    
    All plot function return the same plot dictionary with keys filled in with values that were plotted
    (e.g. ['x'] and ['y']).
    
    Example::
    
    	import mapmanagercore.data
        from mapmanagercore import MapAnnotations
        from pymapmanager.coreUtils import getPlotDict_mpl, getMapValues3
    	
    	path = mapmanagercore.data.getMultiTimepointMap()
    	map = MapAnnotations.load(self.path)
    	plotdict = getPlotDict_mpl()
    	plotdict['xstat'] = 'days'
    	plotdict['ystat'] = 'pDist' # position of spine on its parent segment
    	plotdict = getMapValues3(mmmap, plotdict)
    	
    	# display with matplotlib
    	plotdict['x']
    	plotdict['y']
    	
    """
    PLOT_DICT = {
        'map' : None, #: map (object) mmMap
        'mapname' : None,
        'sessidx' : None, #: sessIdx (int): map session
        'stack' : None, #: stack (object) use for single timepoint analysis

        'xstat' : None, #: xstat (str): Name of statistic to retreive, corresponds to column in stack.stackdb
        'ystat' : None,
        'zstat' : None,
        'roitype' : ['spineROI'], #: roiType
        'segmentid' : [],

        'stacklist' : [],   # list of int to specify sessions/stacks to plot, [] will plot all

        'getMapDynamics' : True, # set True to get map 'dynamics'
        
        'plotbad' : True,
        'plotintbad' : False,
        'showlines' : True,
        'linewidth': 1,
        'showdynamics': True,
        'markersize' : 15,
        'doDark': True,

        #  Filled in by get functions
        'x' : None,
        'y' : None,
        'z' : None,
        'stackidx' : None,
        'reverse' : None,
        'runrow': None,
        'mapsess': None,
    }
    return PLOT_DICT

def buildConnectDataframe(mapAnnotations : MapAnnotations, tp1, tp2, segmentID):
    """Build a DataFrame for connecting spines
    """
    
    # full dataframe
    df = mapAnnotations.points[:]
    df = df.reset_index()

    # reduce to tp1, segmentID
    dfTp1 = df[ (df['t']==tp1) & (df['segmentID']==segmentID)]

    columns = ['Pre ID', 'Pre Pos', 'Post ID', 'Post Pos', 'Distance']
    dfRet = pd.DataFrame(columns=columns)

    # step 1, make a df with tp1
    dfRet[['Pre ID', 'Pre Pos']] = dfTp1[['spineID', 'spinePosition']]
    
    # used to append tp2 spineID not in tp1 (added spines)
    appendRowList = []

    # step 2, insert values of connected spines from tp2 into tp1
    dfTp2 = df[ (df['t']==tp2) & (df['segmentID']==segmentID)]
    for index, row in dfTp2.iterrows():
        postID = row['spineID']
        postSpinePosition = row['spinePosition']

        # find tp2 row in tp1
        rowTp1 = dfRet.loc[dfRet['Pre ID'] == postID]
        if len(rowTp1) > 1:
            logger.error(f'got more than one row {rowTp1}')
        elif len(rowTp1) == 1:
            # assign
            dfRet.loc[rowTp1.index, 'Post ID'] = postID
            dfRet.loc[rowTp1.index, 'Post Pos'] = postSpinePosition

            preSpinePosition = dfRet.loc[rowTp1.index, 'Pre Pos']
            dist = postSpinePosition - preSpinePosition
            dfRet.loc[rowTp1.index, 'Distance'] = dist

        else:
            # append to end
            appendRowList.append({
                'Post ID': postID,
                'Post Pos': postSpinePosition
            })
    
    # works if appendRowList is []
    dfRet = pd.concat([dfRet, pd.DataFrame(appendRowList)], ignore_index=True, sort=False)

    # round results
    decimals = 2    
    dfRet['Pre Pos'] = dfRet['Pre Pos'].apply(lambda x: round(x, decimals))
    dfRet['Post Pos'] = dfRet['Post Pos'].apply(lambda x: round(x, decimals))
    dfRet['Distance'] = dfRet['Distance'].apply(lambda x: round(x, decimals))

    # print(dfRet)
    return dfRet

def getMapValues3(mapAnnotations : MapAnnotations,  plotDict : dict):
    """Get values of a stack annotation across all stacks in the map.

    Args:
        plotDict (dict):
            A plot dictionary describing what to plot.
            Get default from getPlotDict_mpl().

    Returns:

        | pd['x'], 2D ndarray of xstat values, rows are runs, cols are sessions, nan is where there is no stackdb annotation
        | pd['y'], same
        | pd['z'], same
        | pd['stackidx'], Each [i]j[] gives the stack centric index of annotation value at [i][j].
        | pd['mapsess'], Each [i][j] gives the map session of value at annotation [i][j].
        | pd['runrow'],

    """
    startTime = time.time()

    segmentID = plotDict['segmentid']
    xStat = plotDict['xstat']
    yStat = plotDict['ystat']

    logger.info(f'fetching plot dict for segmentID:{segmentID} xStat:{xStat} yStat:{yStat}')

    df = mapAnnotations.points[:]
    
    # move row labels (spineID, t) to columns
    df = df.reset_index()

    # logger.info('df is:')
    # print(df)

    # reduce to segment id
    df = df[ df['segmentID']==segmentID]

    # scatter
    xPlot = df[xStat].to_list()
    yPlot = df[yStat].to_list()
    
    # each point in scatter has a spine id
    # Note: spineID goes across timepoints
    xyPlotSpineID = df['spineID'].to_list()

    # each spineID has a timepoint
    xyPlotTimepoint = df['t'].to_list()

    # each spine has a segment
    xySegmentID = df['segmentID'].to_list()

    xyAccept = df['accept'].to_list()

    markerColor = ['w'] * len(xyPlotSpineID)
    # lines
    
    #new
    xSpineLineDict = {}
    ySpineLineDict = {}
    spineRunDict = {}

    spineIDs = df['spineID'].unique()  # step through connected spineID
    xPlotLines = []
    yPlotLines = []
    for spineID in spineIDs:
        # spineID = int(spineID)
        
        # grab rows of a spineID (across timepoints)
        spineDf = df[ df['spineID']== spineID]
        
        xPlotLine = spineDf[xStat].to_list()
        yPlotLine = spineDf[yStat].to_list()
        
        # this is redundant, merge with xPlineLineDict
        xPlotLines.append(xPlotLine)
        yPlotLines.append(yPlotLine)
        
        spineID_int = int(spineID)
        xSpineLineDict[spineID_int] = xPlotLine
        ySpineLineDict[spineID_int] = yPlotLine
        
        spineRunDict[spineID_int] = spineDf.index.astype(int)

        # set color dynamics
        xt = spineDf['t'].to_list()
        if len(xt) == 1:
            # transient
            _x1 = np.where((np.array(xyPlotSpineID==spineID)))[0]
            markerColor[_x1[0]] = 'b'
        else:
            if xt[0] != 0:
                # added
                _x1 = np.where((np.array(xyPlotSpineID==spineID)))[0]
                markerColor[_x1[0]] = 'g'
            if xt[-1] != 4:
                # deleted
                _x1 = np.where((np.array(xyPlotSpineID)==spineID) & (np.array(xyPlotTimepoint)==xt[-1]))[0]
                # logger.info(f'spineID:{spineID} at tp {xt[-1]} is SUBTRACTED _finalIndex:{_finalIndex}')
                markerColor[_x1[0]] = 'r'
            
    # return values
    
    # old
    plotDict['x'] = xPlot
    plotDict['y'] = yPlot
    plotDict['xyPlotSpineID'] = xyPlotSpineID
    plotDict['xyPlotTimepoint'] = xyPlotTimepoint
    plotDict['xPlotLines'] = xPlotLines
    plotDict['yPlotLines'] = yPlotLines

    plotDict['markerColor'] = markerColor

    plotDict['xSpineLineDict'] = xSpineLineDict
    plotDict['ySpineLineDict'] = ySpineLineDict
    plotDict['spineRunDict'] = spineRunDict

    # new
    # dfPlot = pandas.DataFrame()
    # dfPlot['x'] = xPlot
    # dfPlot['y'] = yPlot
    # dfPlot['spineID'] = xyPlotSpineID
    # dfPlot['timepoint'] = xyPlotTimepoint
    # dfPlot['segmentID'] = xySegmentID
    # dfPlot['dynamics'] = ''
    # dfPlot['dynamics'] = xyAccept
    
    # pd['dfPlot'] = dfPlot

    stopTime = time.time()
    logger.info(f'   took:{round(stopTime - startTime, 2)} seconds')

    return plotDict

class ConnectSpines:
    def __init__(self, map, tp1, tp2, segmentID):
        self.tp1 = tp1
        self.tp2 = tp2
        self.segmentID = segmentID

        #columns = ['Pre ID', 'Pre Pos', 'Post ID', 'Post Pos', 'Distance']
        self.df = buildConnectDataframe(map, tp1, tp2, segmentID)

    # does not make sense, spines with the same id are always connected?
    def isConnected(self, preSpineID, postSpineID) -> bool:
        row = self.df[ self.df['Pre ID']==preSpineID ]

    def connect(self, preSpineID, postSpineID):
        """
        If preSpineID has a post spine, append it to the end.
        If postSpineID has a pre, remove post from pre row
        """
        
        logger.info(f'preSpineID:{preSpineID} postSpineID:{postSpineID}')

        # if pre is connected to post pre and post row will be the same
        preRow = self.df[ self.df['Pre ID']==preSpineID ]
        if len(preRow.index) == 0:
            logger.error(f'did not find preSpineID: {preSpineID}')
            return
        
        postRow = self.df[ self.df['Post ID']==postSpineID ]
        if len(postRow.index) == 0:
            logger.error(f'did not find postSpineID: {postSpineID}')
            return

        print('=== preRow')
        print(preRow)
        print('=== postRow')
        print(postRow)

        preHasPost = not pd.isna(preRow['Post ID'].values[0])
        print(f'   preHasPost:{preHasPost}')

        postHasPre = not pd.isna(postRow['Pre ID'].values[0])
        print(f'   postHasPre:{postHasPre}')

    def disconnect(self, preSpineID, postSpineID):
        pass

    def addSpine(self, tp, spineID):
        if tp == self.tp1:
            tp = self.tp1
        elif tp == self.tp2:
            tp = self.tp2
        else:
            logger.error(f'tp {tp} is not in [{self.tp1}, {self.tp2}]')
            return
    
    def deleteSpine(self, tp, spineID):
        """If deleting from tp1 and we have post spine, append it to the end.
        """
        if tp == self.tp1:
            tp = self.tp1
        elif tp == self.tp2:
            tp = self.tp2
        else:
            logger.error(f'tp {tp} is not in [{self.tp1}, {self.tp2}]')
            return

if __name__ == '__main__':
    logger.setLevel('DEBUG')
    from mapmanagercore import MapAnnotations
    import mapmanagercore.data
    
    path = mapmanagercore.data.getMultiTimepointMap()

    map : MapAnnotations = MapAnnotations.load(path)

    tp1 = 1
    tp2 = 2
    segmentID = 0
    buildConnectDataframe(map, tp1, tp2, segmentID)
    cs = ConnectSpines(map, tp1, tp2, segmentID)
    print(cs.df)

    cs.connect(3, 278)
    # cs.connect(1, 1)