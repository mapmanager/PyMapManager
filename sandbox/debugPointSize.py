"""
pip install scikit-image
"""

import numpy as np
import napari
from skimage import data

g_selected_data = set()

def on_select_point(event):
	layer = event.source
	selected_data = layer.selected_data
	selected_data_list = list(selected_data)
	size = layer.size
	scale = layer.scale
	
	global g_selected_data
	if not setsAreEqual(selected_data, g_selected_data):
		# new selection
		g_selected_data = selected_data
		
		# set the size of selected point
		layer.size[selected_data_list,:] = 1

		layer.refresh()
		
		print('on_select_point()')
		print('  layer:', layer)
		print('  selected_data:', selected_data)
		print('  size:', size)
		print('  scale:', scale)

def on_size(event):
	layer = event.source
	selected_data = layer.selected_data
	size = layer.size
	scale = layer.scale
	print('on_size()')
	print('  layer:', layer)
	print('  selected_data:', selected_data)
	print('  size:', size)
	print('  scale:', scale)

def setsAreEqual(a, b):
	"""Return true if sets (a, b) are equal.
	"""
	if len(a) != len(b):
		return False
	for x in a:
		if x not in b:
			return False
	return True

# without an image layer, points layer size is not working
viewer = napari.view_image(data.astronaut(), rgb=True)

points2d = np.array([[50, 55], [60, 65], [70, 75]])

# max point size seems to be 20 ???
size = [[5, 5], [10,10], [20,20]]

pointsLayer2d = viewer.add_points(points2d,
						size = size,
						symbol = 'o',
						face_color = 'yellow',
						edge_color = 'blue',
						name = 'yellow discs')
pointsLayer2d.mode = 'select'

#pointsLayer2d.size=100

pointsLayer2d.events.highlight.connect(on_select_point)
pointsLayer2d.events.size.connect(on_size)

print('data:', pointsLayer2d.data)
print('size:', pointsLayer2d.size)
print('scale:', pointsLayer2d.scale)
print('edge_width_is_relative:', pointsLayer2d.edge_width_is_relative)
print('edge_width:', pointsLayer2d.edge_width)

# this works
# pointsLayer2d.size = [[5, 5], [10,10], [5,5]]

napari.run()

