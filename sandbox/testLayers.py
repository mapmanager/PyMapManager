import sys

import pymapmanager.mmMap

import pymapmanager.interface
import pymapmanager.annotations
from pymapmanager._logger import logger
from pymapmanager.annotations.pmmLayers import PmmLayers
from pymapmanager.options import Options

def run():
    
    # load a backend stack
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    
    # load one stack
    stack = pymapmanager.stack(path=path, loadImageData=True)
    # logger.info(f'myStack: {stack}')

    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()
    layers = PmmLayers(pa, la)

    spGP = layers.createSpinePointGeoPandas()
    spGP.to_csv("spineGeoPandas.csv")
    logger.info(f'spGP: {spGP}')
    # lGP = layers.createLineGeoPandas()
    # logger.info(f'lGP: {lGP}')

    # options = {"selection": {'z': [29,30]},
    #            "showLineSegments": True,
    #         #    "annotationSelections": { # Note this requires the values to be strings
    #         #         'segmentID': '1',
    #         #         'spineID': '33'},
    #             "annotationSelections": { # Note this requires the values to be strings
    #                 'segmentID': '0',
    #                 'spineID': '99'}, # Keeping original index
    #         #    "annotationSelections": [33],
    #            "showLineSegmentsRadius": 3,
    #            "showSpines": True,
    #            "filters": [], #[1,2,3,4],
    #            "showAnchors": True,
    #            "showLabels": True
    #         }

    options = Options()
    
    test = layers.getLayers(options)
    # lineDF = test[0]

    # logger.info(f"lineDF {lineDF}")

    # lineDF1 = test[1]
    # logger.info(f"lineDF1 {lineDF1}")

    logger.info(f"test: {test[0]}")
    logger.info(f"testing utils: {test[0]._encodeBin()}")
    # lineDF = test[0]
    # lGP.to_csv("out.csv")
    


if __name__ == '__main__':
    run()
