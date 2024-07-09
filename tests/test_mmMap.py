import pytest

import pymapmanager as pmm

def _test_mmMap_init():
    return

    path = '/Users/cudmore/Sites/PyMapManager-Data/public/rr30a/rr30a.txt'
    _map = pmm.mmMap(path)

    print(_map._mapTable)