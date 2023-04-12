import os

from pymapmanager._logger import logger

def pmmDataPath():
    """Get the full/absolute path to PyMapManager-Data folder.
    
    This needs to be manually placed in the same folder that
    the PyMapManager source code is contained in.
    """
    # /Users/cudmore/Sites/PyMapManager/pymapmanager/
    _absPath = os.path.abspath(__file__)
    _path, _file = os.path.split(_absPath)  # pymapmanager/
    _path, _folder = os.path.split(_path)  # PyMapManager/
    _path, _folder = os.path.split(_path)  # ../
    _pmmDataPath = os.path.join(_path, 'PyMapManager-Data')
    #print(_pmmDataPath)
    if not os.path.isdir(_pmmDataPath):
        logger.error(f'Did not find path: {_pmmDataPath}')
        return
    return _pmmDataPath

if __name__ == '__main__':
    _pmmDataPath = pmmDataPath()
    print(_pmmDataPath)
