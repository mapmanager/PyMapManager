
## 202504

To install PyMapManager and MapManagerCore

Make sure you have <your_source_folder> that contains the Core, Py, and Data

    <your_source_folder>
    ├── MapManagerCore
    ├── MapManagerCore-Data
    ├── PyMapManager

From your cloned PyMapManager directory/folder

1) Create and activate a conda environment

    conda create -y -n pmm_env2 python=3.11
    conda activate pmm_env2

2) Install MapManagerCore from source
    
    pip install -e ../MapManagerCore/.

3) Install PyMapManager from source, use `[test]` to install pytest

    pip install -e '.[test]'

4) Run some tests, if these fail -->> DO NOT CONTINUE

Run some MapManagerCore tests (from PyMapManager)

    pytest ../MapManagerCore/tests/test_mmMapLoader.py
    pytest ../MapManagerCore/tests/test_mmMapLoader_image_channel.py

Run main PyMapManager stack widget tests

    pytest src/pymapmanager/tests/interface/test_stack_widgets.py

5) run the PyMapManager GUI with your custom script

This will work if the following manually copied mmap folder exists

`../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap`

    python src/pymapmanager/tests/interface/runInterfaceBob.py

See comments in `runInterfaceJohnson.py'

    # abb, macOS
    # you need to MANUALLY place this new mmap folder
    # path = '../MapManagerCore-Data/data/202504/single_timepoint_202504.mmap'

## Start working on multi timepoint

1) Write function to make best guess of connected spines
 - Need to incorporate a point along the line repesenting the same position on a line (between timepoints)
 - Need to improve algorithm because it allows spine connections to criss cross

2) Write function to force a spine ROI to have a given lnegth. The length of all connected spines need to be the same so they have the same number of pixels in the ROI. Such that the sum intensity will be normalized

# 20241211

1) extend map dendogram to multiple y property

1.5) get linked z scrolling working

2) add functions to 'connect points'

3) [nope] implement 'stack zero coordinate'

    add stack (z, y, x) to each segment 'Pivot Distance' (distance along segment)

## Bugs
    - delete segment is not working
    
## Preparing PMB seminar Dec 19, 2024

- stack widget
    - Implement a simple export to csv for both spines and segments
    - refactor left toolbar as a dock. Inherit from `Main Window` add dock 'left'. This way the user can visually drag it bigger/small and hide it. See scatter widget.
    - implement new `image contrast` widget to show dual slider, an `auto` button, and a color LUT combobox.

- dendrogram widget
    - refactor left toolbar as a dock. Inherit from `Main Window` add dock 'left'. See scatter widget.
    - debug if shift click propogates to stack widget with `zoomToPoint`.
    - debug if plotting with spine angle works.

- image plot widget
    - copy and past the view to the clipboard to export to drawing/presentation software

- stack toolbar
    - `Plot` combobox needs to be debugged. e.g. turning of `annotations` should turn of all other options (except image).

- Annotation list widget
    - Tighten up layout by removing padding/broders between children widgets
    - Add a global option to reduce the font size. I think the modern strategy is to grab the system befault font size and reduce it (rather than specifying an absolute point size). IF this is done in our base classes, these GUI improvements should propogate to all stack widgets (like Scatter Widget).

- tracing widget
    When user adds first point to tracing (shift_click), the point does not show up in annotationPlotWidget. Adding the seconds point it does. Add code special case on first shift+click point in a segment.

- improve class segment
    - when user turns in `set pivot' we intercept a z/y/x shift+click in the image.
    - We need to get two things from this
        1) distance to the line origin of given point using `line_locate_point`
        2) point interpolated at given distance on a line using `line_interpolate_point`

## winter break (cudmore)

 - Moved pymapmanager/ source code folder into a src/ foler.
 - Moved tests/ folder into pymapmanager/ folder.
 - Switch local pip install from setup.py into more modern `pyproject.toml`.
 - Create a new GitHub repo to hold code for building PyMapManager apps with pyinstaller, see:
    https://github.com/mapmanager/PyMapManager-App
 - Got unit test working better. In particular reactivated Johnson code in `test_stack_widgets.py`. Thanks for writing that!

 TODO:

 - Work on Windows version to build an app using pyinstaller. The repo (above) has a copy of the windows build scripts from SanPy, start from there and have a look at the `mac/` build scripts for some hints. Basic workflow is to build a fresh/clean conda environment (with both MapManagerCore and PyMapMAnager local installs) and then tweak the pyinstaller `.spec` file with MapManager specific requirements. I want to get this done as a test run so we do not run into (as many) problems later.

 - Check code that references `segmentID` as the core now makes segments from 1 (rather than 0). Some code is using `range(numSegments)` when it should actualy be using the actual segment label names. This should also account for missing segments like when, say, user deletes segment 3.

 - Revamp code to add channels
  - Within a timepoint, each color channel has to have the same shape. On import of second channel, check the shape. We will have additional logic once it is reasonably working.
  - Saw you added "maxChannels" to analysisParams (in the core). I think it would be more logical to add "number of channels" to the mmap MetaData class. I think `Metadata` is a bit of a mess and needs to be re-written. for now you can just add a `number of channels` int to one of the three subclasses like MetadataPhysical size (for example).

``` 
class Metadata:
    name: str = ''
    channelNames: Dict[int, str] = field(default_factory=lambda:{})
    voxel: VoxelMetadata = field(default_factory=lambda: VoxelMetadata())
    physicalSize: MetadataPhysicalSize = field(default_factory=lambda: MetadataPhysicalSize())
    metadataContrast : MetadataContrast = field(default_factory=lambda: MetadataContrast())
```



