import numpy as np

from pymapmanager import stack
from pymapmanager._logger import logger

class StackContrast():
    def __init__(self, theStack : stack):
        self._stack : stack = theStack
        self._dict = {}

        self._setDefaults()

    def getValue(self, channelIdx, key):
        # channelIdx += 1
        return self._dict[channelIdx][key]
    
    def setValue(self, channelIdx, key, value):
        self._dict[channelIdx][key] = value

    def _setDefaults(self):
        # logger.info('xxx metadata')
        from pprint import pprint
        # pprint(metadata)

        timepointMetadata = self._stack.getMetadata()

        # for channelIdx in range(self._stack.numChannels):
        for channelIdx in self._stack.getChannelList(): # abj
            channelMetadata = timepointMetadata.getChannelMetadata(channelIdx)
            # print('channelMetadata is:')
            # pprint(channelMetadata)

            # minAutoContrast, maxAutoContrast, globalMin, globalMax = self._stack.getAutoContrast(channelIdx=channelIdx)
            minAutoContrast = channelMetadata.minContrast
            maxAutoContrast = channelMetadata.maxContrast
            globalMin = channelMetadata.minInt
            globalMax = channelMetadata.maxInt

            minAutoContrast_rgb = 0
            maxAutoContrast_rgb = 200
            
            # channelIdx in core is now a str (not int)
            # we need to abstract this away from PyMapMAnager
            # it should not care which it is
            channelInt = int(channelIdx)
            
            self._dict[channelIdx] = {
                'colorLUT': self._stack.channelColors[channelInt],
                'globalMin': globalMin,  
                'globalMax': globalMax,
                'minAutoContrast': minAutoContrast,  # set by user
                'maxAutoContrast': maxAutoContrast,  # set by user
                #
                'minAutoContrast-rgb': minAutoContrast_rgb,  # set by user
                'maxAutoContrast-rgb': maxAutoContrast_rgb,  # set by user
            }

        # if self._stack.numChannels > 1:
        #     # rgb, we have 3 channels, each is 8-bit
        #     self._dict['rgb'] = {
        #         'colorLUT': None,  #self._stack.channelColors[channelIdx],
        #         'globalMin': 0,  # set by user
        #         'globalMax': 255,  # set by user
        #         'minAutoContrast': minAutoContrast,
        #         'maxAutoContrast': maxAutoContrast,
        #     }