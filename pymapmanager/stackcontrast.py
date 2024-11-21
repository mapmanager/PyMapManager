import numpy as np

from pymapmanager import stack

class StackContrast():
    def __init__(self, theStack : stack):
        self._stack : stack = theStack
        self._dict = {}


        self._setDefaults()

    def getValue(self, channelIdx, key):
        return self._dict[channelIdx][key]
    
    def setValue(self, channelIdx, key, value):
        self._dict[channelIdx][key] = value

    def _setDefaults(self):
        
        for channelIdx in range(self._stack.numChannels):
            minAutoContrast, maxAutoContrast, globalMin, globalMax = self._stack.getAutoContrast(channelIdx=channelIdx)

            minAutoContrast_rgb = 0
            maxAutoContrast_rgb = 200
            
            self._dict[channelIdx] = {
                'colorLUT': self._stack.channelColors[channelIdx],
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