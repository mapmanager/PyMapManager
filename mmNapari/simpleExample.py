"""
Date: 20220109
Author: Robert Cudmore

Example script to load a mmMap and display the first timepoint mmStack with:
    - 3D image
    - 3D point annotations
    - 3D line tracings

To run locally, you need to specify the full path to the map in mapPath.py

To view the coordinates of line segments and annotations in a table, you need to run:

pip install napari-properties-viewer

Once napari is running, you can view the properties by opening the properties viewer plugin from
Plugins menu -> Add dock widget -> napari-propertiews-viewer: properties table

It can take a minute or so after napari has started for the Plugins menu to be clickable.

"""

import numpy as np
import napari
import pymapmanager

mapPath = '/media/cudmore/data/richard/rr30a/rr30a.txt'
# mapPath = '/Users/vasudhajha/Documents/mapmanager/PyMapManager-Data/rr30a.txt'

def run():
    # load a mmMap
    myMap = pymapmanager.mmMap(mapPath)
    
    # get info on loaded map
    print(myMap)
    #print(myMap.mapInfo())  # TODO: make more informative
    
    # get the real-world x/y scale of each image in micrometers (um)
    # x/y resolution is usually the same, z is always unitless and corrsponds to simply image number
    mapInfo = myMap.mapInfo()
    dx = mapInfo['dx'][0]  # x-resolution (um) of the first mmStack
    dy = mapInfo['dy'][0]
    print ('x resolution in um is: dx', dx, type(dx))  # crap, it is a string
    print ('y resolution in um is: dy', dy, type(dy))  # crap, it is a string
    dx = float(dx)
    dy = float(dy)

    aStack = myMap.stacks[0]  # grab the first mmStack
    
    # CRITICAL
    aStack.loadStackImages()  # CRITICAL: until calling this, images are not loaded

    # grab the nd-image
    oneImageVolume = aStack.images

    # open napari viewer with the image volume and specify the (z, x, y) scale
    viewer = napari.view_image(oneImageVolume, scale=(1, dx, dy))

    # pull 3d point annotations
    df = aStack.stackdb  # pandas DataFrame with x/y/z and roiType columns (lots more columns)
    spines = df[df['roiType'].isin(['spineROI'])]

    # the um x/y/z position of each spine ROI annotation
    x = spines['x'].values
    y = spines['y'].values
    z = spines['z'].values
        
    # package x/y/z into points for napari
    # Note order here [z, y, x], I usually think of order as [z, x, y]
    arrays = [z, y, x]
    points = np.stack(arrays, axis=1)
    print('points:', points.shape)  # check the shape of the points, napari wants annotations in rows and then x/y/z in columns

    #
    # create a points layer with our spineROI point annotations
    size = 2  # the size of the point displayed in napari
    points_layer = viewer.add_points(points, size=size, face_color='r', properties={"x": x, "y": y, "z": z})

    #
    # load line/segment tracings from a mmStack
    xyzLine = aStack.line.getLine() #this returns a 2d numpy array with columns of (x,y,z)
    xLine = xyzLine[:,0]
    yLine = xyzLine[:,1]
    zLine = xyzLine[:,2]

    # package x/y/z into points for napari
    # Note order here [z, y, x], I usually think of order as [z, x, y]
    arrays = [zLine, yLine, xLine]
    linePoints = np.stack(arrays, axis=1)

    #
    # create a points layer with our line segments
    size = 2
    line_points_layer = viewer.add_points(linePoints, size=size, face_color='c', properties={"x": xLine.tolist(), "y": yLine.tolist(), "z": zLine.tolist()})

    #
    # typical of any kind of GUI interface, we need to enter into a loop so the viewer stays up
    napari.run()  # start the "event loop" and show the viewer

if __name__ == '__main__':
    run()