import sys
import time

from typing import List, Union

from queue import Empty, Queue
from threading import Thread

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

import brightest_path_lib
from brightest_path_lib.algorithm import AStarSearch

from pymapmanager._logger import logger

class old_AStarThread(Thread):
    def __init__(self,
            image : np.ndarray,
            start_point : np.ndarray,
            goal_point : np.ndarray,
            queue : Queue):
        super().__init__(daemon=False)
        self.queue = queue
        self.search_algorithm = AStarSearch(image,
                                    start_point=start_point,
                                    goal_point=goal_point,
                                    open_nodes=queue)
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

class AStarWorker(QtCore.QObject):
    signalFinished = QtCore.Signal()
    # signalProgress = QtCore.Signal(object)  # List[[z,y,x]]

    def __init__(self,
                    image,
                    start_point, stop_point,
                    queue):
        super().__init__()
    
        self._image = image
        self._start_point = start_point
        self._goal_point = stop_point
        self._queue = queue

        # self._astarthread = AStarThread(image, start_point, stop_point, queue)
        self._aStarSearch = None

    def run(self):
        logger.info('  run()')
        self._aStarSearch = AStarSearch(self._image,
            start_point=self._start_point,
            goal_point=self._goal_point,
            open_nodes=self._queue)

        self._aStarSearch.search()

        logger.info('  WORKER FINISHED')
        self.signalFinished.emit()

        return

        self._astarthread.start()

        #monitor queue and emit progress
        _updateInterval = 250  # wait for this number of results and update plot
        plotItems = []
        while self._astarthread.is_alive() or not self._queue.empty(): # polling the queue
            if self._astarthread.search_algorithm.found_path:
                break

            try:
                item = self._queue.get(False)
                # update a matplotlib/pyqtgraph/napari interface
                plotItems.append(item)
                if len(plotItems) > _updateInterval:
                    #_plot_points(plotItems, 'c', 8, 0.3)
                    self.signalProgress.emit(plotItems)
                    plotItems = []
            except Empty:
                # Handle empty queue here
                pass

            #time.sleep(0.005)
            # maxtime = 20  # ms
            # QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, maxtime)  # maxtime in ms

        self.signalFinished.emit()

