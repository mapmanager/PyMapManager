"""
Command line script to trace in Fiji using simple Neurite Tracer.

fijiPath: Full path to fiji lifeline 2017
pluginPath: Full path to our custom Jyphon Fiji plugin (do the work)

Usage:
    1) save a file 'tracingparameters.txt'

    '''
    tiffFile=/Volumes/mapmanager/Users/cudmore/Dropbox/data/Shu-Ling/Shu-Ling_tif/mm_maps/ling_map_1/raw/ling_map_1_s0_ch2.tif
    point=228,343,18
    point=261,341,18
    point=285,327,18
    point=330,316,18
    point=360,308,21
    point=407,312,24
    '''

    2) run the plugin

    3) wait for 'tracing_finished.txt' to appear.
        Note, before we trace, we need to remove this file
    
    4) load (x,y,z) tracing from tracing_out.txt



"""
import os
import subprocess

from tracing._logger import logger

# the folder that has our Jython plugin and
#   where we save/load tracing output/input
def runScript():
    tracingFolderPath = '/Users/cudmore/Sites/PyMapManager/sandbox/traceInFiji2017'

    # does not have to be part of pymapmanager
    # usually installed on users system
    fijiPath = '/Users/cudmore/Downloads/Fiji_20170530.app/Contents/MacOS/ImageJ-macosx'

    pluginPath = os.path.join(tracingFolderPath, 'BobNeuriteTracer_v1_.py')

    # 1) remove tracing_finished.txt
    tracingFinishedPath = os.path.join(tracingFolderPath, 'tracing_finished.txt')

    # 2) save 'tracingparameters.txt'
    tracingParametersPath = os.path.join(tracingFolderPath, 'tracingparameters.txt')

    # 3) run the plugin

    print(f'  fijiPath:', fijiPath)
    print(f'  pluginPath:', pluginPath)
    print(f'  tracingFinishedPath:', tracingFinishedPath)
    print(f'  tracingParametersPath:', tracingParametersPath)

    #   Can't use os.system() as it blocks
    commandLineStr = f'{fijiPath} {pluginPath}'

    # this works but blocks
    #os.system(commandLineStr)

    print('  == traceInFiji starting subprocess')
    _popen = subprocess.Popen([fijiPath, pluginPath])
    print('  entering while not done')
    while _popen.poll() is None:
        continue
        # allow ctrl-c ???
        # we need to embed this into PyQt to handle event loop?

    # 4) check for 'tracing_finished.txt'

    print('  == traceInFiji is done.')

class mmTracer:
    def __init__(self) -> None:
        
        self._fijiApp = ''
        # Full path to Fiji.app like
        # Fiji.app/Contents/MacOS/ImageJ-macosx
        
        self._pluginPath = ''
        # Full path to Jython script BobNeuriteTracer_v1_.py
        # This is run as a plugin in Fiji.app

    def setFijiPath(self, path : str):
        if not os.path.isfile(path):
            print(f'ERROR: setFijiPath() did not find poath: {path}')
            return
        
        self._fijiApp = path

if __name__ == '__main__':
    runScript()