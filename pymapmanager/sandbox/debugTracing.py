import os
import sys
import time

from threading import Thread
from queue import Empty, Queue
from typing import List

import numpy as np

from qtpy import QtGui, QtWidgets

import matplotlib.pyplot as plt

import brightest_path_lib
from brightest_path_lib.algorithm import AStarSearch

import pymapmanager as pmm
from pymapmanager.interface.stackWidget import stackWidget

from pymapmanager._logger import logger

class AStarThread(Thread):
    def __init__(self,
            image : np.ndarray,
            start_point : np.ndarray,
            goal_point : np.ndarray,
            queue = None):
        super().__init__(daemon=True)
        self.queue = queue
        self.search_algorithm = AStarSearch(image, start_point=start_point, goal_point=goal_point, open_nodes=queue)
        self._startTime = time.time()

    def cancel(self):
        self.search_algorithm.is_canceled = True
    
    def run(self):
        """
        run A* tracing algorithm
        """
        print("Searching...")
        self.search_algorithm.search()
        _stopTime = time.time()
        print(f'  in {round(_stopTime-self._startTime,3)} seconds')

def _plot_image(image: np.ndarray, start: np.ndarray, end: np.ndarray):

    if len(image.shape) == 3:
        image = image.max(axis=0)

    if image.max() > 255:
        image = image / image.max() * 255
        image = image.astype(int)

    print('plotting image:', image.shape, image.max())

    plt.imshow(image, cmap='gray')
    
    if len(start) == 3:
        z = start[0]
        x = start[2]
        y = start[1]
    else:
        x = start[1]
        y = start[0]
    plt.plot(x, y, 'og')
    
    if len(end) == 3:
        z = end[0]
        x = end[2]
        y = end[1]
    else:
        x = end[1]
        y = end[0]
    plt.plot(x, y, 'or')
    
    plt.pause(0.001)


def _plot_points(points: List[np.ndarray], color='c', size=5, alpha=0.3):
    """Plot points

    Args:
        points: [(y,x)]
    """
    if len(points[0]) == 3:
        xPlot = [point[2] for point in points]
        yPlot = [point[1] for point in points]
        #zPlot
    else:
        xPlot = [point[1] for point in points]
        yPlot = [point[0] for point in points]
        #zPlot

    # yPlot = [point[0] for point in points]
    # xPlot = [point[1] for point in points]

    plt.scatter(xPlot, yPlot, c=color, s=size, alpha=alpha)
    plt.pause(0.0001)

def debugTif():
    import tifffile
    import matplotlib.pyplot as plt

    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    
    # _imgData = tifffile.imread(path)  # 3D
    # logger.info(f'_imgData is shape: {_imgData.shape}')  # shape is (z,y,x)

    stack = pmm.stack(path)
    stack.loadImages(channel=2)
    _imgData = stack.getImageChannel(channel=2)

    _pointAnnotations = stack.getPointAnnotations()
    df = _pointAnnotations.getDataFrame()
    df = df[df['roiType']=='controlPnt']
    print(df)
    xList = df['x'].tolist()
    yList = df['y'].tolist()
    zList = df['z'].tolist()

    logger.info(f'_imgData is shape: {_imgData.shape}')  # shape is (z,y,x)

    onePntStart = 5
    onePntStop = 10
    startPnt = (zList[onePntStart], yList[onePntStart], xList[onePntStart])
    goalPnt = (zList[onePntStop], yList[onePntStop], xList[onePntStop])

    _plot_image(_imgData, startPnt, goalPnt)

    # run tracing
    queue = Queue()
    search_thread = AStarThread(_imgData, startPnt, goalPnt, queue)
    search_thread.start()

    _updateInterval = 10  # wait for this number of results and update plot
    plotItems = []
    while search_thread.is_alive() or not queue.empty(): # polling the queue
        if search_thread.search_algorithm.found_path:
            break

        try:
            item = queue.get(False)
            # update a matplotlib/pyqtgraph/napari interface
            plotItems.append(item)
            if len(plotItems) > _updateInterval:
                
                # Is plotItems[0] in (z,y,x) or (z,x,y) ???
                # print(f'after waiting for {_updateInterval} new values...')
                # print(f'  got plotItems[0] that looks like {plotItems[0]}')
                _plot_points(plotItems)

                plotItems = []

        except Empty:
            # Handle empty queue here
            pass

    if search_thread.search_algorithm.found_path:
        _result = search_thread.search_algorithm.result
        print(f'_result: {len(_result)} {_result[0:5]}')

        _plot_points(search_thread.search_algorithm.result, 'y', 4, 0.9)

    # to keep plot up at end
    plt.show()

