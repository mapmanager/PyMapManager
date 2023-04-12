"""
A map is a  list of stack.
"""
import os
import pandas as pd

class mmMap():
    def __init__(self, filePath : str):
        """
        Args:
            filePath : 
        """
        if not os.path.isfile(filePath):
            raise FileNotFoundError

        self._mapTable = pd.read_table(filePath, index_col=0)

if __name__ == '__main__':
    import pymapmanager as pmm
    path = '/Users/cudmore/Sites/PyMapManager-Data/public/rr30a/rr30a.txt'
    _map = pmm.mmMap(path)

    print(_map._mapTable)