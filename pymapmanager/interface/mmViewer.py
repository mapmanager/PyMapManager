"""A MapManager stack viewer using napari.

TODO:
	- Remove toolbars (top-left) for (delete, add, select, zoom).
	- Replace these with interface including
		- delete: keyboard 'delete'
		- add: shit + click
		- select: always active
		- zoom: shit+mouse wheel (mouse wheel alone will scroll slices)
	- Make selected annotation visible by setting their size

	- Limit signal/slot back to table plugin when selecting points.
		Selecting a range of 100's of points in the line layer is super slow

	- remove edge color, it looks sloppy

	- add code to toggle line and point annotation tables on/off.
		Maybe add a 'MapManager' menu and show state with check-mark in menu

	- selecting an annotation (make symbol bigger and yellow),
		1) does not get cancelled/reverted if user switches layer
			when a point is selected
		2) on selection, symbol turns yellow in table plugin (good)
			on de-selection, table is not updated. Hitting the 'refresh'
			button does update correctly (no longer yellow/selected)

	- Make the table plugin snap to selected row, make it visible

	- Add option to table plugin to only show one row selection.
		Option will be toggled via right-click menu
	
"""

from qtpy import QtCore, QtWidgets, QtGui

import napari

import numpy as np
import pandas as pd

import pymapmanager
import napari_layer_table
#from napari_layer_table import LayerTablePlugin

from pymapmanager.logger import get_logger
logger = get_logger(__name__)

# TODO: (cudmore) this needs to go into annotation class
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
	}
}  # options

