# import numpy as np
from PIL import Image, ImageDraw
# import pylab as plt
# import matplotlib.pyplot as plt
import pylab as plt
import numpy as np
from matplotlib.path import Path

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~ Matplotlib ~~~~~~~~~~~~~~~~~~~~~~~~~~~#
nx, ny = 10, 10
poly_verts = [(1,1),(1,4),(3,4),(3,1)] 
# Extend by 1
# poly_verts = [(0,0),(0,5),(4,5),(4,0)] 
poly_verts2 = [(1,1),(1,5),(3,5),(3,1)] 
# poly_verts2 = [(0,0),(0,6),(4,6),(4,0)] 

# Create vertex coordinates for each grid cell...
# (<0,0> is at the top left of the grid in this system)
x, y = np.meshgrid(np.arange(nx), np.arange(ny))

x, y = x.flatten(), y.flatten()

# points = np.vstack((x,y)).T
points = np.vstack((x,y)).T
# print(points)

path = Path(poly_verts)
mask1 = path.contains_points(points, radius=0)

# print(grid1)
mask1 = mask1.reshape((ny,nx))
mask1 = mask1.astype(int)
# print(grid1)
# plt.imshow(mask1)

path2 = Path(poly_verts2)
mask2 = path2.contains_points(points, radius=0)
# print(grid1)
mask2 = mask2.reshape((ny,nx))
mask2 = mask2.astype(int)

plt.imshow(mask2)

combinedMasks = mask1 + mask2
combinedMasks[combinedMasks == 2] = 0
# print(combinedMasks)

import scipy
# print(combinedMasks)
struct = scipy.ndimage.generate_binary_structure(2, 2)
# Get points surrounding the altered combined mask
dialatedMask = scipy.ndimage.binary_dilation(combinedMasks, structure = struct, iterations = 1)
dialatedMask = dialatedMask.astype(int)


# Remove the inner mask (combined mask) to get the outline
outlineMask = dialatedMask - combinedMasks
# Loop through to create list of coordinates for the polygon
# print(outlineMask)
coords = np.column_stack(np.where(outlineMask > 0))
# print(coords)

plt.imshow(outlineMask)

from scipy.spatial import ConvexHull
import matplotlib.pyplot as plt
import numpy as np

hull = ConvexHull(coords)
print(hull)
print(coords)
# print(hull.simplices)
# plt.plot(coords[:,0], coords[:,1], 'o')
plt.plot(coords[:,1], coords[:,0], 'o')

# Simplex is indexes for original list of coords
for simplex in hull.simplices:
    # print("simplex", simplex)
    # print("coords[simplex, 0]", coords[simplex, 0])
    # print("coords[simplex, 1]", coords[simplex, 1])
    # print("coords[simplex]", coords[simplex])
    # print("coords[simplex, 1]", coords[simplex])

    # plt.plot(coords[simplex, 0], coords[simplex, 1], 'k')
    plt.plot(coords[simplex, 1], coords[simplex, 0], 'k')

    # break
    # plt.plot(coords[simplex], coords[simplex], 'k')

# x_min = 425
# x_max = 440
# y_min = 400
# y_max = 150
#     # # Why does the y go the other way?
# # plt.axis([x_min, x_max, y_min, y_max])
# plt.ylim(y_min, y_max)
# plt.xlim(x_min,x_max)

plt.show()
# plt.imshow(dialatedMask)
# # plt.plot(poly_verts)
# plt.show()



""" You could take the centroid of all the points, then taking the dot product of each point to the centre with a reference point 
(say the first in the list) to the centre, get the angle of each point in your list from an arbitrary reference vector. 
Then order that list on the angle. 
That'll give you the points in a (eg) clockwise winding order, so your line is just p1 -> p2, p2 -> p3 etc... """

# path = Path(poly_verts2)
# grid2 = path.contains_points(points)
# grid2 = grid2.reshape((ny,nx))
# grid2 = grid2.astype(int)

# combinedMask = grid1 + grid2
# # intersection = np.where(combinedMask == 2)
# # coords = np.column_stack(np.where(combinedMask > 0))
# # print(intersection)
# combinedMask[combinedMask == 2] = 0

# print(grid1)
# print(combinedMask)
# plt.imshow(combinedMask)
# plt.imshow(coords)
# plt.show()
# coords = np.column_stack(np.where(combinedMask > 0))



