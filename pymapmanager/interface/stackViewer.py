"""A MapManager stack viewer using napari.    
"""

from pprint import pprint
from typing import List, Union  # Callable, Iterator, Optional

import numpy as np
import pandas as pd

from qtpy import QtCore, QtWidgets  # , QtGui
import napari

import pymapmanager
from pymapmanager.annotations.pointAnnotations import pointTypes
from pointViewer import pointViewer
from lineViewer import lineViewer

import napari_layer_table

from pymapmanager._logger import logger

# TODO: (cudmore) this needs to go into options class
# TODO (cudmore) save/load this dict as JSON and use as user configured program options
# a dictionary of point annotations display properties like (size, color)
options = {
    'pointsDisplay' : {
        'spineROI' : {'size': 5, 'face_color': [1., 0, 0, 1], 'shown': True},
        # TODO: (cudmore) fix type from globalPIvot (I) to globalPivot (i)
        'globalPIvot' : {'size': 3, 'face_color': [1., 0., 1., 1.], 'shown':True},
        #'globalPivot' : {'size': 3, 'face_color': 'magenta', 'shown':False},
        'pivotPnt' : {'size': 3, 'face_color': [1., 0., 1., 1.], 'shown':True},
        'controlPnt' : {'size': 3, 'face_color': [0., 0., 1., 1.],'shown':True},

        # line annotations
        'linePnt' : {'size': 2, 'face_color': [0., 1., 0., 1.],'shown':True},
    },
    'pointSelection' : {
        'selectionMult' : 3,
    },
}  # options

class mmViewer():
    """ A viewer to visualize a 3D image volume and its assocaiated annotation.
   
        stack: The 3D image volume
        points:
        lines:
     """
    def __init__(self, tifPath):
        
        self._tifPath = tifPath
        
        # load the stack
        self._stack = pymapmanager.stack.stack(tifPath)
        print(self._stack)

        self.buildInterface()

        # testing if import of (points, lines) works from mapmanager-igor
        # self.tmpTestImport()

    def buildInterface(self):
        self._viewer = napari.Viewer()

        image = self._stack.getImageChannel(1)
        self._viewer.add_image(image)

        # to hide napari interface panels
        # see: https://forum.image.sc/t/is-it-possible-to-open-the-napari-viewer-with-the-layer-controls-and-layer-list-gui-elements-hidden/47755
        '''
        showDockLayerList = True
        showDockLayerControls = True
        self._viewer.window.qt_viewer.dockLayerList.setVisible(showDockLayerList)
        self._viewer.window.qt_viewer.dockLayerControls.setVisible(showDockLayerControls)
        '''

        #  Order matters, last built will be selected

        self._pointViewer = pointViewer(self._viewer,
                                self._stack.getPointAnnotations(),
                                options)

        self._lineViewer = lineViewer(self._viewer,
                                self._stack.getLineAnnotations(),
                                options)

        #self.testPlugin()

    @property
    def stack(self):
        return self._stack

    @property
    def viewer(self):
        return self._viewer

    def tmpTestImport(self):
        """This will import mapmanager-igor into the stack.
        """
        logger.info('testing import')

        #
        # points
        from pymapmanager.mmImport.import_mm_igor import _import_points_mapmanager_igor
        funcDef = _import_points_mapmanager_igor
        #annotationType = 'point'
        path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_db2.txt'
        #header, df = self._stack.importFromFile(annotationType, funcDef, path)
        #header, df = self._stack.importFromFile(annotationType, funcDef, path)
        header, df = _import_points_mapmanager_igor(path)
        # TODO (cudmore) ask user if OK
        self._stack.getPointAnnotations().importFromData(header, df)

        #
        # lines
        from pymapmanager.mmImport.import_mm_igor import _import_lines_mapmanager_igor
        #annotationType = 'lines'
        funcDef = _import_lines_mapmanager_igor
        path = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_import_mm_igor/rr30a_s0_l.txt'
        #self._stack.importFromFile('lines', funcDef, path)
        #header, df = self._stack.importFromFile(annotationType, funcDef, path)
        header, df = _import_lines_mapmanager_igor(path)
        # TODO (cudmore) ask user if OK
        #self._stack.importFromData(annotationType, header, df)
        self._stack.getLineAnnotations().importFromData(header, df)

    def testPlugin(self):
        # all of our points will be in slice 'zSlice'
        zSlice = 15

        # set viewer to slice zSLice
        #axis = 0
        #viewer.dims.set_point(axis, zSlice)

        # create 3D points
        points = np.array([[zSlice, 10, 10], [zSlice, 20, 20], [zSlice, 30, 30], [zSlice, 40, 40]])

        # create a points layer from our points
        size = [[30,30,30], [30,30,30], [30,30,30], [30,30,30]]
        face_color =  [[1., 0, 0, 1], [1., 0, 0, 1], [1., 0, 0, 1], [1., 0, 0, 1]]
        shown = [True, True, True, True]
        pointsLayer = self._viewer.add_points(points,
                                size=size, 
                                face_color=face_color, 
                                shown=shown,
                                name='debug magenta circles')
        #print(type(pointsLayer))

        # add some properties to the points layer (will be displayed in the table)
        pointsLayer.properties = {
            'Prop 1': ['a', 'b', 'c', 'd'],
            'Prop 2': [True, False, True, False],
        }

        # set the layer to 'select' mode (not needed)
        pointsLayer.mode = 'select'

        # create the plugin.
        #ltp = LayerTablePlugin(viewer, oneLayer=pointsLayer)
        self._tmpTestPlugin = napari_layer_table.LayerTablePlugin(self._viewer, oneLayer=pointsLayer)

        # add the plugin to the viewer
        area = 'right'
        name = 'Debug Layer Table'
        self._dockWidget2 = self._viewer.window.add_dock_widget(self._tmpTestPlugin, area=area, name=name)

def run():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # works, has line and point annotations, 20220416
    tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    
    # test a tif stack with no annotations
    #tifPath = '/Users/cudmore/Sites/PyMapManager-Data/empty-time-point/rr30a_s0_ch2.tif'

    mmv = mmViewer(tifPath)

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
