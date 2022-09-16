"""
"""
from pprint import pprint
from typing import List, Union

import numpy as np
import pandas as pd

from qtpy import QtCore, QtWidgets  

import pymapmanager
from pymapmanager.annotations.pointAnnotations import pointTypes
import napari_layer_table

from pymapmanager._logger import logger

class pointViewer():
    """Display pointAnnotations in viewer and manager a table plugin.
    
    Allow editing of points including (add, delete, move)
    
    Args:
        viewer: napari viewer
        pointAnnotations: pymapmanager.annotations.pointAnnotations
        options (dict) options dict
    """
    def __init__(self, parent, viewer, pointAnnotations, options : dict):
        self._parent = parent  # pymapmanager.interface.stackViewer
        self._viewer = viewer  # napari.viewer
        self._pointAnnotations = pointAnnotations  # pymapmanager.annotations.pointAnnotations
        self._options = options  # dict

        self._units = 'um'  # ('points', 'um')
        
        self._currentRoi = 'All'
        # set by popup, can be 'All'

        self._selected_data = set()
        """Selected point in point annotations"""

        self.buildInterface()

    def getSelectedPointIdx(self):
        return self._selected_data

    '''
    def _myfilterLayerList(self, row, parent):
        """Filter out (hide) layers.
        """
        logger.info('')
        return "<hidden>" not in self._viewer.layers[row].name
    '''
    
    def buildInterface(self):
        pointAnnotations = self._pointAnnotations
                
        colName = ['z', 'y', 'x']
        xyz = pointAnnotations.getValues(colName)
        
        numAnnotations = pointAnnotations.numAnnotations

        shownList = [True] * numAnnotations
        faceColorList = [[1., 0, 0, 1]] * numAnnotations  # like [1., 0, 0, 1]
        sizeList = [5] * numAnnotations

        # TODO (cudmore) get rid of loop, use list comprehension
        for row in range(numAnnotations):
            # point annotations have multiple roi types, each with different color/size
            roiType = pointAnnotations.at[row, 'roiType']
            #segmentID = pointAnnotations.at[row, 'segmentID']

            shown = self._options['pointsDisplay'][roiType]['shown']
            color = self._options['pointsDisplay'][roiType]['face_color']
            size = self._options['pointsDisplay'][roiType]['size']

            shownList[row] = shown
            faceColorList[row] = color
            sizeList[row] = size
            
        ndim = 3

        # add some features
        features = {
            'roiType': pointAnnotations.getValues('roiType'),
            'segmentID': pointAnnotations.getValues('segmentID')
        }

        # selection layer
        name = 'Point Selection <hidden>'
        self.pointsLayerSelection = self._viewer.add_points(name=name,
                                        ndim = 3)

        # hide our pointsLayerSelection in the viewer layer list
        #self._viewer.window.qt_viewer.layers.model().filterAcceptsRow = self._myfilterLayerList

        '''
        if self._units == 'points':
            scale = [1, 1, 1]
        elif self._units == 'um':
            scale = [1, 0.12, 0.12]
        '''

        self.pointsLayer = self._viewer.add_points(xyz,
                            ndim = ndim,
                            #scale = scale,
                            size = sizeList,
                            face_color = faceColorList,
                            shown = shownList,
                            #text=f'{roiType}',
                            features = features,
                            name = 'Point Annotations')

        self.pointsLayer.mode = 'select'
        
        # to visually select in our seletion layer
        #self.pointsLayer.events.highlight.connect(self.on_select_point_in_viewer)

        # when creating with oneLayer, the plugin will not switch layers
        self.pointsTable = napari_layer_table.LayerTablePlugin(self._viewer,
                                oneLayer=self.pointsLayer,
                                onAddCallback=self.on_add_point_callback)
        
        # receive (add, delete, move)
        self.pointsTable.signalDataChanged.connect(self.on_user_edit_points)

        # only allow new points with shift-click when a pointType is selected
        # see: self.on_roitype_popup() where we turn this off when 'All' is selected
        #self.pointsTable._shift_click_for_new = False
        #self.pointsTable._updateMouseCallbacks()
        self.pointsTable.newOnShiftClick(False)
        
        # add to vlayout
        vlayout = self.pointsTable.layout()

        hLayout = QtWidgets.QHBoxLayout()
        
        label = QtWidgets.QLabel('Type')
        
        popup = QtWidgets.QComboBox()
        popup.setToolTip('Specify roi types to display')
        # TODO (cudmore) use all items in pointAnnotations.pointTypes
        #roiItems = [e.value for e in pymapmanager.annotations.pointAnnotations.pointTypes]
        roiItems = [e.value for e in pointTypes]
        roiItems.insert(0, 'All')
        popup.addItems(roiItems)
        popup.currentTextChanged.connect(self.on_roitype_popup)

        hLayout.addWidget(label)
        hLayout.addWidget(popup)

        vlayout.insertLayout(1, hLayout)

        # filter based on roiType
        self.filterByRoiType('All')

        # show
        area = 'right'
        name = 'Point Annotations'
        self._dockWidget = self._viewer.window.add_dock_widget(self.pointsTable, 
                            area=area, name=name)

    def on_add_point_callback(self, rows : set, properties : pd.DataFrame) -> Union[None, dict]:
        """Callback from layer-table-plugin.
        
        User added a new point annotation.
        
        Return the (properties, face_color, size) of the new point.
                
        1) Problem is, on new point in napari, if layer has properties
        the new point properties are just from the last point (before the add).

        2) also have to set layer (face_color, size)
        """
        
        logger.info('')
        
        currentPointType = self._currentRoi  # selection in display popup
        
        if currentPointType == 'All':
            logger.info(f'rejecting on "{currentPointType}"')
            return None

        # spineROI requires a segment ID
        segmentID = self._parent.getSelectedSegmentID()
        if currentPointType == 'spineROI' and segmentID is None:
            logger.info(f'rejecting on "{currentPointType}" and segmentID: {segmentID}')
            return None

        returnDict = {}
        
        # modify
        #properties['roiType'][rows] = currentPointType
        returnDict['roiType'] = currentPointType
        returnDict['segmentID'] = segmentID

        # face_color
        size = self._options['pointsDisplay'][currentPointType]['size']
        face_color = self._options['pointsDisplay'][currentPointType]['face_color']
        
        returnDict['face_color'] = face_color
        returnDict['size'] = size

        return returnDict

    def on_user_edit_points(self,
                    eventType : str,
                    selection : set,
                    df : pd.DataFrame):
        """Respond to edits coming from the napari viewer.

        This includes (add, delete, move, select). Maybe more?

        Args:
            df (pd.DataFrame): 
        """
        selectionList = list(selection)
        listOfDict = df.to_dict('records')
        
        # TODO (cudmore) on 'move' need to update position in 'selection layer'
        logger.info('')
        print('  eventType:', eventType)
        pprint(df)

        pointAnnotations = self._pointAnnotations

        if eventType =='add':
            for rowDict in listOfDict:
                #rowIdx = rowDict['rowIdx']
                roiTypeStr = rowDict['roiType']
                x = rowDict['x']
                y = rowDict['y']
                z = rowDict['z']
                
                # add point annotation
                roiType = pointTypes[roiTypeStr]
                segmentID = None
                pointAnnotations.addAnnotation(roiType, segmentID, x, y, z)
                
            self.refreshPointSelection(selectionList)

            self.checkPointState()

        elif eventType =='delete':
            '''
            rowList = []
            for rowDict in listOfDict:
                rowIdx = rowDict['rowIdx']
                rowList.append(rowIdx)
            '''

            # delete point annotation
            print(f'  deleting rows {selectionList}')
            pointAnnotations.deleteAnnotation(selectionList)

            noSelection = []
            self.refreshPointSelection(noSelection)

            self.checkPointState()

        elif eventType =='change':
            #rowList = []
            #for _rowIdx, rowDict in enumerate(listOfDict):
            for _dictIdx, _rowIdx in enumerate(selectionList):
                rowDict = listOfDict[_dictIdx]
                x = rowDict['x']
                y = rowDict['y']
                z = rowDict['z']
                
                # move point
                pointAnnotations.setValue('x', _rowIdx, x)
                pointAnnotations.setValue('y', _rowIdx, y)
                pointAnnotations.setValue('z', _rowIdx, z)
                
                #rowList.append(rowIdx)

            # move selection
            # TODO (cudmore) is this needed? Did viewer already handle this?
            self.refreshPointSelection(selectionList)

            self.checkPointState()

        elif eventType == 'select':
            selectionList = list(selection)
            self.refreshPointSelection(selectionList)

    def refreshPointSelection(self, selectedRowList : List[int]):
        """Refresh the selected points.
        
        Args:
            selectedRowList: List to select, if [] then cancel selection
        """
        #logger.info(f'selectedRowList {selectedRowList}')
        
        selectionMult = self._options['pointSelection']['selectionMult']
        
        # fetch value from data layer
        layer = self.pointsLayer
        newSelectedPoints = layer.data[selectedRowList]
        newSelectedPoints = np.array(newSelectedPoints)
        newSelectedSize = layer.size[selectedRowList] * selectionMult

        # set in selection layer
        self.pointsLayerSelection.data = newSelectedPoints
        self.pointsLayerSelection.size = newSelectedSize
        self.pointsLayerSelection.face_color = [1, 1, 0, 1]  # yellow
        
    def old_on_select_point_in_viewer(self, event):
        """Respond to point selection in viewer.
        
        Increase the size of selected point and change their color.

        Using a selection layer `pointsLayerSelection`
        
        Note:
            Extend to both point and line selection.
            Need to add an 'roiType' column to line annotations
        """
                        
        logger.info('  REMOVE THIS !!!!')
        return
        
        layer = event.source
        selected_data = layer.selected_data  # new selection
        if not pymapmanager.utils.setsAreEqual(selected_data, self._selected_data):
            logger.info(f'new selected_data {selected_data}')

            # keep track of our current selection
            self._selected_data = selected_data

            selectedDataList = list(selected_data)
            self.refreshPointSelection(selectedDataList)
            
            # This is unstable in napari, sometimes needed, sometimes not???
            # we need this to update the interface
            # this triggers events and causes error if we arrived her on 'new'
            #self.pointsLayerSelection.events.face_color()

    def on_roitype_popup(self, currentRoiType):
        """Filter the point annotation list of roi
        
        Only show roiType equal to currrentRoiType
        """
		
        logger.info(f'currentRoiType:{currentRoiType}')

        self._currentRoi = currentRoiType  # can be all

        # want to toggle new points with shift click
        # turn shift+click on/off in table plugin
        turnOn = currentRoiType != 'All'
        self.pointsTable.newOnShiftClick(turnOn)

        # filter table
        self.filterByRoiType(currentRoiType)

        # show/hide points in viewer/layer
        if currentRoiType == 'All':
            shownMask = [True] * self._pointAnnotations.numAnnotations
        else:
            shownMask = self._pointAnnotations.getDataFrame()['roiType'] == currentRoiType
        self.pointsLayer.shown = shownMask

        self.pointsLayer.events.face_color()  # trigger refresh, there must be a better way

    def filterByRoiType(self, roiType :str):
        """Filter 'roiType' column with only values of roiType
        """
        try:
            roiColIdx = self.pointsTable.myTable2.getColumns().get_loc('roiType')
            if roiType == 'All':
                # Match all with QRegExp is empty string ''
                roiType = ''   # '(.)*' # '[^\n]*' #"(.*?)" #'(?s:.)'  # '(.*?)' '(?s:.)'
            logger.info(f'matching roiType column to reg exp roiType:"{roiType}"')
            self.pointsTable.myTable2.proxy.setFilterRegExp(QtCore.QRegExp(roiType,
                                                    QtCore.Qt.CaseInsensitive,
                                                    QtCore.QRegExp.FixedString));
            self.pointsTable.myTable2.proxy.setFilterKeyColumn(roiColIdx);
        except (KeyError) as e:
            logger.warning(f'did not find column "roiType"')

    def checkPointState(self):
        """Compare our backend point to a viewer points to ensure they are the same.
        """
        
        pointsLayerData = self.pointsLayer.data  # np.ndarray

        if len(self._pointAnnotations) != len(pointsLayerData):
            print('')
            logger.error('data does not match')
            print(f'  layer data shape is {pointsLayerData.shape}')
            print(f'  pandas data shape is {self._pointAnnotations.shape}')
            print('')

if __name__ == '__main__':
    pass
    #pv = PointViewer(None, None, None)