# height, width = 10, 10
# poly_verts = [(1,1),(1,4), (3,1),(3,4)] 
# poly_verts2 = [(1,1),(3,1),(1,5),(3,5)] 

# poly_path=Path(poly_verts)

# x, y = np.mgrid[:height, :width]
# coors=np.hstack((x.reshape(-1, 1), y.reshape(-1,1))) # coors.shape is (4000000,2)

# mask = poly_path.contains_points(coors)
# plt.imshow(mask.reshape(height, width))
# plt.show()



""" import cv2
combinedMask = combinedMask.astype(np.uint8) 
contours, _ = cv2.findContours(combinedMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
polygons = []

for object in contours:
    coords = []
    
    for point in object:
        coords.append(int(point[0][0]))
        coords.append(int(point[0][1]))

    polygons.append(coords)

print(polygons) """
# print(grid1)
# print(combinedMask)

# print(grid1 + grid2)
# plt.imshow(grid1)
# plt.imshow(grid2)
# plt.imshow(grid1 + grid2)
# plt.imshow(coords)
# plt.imshow(combinedMask)
# plt.show()




#~~~~~~~~~~~~~~~~~~~~~~~~~~~ PIL ~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Testing one polyogn in PIL 
# [(1,1),(3,1),(1,4),(3,4)] 
# polygon = [(1,1),(3,1),(1,4),(3,4)] 
# width = 10
# height = 10

# polygon2 = [(3,1),(5,1)] 
# width = 10
# height = 10

# img = Image.new('L', (width, height))
# # ImageDraw.Draw(img).polygon(polygon,  fill ="red",outline ="red")
# ImageDraw.Draw(img).polygon(polygon)
# mask1 = np.asarray(img)
# print("mask1", mask1)


# Testing two polygons in PIL
# img2 = Image.new('RGBA', (width, height))
# ImageDraw.Draw(img2).polygon(polygon2, fill ="blue",outline ="blue")
# mask2 = np.array(img2)
# print("mask2", mask2)
# combined_mask = mask1 + mask2 
# print("combined_mask", combined_mask)
# # print(mask)
# # plt.imshow(mask.reshape(height, width))
# # np.where(combined_mask == 2)

# plt.imshow(combined_mask)
# # plt.imshow(mask2)
# plt.imshow(mask1)
# plt.show()


# polygon = [(1,1),(2,2)] 
# width = 3
# height = 3

# img = Image.new('L', (width, height))
# ImageDraw.Draw(img).polygon(polygon, outline=1, fill=1)
# mask = numpy.array(img)
# print(mask)
# plt.imshow(mask)
# plt.show()

# import pylab as plt
# import numpy as np
# from matplotlib.path import Path

# width, height=200, 200

# polygon=[(0.1*width, 0.1*height), (0.15*width, 0.7*height), (0.8*width, 0.75*height), (0.72*width, 0.15*height)]
# poly_path=Path(polygon)

# x, y = np.mgrid[:height, :width]
# coors=np.hstack((x.reshape(-1, 1), y.reshape(-1,1))) # coors.shape is (4000000,2)

# mask = poly_path.contains_points(coors)
# plt.imshow(mask.reshape(height, width))
# plt.show()



#~~~~~~~~~~~~~~~~~~~~~~~~~~~ Shapely ~~~~~~~~~~~~~~~~~~~~~~~~~~~#
""" from shapely import Polygon
import matplotlib.pyplot as plt

p = Polygon([(1,1),(2,2),(4,2),(3,1)])
q = Polygon([(1.5,2),(3,5),(5,4),(3.5,1)])
# print(p.intersects(q))  # True
# print(p.intersection(q).area)  # 1.0
initialIntersection = p.intersection(q)
secondIntersection = initialIntersection.intersection(p)
print(secondIntersection)

x,y = p.exterior.xy
x2,y2 = q.exterior.xy

plt.plot(x,y)
plt.plot(x2,y2)
plt.show() """


# width, height=10, 10

# polygon=[(1,1),(3,1),(1,4),(3,4)] 
# poly_path=Path(polygon, codes=79)

# x, y = np.mgrid[:height, :width]
# coors=np.hstack((x.reshape(-1, 1), y.reshape(-1,1))) # coors.shape is (4000000,2)

# mask = poly_path.contains_points(coors)
# mask = mask.astype(int)
# mask = mask.reshape(height, width)
# print(mask)
# plt.imshow(mask)
# plt.show()