

## Roadmap

### ToDo

 - Should be very possible to make a docker to install debian+nginx+uwsgi+flask+pymapmanager

	https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/

 - Re-organize mmserver/mmclient into one folder. Have flask server templaes/index.html from `python mmserver.py`. Have nginx server templates/index.thml as native html/javascript (no flask)
 - Add a configure.html to visually configure server
    - for a `username` show list of maps in `data/`
    - have `upload annotations button` ask for a hdd folder and upload via rest.
        - will probably not work because web interface is not allowed to operate outside its root directory
        - maybe add a local `drop` folder to make this possible? User drops a map folder in here (it is inside mmserver/)
    
 - Get simple login working. I don't understand how Flask session and multiple instances in uwsgi/gunicorn works?
 
 
### Big picture

 - Have web interface load a map pool and plot based on time-point conditions across a number of maps. Goal here is to reproduce figures in a paper.
 - Upload annotations (and eventually images) from within Igor
 - Enable editing and saving of maps via web interface.
 - Make a docker to easily install and run PyMapManager client/server on a local machine (MacOS, Linux, Windows).
 
### General

 - posting a map from Igor
    - mmio will allow mmio.postmap() from folder
    - make mmio also post map from zip
    - have igor call an igor script (not part of class library)
        - given a folder path, zip the map and post it

 - then unzip and place files in correct spot
 - add class GlobalMaps() to mmserver.
    - Set and get maps from either a global dict (when run as python mmserver.py) or a redis database when run insode uWSGI
 
### Front end javascript

 - Intercept keyboard in leaflet, use this to switch (channel 1, channel 2, channel 3)
 - Group all plotly and then leaflet variables into a dict like mp. and ml. for my plotly and my leaflet.
 - Snap to missing tp data using pivot points. Have rest 'mapinfo' return list of pivot points (from original file) and then javascript interface to set pivot point in javascript

 - Figure out a way to preload or cache already loaded images. Should be some sort of fast hash table but to start, have a dict of {'rr30a_tp_slice': image-data}
 - Set/get cookies in client browser. To do this, place ALL plotly options and then leaflet options into a dict. Save all values in each dict as cookies.
    - marker size
    - leaflet marker size
    - set name for session in session list from (None, original file, session condition)
    - default channel

### Front end REST

 - Use redis to share data between workers in gunicorn/uWSGI
 - normalize naming conventions
    - all calls start with /api/
 - Add username/password.
 - Move /data outside of /mmserver/data, outside of github repo in general
 - Use tifffile to read .tif files. We currently read .png with scipy (remove scipy dependency).
 
### Client/server runnning on Linux

- Make sure we can do proper web server.
    - nginx
    - javascript client: nginx redirect http://mapmanager.net/mmclient to /users/cudmore/mmclient
    - flask rest server: nginx redirect http://mapmanager.net/api to mmserver .socket
    - make sure mmserver.js parses web url, strip /mmclient and append /api/ for rest calls
    - redis-server, to allow mmserver.py to run in gunicorn/uWSGI with multiple workers (threads). How often should I clear the database? Maybe load all maps on server start?

### Back end python package PyMapManager

 - Write code to pool spine intensity across maps based on session condition (done in Igor and Matlab). Add interface to javascript. This will be used to reproduce a figure from a paper. It should be easy, simple, and work really well.
 - Finalize system to detect 'no segments'
 - Make a test run of editing map. As user is working, save work in browser, on 'save' button, push to server and save to file (not redis).
 
### Igor

 - Write Igor code to export a vascular map
    - stack db will have 2x type (nodeROI, slabROI)
    - object map will hold just nodeROI (they are linked through time)
    - on click in in plotly/leaflet, don't plotRun() is slabROI (there is no map for slabs
    
## Change log

 - 20180301
 	- We now have a docker to install the client/server with zero configuration
 	
 - 20180106
    - We now open 'otherROI' files
    - Can now set marker size in leaflet maps
    - leflet maps report user click, tp and spine
    
 - [done] Generate API documentation from doc strings
 - [done] Load individual slices dynamically (how to query number of slices in .tif file?)
 - [done] Use the mmserver REST API to make a standalone web-app using Flask, Angular, and Plotly
 - [done] Implement visualization of a spine run in mmserver.
 - Make mmserver link all plot, clicking in one will highlight in other.
 - mmserver needs to use `map pool` so publication data can easily be presented.

