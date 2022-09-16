"""
"""

from pprint import pprint
from typing import List, Union

import numpy as np
import pandas as pd

from qtpy import QtCore  

from pymapmanager._logger import logger
import napari_layer_table

from types import MethodType
def _my_update_displayed(self):
    """Monkey patched version of Napari function.
    
    This is a modified version of code found in _shape_list._update_displayed()

    See:
        self.lineLayer._data_view._update_displayed

    TODO:
        get a shape (type path) to display its points +/- current image plane.
    """
    
    """Update the displayed data based on the slice key."""
    # The list slice key is repeated to check against both the min and
    # max values stored in the shapes slice key.
    slice_key = np.array([self.slice_key, self.slice_key])

    # Slice key must exactly match mins and maxs of shape as then the
    # shape is entirely contained within the current slice.
    if len(self.shapes) > 0:
        doOriginal = False
        if doOriginal:
            self._displayed = np.all(self.slice_keys == slice_key, axis=(1, 2))
        else:
            #print('type(self.slice_keys <= slice_key)', type(self.slice_keys <= slice_key))
            #_tmp = self.slice_keys <= slice_key  # <class 'numpy.ndarray'>
            #print('  _tmp.shape', _tmp.shape)  # shape (5, 2, 1)
            #print(_tmp)
            #self._displayed = np.all(self.slice_keys <= slice_key, axis=(1, 2))
            #print('  slice_key:', type(slice_key), slice_key)
            _my_slice_range = 6
            _upper_slice_key = slice_key - _my_slice_range
            _lower_slice_key = slice_key + _my_slice_range
            self._displayed = np.all((self.slice_keys >= _upper_slice_key) & \
                                (self.slice_keys <= _lower_slice_key), axis=(1, 2))
    else:
        self._displayed = []
    disp_indices = np.where(self._displayed)[0]

    z_order = self._mesh.triangles_z_order
    disp_tri = np.isin(
        self._mesh.triangles_index[z_order, 0], disp_indices
    )
    self._mesh.displayed_triangles = self._mesh.triangles[z_order][
        disp_tri
    ]
    self._mesh.displayed_triangles_index = self._mesh.triangles_index[
        z_order
    ][disp_tri]
    self._mesh.displayed_triangles_colors = self._mesh.triangles_colors[
        z_order
    ][disp_tri]

    disp_vert = np.isin(self._index, disp_indices)
    self.displayed_vertices = self._vertices[disp_vert]
    self.displayed_index = self._index[disp_vert]

'''
logger.info('MONKEY')
import napari
#from napari.layers.shapes import _shape_list
#napari.layers.shapes._shape_list._update_displayed = _my_update_displayed
napari.layers.shapes._shape_list._update_displayed = MethodType(_my_update_displayed, 
                napari.layers.shapes._shape_list)
'''

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

        self._selected_data = set()

        self.buildInterface()
    
    def getSelectedSegmentID(self) -> Union[int, None]:
        """Return the selected segment.
        
        Currently limited to one segment
        """
        # self._selected_data is a set
        if len(self._selected_data)>1:
            logger.error('expecing _selected_data to have len()<=1')
            return None
        elif len(self._selected_data) == 1:
            return list(self._selected_data)[0]
        else:
            return None

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

        #napari.layers.shapes._shape_list._update_displayed = _my_update_displayed

        edge_width = 5  # TODO (cudmore) add to options
        edge_color = 'green' # TODO (cudmore) color each segmentID different
        self.lineLayer = self._viewer.add_shapes(
            plotSegments,
            ndim = ndim,
            shape_type = 'path',
            edge_width = edge_width, 
            edge_color = edge_color,  
            name = 'Tracing'
        )

        # monkey patch _update_displayed with our own function (_my_update_displayed)
        # 1
        #self.lineLayer._data_view._update_displayed = _my_update_displayed
        # 2
        #self.lineLayer._data_view._update_displayed = MethodType(_my_update_displayed,
        #                self.lineLayer._data_view._update_displayed)
        # 3
        # MethodType(newFunc, instance)
        self.lineLayer._data_view._update_displayed = MethodType(_my_update_displayed,
                        self.lineLayer._data_view)

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
        logger.info(f'action:{action} selection:{selection}')
        if action == 'select':
            self._selected_data = selection
        elif action == 'add':
            logger.info('TODO add to backend')
        elif action == 'delete':
            logger.info('TODO delete from backend')
        elif action == 'add':
            logger.info('TODO move in backend')
        else:
            logger.error(f'did not understand action: {action}')

    def old_on_select_line_in_viewer(self, event):
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
