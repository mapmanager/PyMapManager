## Bugs

 - Histogram, does not update correctly when switching to (or opened with) ch2

 - Selecting segment (e.g. in line list) does not highlight segment in image plot (line plot widget)
	We should get rid of secondary pg plot widgets (for selection) and just set color/marker/size on selection.
	This is true for spines/points and lines

 - In scatter plot. When opened from a stack from a multi-timepoints map, selecting hue of ‘segment ID’ triggers the following. Similar error on toggling 'accept' checkbox.

```bash
   INFO - scatter_plot_widget.py setScatterPlot() line:759 -- hueColumn segmentID id:131
   INFO - scatter_plot_widget.py setScatterPlot() line:759 -- hueColumn segmentID id:133
Traceback (most recent call last):
  File "/Users/cudmore/Sites/PyMapManager/pymapmanager/interface2/core/scatter_plot_widget.py", line 1296, in _onNewHueColumnStr
    self.rePlot()
  File "/Users/cudmore/Sites/PyMapManager/pymapmanager/interface2/core/scatter_plot_widget.py", line 1143, in rePlot
    self.setScatterPlot(xStat, yStat, xyStatIndex)
  File "/Users/cudmore/Sites/PyMapManager/pymapmanager/interface2/core/scatter_plot_widget.py", line 760, in setScatterPlot
    hueId = self._df[hueColumn].iloc[id]
            ~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File "/Users/cudmore/opt/miniconda3/envs/pmm-env/lib/python3.11/site-packages/pandas/core/indexing.py", line 1191, in __getitem__
    return self._getitem_axis(maybe_callable, axis=axis)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/cudmore/opt/miniconda3/envs/pmm-env/lib/python3.11/site-packages/pandas/core/indexing.py", line 1752, in _getitem_axis
    self._validate_integer(key, axis)
  File "/Users/cudmore/opt/miniconda3/envs/pmm-env/lib/python3.11/site-packages/pandas/core/indexing.py", line 1685, in _validate_integer
    raise IndexError("single positional indexer is out-of-bounds")
IndexError: single positional indexer is out-of-bounds
```


## Changes

- Switch ‘line list’ to ‘segment list’, for GUI, try and use ‘segment’ throughout


## Ideas

- When we run a plugin in the stackwidget2 dock, is it necessary to keep track of it for the 'window' menu? It is in the dock and has a tab that allows user to select it and close it. Currently it gets inserted into the window menu but selecting that menu does nothing (does not bring it to the front).

- As plugins are run, we might want to set their window title to '<file> : <plugin name>'. Where <file> is the name of the mmap file, already displayed in the main stackwidget2 window. This way, the user can understand the 'mmap' that each plugin window/widget is associated with.

If a plugin is run a 2nd/3rd/4th time, we could give it a unique window title like '<file> : <plugin name> - 2', ''<file> : <plugin name> - 3'. This is how Microsoft Word works with new documents being 'Document' then 'Document2', then 'Document3'. This unique window title would allow us to keep track of which plugin window is which (versus having a uuid)???

Right now, if I run a plugin multiple times, the window menu shows the 'Scatter Plot' over and over (I do not know which one is which). One strategy is ot have something like 'Scatter Plot - 1', 'Scatter Plot - 2', etc. To correspond to the actual window title of the plugin window.


- Finally, when user closes a stackwidget2, we probably want to close all its associated plugins?