def debugTracing(sw : stackWidget):
        # TODO (cudmore) for adding brightest path
        # update self._imageLabel with tracing results and self.update()
        _imageLabel = sw.myStack.getImageSlice(0).copy()  # np.ndarray
        _imageLabel[:] = 0
        sw._myGraphPlotWidget._myImageLabel.setImage(_imageLabel, opacity=0.5)  # pg.ImageItem
        sw._myGraphPlotWidget.update()

        do2D = True

        if do2D:
            _image = sw.myStack.getMaxProject(channel=2)
        else:
            # 3D
            _image = sw.myStack.getImageChannel(2)

        print('_image:', _image.shape)

        # for this tif, start/goal points can be
        # start_point: [ 31 236 364]
        # goal_point: [ 28 250 931]

        # TODO (cudmore) get start/stop rows of one segment
        # dfSegment = sw.myStack.getLineAnnotations().getSegment(0)
        # print(len(dfSegment))
        
        # we always trace between pairs of pointAnnotation type 'ocntrolPnt'
        # get point annotations 'controlPnt' for segmentID 0
        # pa = sw.myStack.getPointAnnotations()
        # _df = pa.getSegmentPlot(segmentID=0, roiTypes=['controlPnt'])

        #print(_df)

        # start/goal from segmentID 0
        la = sw.myStack.getLineAnnotations()
        xStart = la.getValue('x', 10)
        yStart = la.getValue('y', 10)
        zStart = la.getValue('z', 10)
        xGoal = la.getValue('x', 300)
        yGoal = la.getValue('y', 300)
        zGoal = la.getValue('z', 300)

        xStart = int(xStart)
        yStart = int(yStart)
        zStart = int(zStart)
        xGoal = int(xGoal)
        yGoal = int(yGoal)
        zGoal = int(zGoal)
        
        if do2D:
            start_point = np.array([yStart, xStart]) # (y,x)
            goal_point = np.array([yGoal, xGoal]) # (y,x)
        else:
            # 3D
            start_point = np.array([zStart, yStart, xStart]) # (y,x)
            goal_point = np.array([zGoal, yGoal, xGoal]) # (y,x)
        
        print('start_point:', start_point)
        print('goal_point:', goal_point)
        
        queue = Queue()
        search_thread = AStarThread(_image, start_point, goal_point, queue)
        search_thread.start()

        _updateInterval = 256  # wait for this number of results and update plot
        plotItems = []
        while search_thread.is_alive() or not queue.empty(): # polling the queue
            if search_thread.search_algorithm.found_path:
                break

            try:
                item = queue.get(False)
                # update a matplotlib/pyqtgraph/napari interface
                plotItems.append(item)
                if len(plotItems) > _updateInterval:
                    #_plot_points(plotItems, 'c', 8, 0.3)
                    
                    # plotItems[0] is (z, y, x)
                    # logger.info(f'updating interface with {len(plotItems)} items')
                    # logger.info(f'  plotItems[0] is: {plotItems[0]}')

                    # set _imageLabel with new searched points
                    if do2D:
                        yPlot = [point[0] for point in plotItems]
                        xPlot = [point[1] for point in plotItems]
                    else:
                        yPlot = [point[1] for point in plotItems]
                        xPlot = [point[2] for point in plotItems]
                        zPlot = [point[0] for point in plotItems]
                    _imageLabel[yPlot, xPlot] = 255
                    sw._myGraphPlotWidget._myImageLabel.setImage(_imageLabel, opacity=0.5)  # pg.ImageItem
                    sw._myGraphPlotWidget.update()


                    plotItems = []

            except Empty:
                # Handle empty queue here
                pass

        if search_thread.search_algorithm.found_path:
            _result = search_thread.search_algorithm.result
            print(f'_result: {type(_result)} {len(_result)} {_result[0]}')

def run():
        path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
        myStack = pmm.stack(path=path)
        
        myStack.loadImages(channel=1)
        myStack.loadImages(channel=2)
        
        # do this once and save into backend and file
        # myStack.createBrightestIndexes(channelNum = 2)

        # run pyqt interface
        app = QtWidgets.QApplication(sys.argv)

        bsw = stackWidget(myStack=myStack)

        # useful on startup, to snap to an image
        bsw._myGraphPlotWidget.slot_setSlice(30)

        bsw.show()

        # this will only show us the answer, we need to actually add 'trace' to user interface
        #debugTracing(bsw)

        sys.exit(app.exec_())

if __name__ == '__main__':
    run()  # in full pymapmanager interface (complicated)
    #debugTif()