import os
import json
from typing import List

from json.decoder import JSONDecodeError

from pymapmanager._logger import logger

class Preferences:
    """Application preferences.
    
    This is saved and loaded into a user folder.
    """
    def __init__(self, app):
        
        self._app = app
        
        # self._version = 0.1
        # self._version = 0.23  # adding default window size
        self._version = 0.24  # upgrade to zar
        self._version = 0.25  # removed load stack (we only load mmap either from tif or mmap file)
        # johnson, when you change the format of saved json, manually bump the version
        self._version = 0.26 # abj: dictionary to hold path, timepoints number, and save 
        self._version = 0.27 # added recentMapFolder

        self._maxRecent = 10
        self._configDict = self.load()

    def getStackWindowGeometry(self) -> List[int]:
        """Get window geometery as [left, top, width, height].
        """
        posDict = self._configDict['windowGeometry']
        x = posDict['x']
        y = posDict['y']
        width = posDict['width']
        height = posDict['height']
        theRet = [x, y, width, height]
        return theRet
    
    # def getMostRecentStack(self):
    #     return self.configDict["mostRecentStack"]

    # def getRecentStacks(self):
    #     return self.configDict["recentStacks"]

    # def getMostRecentMap(self) -> str:
    #     return self.configDict["mostRecentMap"]

    # def getRecentMaps(self):
    #     return self.configDict["recentMaps"]
    
    # abj
    def getMostRecentMap(self) -> str:
        return self.configDict["mostRecentMapDict"]

    def getRecentMapDicts(self):
        return self.configDict["recentMapDicts"]

    @property
    def configDict(self):
        return self._configDict

    def __setitem__(self, key, item):
        if key not in self._configDict.keys():
            logger.warning(f'did not find key "{key}"')
            return
        self._configDict[key] = item

    def __getitem__(self, key):
        if key not in self._configDict.keys():
            logger.warning(f'did not find key "{key}"')
            return
        return self._configDict[key]

        self.save()

    def old_addMapPath(self, mapPath : str):
        """Add a map path to recent maps
        """

        if mapPath not in self.configDict["recentMaps"]:
            self.configDict["recentMaps"].append(mapPath)
            
            # reduce/limit list to last _maxRecent
            self.configDict["recentMaps"] = self.configDict["recentMaps"][-self._maxRecent :]

        # always set as the most recent file
        self.configDict["mostRecentMap"] = mapPath

        self.save()

    def _find_index_of_dict_with_value(self, dicts, key, value):
        for index, dictionary in enumerate(dicts):
            if dictionary.get(key) == value:
                return index
        return None # none if not found

    def clearMapPathDict(self):
        self.configDict["recentMapDicts"] = []
        
    def addMapPathDict(self, mapPathDict : dict):
        """Add a map path dict to recent maps

        map path dict:
            'Path': pathToOpenedMap,
            'Last Save Time' : 'yyyymmdd hh:mm'
            'Timepoints: 1,

        """
        currentPath = mapPathDict["Path"]
        # check to see if path is unique
        dictList = self.configDict["recentMapDicts"]
        indexCheck = self._find_index_of_dict_with_value(dictList, "Path", currentPath)
        # if mapPathDict["Path"] not in 

        if indexCheck is None:
            self.configDict["recentMapDicts"].append(mapPathDict)
            
            # reduce/limit list to last _maxRecent
            self.configDict["recentMapDicts"] = self.configDict["recentMapDicts"][-self._maxRecent :]
        
        else:
            # replace current map dict with new map dict
            self.configDict["recentMapDicts"][indexCheck] = mapPathDict

        # always set as the most recent file
        self.configDict["mostRecentMapDict"] = mapPathDict

        self.save()

    # abj
    def addMapFolder(self, folderPath):
        """
        """
        # self.configDict["mostRecentMapDict"]
        if folderPath not in self.configDict["recentMapFolders"]:
            self.configDict["recentMapFolders"].append(folderPath)
        
        self.save()

    def preferencesSet(self, key1, key2, val):
        """Set a preference. See `getDefaults()` for key values."""
        try:
            self._configDict[key1][key2] = val
        except KeyError:
            logger.error(f'Did not set preference with keys "{key1}" and "{key2}"')

    def preferencesGet(self, key1, key2):
        """Get a preference. See `getDefaults()` for key values."""
        try:
            return self._configDict[key1][key2]
        except KeyError:
            logger.error(f'Did not get preference with keys "{key1}" and "{key2}"')

    def getPreferencesFile(self):
        appDataFolder = self._app.getAppDataFolder()
        if not os.path.isdir(appDataFolder):
            os.mkdir(appDataFolder)
        return os.path.join(appDataFolder, 'preferences.json')
    
    def load(self):
        """Always load preferences from:
            <user>/Documents/SanPy/preferences/sanpy_preferences.json
        """

        preferencesFile = self.getPreferencesFile()

        useDefault = True
        if os.path.isfile(preferencesFile):
            logger.info("Loading preferences file")
            logger.info(f"  {preferencesFile}")
            try:
                with open(preferencesFile) as f:
                    loadedJson = json.load(f)
                    loadedVersion = loadedJson["version"]
                    logger.info(f"  loaded preferences version {loadedVersion}")
                    if loadedVersion < self._version:
                        # use default
                        logger.warning(
                            "  older version found, reverting to current defaults"
                        )
                        logger.warning(
                            f"  loadedVersion:{loadedVersion} currentVersion:{self._version}"
                        )
                        pass
                    else:
                        return loadedJson
            except JSONDecodeError as e:
                logger.error(e)
            except TypeError as e:
                logger.error(e)
        if useDefault:
            logger.info("  Using default preferences")
            return self.getDefaults()

    def save(self):
        preferencesFile = self.getPreferencesFile()

        logger.info(f'Saving preferences file as: "{preferencesFile}"')

        with open(preferencesFile, "w") as outfile:
            json.dump(self._configDict, outfile, indent=4, sort_keys=True)

    def getDefaults(self) -> dict:
        """Get default preferences.

        Be sure to increment self._version when making changes.
        """
        configDict = {}

        configDict["version"] = self._version
        configDict["theme"] = 'dark'  # in ['dark', 'light', 'auto']

        # configDict["recentStacks"] = []
        # configDict["mostRecentStack"] = ""

        # configDict["recentMaps"] = []
        # configDict["mostRecentMap"] = ""

        configDict["recentMapDicts"] = []
        configDict["mostRecentMapDict"] = ""

        configDict["recentMapFolders"] = []

        # stack window geometry
        # PyQt5.QtCore.QRect(80, 126, 734, 547)
        configDict["windowGeometry"] = {}
        configDict["windowGeometry"]["x"] = 75
        configDict["windowGeometry"]["y"] = 75
        configDict["windowGeometry"]["width"] = 734
        configDict["windowGeometry"]["height"] = 547

        configDict['logLevel'] = 'INFO'

        return configDict

    def getRecentMapsDataframe(self):
        pass

    def clearRecentFiles(self):
        self.configDict["recentMapDicts"].clear()
        self.configDict["mostRecentMapDict"] = ""
        self.save()
