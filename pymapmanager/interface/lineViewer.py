"""
"""

from pprint import pprint
from typing import List, Union

import numpy as np
import pandas as pd

from qtpy import QtCore  

from pymapmanager._logger import logger
import napari_layer_table

class lineViewer():
    """Display lineAnnotations in viewer .
    
    TODO: Allow editing of lines points and segments including (add, delete, move)
    
    Args:
        viewer: napari viewer
        pointAnnotations: pymapmanager.annotations.pointAnnotations
        options (dict) options dict
    """
    def __init__(self, viewer, lineAnnotations, options):
        self._viewer = viewer
        self._lineAnnotations = lineAnnotations
        self._options = options

        self.buildInterface()
    
    @property
    def lineAnnotations(self):
        return self._lineAnnotations
       
    def buildInterface(self):
        # line as a shapes layer
        # does not work because if shape is spanning multiple z image planes, we do not see it in x/y view !!!
        xyzSegments = self.lineAnnotations.getSegment_xyz() # list of (z,y,x) segments
        plotSegments = []
        for xyzSegment in xyzSegments:
            if len(xyzSegment) < 2:
                # TODO (cudmore) fix this, shape layer does not accept path of len() 1
                continue
            plotSegments.append(xyzSegment)

        logger.info(f'xyzSegments has {len(xyzSegments)} segments')
        
        #print(f'  calling add_shapes with plotSegments: {len(plotSegments)}')
        
        if len(plotSegments) == 0:
            # no segments, how do we make a shape layer that is empty?
            #logger.error('NO SEGMENTS, NOT BUILDING')
            # need to pass None, not []
            plotSegments = None

        ndim = 3

        edge_width = 5  # TODO (cudmore) add to options
        self.lineLayer = self._viewer.add_shapes(
            plotSegments,
            ndim = ndim,
            shape_type = 'path',
            edge_width = edge_width, 
            #edge_color='green'  # TODO (cudmore) color each segmentID different
            name = 'Tracing'
        )

        #self.lineLayer.events.highlight.connect(self.on_select_line_in_viewer)

        # TODO (cudmore) once napari-layer-table handes shapes ... use it
        self.lineTable = napari_layer_table.LayerTablePlugin(self._viewer,
                                oneLayer=self.lineLayer,
                                onAddCallback=self.on_add_line_callback)

        self.lineTable.signalDataChanged.connect(self.on_user_edit_lines)

        # show
        area = 'right'
        name = 'Line Annotations'
        self._dockWidget = self._viewer.window.add_dock_widget(self.lineTable, 
                            area=area, name=name)

    def on_add_line_callback(self, selection: set,
                    df: pd.DataFrame) -> Union[None,dict]:
        """ Decide if we want to add a lines.
        """
        return None

    def on_user_edit_lines(self, action : str,
                    selection: set,
                    df: pd.DataFrame):
        """Respond to users edits and modify internal dta.
        """
        logger.info('')
    
    def on_select_line_in_viewer(self, event):
        """Shape/line layer selection.
        """
        logger.info('')
        
        layer = event.source
        
        if len(layer.data) == 0:
            logger.info(f'  NO DATA: len is {len(layer.data)} with type {type(layer.data)}')
            return
        
        selected_data = layer.selected_data

        print('  layer:', layer)
        print('  selected_data:', selected_data)
        print('  type(layer.data):', type(layer.data))  # list of np.ndarray (rows/shapes/lines, 3)
        
        # data is a list of np.ndarray
        # is ndarray is Mxn with M:num points, n:num dim
        # basically [z, y, x]
        print('  data[0]:', type(layer.data[0]), layer.data[0].shape)
        #print('    ', layer.data[0])

        for idx, shape in enumerate(layer.data):
            print('  shape idx', idx, 'has shape:', shape.shape)
            zMean = np.mean(shape[:,0])
            yMean = np.mean(shape[:,1])
            xMean = np.mean(shape[:,2])
            
        #print(vars(layer))

    def on_segmentid_popup(self, currentSegment):
        logger.info(f'currentSegment:{currentSegment}')

        # filter table
        self.filterBySegmentType(currentSegment)
    
    def filterBySegmentType(self, segmentID :str):
        segmentColIdx = self.lineTable.myTable2.getColumns().get_loc('segmentID')
        if segmentID == 'All':
            # Match all with QRegExp is empty string ''
            segmentID = ''   # '(.)*' # '[^\n]*' #"(.*?)" #'(?s:.)'  # '(.*?)' '(?s:.)'
        logger.info(f'matching segmentID column to reg exp roiType:"{segmentID}"')
        self.lineTable.myTable2.proxy.setFilterRegExp(QtCore.QRegExp(segmentID,
                                        QtCore.Qt.CaseInsensitive,
                                        QtCore.QRegExp.FixedString));
        self.lineTable.myTable2.proxy.setFilterKeyColumn(segmentColIdx);
