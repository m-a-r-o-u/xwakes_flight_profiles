# Extract XWakes Flight Profiles

Script to extract profiles from the xwakes flight data.

Based on the scipy.signal.find_peak algorithm.
Calculate the highest peaks and lowest valleys.

## Implementation

Peaks should be above 800 meters
Valley should be below 100 meters
Neighouring peaks or Valleys should be 50 meters appart

Responsible parameters:
    plow = 800
    vhig = 100
    prom = 50

## Interface

Input: --ifile /path/to/matlab/file/with/extension/.mat
       --obase /path/to/outputfile/base (no extension)

Output: Two files are created:
    a plot to check the found profiles
    a text file containing the following information:
    start and finish systime of each profile segment,
    the mean lats, lons, wspd and wdir over the profiles
