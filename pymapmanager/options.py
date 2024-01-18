"""
Options

A state class that keeps track of everything to make displaying objects in the GUI easier.
"""

import pandas as pd
from pymapmanager._logger import logger

class Options():

    def __init__(self):
        """A class to encapsulate options that are used to track state of what is currently displayed in GUI.
        
        This behaves like a dictionary where parameter names are keys
        """
        self._optionsDict = {}

        self._defineOptions()


    def getOptionsList(self):
        """ Retrieve the key names of all parameters in the Dictionary
        
        """
        optionsList = []
        for key in self._optionsDict:
            optionsList.append(key)
     
        return optionsList
    
    def getCurrentValue(self, key):
        return self._optionsDict[key]['currentValue'] 
    
    def getOptionsDict(self):
        return self._optionsDict
    
    def _defineOptions(self):
        """Define all the Options parameters.
        """
        # "selection": {'z': [29,30]},
        #             "showLineSegments": True,
        #             "annotationSelections": { # Note this requires the values to be strings
        #                     'segmentID': '1',
        #                     'spineID': '33'},
        #             #    "annotationSelections": [33],
        #             "showLineSegmentsRadius": 3,
        #             "showSpines": True,
        #             "filters": [], #[1,2,3,4],
        #             "showAnchors": True,
        #             "showLabels": True

        # TODO: Connect options to desktop GUI to use with signals/ slot
        # self._addOption("slices", [29,30])
        # self._addOption("annotationSelections", {
        #                     'segmentID': '1',
        #                     'spineID': '33'})
            # # self._addOption("segmentID", [1])
            # # self._addOption("spineID", [33])
        # self._addOption("filters", [])
        # self._addOption("showLineSegmentsRadius", [3])
        # self._addOption("showLineSegments", True)
        # self._addOption("showSpines", True)
        # self._addOption("showAnchors", True)
        # self._addOption("showLabels", True)

        self._addOption("sliceRange", [])
        self._addOption("annotationSelections", {
                            'segmentID': '',
                            'spineID': ''})
        # self._addOption("segmentID", [1])
        # self._addOption("spineID", [33])
        self._addOption("filters", [])
        self._addOption("showLineSegmentsRadius", [3])
        self._addOption("showLineSegments", True)
        self._addOption("showSpines", True)
        self._addOption("showAnchors", True)
        self._addOption("showLabels", True)

    def _paramExists(self, key):
        """Check if a Options parameter exists.
        """
        return key in self._optionsDict.keys()
    
    def _addOption(self, key : str,
                        defaultValue,
                    ):
        """Add a new Option
        
        Args:
            key : the name of the Option parameter
            defaultValue : the default value for the Option parameter
            currentValue : the current value for the Option parameter
        
        Raises:
            KeyError: if the key already exists, it is not added
        """
        if self._paramExists(key):
            logger.error(f'key "{key}" already exists in dict ... not added')
            return
        
        _dict = {
            'currentValue': defaultValue,
            'defaultValue': defaultValue,
        }
        self._optionsDict[key] = _dict

    def setCurrentValue(self, key : str, value):
        """Set an Options parameter's current value.
        """
        if not self._paramExists(key):
            logger.error(f'key "{key}" does not exists in dict ... not set')
            return

        self._optionsDict[key]['currentValue'] = value

    def setSliceRange(self, sliceRange):
        """Set an Slice rangeS

        Args:
            sliceRange: [startInteger, endInteger] 
        """
        self.setCurrentValue("sliceRange", sliceRange)

    def setSelection(self, segmentID, spineID):
        """Set an Options parameter's current value.


        Args:
            sliceRange:  {'segmentID': '',
                            'spineID': ''})
        """

        if spineID != None:
            self.setCurrentValue("annotationSelections", {'segmentID': str(segmentID),
                                'spineID': str(spineID)})
        else:
            self.setCurrentValue("annotationSelections", None)

    def setMultipleSelection(self, segmentIDs, spineIDs):
        """Set an Options parameter's current value.


        Args:
            sliceRange:  {'segmentID': '',
                            'spineID': ''})
        """
        tmpDict = {}
        for i in spineIDs:
            tmpDict["segmentID"].append(segmentIDs[i])
            tmpDict["spineID"].append(i)
        
        logger.info(f"tmpDict {tmpDict}")
        self.setCurrentValue("annotationSelections", tmpDict)
                              
        # self.setCurrentValue("annotationSelections", {'segmentID': str(segmentID),
        #                     'spineID': str(spineID)})
    
    def __getitem__(self, key):
        """Allow [] indexing with ['key'].

        Returns:
            The current value for a given key
        """
        try:
            return self._optionsDict[key]['currentValue']
        except (KeyError) as e:
            logger.error(f'{e}')

# if __name__ == '__main__':
 