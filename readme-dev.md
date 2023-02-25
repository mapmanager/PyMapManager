
## This is a rewrite of the original pymapmanager backend

## Development pipeline

To check your local branch or main you want to do a few things.

1) Run all tests with `pytest`. The `--maxfail=2` will stop testing after just 2 errors and is sometmies easier to debug.

    ```
    pytest --maxfail=2
    ```

2) We are using flake8 for code linting. We only check for a few error (E9, F63, etc). See [flake documentation](https://flake8.pycqa.org/en/latest/user/error-codes.html) for more info.

    ```
    flake8 pymapmanager --count --select=E9,F63,F7,F82 --show-source --statistics
    ```

    If this **passes**, you will just see a '0'. If this **fails** you might see something like this:

    ```
    src/napari_layer_table/debugInterface.py:77:10: F821 undefined name 'shapesLayer'
    sl = shapesLayer(viewer, shapes_layer)
         ^
    1     F821 undefined name 'shapesLayer'
    ```

3) We need to run tox locally

I do not understand how this works. Sems we need tox to know about different version of Python 3.7/3.8, etc.

```
python -m tox
```

4) If you made changes to the mkdocs documentation, you need to check that too.

    The mkdocs files are in [mkdocs.yml](mkdocs.yml) file and in the [docs/](docs/) folder.

    ```
    mkdocs build
    ```

    You can always run the documentation in a local browser using

    ```
    mkdocs serve
    ```

    Running `mkdocs build` is actualy usefull for finding missing parts and typos in doc strings. The output is often like this:

    ```
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:92: No type or annotation for returned value None
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:354: No type or annotation for parameter 'value'
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:436: Parameter 'compareColName' does not appear in the parent signature
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:669: Failed to get 'name: description' pair from 'funDef (def) function that takes a path and return (header, df)'
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:670: Failed to get 'name: description' pair from 'path (str) Path to file for import'
    WARNING  -  griffe: pymapmanager/annotations/baseAnnotations.py:670: Empty parameters section at line 3
    ```

5) Pushing a new version

    If you are ready to push a new version to **main**, you need to update the version in [pymapmanager/version.py](pymapmanager/version.py). Otherwise, pushing the code to PyPi (for pip install) will fail.

    ```
    [metadata]
    name = napari-layer-table
    version = 0.0.9
    ```

## TODO (20230201)

    - in stackWidget, catch user moving window and set position in options dict

    - as you are writing code, you can start writing test immediately. To call one pytest function, use

    ```
    pytest pymapmanager/tests/test_mmMap.py::test_mmMap_init
    ```
    
## TODO (20220329):
	- Remove toolbars (top-left) for (delete, add, select, zoom).
	- Replace these with interface including
		- delete: keyboard 'delete'
		- add: shit + click
		- select: always active
		- zoom: shit+mouse wheel (mouse wheel alone will scroll slices)
	- Make selected annotation visible by setting their size

	- Limit signal/slot back to table plugin when selecting points.
		Selecting a range of 100's of points in the line layer is super slow

	- remove edge color, it looks sloppy

	- add code to toggle line and point annotation tables on/off.
		Maybe add a 'MapManager' menu and show state with check-mark in menu

	- selecting an annotation (make symbol bigger and yellow),
		1) does not get cancelled/reverted if user switches layer
			when a point is selected
		2) on selection, symbol turns yellow in table plugin (good)
			on de-selection, table is not updated. Hitting the 'refresh'
			button does update correctly (no longer yellow/selected)

	- Make the table plugin snap to selected row, make it visible

	- Add option to table plugin to only show one row selection.
		Option will be toggled via right-click menu

## How to run

To run this code you need to use my new file format and hard-drive structure of stack and annotations (maps coming later)

Clone the mapmanager-data repo

    https://github.com/mapmanager/PyMapManager-Data


## 1) New file format directory structure

Here is an example of the file directory structure for one stack (a stack is just a .tif file)

```
/PyMapManager-Data/one-timepoint
├── rr30a_s0
│   ├── rr30a_s0_db2.txt
│   ├── rr30a_s0_Int1.txt
│   ├── rr30a_s0_Int2.txt
│   ├── rr30a_s0.json
│   ├── rr30a_s0_l.txt
│   └── rr30a_s0_user.txt
├── rr30a_s0_ch1.tif
└── rr30a_s0_ch2.tif
```

Each raw data .tif stack like rr30a_s0_ch1.tif (regardless of its hard-drive location) will have an enclosing folder (rr30a_s0) that contains all our saved files (mostly csv text files)

This is working in principal for a single stack.

## 2) Directory structure of new code

```
pymapmanager
├── __init__.py
├── analysis
│   ├── __init__.py
│   ├── lineAnalysis.py
│   └── pointAnalysis.py
├── annotations
│   ├── __init__.py
│   ├── baseAnnotations.py
│   ├── lineAnnotations.py
│   └── pointAnnotations.py
├── interface
│   ├── __init__.py
│   └── mmViewer.py
├── logger.py
├── map.py
├── mmStackLine.py
├── plotting
│   ├── __init__.py
│   └── plottingUtils.py
├── sandbox
│   └── debugPointSize.py
├── stack.py
├── utils.py
└── version.py

You can then run individual pieces as a simplistic 'test' ... like:

```
python pymapmanager/stack.py 
```

## 3) This is my rational for the code design

This is the core of pymapmanager, a stack and a map ...

```
├── pymapmanager
│   ├── map.py
│   ├── stack.py
```

Contains code to handle different types of annotations. Two main type are (point, line). We will extend this in the future ...

```
│   ├── annotations
│   │   ├── baseAnnotations.py
│   │   ├── __init__.py
│   │   ├── lineAnnotations.py
│   │   ├── pointAnnotations.py
```

Contains purely computational code, lots of numpy and math. So we do not contaminate our other code with lengthy functions.

```
├── pymapmanager
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── lineAnalysis.py
│   │   ├── pointAnalysis.py
```

Some basic plotting functions I am using as 'visual' tests ???

```
│   ├── plotting
│   │   ├── __init__.py
│   │   ├── plottingUtils.py
```


## Notes

- 20220129

### Problem with segmentID being shared between line annotations and point annotations

Many point annotations will have a parent 'segmentID' that corresponds to the 'segmentID' of a lineAnnotation. If an entire segment of a lineAnnotation is deleted, the reference in pointAnnotation to that segmentID needs to be update

1) Don't allow a segment to be deleted if it has points with it as a parent.
2) We are assuming our segmentID in lineAnnotations is a contiguous list of int(s), [0, 1, 2, 3, ...] with no gaps.

    When we delete a segment by its segmentID, we introduce gaps

    We could decriment all segmentID beyond what was deleted

    We then also have to decriment all pointAnnotations segmentID in the same way
    

### We need bounds check on annotation to be sure they are within (slices, x, y) of parent stack

