
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
    When user adds first point to tracing (shoft_click), the point does not show up in annotationPlotWidget. Adding the seconds point it does. Add code special case on first shift+click point in a segment.

- improve class segment
    - when user turns in `set pivot' we intercept a z/y/x shift+click in the image.
    - We need to get two things from this
        1) distance to the line origin of given point using `line_locate_point`
        2) point interpolated at given distance on a line using `line_interpolate_point`