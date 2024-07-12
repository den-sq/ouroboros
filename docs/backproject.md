# Backprojection 

After straightened volume produced by the [slicing step](./slicing.md) is segmented, Ouroboros's Backproject Page can be used to project the segmentation back into the coordinate space of the original volume.

### Using the Backproject Page

**Basic Usage Demo**

![Basic Usage Demo](./assets/backproject/Backproject%20Page%20Demo.gif)

**Reusing Options from a Previous Run**

See the same section under [Slice Page](./slicing.md).

### How Does Backprojection Work?

A large amount of helpful data is saved in `*-configuration.json` file after the slicing process. This data contains all of the rectangle corners from slicing, and the bounding boxes the slices are associated with. With this data, Ouroboros recalculates the 2D coordinate grids of 3D points for each slice.

**Trilinear Interpolation**

The straightened volume slices are loaded in as a memmap (an in-memory reference to the tiff image on the hard-drive or SSD). 

Then, an empty volume is created with the same dimensions as the bounding box. A custom trilinear interpolation implementation is used to copy the slice data into the empty volume. 

These volumes are saved to local tiff images. After all volumes have been calculated, Ouroboros creates chunks of an empty volume (same size as the original volume) and copies the data from the smaller volumes into the chunk, and then saves that chunk as a tiff with compression. 

Finally, all chunks are combined to produce either a minimum bounding box in the space of the original volume with all of the backprojected data, or a full-size volume with the backprojected data.

**Why Is Interpolation Needed?**

The slices in the straightened volume were originally produced through interpolation. Each slice has a 2D grid of 3D points, and the values at these points were approximated through interpolation.

In order to put the data back, we have to interpolate in the opposite direction. Each point contributes to the value of its neighbors based on how close it is to them. 

