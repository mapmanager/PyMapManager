import numpy as np

from pymapmanager import stack

class StackContrast():
    def __init__(self, theStack : stack):
        self._stack : stack = theStack
        self._dict = {}

        self._channelColor = ['g', 'r', 'b']

        self._setDefaults()

    def getValue(self, channelIdx, key):
        return self._dict[channelIdx][key]
    
    def setValue(self, channelIdx, key, value):
        self._dict[channelIdx][key] = value

    def _setDefaults(self):
        _defaultDisplayBitDepth = 11
        
        for channelIdx in range(self._stack.numChannels):
            minAutoContrast, maxAutoContrast = self._stack.getAutoContrast(channelIdx=channelIdx)

            self._dict[channelIdx] = {
                'colorLUT': self._channelColor[channelIdx],
                'minContrast': minAutoContrast,  # set by user
                'maxContrast': maxAutoContrast,  # set by user
                'minAutoContrast': minAutoContrast,
                'maxAutoContrast': maxAutoContrast,
                'bitDepth': self._stack.header['bitDepth'],
                'displayBitDepth': _defaultDisplayBitDepth
            }
