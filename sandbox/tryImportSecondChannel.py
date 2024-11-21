
from mapmanagercore import MapAnnotations, MultiImageLoader
import mapmanagercore.data
from ..lazy_geo_pd_images import LazyImagesGeoPandas, ImageLoader

loader = MultiImageLoader()

path_ch1 = mapmanagercore.data.getTiffChannel_1()

loader.read(path_ch1, channel=0)
_build : ImageLoader = loader.build()

map = MapAnnotations(_build)

# try and add a second channel to map
# we need to add the second channel to LazyImagesGeoPandas._images

path_ch2 = mapmanagercore.data.getTiffChannel_2()
loader2.read(path_ch2, channel=0)  # ????
_build2 : ImageLoader = loade2.build()

# general problem is that this was all designed to be pre-built with all desired channels
# we need it to work 'from scratch'
