import numpy
from PIL import Image, ImageDraw
import pylab as plt
import numpy as np

polygon = [(1,1),(1,4),(3,4),(3,1)] 
polygon2 = [(1,1),(1,5),(3,5),(3,1)] 

# polygon = [(x1,y1),(x2,y2),...] or [x1,y1,x2,y2,...]
width = 10
height = 10

img = Image.new('1', size=(width, height))
ImageDraw.Draw(img).polygon(polygon, outline=1, fill=None)
mask = numpy.array(img)
mask = mask.astype(int)

img2 = Image.new('1', size=(width, height))
ImageDraw.Draw(img2).polygon(polygon2, outline=1, fill=None)
mask2 = numpy.array(img2)
mask2 = mask2.astype(int)

combinedMask = mask2 + mask
print(combinedMask)
# combinedMask[combinedMask == 2] = 0
# coords = np.column_stack(np.where(combinedMask > 0))
# print(coords)

# print(combinedMask)
plt.imshow(combinedMask)
plt.show()
