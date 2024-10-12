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
        # johnson, when you change the format of saved json, manually bump the version

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
    
    def getMostRecentStack(self):
        return self.configDict["mostRecentStack"]

    def getRecentStacks(self):
        return self.configDict["recentStacks"]

    def getMostRecentMap(self):
        return self.configDict["mostRecentMap"]

    def getRecentMaps(self):
        return self.configDict["recentMaps"]

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

    def _old_addStackPath(self, stackPath : str):
        """Add a single timepoint stack.
        
        Similar to addMapPath.
        """

        if stackPath not in self.configDict["recentStacks"]:
            self.configDict["recentStacks"].append(stackPath)
            # limit list to last _maxNumUndo
            self.configDict["recentStacks"] = self.configDict["recentStacks"][
                -self._maxRecent :
            ]

        # always set as the most recent file
        self.configDict["mostRecentStack"] = stackPath

        self.save()

    def addMapPath(self, mapPath : str):
        """Add a map path.
        Similar to addMapPath.
        """

        if mapPath not in self.configDict["recentMaps"]:
            self.configDict["recentMaps"].append(mapPath)
            # limit list to last _maxNumUndo
            self.configDict["recentMaps"] = self.configDict["recentMaps"][-self._maxRecent :]

        # always set as the most recent file
        self.configDict["mostRecentMap"] = mapPath

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

        configDict["recentStacks"] = []
        configDict["mostRecentStack"] = ""

        configDict["recentMaps"] = []
        configDict["mostRecentMap"] = ""

        # stack window geometry
        # PyQt5.QtCore.QRect(80, 126, 734, 547)
        configDict["windowGeometry"] = {}
        configDict["windowGeometry"]["x"] = 75
        configDict["windowGeometry"]["y"] = 75
        configDict["windowGeometry"]["width"] = 734
        configDict["windowGeometry"]["height"] = 547

        configDict['logLevel'] = 'INFO'

        return configDict