## Running development servers

	cd mmserver
	python mmserver.py
	
	cd mmclient
	reload -b
	
## Sphinx

This is to auto generated API documentation from embedded docstrings in the python code using Sphinx. The output is available on readthedocs.


1) Don't foget to add modules that depend on C code to `MOCK_MODULES` section of `conf.py`.

2) Whenever I change modules (like when I removed interface/)

last `../version.py` should exclude `pymapmanager/version.py` from output.

Note: I am using pymapmanager/version.py to import a common __version__ into PyMapManager/setup.py and inserting __version__ into pymapmanager module (via pymapmanager/__init__.py)

	cd PyMapManager/pymapmanager/docs
	sphinx-apidoc -f -o source ../ ../version.py

Output should look like:

	Creating file source/pymapmanager.rst.
	Creating file source/modules.rst.

3) Make the docs in /build/

	cd PyMapManager/pymapmanager/docs
	#sphinx-build -b html source/ build
	#sphinx-build -b html . build
	make html
	
4) Push to Github and then go to ReadTheDocs and click `build`.

This relies on a webhook made inside the Github repo (forgot exactly how/where).

## MkDocs

This is for 'human readable' documentation website available at http://blog.cudore.io/PyMapMAnager

Serve locally

```
cd ~/Dropbox/PyMapManager/docs
mkdocs serve
```

Push to github. This needs to be pushed from local github repo, not Dropbox repo.

```
cd ~/Sites/PyMapManager/docs
mkdocs gh-deploy --clean
```

## Synchronize with Unison

```
# Unison preferences file
root = /Users/cudmore/Dropbox/PyMapManager/
root = /Users/cudmore/Sites/PyMapManager

ignore = Name .DS_Store
ignore = Name *.DS_Store
ignore = Name *.pyc
ignore = Name *.tif
ignore = Name *.egg-info
ignore = Path .git
ignore = Path .idea

#when synchronizing between platforms or hdd formats
#rsrc = false
#perms = 0

# Be fast even on Windows
#fastcheck = yes

#servercmd=/home1/robertcu/unison
```

## Export iPython notebooks to html

```
jupyter nbconvert --ExecutePreprocessor.kernel_name=python3 --to html --execute --ExecutePreprocessor.timeout=120

jupyter nbconvert --ExecutePreprocessor.kernel_name=python2 --to html --execute --ExecutePreprocessor.timeout=120
```

## Search and replace across a number of files

search for `windows` and replace with `linux`

	grep -rl 'windows' ./ | xargs sed -i 's/windows/linux/g'

	grep -rl 'windows' ./ | xargs sed -i "" 's/windows/linux/g'
	
	find ./ -type f -exec sed -i "" "s/oldstring/new string/g" {} \;

search all files in current directory `./` for `    ` and replace with ``

	grep -rl '    ' ./ | xargs sed -i "" 's/    //g'	

from /PyMapMAnager/docs, search for '    ' and replace it with ''

	grep -rl '    ' ./docs/examples | xargs sed -i "" 's/    //g'
	
## Pushing changes to home Debian server

 1. Use Unison to update entire PyMapManager folder (pymapmanager, mmclient, mmserver)
 
 This lives in `/home/cudmore/PyMapManager`
 
 2. If I changed core soure code, make sure `pymapmanager` is updated
 
```
cd
pip uninstall PyMapManager
pip install -e PyMapManager
```

 3. Copy mmclient into /var/www/html
 
```
cd
cd PyMapManager
sudo cp -fr mmclient /var/www/html/
```

 4. Run mmserver/ in screen using gunicorn
 
Make sure it is not already running with `screen -r`. Or with `ps -aux | grep gunicorn`
 
```
cd
cd PyMapManager/mmserver
screen
gunicorn -b 0.0.0.0:5010 mmserver:app
```


## Pushing changes in mmclient/ to robertcudmore.org

No need for this any more !


## Pushing to [PyPi][pypi]

Version 0.0.1 is working with `pip install PyMapManager`!

