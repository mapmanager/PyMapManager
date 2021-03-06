"""
3D Paths
========
Display two vectors layers ontop of a 4-D image layer. One of the vectors
layers is 3D and "sliced" with a different set of vectors appearing on
different 3D slices. Another is 2D and "broadcast" with the same vectors
apprearing on each slice.
"""

import numpy as np
from skimage import data
import napari


blobs = data.binary_blobs(
            length=128, blob_size_fraction=0.05, n_dim=3, volume_fraction=0.05
        )

viewer = napari.Viewer(ndisplay=3)
viewer.add_image(blobs.astype(float))

# sample vector coord-like data
path = np.array([
    np.array([[0, 0, 0], [0, 10, 10], [0, 5, 15], [20, 5, 15],
    [56, 70, 21], [127, 127, 127]]),
    np.array([[0, 0, 0], [0, 20, 20], [0, 15, 25], [0, 15, 25],
        [0, 80, 31], [0, 137, 137]])
    ])

print('Path', path.shape)
layer = viewer.add_shapes(
    path, shape_type='path', 
    ndim=3,
    edge_width=4, edge_color=['red', 'blue']
)

if __name__ == '__main__':
    napari.run()