class mmViewer():
	def __init__(self, tifPath):
		
		self._tifPath = tifPath
		self._stack = pymapmanager.stack.stack(tifPath)
		print(self._stack)

		self._viewer = napari.Viewer()

		image = self._stack.getImageChannel(1)
		self._viewer.add_image(image)

		# to hide napari interface panels
		# see: https://forum.image.sc/t/is-it-possible-to-open-the-napari-viewer-with-the-layer-controls-and-layer-list-gui-elements-hidden/47755
		showDockLayerList = True
		showDockLayerControls = True
		self._viewer.window.qt_viewer.dockLayerList.setVisible(showDockLayerList)
		self._viewer.window.qt_viewer.dockLayerControls.setVisible(showDockLayerControls)

		self._selected_data = set()
		"""Selected point in point annotations"""

		#  Order matters, last built will be selected
		self.buildLineAnnotation()
		self.buildPointAnnotations()

	@property
	def stack(self):
		return self._stack

	@property
	def viewer(self):
		return self._viewer

	def buildPointAnnotations(self):
		# pymapmanager.annotations.pointAnnotations.pointAnnotations
		pointAnnotations = self._stack.getPointAnnotations()
		
		xyz = pointAnnotations.getPoints_xyz(asPixel=True)
		#print(xyz.shape)

		#self.defaultSize = 2
		
		# add a color column
		numAnnotations = pointAnnotations.numAnnotations
		allRows = range(numAnnotations)
		#pointAnnotations.asDataFrame().at[allRows, 'color'] = [1, 0, 0, 1] * numAnnotations
		pointAnnotations.asDataFrame()['face_color'] = ''
		pointAnnotations.asDataFrame()['shown'] = ''
		pointAnnotations.asDataFrame()['size'] = ''
		for row in range(numAnnotations):
			# point annotations have multiple roi types, each with different color/size
			roiType = pointAnnotations.asDataFrame().at[row, 'roiType']

			shown = options['pointsDisplay'][roiType]['shown']
			color = options['pointsDisplay'][roiType]['face_color']
			size = options['pointsDisplay'][roiType]['size']

			pointAnnotations.asDataFrame().at[row, 'face_color'] = color
			pointAnnotations.asDataFrame().at[row, 'shown'] = shown
			pointAnnotations.asDataFrame().at[row, 'size'] = [size, size, size]  # assuming 3D

		# need to use layer shown to show/hide individual points

		self.pointsLayer = self._viewer.add_points(xyz,
							size=pointAnnotations.asDataFrame()['size'].tolist(),
							face_color=pointAnnotations.asDataFrame()['face_color'].tolist(),
							shown=pointAnnotations.asDataFrame()['shown'].tolist(),
							text=f'{roiType}',
							name='Point Annotations')

		self.pointsLayer.mode = 'select'
		# add some properties
		#print('properties:', self.pointsLayer.properties)
		self.pointsLayer.properties = {
			'roiType': pointAnnotations.getColumn('roiType')
		}

		self.pointsLayer.events.highlight.connect(self.on_select_in_viewer)

		# when creating with oneLayer, the plugin will not switch layers
		self.pointsTable = napari_layer_table.LayerTablePlugin(self._viewer,
								oneLayer=self.pointsLayer)

		# add to vlayout
		vlayout = self.pointsTable.layout()

		hLayout = QtWidgets.QHBoxLayout()
		
		label = QtWidgets.QLabel('roiTypes')
		
		popup = QtWidgets.QComboBox()
		roiItems = pointAnnotations.getColumn('roiType').unique()
		roiItems = roiItems.tolist()
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

	def buildLineAnnotation(self):
		la = self.stack.getLineAnnotations()
		
		# TODO (cudmore) make 'roiType' a column in all annotations.baseAnnotations
		#	when creating annotations.lineAnnotations() pass roiType='linePnt'
		#   use baseAnnotations.roiTypesClass.linePnt
		roiType = 'linePnt'
		la.asDataFrame()['roiType'] = roiType  # add a column
		
		xyz = la.getPoints_xyz(asPixel=True)

		# line annotations are all the same roiType, use one color
		self.lineLayer = self._viewer.add_points(xyz,
							size=options['pointsDisplay'][roiType]['size'],
							face_color=options['pointsDisplay'][roiType]['face_color'],
							shown=True,  # pointAnnotations.asDataFrame()['shown'].tolist(),
							name='Line Annotations')

		self.lineLayer.mode = 'select'
		# add some properties
		#print('properties:', self.pointsLayer.properties)
		self.lineLayer.properties = {
			'segmentID': la.getColumn('segmentID').astype(str),
			'roiType': la.getColumn('roiType')
		}

		self.lineLayer.events.highlight.connect(self.on_select_in_viewer)

		self.lineTable = napari_layer_table.LayerTablePlugin(self._viewer, 
							oneLayer=self.lineLayer)

		# add to vlayout
		vlayout = self.lineTable.layout()

		hLayout = QtWidgets.QHBoxLayout()
		
		label = QtWidgets.QLabel('segmentID')
		
		popup = QtWidgets.QComboBox()
		segmentItems = la.getColumn('segmentID').unique()
		segmentItems = segmentItems.astype(str)
		segmentItems = segmentItems.tolist()
		segmentItems.insert(0, 'All')
		popup.addItems(segmentItems)
		popup.currentTextChanged.connect(self.on_segmentid_popup)

		hLayout.addWidget(label)
		hLayout.addWidget(popup)

		vlayout.insertLayout(1, hLayout)

		# TODO: (cudmore) generalize this
		# self.lineLayer.events.highlight.connect(self.on_select_in_viewer)

		# show
		area = 'right'
		name = 'Line Annotations'
		self._dockWidget2 = self._viewer.window.add_dock_widget(self.lineTable, 
							area=area, name=name)

	def on_select_in_viewer(self, event):
		"""Respond to point selection in viewer.
		
		Increase the size of selected point and change their color.

		Note:
			Extend to both point and line selection.
			Need to add an 'roiType' column to line annotations
		"""
		selectionMult = 3  # TODO (cudmore) add to options
		
		layer = event.source
		if 1:  # layer == self.pointsLayer:
			selected_data = layer.selected_data
			if not pymapmanager.utils.setsAreEqual(selected_data, self._selected_data):
				logger.info(f'new selected_data:{selected_data}')
				if len(self._selected_data)>0:
					# cancel previous point selection
					layer.size[list(self._selected_data)] = np.divide(
						layer.size[list(self._selected_data)],
						selectionMult
					)
					# DONE: get the default color for each 'roiType' from
					# face_color = options['pointsDisplay'][roiType]['face_color']
					roiTypes = layer.properties['roiType'][list(self._selected_data)]
					colorList = []
					for roiType in roiTypes:
						colorList.append(options['pointsDisplay'][roiType]['face_color'])
					layer.face_color[list(self._selected_data)] = colorList  # [1, 0, 0, 1]

				# set the size of the new selection
				self._selected_data = selected_data
				layer.size[list(selected_data)] = layer.size[list(selected_data)] * selectionMult
				# TODO (cudmore) add an option to specify selection color (currently using yellow)
				layer.face_color[list(selected_data)] = [1, 1, 0, 1]  # yellow
				
				# refresh
				#layer.refresh()
				#layer.events.size()
				layer.events.face_color()

	def on_segmentid_popup(self, currentSegment):
		logger.info(f'currentSegment:{currentSegment}')

		# filter table
		self.filterBySegmentType(currentSegment)
	
	def on_roitype_popup(self, currentRoiType):
		"""Filter the point annotation list of roi to just roiType equal to currrentRoiType
		"""
		
		logger.info(f'currentRoiType:{currentRoiType}')
		
		# filter table
		self.filterByRoiType(currentRoiType)
		
		# show/hide in viewer
		pa = self._stack.getPointAnnotations()
		if currentRoiType == 'All':
			shownMask = [True] * pa.numAnnotations
		else:
			shownMask = pa.asDataFrame()['roiType'] == currentRoiType
		self.pointsLayer.shown = shownMask

		self.pointsLayer.events.face_color()

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

def run():
	import sys
	app = QtWidgets.QApplication(sys.argv)

	#tifPath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
	tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
	
	mmv = mmViewer(tifPath)

	sys.exit(app.exec_())

if __name__ == '__main__':
	run()
