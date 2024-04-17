"""Collection of function to mutate (edit) mapmanagercore.
"""
from typing import List, Union, Optional

from mapmanagercore import MapAnnotations

# import pymapmanager

from pymapmanager._logger import logger

def editSpineEvent(mmWidget : "mmWidget",
                spineID : List[int],
                col : str,
                value : object):
    """Update spine properies (row, col, value) in core.
    """
    coreMap = mmWidget.getStackWidget().getStack().getCoreMap()

    for oneEdit in editSpineProperty:
        spineID = oneEdit['spineID']
        col = oneEdit['col']
        value = oneEdit['value']

        value = {
            col:  value
        }

        # map.updateSpine(spineId=id, value={"f": 1})
        coreMap.updateSpine(spineId=spineID, value=value)

        logger.info(f'=== updateSpine spine {spineID} in backend')
        
def addSpine(theMap : MapAnnotations,
             x : int, y : int, z : int,
             segmentID : int
             ):
    """Add a new spine to backend core.

    Parameters
    ----------
    map :
    x,y,z : int
    segmentID : int
    """
    spineID = theMap.addSpine(segmentId=segmentID, x=x, y=y, z=z)
    logger.info(f'=== added spine {spineID} to backend')
    return id

def deleteSpine(theMap : MapAnnotations,
                spineID
                ):
    """Delete spine from backend core.
    """
    theMap.deleteSpine(spineID)
    logger.info(f'=== deleted spine {spineID} to backend')
    return True



