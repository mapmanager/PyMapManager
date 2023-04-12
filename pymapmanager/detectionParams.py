"""
This is a common patttern we want to use in lots of places.

What I really want is a ...
"""

import pandas as pd

from pymapmanager._logger import logger

class DetectionParams:
    def __init__(self):
        """A class to encapsulate common image analysis detections parameters.
        
        This behaves like a dictionary where parameter names are keys
        """
        self._dict = {}

        self._defineDetectionParams()

    def _defineDetectionParams(self):
        """Define all the detection parameters.
        """
        key = 'extendHead'
        defaultValue = 5
        description = 'Extend the head of a spine'
        see = 'Creating a rect roi for a spine'
        self._addDetectionParam(key, defaultValue=defaultValue, description=description, see=see)

        key = 'extendTail'
        defaultValue = 3
        description = 'Extend the tail of a spine'
        see = 'Creating a rect roi for a spine'
        self._addDetectionParam(key, defaultValue=defaultValue, description=description, see=see)


    def _addDetectionParam(self, key : str,
                        defaultValue,
                        description : str,
                        see : str):
        """Add a new detection parameter key.
        
        Args:
            key : the name of the detection parameter
            defaultValue : the default value for the detection parameter
            description : human redable descition of what the detection parameter does
            see : notes on what part of the code to look for usage
        
        Raises:
            KeyError: if the key already exists, it is not added
        """
        if self._paramExists(key):
            logger.error(f'key "{key}" already exists in dict ... not added')
            return
        
        _dict = {
            'currentValue': defaultValue,
            'defaultValue': defaultValue,
            'description': description,
            'see': see
        }
        self._dict[key] = _dict

    def setCurrentValue(self, key : str, value):
        """Set a detection parameter current value.
        """
        if not self._paramExists():
            logger.error(f'key "{key}" does not exists in dict ... not set')
            return

        self._dict[key]['currentValue'] = value

    def _paramExists(self, key):
        """Check if a detection parameter exists.
        """
        return key in self._dict.keys()
    
    def __getitem__(self, key):
        """Allow [] indexing with ['key'].

        Returns:
            The current value for a given key
        """
        try:
            return self._dDict[key]['currentValue']
        except (KeyError) as e:
            logger.error(f'{e}')

    def _getDocs(self) -> str:
        """Make self documentation from our dict.
        
        Notes:
            This is not ideal, we really want each key as a row
            and all values like (currentValue, description) as columns
        """
        df = pd.DataFrame(self._dict)
        return df
    
if __name__ == '__main__':
    dp = DetectionParams()
    print(dp._getDocs())
