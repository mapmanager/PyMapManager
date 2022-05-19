## Using the REST API in a program

In addition to the browser interface, the PyMapManager server provides a REST interface allowing Map Manager data to be retrieved from almost any programming environment.

### In Python using the PyMapManager package

```python
from pymapmanager import mmMap
urlmap = 'rr30a'
m = mmMap(urlmap=urlmap)
```

What we just did was very powerful. We just loaded a map from an internet REST server!

### In pure Python

```python
import json
import urllib2

url='http://localhost:5000/api/v1/getmaptracing/public/rr30a?mapsegment=&session=3&xstat=x&ystat=y&zstat=z'

mytracing = json.load(urllib2.urlopen("url"))

# plot with matplotlib
import matplotlib.pyplot as plt
plt.plot(mytracing['x'],mytracing['y'])
```

### In Matlab

```matlab
url='http://localhost:5000/api/v1/getmaximage/public/rr30a/0/2'
myimage = webread(url);
imshow(myimage)
```
### In Igor

```
print fetchurl("http://localhost:5000/api/v1/maplist/public")
```

## REST API

The following REST routes specify end-points that will return JSON text or images.

We will be using the `public` user and the `rr30a` map included in the `mmserver/data/` folder.

The links on this page point to a development server that may or may not be running.

### Get help

[http://localhost:5000/help][/help]

### Get a list of maps

[http://localhost:5000/api/v1/maplist/public][/api/v1/maplist/public]

### Load a map

[api/v1/loadmap/public/rr30a][/loadmap/public/rr30a]

### Get annotation values

Here we will get an x-stat `days`, a y-stat `pDist`, and a z-stat `z` for map segment 0 across all sessions

[http://localhost:5000/v2/public/rr30a/getmapvalues?mapsegment=0&session=&xstat=days&ystat=pDist&zstat=z][getmapvalues]


### Get a tracing

Here we will get the x/y/z of a tracing (in um) for all map segments in session 3

[http://localhost:5000/v2/public/rr30a/getmaptracing?mapsegment=&session=3&xstat=x&ystat=y&zstat=z][gettracing]

### Get an image

Here we will get the 20th image in the stack for timepoint 3, channel 2

[http://localhost:5000/getimage/public/rr30a/3/2/20][getimage]

## Get a maximal intensity projection

Here we will get the maximal intensity projection of timepoint 0, channel 2

[http://localhost:5000/getmaximage/public/rr30a/0/2][getmax]



[/help]: http://localhost:5000/help
[/api/v1/maplist/public]: http://localhost:5000/api/v1/maplist/public
[/loadmap/public/rr30a]: http://localhost:5000/api/v1/loadmap/public/rr30a
[getmapvalues]: http://localhost:5000/api/v1/getmapvalues/public/rr30a?mapsegment=0&session=&xstat=days&ystat=pDist&zstat=z
[gettracing]: http://localhost:5000/api/v1/getmaptracing/public/rr30a?mapsegment=&session=3&xstat=x&ystat=y&zstat=z
[getimage]:
[getimage]: http://localhost:5000/api/v1/getimage/public/rr30a/3/2/20
[getmax]: http://localhost:5000/api/v1/getmaximage/public/rr30a/0/2
