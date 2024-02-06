import pymapmanager as pmm
import pandas as pd
from pymapmanager.annotations import PmmLayers
from pymapmanager._logger import logger

def get_selected(df: pd.DataFrame, pointName: str, selected_ids: [str, str]):
    if df.index.name == pointName:
        # logger.info(f"df.index.name: {df.index.name}")
        # # logger.info(f"df.index == selected_ids[selection_id]: {df.index == selected_ids[selection_id]}")
        # logger.info(f"selected_ids[selection_id]: {selected_ids[selection_id]}")
        # logger.info(f"df.index: {df.index}")
        runningMask = None
        for i in selected_ids[pointName]:
           logger.info(f"i: {i}")
           logger.info(f"comparison: {df.index == i}")
           runningMask = df.index == i
        return df.index
    # logger.info(f"df: {df}")
    # logger.info(f"df[selection_id]: {df[selection_id]}")
    # logger.info(f"selected_ids[selection_id]: {selected_ids[selection_id]}")
    
    return df[pointName] == selected_ids[pointName]

def old_get_selected(df: pd.DataFrame, selection_id: str, selected_ids: [str, str]):
    if df.index.name == selection_id:

        return df.index == selected_ids[selection_id]
    
    return df[selection_id] == selected_ids[selection_id]

if __name__ == '__main__'   :
    
    
    path = '../PyMapManager-Data/one-timepoint/rr30a_s0_ch2.tif'

    
    # load one stack
    stack = pmm.stack(path=path, loadImageData=True)
    from pymapmanager.annotations.pmmLayers import PmmLayers
    from pymapmanager.options import Options
    pa = stack.getPointAnnotations()
    la = stack.getLineAnnotations()
    layers = PmmLayers(pa, la)
    df = layers.createSpinePointGeoPandas()
    selection_id = "spineID"
    logger.info(f"df: {df}")
    # selectionIDCustom = {'segmentID': '1', 'spineID': '99'}
    selectionIDCustom = {'segmentID': ['1','1'], 'spineID': ['99', '100']}
    selction = get_selected(df, selection_id, selected_ids= selectionIDCustom)
    logger.info(f"selction: {selction}")