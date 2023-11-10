import enum
import uuid
import sys

from queue import Empty, Queue
from threading import Thread
from typing import List

import tifffile

import numpy as np
import pandas as pd

import brightest_path_lib
from brightest_path_lib.algorithm import NBAStarSearch

class TracingThread(Thread):
    def __init__(self,
        image : np.ndarray,
        start_point : np.ndarray,
        goal_point : np.ndarray,
        queue = None):
        super().__init__(daemon=True)
        self.queue = queue
        self.search_algorithm = NBAStarSearch(image,
											start_point=start_point,
											goal_point=goal_point,
											open_nodes=queue)
    
    def cancel(self):
        self.search_algorithm.is_canceled = True
    
    def run(self):
        self.search_algorithm.search()
		
class pointTypes(enum.Enum):
    controlPoint = 'controlPoint'
    tracingPoint = 'tracingPoint'

class LineSegment():
	def __init__(self):
		
		self._columns = [
			'uuid',
			'x',
			'y',
			'z',
			'pointType'
		]
		
		self._df = pd.DataFrame(columns = self._columns)

	def addControlPoint(self, z, y, x):
		randomUuid = str(uuid.uuid4())
		pointDict = {
			'uuid' : randomUuid,
			'x' : x,
			'y': y,
			'z': z,
			'pointType': pointTypes.controlPoint.value
		}
		self._df.loc[len(self._df.index)] = pointDict

	def getControlPoints(self):
		df = self._df[ self._df['pointType'] == pointTypes.controlPoint.value]
		return df
	
	def getDataFrame(self):
		return self._df
	
	def getPointFromIdx(self, rowIdx : int, asDict = True):
		"""
		asDict is not necc. as pandas series behave like dict?
		"""
		row = self._df.loc[rowIdx]
		if asDict:
			return dict(row)
		else:
			return row
	
	def _getStartStop(self, uuidStop):
		df = self.getControlPoints()
		
		dfStop = df[ df['uuid']==uuidStop ]
		if dfStop.index == 0:
			print('error')
			return
		
		z = dfStop['z'].values[0]
		y = dfStop['y'].values[0]
		x = dfStop['x'].values[0]
		stopPoint = np.array([z, y, x])

		# find row of uuid start
		dfStart = df.loc[dfStop.index-1]
		z = dfStart['z'].values[0]
		y = dfStart['y'].values[0]
		x = dfStart['x'].values[0]
		startPoint = np.array([z, y, x])

		# print('startPoint:', startPoint)
		# print('stopPoint:', stopPoint)

		return startPoint, stopPoint
	
	def traceThread(self, imgData : np.ndarray, uuidStop : 'uuid', queue):
		"""Given a controlPoint, trace from previous control point to uuidEnd.
		"""
	
		startPoint, stopPoint = self._getStartStop(uuidStop)
		
		# search_algorithm = NBAStarSearch(imgData, start_point=startPoint, goal_point=stopPoint)
		# brightest_path =search_algorithm.search()
		# print('brightest_path:', brightest_path)

		search_thread = TracingThread(imgData, startPoint, stopPoint, queue)
		search_thread.start()  # start the thread, internally Python calls tt.run()

		# while search_thread.is_alive() or not queue.empty(): # polling the queue
		# 	# comment this out to see the full animation
		# 	if search_thread.search_algorithm.found_path:
		# 		print('found answer')
		# 		break

		return search_thread
	
def testRun():
	tifPath = '/media/cudmore/data/Dropbox/PyMapManager-Data/maps/rr30a/rr30a_s0_ch2.tif'
	imgData = tifffile.imread(tifPath)
	
	print('imgData:', imgData.shape)

	# load point annotations df and grab segment id 0
	paPath = '/media/cudmore/data/Dropbox/PyMapManager-Data/maps/rr30a/rr30a_s0/rr30a_s0_pa.txt'
	segmentID = 0
	dfPoints = pd.read_csv(paPath, header=1)
	dfPoints = dfPoints[ dfPoints['segmentID']==segmentID]
	dfPoints = dfPoints[ dfPoints['roiType']=='controlPnt']
	
	ls = LineSegment()

	for i in range(5):
		onePoint = dfPoints.iloc[i]

		z = onePoint['z']
		y = onePoint['y']
		x = onePoint['x']
		ls.addControlPoint(z, y, x)

	pointDict = ls.getPointFromIdx(1)
	uuidStop = pointDict['uuid']

	# non thread
	queue = Queue()
	_traceThread = ls.traceThread(imgData, uuidStop, queue=queue)
	print('back in testRun()')

	_traceThread.cancel()

	while _traceThread.is_alive() or not queue.empty(): # polling the queue
		# comment this out to see the full animation
		if _traceThread.search_algorithm.found_path:
			print('found answer')
			break

	# df = ls.getControlPoints()
	# print(df)

if __name__ == '__main__':
	testRun()