class moveToStackWidget(QtWidgets.QWidget):
    """Will eventually be member function of stack widget ?
    """
    signalProgress = QtCore.Signal(object)  # List[[z,y,x]]

    def __init__(self, sw, stack):
        super().__init__()
        logger.info('!!!!!!!!!!!!!!!!')
        
        self._progressSteps = 0

        self._stackWidget = sw
        self._stack = stack                
        self._stackData = stack.getImageChannel(channel=2)

        pa = stack.getPointAnnotations()
        df = pa.getSegmentControlPnts(segmentID=0)
        df = df.reset_index()

        #print(df)

        self._queue = Queue()  # we own the queue, monitor directly

        self._searchedMask = self._stack.getImageSlice(0,1).copy()
        self._searchedMask[:] = 0

        for row in range(len(df)-1):
            # start tracing at controlPnt 0
            x = df.loc[row]['x']
            y = df.loc[row]['y']
            z = df.loc[row]['z']
        
            stopRow = 15  # arbitrary choice of where to trace to
            x2 = df.loc[stopRow]['x']
            y2 = df.loc[stopRow]['y']
            z2 = df.loc[stopRow]['z']
        
            # self._startPnt = (z, y, x)
            # self._stopPnt = (z2, y2, x2)
            self._startPnt = np.array((z, y, x))
            self._stopPnt = np.array((z2, y2, x2))

            # to debug, do just 2x point to point tracing
            break

    def runLongTask(self):
        """Run tracing between 2 points.
        """
        logger.info('')
        logger.info(f'  _stackData:{self._stackData.shape}')
        logger.info(f'  _startPnt:{self._startPnt}')
        logger.info(f'  _stopPnt:{self._stopPnt}')
        
        self._progresssSteps = 0

        # Create a QThread object
        self.thread = QtCore.QThread()
        # Create a worker object
        self.worker = AStarWorker(self._stackData, self._startPnt, self._stopPnt, self._queue)
        # Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.signalFinished.connect(self.thread.quit)
        self.worker.signalFinished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        #self.worker.signalProgress.connect(self.slot_reportProgress)  # receive points
        
        # Start the thread
        self.thread.start()

        # otherwise thread is not actually started in the next line of code
        #time.sleep(0.01)

        logger.info('!!! RETURNED FROM start()')

        # monitor queue and emit progress
        _updateInterval = 250  # wait for this number of results and update plot
        plotItems = []
        #while self.thread.isRunning() or not self._queue.empty():
        while self.thread.isRunning() and not self.thread.isFinished():
            # if self.worker._aStarSearch.search_algorithm.found_path:
            #     logger.info('A* search found a path ... exiting while loop to monitor queue')
            #     break

            # always empty ???
            #print('queue is always empty???', list(self._queue.queue))

            try:
                item = self._queue.get(False)
                # update a matplotlib/pyqtgraph/napari interface
                plotItems.append(item)
                if len(plotItems) > _updateInterval:
                    #_plot_points(plotItems, 'c', 8, 0.3)
                    #self.signalProgress.emit(plotItems)
                    self.slot_reportProgress(plotItems)
                    plotItems = []
            except Empty:
                # Handle empty queue here
                pass

            maxtime = 5  # ms, choice here will drastically change the responsiveness of the pyqt interface
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, maxtime)  # maxtime in ms
            
        logger.info('!!! after while')
        
        # Final resets
        # self.longRunningBtn.setEnabled(False)
        # self.thread.finished.connect(
        #     lambda: self.longRunningBtn.setEnabled(True)
        # )

        # self.thread.finished.connect(
        #     lambda: self.stepLabel.setText("Long-Running Step: 0")
        # )

    def slot_reportProgress(self, pnts : List[tuple[int,int,int]]):
        logger.info(f'_progressSteps:{self._progressSteps} received {len(pnts)} pnts. pnts[0]:{pnts[0]}')
        self._progressSteps += 1

        # a mask of A* tracing progress
        #logger.info('todo: fix logic of _myTracingMask, this recreates on each set slice')
        # _imageLabel = self._stack._sliceImage.copy()
        # _imageLabel[:] = 0

        yPnts = []
        xPnts = []
        for pnt in pnts:
            yPnts.append(pnt[1])
            xPnts.append(pnt[2])

        self._searchedMask[yPnts, xPnts] = 255
        # self._imageLabel = _imageLabel  # update self._imageLabel with tracing results and self.update()
        self._stackWidget._myGraphPlotWidget._myTracingMask.setImage(self._searchedMask, opacity=0.5)

        # self._stackWidget._myGraphPlotWidget.update()  # update pyqtgraph interface

        # maxtime = 20  # ms
        # QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, maxtime)  # maxtime in ms

def run():
    import pymapmanager as pmm
    import pymapmanager.interface

    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'
    myStack = pmm.stack(path=path)
    
    #myStack.loadImages(channel=1)
    myStack.loadImages(channel=2)
    
    # do this once and save into backend and file
    # myStack.createBrightestIndexes(channelNum = 2)

    # run pyqt interface
    app = QtWidgets.QApplication(sys.argv)

    bsw = pmm.interface.stackWidget(myStack=myStack)

    # useful on startup, to snap to an image
    bsw._myGraphPlotWidget.slot_setSlice(30)

    bsw.show()

    # this will only show us the answer, we need to actually add 'trace' to user interface
    #debugTracing(bsw)
    mtsw = moveToStackWidget(bsw, myStack)
    
    # run the actual tracing (hard coded 2 points to trace between)
    mtsw.runLongTask()
    
    print('!!! BACK IN __main__')

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()