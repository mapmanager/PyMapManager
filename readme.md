[![PyPI version](https://badge.fury.io/py/pymapmanager.svg)](https://badge.fury.io/py/pymapmanager)
[![Python](https://img.shields.io/badge/python-3.7|3.8|3.9|3.10|3.11-blue.svg)](https://www.python.org/downloads/release/python-3111/)
[![tests](https://github.com/mapmanager/PyMapManager/workflows/Test/badge.svg)](https://github.com/mapmanager/PyMapManager/actions)
[![codecov](https://codecov.io/github/mapmanager/PyMapManager/branch/master/graph/badge.svg?token=0ZR226588I)](https://codecov.io/github/mapmanager/PyMapManager)
[![OS](https://img.shields.io/badge/OS-Linux|Windows|macOS-blue.svg)]()
[![License](https://img.shields.io/badge/license-GPLv3-blue)](https://github.com/cudmore/mapmanager/blob/master/LICENSE)

PyMapManager is an ecosystem of tools to load and visualize time-series annotations and 3D image volumes. For a complete overview, see the main [PyMapManager](https://mapmanager.net/PyMapManager/) documentation.

<span style="color:red">
**Note:** This code is under active development and is not ready for general use. Check back later and we will eventually have a working version.
</span>

<BR>

PyMapManager has a modular architecture with the following components:

 - Backend API
 - Frontend desktop GUI
 - Frontend web interface

## Install

Create and activate a conda virtual environment

```
conda create -y -n pmm-env python=3.11
conda activate pmm-env
```

Clone the GitHub repository

```
git clone git@github.com:mapmanager/PyMapManager.git
cd PyMapManager
```

Install the backend from source

```
pip install -e .
```

Install the front-end desktop GUI and backend

```
pip install -e .[gui]
```

If you are using the `zsh` shell, you need to install using quotes (") like

```
pip install -e ".[gui]"
```

## Run

We are still in the early stages of development.

Make sure you have the `PyMapManager-Data` folder in the same folder as `PyMapManager`.

```
python snadbox/runStackWidget.py
```

## Desktop Application

The next generation desktop application version of Map Manager. Written in Python using the Qt interface library and using the PyMapManager Python package as an back-end.

<IMG SRC="docs/img/pyMapManager_v2.png" width=800>

This screen shot shows the main PyQt interface with a map plot (top left), an annotation plot (bottom left), and an image stack window (right).

~~This project will be merged with <A HREF="https://github.com/cmicek1/TiffViewer">PyQt TiffViewer</A> created by <A HREF="https://github.com/cmicek1">Chris Micek</A>. The PyQt GUI interface is in [PyQtMapManager/](PyQtMapManager/)~~


See the [examples/](examples/) folder for Jupyter notebooks with more examples.

Please see the <A HREF="http://pymapmanager.readthedocs.io/en/latest/">API Documentation</A> and a backup copy <A HREF="http://robertcudmore.org/mapmanager/PyMapManager/docs/">here</A>.


## Map Manager web server

A web server to browse and share Map Manager annotations and time-series images. In addition to the point-and-click interface, there is also a [REST API][rest-api] to programmatically retrieve data.

Running the server is easy with either Python or Docker, see the [server installation](http://cudmore.github.io/PyMapManager/install-server/) for more information.

### Web GUI

The server includes web based browsing and plotting of Map Manager annotations.

<IMG SRC="docs/img/mmserver_purejs.png" width=900>

... and browsing of 3D image volume time-series with annotations.

<IMG SRC="docs/img/mmserver_leaflet.png" width=900>
<IMG SRC="docs/img/mmserver_leaflet2.png" width=900>



[redis]: https://redis.io/
[rest-api]: http://cudmore.github.io/PyMapManager/rest-api/
