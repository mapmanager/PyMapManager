
## First steps

    - Implement a GUI to display a single timepoint stack in Napari
    - Once a mmMap is loaded, you can display mmMap.stack[0] in napari
    - This includes:
        - raw 3D image data
        - Display all spineROI annotations in the Napari viewer as a 'points' layer
    - Add an interface elements to napari including
        - list of spineROI in the map
    - When user clicks on an annotation in the list, snap to and highlight that annotation in the image/point layers
    - When a user click on an annotation in the image, snap to and highlight that annotation in the list

## mmStack

see the current api here: https://pymapmanager.readthedocs.io/en/latest/source/PyMapManager.html#module-pymapmanager.mmStack

The mmStack class encapsulates an nd-image and a list of annotations.

nd-image:
    - Load
    - Retreive single image planes

Annotations
    
    We have a number of different types of annotations. Basically each annotation corresponds to an identifiable feature in the nd-image. Each annotation has a 'real-world' description of the type of structure it is referng to.

    We need to implement a CRUD interface for all annotations (Create-Read-Update-Delete).
    
    point annotations

        These are stored as a Pandas Dataframe, one row per annotation with a number of columns specifying the features of each annotation.

        Here are some examples of columns (features) in a point annotation:

        x (int): X pixel in the nd-image
        y (int): Y pixel in the nd-image
        z (int): Z pixel in the nd-image (for a 3D stack, z corresponds to the image plane)
        note (str): A user specified note
        cDate (int): Creation date encoded as python time.time() seconds (e.g. linux epoch)
        mDate (int): Creation date encoded as python time.time() seconds (e.g. linux epoch)
        roiType (Enum): The 'real world' structure of the annotation. For example ['globalPIvot' 'pivotPnt' 'controlPnt' 'spineROI']

        Example algorithms we use on different roiType:
        
        roiType of 'controlPnt' is a sequential set of points specified by the user that coursely traces along a bright filament (dendrite or axon). We then use to algorithmically fit the brightest path between these points (see line annotation).

        roiType of 'spineROI' represent the location of a neuornal spine. We then algorithmically draw a number of ROIs (NOT IMPLEMENTED) to calculate the parameters of the intensity of the image around this point. This algorithm generates a number of new 'features' of the ROI, each is then added as a column in the Pandas DataFrame for this ROI.

    line annotations

        Line annotations are basically a list of point annotations with some bookkeeping. To allow mulutiple disjoint but connected lines within an mmStack, we assign each point to a segmentID and use a 'prevID' to keep track of points within a given line segment and when they change into a new branch.

        To organize line segments into a 'tree' like structure we use the simple text file format called SWC (see: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0228091).

        Basically, each point in the line has (x,y,z) coordinates as well as a 'previous' ID. The start of a tracing has previous=-1. Each sequential point along a line has 'previous' equal to its index-1. When there is a new line previous != index-1 but is some other point in the tracing. This is a really poor description of this simple format, can explain more later.

        The user specifies a sparse set of 'controlPnt' annotations along a bright filament and we then compute the brightest path between these points. This path finding is not yet implemented in Python. We could use the Fiji Simple Neurite Tracer plugin to find the brightest path. I have scripts to trigger Fiji with the sparse set of controlPointROI and return a fine grained path of (x,y,z). We might want to implement this kind of brightest path algorithm (generally an A* algorithm)

        Fiji/ImageJ is open source image visualization and analysis used by many: https://imagej.net/software/fiji/

        Here are some examples of columns (features) in a line annotation:

        x (int): X pixel in the nd-image
        y (int): Y pixel in the nd-image
        z (int): Z pixel in the nd-image (for a 3D stack, z corresponds to the image)
        radius (float): If the line is tracing a filament like structure in an image, we calculate the radius/diameter with some analysis.
        segmentID (int): Each point in a line belongs to a segment (0,1,2,...)
        prev (int) Each point has a prev index, for point i:
            case: prev = -1 then this point is the root of the tree
            case: prev = i-1 then it is a continuation of a line. 
            case: prev != i-1 then this point connects to some other segment


    roi annotations
        We don't have these yet. ROI annotations will hold a list of points to include in the region-of-interest (ROI). This could hold an ROI you might create by drawiing an arbitrary shape on top of an image (e.g. with a lasso tool)


We need API functions to retreive, add, delete, and edit annotation (e.g. CRUD)


## Definitions:

image plane: When we have a 3D nd-image made of individual image slices [i,:,:]

image slice: See image plane