This will be available at [https://pypi.python.org/pypi/pymapmanager](https://pypi.python.org/pypi/pymapmanager) and can be installed with `pip install PyMapManager`.

There is also a test server at [https://testpypi.python.org/pypi](https://testpypi.python.org/pypi)

1. Make sure there is a `~/.pypirc` file

```
[distutils]
index-servers =
  pypi
  pypitest

[pypi]
username=your_username
password=your_password

[pypitest]
username=your_username
password=your_password
```

2. Update version in `PyMapManager/setup.py`

      version='0.0.1',

3. Makes .tar.gz in `dist/`

	cd PyMapManager
	python setup.py sdist
	
4.1 push to test server

	python setup.py sdist upload -r pypitest
	
4.2. Push to PyPi website

	python setup.py sdist upload
	

## images

I need to decide between

mmServer.py is using

	from skimage.io import imsave, imread

mmMap is using

	import scipy.misc

## cookies

see: https://stackoverflow.com/questions/14573223/set-cookie-and-get-cookie-with-javascript

## redis flask server

We need to use a global database when running production server where mmserver is spawned into multiple processes and can not share `global` python objects. Redis requires a bit of work to package objects into json serializable objects so for now just use pickle to do the heaver lifting. Map rr30 is ~24 MB when pickled, rough estimate is we get ~44 picked maps per 1 GB of memory (in practice we will get a bit more).

### install redis-server

	# osx
	brew install redis
	# linux
	sudo apt-get install redis

### Make redis-server run at system boot


```
osx
   To have launchd start redis now and restart at login:
     brew services start redis
   Or, if you don't want/need a background service you can just run:
    redis-server /usr/local/etc/redis.conf

# linux
figure this out
```

### Run redis server manually

	redis-server
	
### Check redis-server is running

	redis-cli ping
	
### To clear all data from server

	redis-cli FLUSHALL

### run in development mode (on osx)

	cd
	cd PyMapManager/mmserver
	sudo gunicorn -w 4 -b 127.0.0.1:5010 mmserver:app
	
```
#!/bin/python

'''
# for code to put/get from redis server
# see: http://calderonroberto.com/blog/flask-and-redis-is-fun/

# Dependencies:
# pip install flask
# pip install redis
#
# Then run server with `redis-server`, default address is 127.0.0.1:6379
# Re-running the server still has old data
# To clear, use redis-cli (while server is running)
# redis-cli FLUSHALL

## Install redis-server

This should install as a running service, check that it is still running on reboot

### On OSX

	brew install redis-server

### On debian

	sudo apt-get install redis-server

## Clear the whole redis server (all its databases)

	redis-cli FLUSHALL

## can't add python class objects to redis, use pickle

https://stackoverflow.com/questions/15219858/how-to-store-a-complex-object-in-redis-using-redis-py

'''

from flask import Flask
from flask import request
import flask
import redis
import time
import json
from flask import Response, stream_with_context

# see: https://stackoverflow.com/questions/15219858/how-to-store-a-complex-object-in-redis-using-redis-py
import pickle

from pymapmanager.mmMap import mmMap

app = Flask(__name__)
app.debug = True
db = redis.Redis('localhost') #connect to server

ttl = 31104000 #one year

@app.route('/set/<themap>')
def one(themap):
    print 'themap:', themap
    mappath = '/Users/cudmore/Dropbox/PyMapManager/mmserver/data/public/' + themap + '/' + themap + '.txt'
    m = mmMap(mappath)
    pickled_object = pickle.dumps(m)
    db.set(themap, pickled_object) # themap is a string key '' here
    #db.delete(themap)
    #db.hmset(themap, {'a':1})
    return 'ok'
    
@app.route('/get/<themap>')
def two(themap):
    if not db.exists(themap):
        return "Error: redis map doesn't exist"
    
    mapObject = pickle.loads(db.get(themap))
    print 'mapObject:', mapObject

    #event = db.hgetall(themap)
    #print 'event:', event
    #return json.dumps(event)
    return json.dumps(str(mapObject))
	
if __name__ == "__main__":
    app.run()
```

## Debian

### Redis

    /etc/init.d/redis-server stop

### nginx

    sudo service nginx stop
    
    
[pypi]: https://pypi.python.org/pypi/pymapmanager