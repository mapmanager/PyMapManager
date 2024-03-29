"""
Add points on nD shapes
=======================
Add points on nD shapes in 3D using a mouse callback
"""

import napari
import numpy as np

# Create rectangles in 4D
shapes_data = np.array(
    [
        [
            [0, 50, 75, 75],
            [0, 50, 125, 75],
            [0, 100, 125, 125],
            [0, 100, 75, 125]
        ],
        [
            [0, 10, 75, 75],
            [0, 10, 125, 75],
            [0, 40, 125, 125],
            [0, 40, 75, 125]
        ],
        [
            [1, 100, 75, 75],
            [1, 100, 125, 75],
            [1, 50, 125, 125],
            [1, 50, 75, 125]
        ]
    ]
)

def on_select_point_in_viewer(event):
    print(f'{shapes_layer}')
    print(f'{len(shapes_layer.data)}')  # data is a list
    print(f'{shapes_layer}')

shapes_data = [
        [1,10,10], [1,20,20]
]

'''shapes_data = [
        [float('nan'),float('nan'),float('nan')], [float('nan'),float('nan'),float('nan')]
]
'''

# add an empty 4d points layer
viewer = napari.view_points(ndim=3, size=3)
points_layer = viewer.layers[0]

shapes_layer = viewer.add_shapes(
    shapes_data,
    shape_type='path'
)

shapes_layer.events.highlight.connect(on_select_point_in_viewer)

    
# set the viewer to 3D rendering mode with the first two rectangles in view
'''
viewer.dims.ndisplay = 3
viewer.dims.set_point(axis=0, value=0)
viewer.camera.angles = (70, 30, 150)
viewer.camera.zoom = 2.5
'''

if __name__ == '__main__':
    napari.run()