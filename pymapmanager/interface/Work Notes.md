Notes
see if i can make it faster
be able to return all the four coordinates to make the rectangle ROI
Figure out polygon intersection of the ROIs
work on 2nd function that calls it for all points
    - need to save the brightest indexes into the backend
incorporate threading
code profiling

stackWidget.slot_addingAnnotation:
    if we're going to add a spine:
        then expand the dictionary with new information (lineAnnotation, segmentID, Image)


create two overlapping images and test for masks

Loop through to create correct order of coordinates to plot new polygon
Attempt to do it for actual data
Create function to return coordinates for line ROI
    - take in a parameter "radius" to determine how many points long the polygon should be 

We now have mask of desired region
We need to account for disjoint masks and remove the other one
Time to do calculation of its intensity at various points
function(steps, size(n))
    keep the lowest intensity and track its values in a dictionary

Figure out:
1. Disjoint masks
2. Moving entire masks and measuring intensity
3. Graph the altered spine ROI perfectly

ask why we keep the lowest one?

3/8
Fix line polygon
We have coordinates in wrong order, figure out how to organize them when plotting
Figure out how to plot polygons in interface
Perfect the polygons so that they look good
Work on getRadiusLines(lineAnnotations) function
member functions with j to indicate its me
test them in sandbox/ make unit tests


3/24
masks has extra (2 separate masks) during some tests
    - filter it so that we only have mask that contains original point

rotational sort - doesnt correctly connect at times
    - possible because we are using atan2?
    - maybe choose a different central point?

possible way to plot the polygon better
    - take left line coords (by seeing which points lie within the mask) and plot them with the two top coords of the spoin ROI

save brightest indexes into backend and save into a different file

Channel number, how many points to search along the line, extendHead, Width
    - make these into parameters rather than have it hardcoded


Write a Script:
    open copy of data
    step through every spine and calculate the brightest index
    grab the segment ID of the spine and fill in the brightest index and save pointAnnotations


4/19:
    sanpy:
        figure out how to include icon within the exe created from workflow 
    
    pmm:
        moving spines
        reconnecting spines
        Current problem need to figure out how to detect line point clicks, 
        right now I am only detecting the spine point

4/21
    new script to calculate offset values and store into backend
    load the stack load image grab random spine. grab either ROI or intermediate mask to calculated variables
    choose xy offset that chooses the minium

    Bugs to fix:
        - some of the ROIS are connecting properly
        - other segments besides 0 are reconnecting right


5/1:
    Clean up code
    call setbackgroundROI within updateSpineINnt

    Write script to open stack, use point annotations to calculate the ROIS and export them
    when calculating lowest intensity ensure that we are using both the segment and spineROI
    store segment and segmentbackground separately

    update slot_addingAnnotation within stackwidget to get the correct image
    update stackwidget to do more simple backend calls

    shift click doesnt reset selection

    debug why we are plotting with left instead of right points within matplotlib
        - interrogate each function call

    Move sandbox files to util folder (update functions to be able to be called with arguments)


5/11:
    Round the value of left/ right points in segmentROI for better plot?

    Move sandbox files to util folder (update functions to be able to be called with arguments)

    Get median filter to work in johnsonRadiusLines.py

    Spine to line connection using slices

    Dictionary for analysis parameters (class)
        - extend head/tail
        - how far we walk
        - median filter value
        * QTwidget to display and edit
            -> sandbox to just display values in the dictionary
            -> look
    
    Class to implement it as a qwidget

5/22:
    Median filter beforehand

    Visual glitch that show connections

    Class to implement analysis parameters

    change to connection of the spine to line to the spine to right/left value

5/25:
    Window
        - dialogue to accept or cancel
        - set default
        - connect to backend
    
    Calculating intensity parameters
        - when new spine is created
        - 
    
    New Class/ QWidget 
        - scatter plot to plot the analysis
        - signal slot 
    
    Get Parameter Class Values into PointAnnotations

    For testing:
        1) Manually change detection parameter
        2) Analyze Spine button
            - button calls UpdateSpineInt()
            - do it for just one


    TODO: When Delete or unselecting spine
        1) Unselect segment ROI and Background ROI TOO


6/8:
    Nice to have code to filter out columns that we dont want to save

    Use numpy doc string

    Multiprocessing

    Work on making signal from ScatterPlotWidget, to imageplotWidget

    Work on  making the interface less slow

    1) Add Radius into analysis Params connect to backend 
        - For testing:
        1) Manually change detection parameter
        2) Analyze Spine button
            - button calls UpdateSpineInt()
            - do it for just one

    Remove or update signal for updating single spine int

    Remember: imageplotwidget detects onMouseclick and sends the event information

6/14:
    Multprocessing

    Analysis Param Widget
        - values are currently being updated immediately rather than with a save button
        - value changes aren't reflected in the interface until reselection   
        - Create apply button

    Scatter Plot
        - check box to flip y axis
        - escape highlights all points - fix
            -combo box to select specific roi type (unique values)
        - combo box to limit the segment
            - all (to show all segements)
            - populate with number of segments
        - hold states in dictionary to know what we need to plot
            - hold a pointer to the rowIdxes
        - whenever user updates x or y 
            - update position of selected spinepoints (coordinates)
    
    Add menu item (checkbox)
        - accept 
            - a new column within point annotations
            - by default = true
        - color in both of the scatter plots
            - (white)
