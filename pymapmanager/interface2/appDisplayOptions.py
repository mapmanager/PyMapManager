from pymapmanager._logger import logger

class AppDisplayOptions():
    """Class to encapsulate all display options.
    
    Behaves just like a dict of dict.
    """
    def __init__(self):
        self._displayOptionsDict : dict = self._getDefaultDisplayOptions()

    def __getitem__(self, key):
        """Allow [] indexing with ['key'].
        """
        try:
            #return self._dDict[key]['currentValue']
            return self._displayOptionsDict[key]
        except (KeyError) as e:
            logger.error(f'{e}')

    def save(self):
        """Save dict to json file.
        """
        pass

    def load(self):
        """Load dict from json file.
        """
        pass

    def _getDefaultDisplayOptions(self):
        # TODO: make widget to display
        # TODO: make a version of this for analysis variables
        theDict = {}

        # interface.stackWidget
        theDict['windowState'] = {}
        theDict['windowState']['defaultChannel'] = 2
        theDict['windowState']['showContrast'] = False
        # TODO: add booleans for all our children (lineListWidget, pointListWidget)
        # TODO: add boolean for children in ImagePlotWidget (_myImage, _aPointPlot, _aLinePlot)
        theDict['windowState']['doEditSegments'] = False  # toggle in lineListWidget
        theDict['windowState']['left'] = 100  # position on screen
        theDict['windowState']['top'] = 100  # position on screen
        theDict['windowState']['width'] = 700  # position on screen
        theDict['windowState']['height'] = 500  # position on screen

        # TODO: pass into imageplotwidget
        theDict['windowState']['doSlidingZ'] = False  # added 20240706
        theDict['windowState']['zPlusMinus'] = 3
        
        # interface.pointPlotWidget
        theDict['pointDisplay'] = {}
        theDict['pointDisplay']['width'] = 2
        theDict['pointDisplay']['color'] = 'r'
        theDict['pointDisplay']['symbol'] = 'o'
        theDict['pointDisplay']['size'] = 8
        theDict['pointDisplay']['zorder'] = 4  # higher number will visually be on top
        # user selection
        theDict['pointDisplay']['widthUserSelection'] = 2
        theDict['pointDisplay']['colorUserSelection'] = 'y'
        theDict['pointDisplay']['symbolUserSelection'] = 'o'
        theDict['pointDisplay']['sizeUserSelection'] = 10
        theDict['pointDisplay']['zorderUserSelection'] = 10  # higher number will visually be on top

        # May 11, 2023 adding value to test
        theDict['pointDisplay']['zPlusMinus'] = 3

        # TODO:
        # Add stuff to control connected line plot
        theDict['spineLineDisplay'] = {}
        theDict['spineLineDisplay']['width'] = 3
        theDict['spineLineDisplay']['color'] = 'r'
        theDict['spineLineDisplay']['symbol'] = 'o'
        theDict['spineLineDisplay']['size'] = 5
        theDict['spineLineDisplay']['zorder'] = 7  # higher number will visually be on top

        # interface.linePlotWidget
        theDict['lineDisplay'] = {}
        theDict['lineDisplay']['width'] = 1
        theDict['lineDisplay']['color'] = 'b'
        theDict['lineDisplay']['symbol'] = 'o'
        theDict['lineDisplay']['size'] = 5
        theDict['lineDisplay']['zorder'] = 1  # higher number will visually be on top

        # user selection
        theDict['lineDisplay']['widthUserSelection'] = 2
        theDict['lineDisplay']['colorUserSelection'] = 'c'
        theDict['lineDisplay']['symbolUserSelection'] = 'o'
        theDict['lineDisplay']['sizeUserSelection'] = 9
        theDict['lineDisplay']['zorderUserSelection'] = 2  # higher number will visually be on top

        #
        theDict['lineDisplay']['zPlusMinus'] = 3
        # abj: 6/20
        theDict['lineDisplay']['radius'] = 3

        return theDict
