
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
    