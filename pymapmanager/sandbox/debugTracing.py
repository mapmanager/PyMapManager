import os
import sys

from threading import Thread
from queue import Empty, Queue

import numpy as np

from qtpy import QtGui, QtWidgets

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
    
    def cancel(self):
        self.search_algorithm.is_canceled = True
    
    def run(self):
        """
        run A* tracing algorithm
        """
        print("Searching...")
        self.search_algorithm.search()
        print("Done")

def debugTif():
    import tifffile
    import matplotlib.pyplot as plt

    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    
    _imgData = tifffile.imread(path)  # 3D
    logger.info(f'_imgData is shape: {_imgData.shape}')  # shape is (z,y,x)

    # load path (e.g. rr30a_s0_ch2.tif) into Fiji and manually ddetermine start/stop points
    startPnt = (32, 240, 355)  # (z,y,x)
    zStart = startPnt[0]

    goalPnt = (31, 215, 813)  # (z,y,x)
    zGoal = goalPnt[0]

    #
    # show these in start/goal in matplotlib
    # plt.imshow(_imgData[zStart])
    # plt.plot(startPnt[2], startPnt[1], 'og')  # (x,y)
    # plt.imshow(_imgData[zGoal])
    # plt.plot(goalPnt[2], goalPnt[1], 'or')  # (x,y)
    # plt.show()

    # run tracing
    queue = Queue()
    search_thread = AStarThread(_imgData, startPnt, goalPnt, queue)
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
                
                # Is plotItems[0] in (z,y,x) or (z,x,y) ???
                # print(f'after waiting for {_updateInterval} new values...')
                # print(f'  got plotItems[0] that looks like {plotItems[0]}')
                                
                plotItems = []

        except Empty:
            # Handle empty queue here
            pass

    if search_thread.search_algorithm.found_path:
        _result = search_thread.search_algorithm.result
        print(f'_result: {type(_result)}')

def debugTracing(sw : stackWidget):
        # TODO (cudmore) for adding brightest path
        # update self._imageLabel with tracing results and self.update()
        _imageLabel = sw.myStack.getImageSlice(0).copy()  # np.ndarray
        _imageLabel[:] = 0
        sw._myGraphPlotWidget._myImageLabel.setImage(_imageLabel, opacity=0.5)  # pg.ImageItem
        sw._myGraphPlotWidget.update()

        do2D = False

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
        
        # start/goal from segmentID 0
        la = sw.myStack.getLineAnnotations()
        xStart = la.getValue('x', 10)
        yStart = la.getValue('y', 10)
        zStart = la.getValue('z', 10)
        xGoal = la.getValue('x', 600)
        yGoal = la.getValue('y', 600)
        zGoal = la.getValue('z', 600)

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
            print(f'_result: {type(_result)}')

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
        debugTracing(bsw)

        sys.exit(app.exec_())

if __name__ == '__main__':
    #run()  # in full pymapmanager interface (complicated)
    debugTif()