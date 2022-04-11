"""A MapManager stack viewer using napari.	
"""

from pprint import pprint

from qtpy import QtCore, QtWidgets  # , QtGui

import napari

import numpy as np
import pandas as pd

import pymapmanager
import napari_layer_table

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

		#self.testPlugin()

	@property
	def stack(self):
		return self._stack

	@property
	def viewer(self):
		return self._viewer

	def buildPointAnnotations(self):
		# pymapmanager.annotations.pointAnnotations.pointAnnotations
		pointAnnotations = self._stack.getPointAnnotations()
		
		# TODO: Check if pointAnnotations is None.
		
		colName = ['z', 'y', 'x']
		xyz = pointAnnotations.getValues(colName)
		#print(xyz.shape)
		
		# add a color column
		numAnnotations = pointAnnotations.numAnnotations
		allRows = range(numAnnotations)
		#pointAnnotations.getDataFrame().at[allRows, 'color'] = [1, 0, 0, 1] * numAnnotations
		pointAnnotations['face_color'] = ''
		pointAnnotations['shown'] = ''
		pointAnnotations['size'] = ''
		#pointAnnotations.getDataFrame()['face_color'] = ''
		#pointAnnotations.getDataFrame()['shown'] = ''
		#pointAnnotations.getDataFrame()['size'] = ''
		for row in range(numAnnotations):
			# point annotations have multiple roi types, each with different color/size
			#roiType = pointAnnotations.getDataFrame().at[row, 'roiType']
			roiType = pointAnnotations.at[row, 'roiType']
			#roiType = pointAnnotations.getValues('roiType', row).astype(str)

			shown = options['pointsDisplay'][roiType]['shown']
			color = options['pointsDisplay'][roiType]['face_color']
			size = options['pointsDisplay'][roiType]['size']

			pointAnnotations.at[row, 'face_color'] = color
			pointAnnotations.at[row, 'shown'] = shown
			pointAnnotations.at[row, 'size'] = [size, size, size]  # assuming 3D

		# need to use layer shown to show/hide individual points

		#print(pointAnnotations.getDataFrame()['size'].tolist())
		#print(pointAnnotations.getDataFrame()['face_color'].tolist())
		#print(pointAnnotations.getDataFrame()['shown'].tolist())
		
		self.pointsLayer = self._viewer.add_points(xyz,
							size=pointAnnotations.getDataFrame()['size'].tolist(),
							face_color=pointAnnotations.getDataFrame()['face_color'].tolist(),
							shown=pointAnnotations.getDataFrame()['shown'].tolist(),
							#text=f'{roiType}',
							name='Point Annotations')

		self.pointsLayer.mode = 'select'
		
		# add some properties
		self.pointsLayer.properties = {
			'roiType': pointAnnotations.getValues('roiType')
		}

		self.pointsLayer.events.highlight.connect(self.on_select_point_in_viewer)

		# when creating with oneLayer, the plugin will not switch layers
		self.pointsTable = napari_layer_table.LayerTablePlugin(self._viewer,
								oneLayer=self.pointsLayer)
		self.pointsTable.signalDataChanged.connect(self.on_user_edit_points)
		#self.pointsTable.pointsAdded.connect(self.slot_pointsAdded)

		#
		# make a selection layer
		self.pointsLayerSelection = self._viewer.add_points([0,0,0], name='Point Selection')

		# add to vlayout
		vlayout = self.pointsTable.layout()

		hLayout = QtWidgets.QHBoxLayout()
		
		label = QtWidgets.QLabel('roiTypes')
		
		popup = QtWidgets.QComboBox()
		roiItems = np.unique(pointAnnotations.getValues('roiType'))
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

	def on_user_edit_points(self, eventType, df):
		logger.info('')
		print('  eventType:', eventType)
		pprint(df)

	def buildLineAnnotation(self):
		la = self.stack.getLineAnnotations()
		
		# TODO (cudmore) make 'roiType' a column in all annotations.baseAnnotations
		#	when creating annotations.lineAnnotations() pass roiType='linePnt'
		#   use baseAnnotations.roiTypesClass.linePnt
		#roiType = 'linePnt'
		#la.getDataFrame()['roiType'] = roiType  # add a column
		
		# shape path needs at least two points
		# ValueError: Shape needs at least two vertices, 1 provided.
		#la.addAnnotation(20, 30, 0, segmentID=6)
		#la.addAnnotation(40, 40, 0, segmentID=6)

		# line as a shapes layer
		# does not work because if shape is spanning multiple z image planes, we do not see it in x/y view !!!
		xyzSegments = la.getSegment_xyz() # list of (z,y,x) segments
		'''
		voxelx = 0.12
		voxely = 0.12
		for xyzSegment in xyzSegments:
			xyzSegment[:,1] /= voxely
			xyzSegment[:,2] /= voxelx
		'''
		logger.info(f'xyzSegments has {len(xyzSegments)} segments')
		
		edge_width = 5
		self.lineLayer = self._viewer.add_shapes(
			xyzSegments, shape_type='path', edge_width=edge_width, 
			edge_color='green'  # TODO (cudmore) color each segmentID different
		)

		self.lineLayer.events.highlight.connect(self.on_select_line_in_viewer)

		# line as a tracks layer, tracks DOES NOT take a list of tracks
		# [id, tp, z, y, x]
		'''
		trackSegments = la.getSegment_tracks() # list of (z,y,x) segments
		voxelx = 0.12
		voxely = 0.12
		trackSegments[:,3] /= voxely
		trackSegments[:,4] /= voxelx
		logger.info(f'trackSegments has shape {trackSegments.shape}')
		print(trackSegments[:,2])
		self._viewer.add_tracks(trackSegments, name='tracks')
		'''

		# line as a points layer
		'''
		xyz = la.getValues(['z', 'y', 'x'])
		voxelx = 0.12
		voxely = 0.12
		xyz[:,1] /= voxely
		xyz[:,2] /= voxelx

		
		self.lineLayer = self._viewer.add_points(xyz,
							size=options['pointsDisplay'][roiType]['size'],
							face_color=options['pointsDisplay'][roiType]['face_color'],
							shown=True,  # pointAnnotations.getDataFrame()['shown'].tolist(),
							name='Line Annotations')

		self.lineLayer.mode = 'select'

		# add some properties
		#print('properties:', self.pointsLayer.properties)
		segmendID = la.getValues('segmentID')
		roiType = la.getValues('roiType')
		self.lineLayer.properties = {
			'segmentID': segmendID,
			'roiType': roiType,
		}

		self.lineLayer.events.highlight.connect(self.on_select_in_viewer)
		'''

		# create a layer table plugin
		"""
		self.lineTable = napari_layer_table.LayerTablePlugin(self._viewer, 
							oneLayer=self.lineLayer)

		# add to vlayout
		vlayout = self.lineTable.layout()

		hLayout = QtWidgets.QHBoxLayout()
		
		label = QtWidgets.QLabel('segmentID')
		
		popup = QtWidgets.QComboBox()
		#segmentItems = np.unique(la.getValues('segmentID'))
		segmentItems = la.unique('segmentID')
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
		"""

	def on_select_line_in_viewer(self, event):
		"""Shape/line layer selection.
		"""
		logger.info('')
		
		layer = event.source
		selected_data = layer.selected_data

		print('  layer:', layer)
		print('  selected_data:', selected_data)
		
		# data is a list of np.ndarray
		# is ndarray is Mxn with M:num points, n:num dim
		# basically [z, y, x]
		print('  data:', type(layer.data[0]), layer.data[0].shape)
		#print('    ', layer.data[0])

		for idx, shape in enumerate(layer.data):
			print('  shape idx:', idx, shape.shape)
			zMean = np.mean(shape[:,0])
			yMean = np.mean(shape[:,1])
			xMean = np.mean(shape[:,2])
			
		#print(vars(layer))

	def on_select_point_in_viewer(self, event):
		"""Respond to point selection in viewer.
		
		Increase the size of selected point and change their color.

		Using a selection layer `pointsLayerSelection`
		
		Note:
			Extend to both point and line selection.
			Need to add an 'roiType' column to line annotations
		"""
		
		logger.info('')
		selectionMult = 3  # TODO (cudmore) add to options
		
		layer = event.source
		if 1:  # layer == self.pointsLayer:
			selected_data = layer.selected_data  # new selection
			if not pymapmanager.utils.setsAreEqual(selected_data, self._selected_data):
				logger.info(f'new selected_data:{selected_data}')
				# cancel previous selection
				'''
				if len(self._selected_data)>0:
					print('  clearing self._selected_data:', self._selected_data)
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
					print('  clearing new colorList:', colorList)
					layer.face_color[list(self._selected_data)] = colorList  # [1, 0, 0, 1]
				'''

				# was this
				'''
				# set the size of the new selection
				self._selected_data = selected_data
				layer.size[list(selected_data)] = layer.size[list(selected_data)] * selectionMult
				# TODO (cudmore) add an option to specify selection color (currently using yellow)
				layer.face_color[list(selected_data)] = [1, 1, 0, 1]  # yellow
				'''
				
				# replace entire xxx with selected points
				# increase size and make yellow
				self._selected_data = selected_data

				selectedDataList = list(selected_data)
				newSelectedPoints = layer.data[selectedDataList]
				newSelectedPoints = np.array(newSelectedPoints)
				newSelectedSize = layer.size[selectedDataList] * selectionMult
				#print('ndim:', self.pointsLayerSelection.ndim)
				#print('newSelectedPoints:', newSelectedPoints.shape, newSelectedPoints)
				#print('newSelectedSize:', newSelectedSize)
				self.pointsLayerSelection.data = newSelectedPoints
				self.pointsLayerSelection.size = newSelectedSize
				self.pointsLayerSelection.face_color = [1, 1, 0, 1]  # yellow

				# refresh
				#layer.refresh()
				#layer.events.size()
				
				# we need this to update the interface
				# this triggers events and causes error if we arrived her on 'new'
				#layer.events.face_color()
				self.pointsLayerSelection.events.face_color()

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
			shownMask = pa.getDataFrame()['roiType'] == currentRoiType
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

	#tifPath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
	tifPath = '/Users/cudmore/Sites/PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
	
	mmv = mmViewer(tifPath)

	sys.exit(app.exec_())

if __name__ == '__main__':
	run()
