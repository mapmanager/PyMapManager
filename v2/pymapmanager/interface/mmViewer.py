"""A mm stack viewer using napari.

TODO:
	- Remove toolbars (top-left) for (delete, add, select, zoom).
	- Replace these with interface including
		- delete: keyboard 'delete'
		- add: shit + click
		- select: always active
		- zoom: shit+mouse wheel (mouse wheel alone will scroll slices)
"""

import sys
from PyQt5 import QtCore, QtWidgets, QtGui

import napari

import numpy as np
import pandas as pd

import pymapmanager
import napari_layer_table
#from napari_layer_table import LayerTablePlugin

class mmViewer():
	def __init__(self, tifPath):
		#super().__init__()
		
		self._tifPath = tifPath
		self._stack = pymapmanager.stack.stack(tifPath)
		print(self._stack)

		self._viewer = napari.Viewer()

		image = self._stack.getImageChannel(1)
		self._viewer.add_image(image)

		# pymapmanager.annotations.pointAnnotations.pointAnnotations
		pointAnnotations = self._stack.getPointAnnotations()
		
		xyz = pointAnnotations.getPoints_xyz(asPixel=True)
		#print(xyz.shape)

		self.pointsLayer = self._viewer.add_points(xyz,
							size=10,
							face_color='red',
							name='green circles')

		self.pointsLayer.mode = 'select'
		# add some properties
		#print('properties:', self.pointsLayer.properties)
		self.pointsLayer.properties = {
			'roiType': pointAnnotations.getColumn('roiType')
		}

		# to hide napari interface stuff
		# see: https://forum.image.sc/t/is-it-possible-to-open-the-napari-viewer-with-the-layer-controls-and-layer-list-gui-elements-hidden/47755
		self._viewer.window.qt_viewer.dockLayerList.setVisible(False)
		self._viewer.window.qt_viewer.dockLayerControls.setVisible(False)


		self.layerTable = napari_layer_table.LayerTablePlugin(self._viewer, oneLayer=self.pointsLayer)

	@property
	def stack(self):
		return self._stack

	@property
	def viewer(self):
		return self._viewer

def run():
	app = QtWidgets.QApplication(sys.argv)

	tifPath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
	mmv = mmViewer(tifPath)

	sys.exit(app.exec_())

if __name__ == '__main__':
	run()

	'''import tifffile
	tifPath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0_ch2.tif'
	tiffData = tifffile.imread(tifPath)

	imageLayer = mmv.add_image(tiffData, colormap='gray')
	
	#
	dbPath = '/media/cudmore/data/richard/rr30a/firstMap/stacks/rr30a_s0/rr30a_s0_db2.txt'
	df = pd.read_csv(dbPath, header=1)
	print(df.columns)

	# want to grab z/x/y into 2d np array
	x = df['x'].values
	y = df['y'].values
	z = df['z'].values
	
	# these are in um, I know um/pixle is "voxelx=0.12" um/pixel
	x /= 0.12
	y /= 0.12

	pointData = np.transpose([z, y, x])  # order of napari is (z,x,y)
	pointsLayer = mmv.add_points(pointData,
							size=20, face_color='green', name='green circles')
	'''

	#napari.run()
