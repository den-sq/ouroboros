# Backprojection 

After straightened volume produced by the [slicing step](./slicing.md) is segmented, Ouroboros's Backproject Page can be used to project the segmentation back into the coordinate space of the original volume.

### Using the Backproject Page

**Basic Usage Demo**

![Basic Usage Demo](../assets/backproject/Backproject%20Page%20Demo.gif)

**Reusing Options from a Previous Run**

See the same section under [Slice Page](./slicing.md).

**Compression Options**

One of the options on the Backproject page allows the user to configure the output compression format.

Common options

- `zlib`
- `zstd`
- `none` (no compression, not recommended)

For more information, see [Tifffile](https://github.com/cgohlke/tifffile/blob/166092f3e7b38cd1af430846157711f916ed5200/tifffile/tifffile.py#L13068C9-L13068C20), the Python package responsible for the compression.

**Output Position Offset**

By default, the slicing output tiff image is backprojected into the space of its minimum bounding box, rather than the space of the entire source scan.

The offset of the minimum bounding box is stored in the output tiff's description metadata. It is also stored in the configuration file (which is modified by the backproject step).

### Slicing Options

📁 - Drag and drop files from File Explorer panel into this option.

- 📁 `Straightened Volume File` - Path to the volume of slices to backproject (e.g. the output tif of the slicing step).
- 📁 `Slice Configuration File` - Path to the `-configuration.json` file which includes information generated during slicing needed for backprojection.
- 📁 `Output File Folder` - The folder to save all the resulting files into.
- `Output File Name` - Base name for all output files.
- `Output MIP Level` - The MIP level to output the backprojection in (essentially an upsample option). Use this if you downsampled in the slicing step.
- `Upsample Order` - The interpolation order Ouroboros uses to interpolate values from a lower MIP level. If you check the binary option, feel free to set this to 0.
- `Backprojection Compression` - The compression option to use for the backprojected tiff(s). Recommended options: `none`, `zlib`, `zstd`.
- `Output Single File` - Whether to output one tiff stack file or a folder of files.
- `Output Min Bounding Box` - Save only the minimum volume needed to contain the backprojected slices. The offset will be stored in the `-configuration.json` file under `backprojection_offset`. This value is the (x_min, y_min, z_min).
- `Binary Backprojection` - Whether or not to binarize all the values of the backprojection. Enable this to backproject a segmentation.
- `Offset in Filename` - Whether or not to include the (x_min, y_min, z_min) offset for min bounding box in the output file name. Only applies if `Output Min Bounding Box` is true.
- `Max RAM (GB)` - 0 indicates no RAM limit. Setting a RAM limit allows Ouroboros to optimize performance and avoid overusing RAM.

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

