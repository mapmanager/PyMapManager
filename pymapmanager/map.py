"""
Coming Soon !!!
"""
import os

import pymapmanager.stack

from pymapmanager._logger import logger

class map():
    """
    A map is a list of pymapmanager.stack.stack with book-keeping to connect annotations between stacks.
    
    The list of stacks is conceptually a list of time-points. Stacks imaged at different times from seconds to weeks.
    """
    
    def __init__(self, folderPath : str):
        
        # we expect a folder, check if we got a file
        if os.path.isfile(folderPath):
            folderPath = os.path.split(folderPath)[0]

        folderName = os.path.split(folderPath)[1]
        mapFileName = folderName + '.txt'
        
        self._stacks = []
        """ A list of pymapmanager.stack.stack"""
        
        self._mapFolderPath = folderPath
        self._mapFilePath = os.path.join(folderPath, mapFileName)
        """Full path to folder containing the map"""

        loadedDict = self.load()

        if loadedDict is not None:
            self._mapDict = loadedDict
        else:
            self._mapDict = self.newMap()

    def __str__(self):
        printList = []
        printList.append('map')
        printList.append(f'{self._mapFilePath}')
        printList.append(f'num stacks {self.numStacks}')
        return ' '.join(printList)
    
    def newMap(self):
        logger.info(f'Making new map: {self._mapFilePath}')
        mapDict = self._defaultMapDict()
        return mapDict

    def load(self):
        """
        Load a map from .txt file
        """
        if os.path.isfile(self._mapFilePath):
            # load
            return 'eventually contents'
        else:
            return None

    def save(self):
        """
        Save both our .txt file and any changes to stack annotations.
        """
        pass

    def getStacksFolder(self):
        """
        """
        return os.path.join(self._mapFolderPath, 'stacks')

    def addStack(self, tifPath):
        """
        Add a stack to the map.
        
        Requires loading from file. See addStackObject() to add a stack from already loaded pymapmanager.stack.stack
        """
    
        # load the stack with no data, use this to get all stack paths (tif(s), point annotation, line annotation
        theStack = pymapmanager.stack.stack(tifPath, loadData=False)
        print(theStack)
        print(theStack.printHeader())
        
        # copy the (tifs(s), point, and line annotations into map folder
        tifPathList = theStack._tifPathList
        for srcPath in tifPathList:
            #srcFile = os.path.split(srcTifPath)[1]
            dstPath = self.getStacksFolder()

        self._stacks.append(theStack)

    def _defaultMapDict(self):
        theDict = {
            'mapfilepath': self._mapFilePath,
            'numstacks': self.numStacks

        }
        return theDict.copy()

    def getStack(self, stackIdx : int):
        return self._stacks[stackIdx]

    def _saveStack(self, stackIDx : int):
        pass

    @property
    def numStacks(self):
        return len(self._stacks)

def run():
    folderPath = '/media/cudmore/data/richard/rr30a/firstMap'
    myMap = map(folderPath)
    print(myMap)

    #stackPath = '/media/cudmore/data/richard/rr30a/stacks/rr30a_s0_ch2.tif'
    # a tif with no annotations or header
    stackPath = '/media/cudmore/data/richard/rr30a/naked-tif/rr30a_s0_ch2.tif'
    myMap.addStack(stackPath)

    # test plot
    if 0:
        import matplotlib.pyplot as plt
        import pymapmanager.plotting.plottingUtils
        roiType = ['spineROI']
        segmentID = [2]
        stackIdx = 0
        myStack = myMap.getStack(stackIdx)
        pymapmanager.plotting.plottingUtils.plotMax(myStack, roiType=roiType, segmentID=segmentID)
        plt.show()
    
if __name__ == '__main__':
    run()