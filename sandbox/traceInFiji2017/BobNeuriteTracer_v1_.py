#Robert H Cudmore
#20161213

'''
	1) load tif
	   Remove scale, tracing assumes we have 1x1x1 voxels
	2) load list of 3d points
	3) for each pnt i, trace from pnt i to pnt i+1
	     collect the tracing in a list
	5) save the list
	...
	...
	6) import back into igor

	Notes=====
	- Do not use 'with', it is not supported in Fiji 2013 (Python 2.6)
	- run this with command line

/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx /Users/cudmore/Dropbox/bob_fiji_plugins/BobNeuriteTracer_v1_.py
	or
/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx --headless --run /Users/cudmore/Dropbox/bob_fiji_plugins/BobNeuriteTracer_v1_.py


	on windows, fiji opens files with
C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif

	copied from igor
C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py 'tiffilename=\"C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif\", controlfilename=\"C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\stackdb\\line\\s_0071_c1.txt\"'
	massaged to paste into command line
C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py 'tiffilename="C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif", controlfilename="C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\stackdb\\line\\s_0071_c1.txt"'

C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --headless --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py 'tiffilename="C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif, controlfilename=C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\stackdb\\line\\s_0071_c1.txt'


C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --headless --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py 'tiffilename="C\Users\cudmore\Dropbox\MapManagerData\batch_test\batch_test_tif\s_0071_ch1.tif, controlfilename=C\Users\cudmore\Dropbox\MapManagerData\batch_test\batch_test_tif\stackdb\line\s_0071_c1.txt'

C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --headless --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py tiffilename=C:/Users\cudmore\Dropbox\MapManagerData\batch_test\batch_test_tif\s_0071_ch1.tif, controlfilename=C:\Users\cudmore\Dropbox\MapManagerData\batch_test\batch_test_tif\stackdb\line\s_0071_c1.txt


ALMOST, this works for tiff but gets nothin for control
C:\\Users\\cudmore\\Fiji.app\\ImageJ-win64.exe --console --headless --run C:\\Users\\cudmore\\Dropbox\\bJHU\\Tracing\\BobNeuriteTracer_v1_.py tiffilename=\"C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif\" controlfilename=\"C:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\stackdb\\line\\s_0071_c1.txt\"

'''

import os, sys

from ij import IJ

from tracing import PathAndFillManager
from tracing import TracerThread

#TracerThread tracer = new TracerThread(imagePlus, 0, 255, timeoutSeconds, reportEveryMilliseconds, x1, y1, z1, x2, y2, z2, reciprocal, depth == 1, hessian, ((hessian == null) ? 1 : 4), null, hessian != null );

# mac
#defaultTiff = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/s_0071_ch1.tif'
#defaultControl = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/stackdb/line/s_0071_c0.txt'
# windows
#defaultTiff = 'c:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\s_0071_ch1.tif'
#defaultControl = 'c:\\Users\\cudmore\\Dropbox\\MapManagerData\\batch_test\\batch_test_tif\\stackdb\\line\\s_0071_c0.txt'

doDebug = 1

def runmain(tracingfolderpath):

	# tracingfolderpath gives us MapManager tracing path
	if not tracingfolderpath:
		tracingfolderpath = '/Users/cudmore/jhu/bJHU/Tracing/'
	
	# load thattiff.txt
	tracingparametersPath = os.path.join(tracingfolderpath, 'tracingparameters.txt')

	myPrint('tracingparametersPath:'+tracingparametersPath)
	
	tiffFilePath = ''
	pnts = []
	
	f = open(tracingparametersPath, 'rU')
	# tiffPath=/Volumes/vasculature/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/s_0071_ch1.tif
	line = f.readline().rstrip()
	lhs, rhs = line.split('=')
	tiffFilePath = rhs
	myPrint('tiffFilePath:'+tiffFilePath)
	
	line = f.readline().rstrip()
	while line:
		#print 'line:', line
		lhs, rhs = line.split('=')
		x, y, z = rhs.split(',')
		pnts.append([int(x),int(y),int(z)])
		line = f.readline().rstrip()
	f.close()

	myPrint('found ' + str(len(pnts)) + ' points to fit.')

	#
	# Load tif
	imp = IJ.openImage(tiffFilePath)  
	if imp is None:
		print 'error opening tiff file:', tiffFilePath
		print '->> Aborting'
		return 0
	myPrint('opened tiffilename:'+tiffFilePath)
	
	#
	# remove calibration, all tracing is done in pixels
	imp.setCalibration(None)
	
	width = imp.getWidth()
	height = imp.getHeight()
	depth = imp.getStackSize()

	#
	# for each control point, accumulate tracing points into finalPntList
	finalPntList = []
	for i, pnt in enumerate(pnts):
		
		if i < len(pnts)-1:
			pass
		else:
			continue
		
		# trace from pnt i to pnt j (i+1)
		ix = pnts[i][0]
		iy = pnts[i][1]
		iz = pnts[i][2]
		
		jx = pnts[i+1][0]
		jy = pnts[i+1][1]
		jz = pnts[i+1][2]
		
		#Use the reciprocal of the value at the new point as the cost
		#in moving to it (scaled by the distance between the points).
		reciprocal = True;
		
		timeoutSeconds = 5
		reportEveryMilliseconds = 3000
		
		#hessian = None
			
		tracer = TracerThread(imp, 0, 255, timeoutSeconds, reportEveryMilliseconds, ix,iy,iz,jx,jy,jz, reciprocal, depth == 1, None, 1, None, False )
		tracer.run()
		result = tracer.getResult().getPoint3fList()
	
		for resultPnt in enumerate(result):
			#print 'resultPnt:', resultPnt[1].x
			#print type(resultPnt[1])
			x = resultPnt[1].x
			y = resultPnt[1].y
			z = resultPnt[1].z
			finalPntList.append([x, y, z])


	myPrint('fit with ' + str(len(finalPntList)) + ' points')
	
	#
	# save tracing to output file <in>.mast
	outfile = os.path.join(tracingfolderpath,'tracing_out.txt')
	of = open(outfile, "w")
	for pnt in finalPntList:
		#print pnt
		outline = '(' + str(pnt[0]) + ',' + str(pnt[1]) + ',' + str(pnt[2]) + ')'
		of.write(outline + '\n')
	of.close()
	myPrint('saved tracing to:'+outfile)
	
	#
	# make a file to signal we are finished
	finishfile = os.path.join(tracingfolderpath,'tracing_finished.txt')
	of = open(finishfile, "w")
	of.write('finished' + '\n')
	of.close()
	myPrint('saved finished file to:'+finishfile)

	myPrint('Done')
	
def myPrint(theStr):
	global doDebug
	if doDebug:
		print theStr
		
if __name__ in ['__main__', '__builtin__']:
	
	print '=== in main of bobneuritetracer'
	#print '__file__:', __file__
	
	# on mac, sys.argv gives us the path to this file
	# ['/Users/cudmore/jhu/bJHU/Tracing/BobNeuriteTracer_v1_.py']
	myPrint('sys.argv[0]:'+sys.argv[0])
	thePath = ''
	if len(sys.argv) == 1 and sys.argv[0]:
		thePath, theFile = os.path.split(sys.argv[0])
	else:
		print 'WARNING: BobNeuriteTracer_v1.py needs to be called from command line'
		
	runmain(thePath)