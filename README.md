# SciVis

# Overview
SciVis is a visualization tool for genomic data, especially structural variants, using the VCF file format. Currently four different visualization modes are supported, see below. Multiple concurrent visualizations of different datasets are supported through a tabbed view, and can be exported as images. The program is not to be seen as a very finished product, but is still under development.

SciVis is built on PySide and Python 3.

![Montage!](/Screenshots/Montage.png)

# Installation
Either try running one of the following binaries:

Windows (10): https://github.com/akvpr/SciVis/releases/download/0.1.0/SciVis_Win10.zip

OS X (10.11): https://github.com/akvpr/SciVis/releases/download/0.1.0/SciVis_osx.zip

Note that the OS X release might be particularly wonky. Try running ./SciVis from terminal if the .app does not start.

Linux (Debian Stretch): https://github.com/akvpr/SciVis/releases/download/0.1.0/SciVis_linux.zip

Or install PySide and run app.py through python.

#Settings
User settings are located in the userSettings.conf file and can be customized either before running the program or during.

# Circular diagram
The circular diagram reads data from a vcf file (for variant data) and a tab file (for coverage data) and arranges chromosomes in a circle divided into circle sectors. The variants are visualized as lines between the start and end position on corresponding chromosomes.
The diagram is constructed by circular layers. The innermost layer is a coverage graph followed by the chromosome layer. Additional layers can be added as tab delimited files and these will always be added as the outermost layer.

# Coverage diagram
The coverage diagram is an interactive plot of the coverage data in the genome. Bed tracks can be added, as well as tab delimited files for excluding regions. Positions of variants can be marked in the plot, and settings such as base pair resolution and deletion and duplication limits can be customized.

# Karyotype diagram
This diagram visualizes variants as lines between cytobands in a karyotype. Only variants where the start and end positions are located on different cytobands are shown.

# Heatmap
The heatmap visualizes the position of specific variant types on two chromosomes (both can be the same chromosome). 
Many variants close together gives a lighter color compared to surrounding areas.  

# Usage
SciVis requires a vcf file (containing variant data) and a tab file (containing coverage data) to run and these need to be supplied by the user. These files can be saved as a pickle (.pkl) file by the program for easier loading. Multiple datasets can be read. Before you create a new diagram you need to choose which dataset to be used.
All diagrams has an *Export image* function which generates an image of the active diagram for use in presentations or similar.
## Circular diagram
The following functions are present at the top toolbar:
* *Chromosomes* brings up a table with chromosome info, this table is also present to the far right of the diagram
* *Update diagram* updates the active view
* *Toggle coverage* toggles the coverage graph on/off
* *Add image to plot* adds an image to the diagram
* *Color regions with file* reads a tab file with color data
* Bed files can be added as an additional layer around the circular diagram from the *Add layer* button. The *Add layer* function also supports tab files for positional data.

The chromosome window to the far right has the following functions:
* The display button shows/hides selected chromosomes
* The connection button shows/hides all active variants for the selected chromosomes
* The variant button brings up a window with a table of all variants for the selected chromosome

Depending on which chromosome is selected in the chromosome window corresponding variants will be shown in the variant window.
* The toggle button will activate/inactivate individual variants
* The mark button will highlight the selected variants in the diagram - this mark will persist between diagrams of the same dataset

## Coverage diagram
Navigation of the diagram is done through reshaping the red box around the chromosome at the top with the mouse. The area of the graph corresponds to the position of the red box on the chromosome. Small increments of movement can be done by the arrow keys.

The toolbar consists of the following functions:
* *Chromosomes* brings up a table with chromosome info, this table is also present to the far right of the diagram
* *Add bed track* adds a bed file beneath the coverage graph as a horizontal track
* *Add exclude file* data from a tab file is read to exclude regions of the graph
* *Add GC file* adds GC data to the graph for excluding particular regions
* *Plot type* switch between a scatter or line plot
* Exact positioning of the red box is done by the *Start* and *End* text boxes
* *Search* is used to mark the position of a specific cytoband or any bed element in the chromosome

The two tables to the far right of the diagram has the same functions as for the circular diagram

## Karyotype diagram
The top toolbar consists of the following functions:
* *Chromosomes* brings up a table with chromosome info, this table is also present to the far right of the diagram
* *Reset layout* resets all the chromosomes to their start positions
* *Update diagram* updates the active view

The chromosome table to the far right has one additional function apart from the ones described for the circular and coverage diagrams:
* Toggle cytoband names* Show/hide cytoband names next to each chromosome

## Heatmap
To zoom in on an element on the heatmap simply click on it.
Click and drag to select a specific area on the heatmap.

The following functions are present in the top toolbar:
* *Chromosomes* brings up a table with chromosome info, this table is also present to the far right of the diagram
* Selection of which chromosomes that should be compared with respect to which variant type.
* *Bin size* the size of each chunk the chromosome has been divided in to (in kilo base pairs)
* *Color* selection of the color scheme for the heatmap
* *Back* if zoomed in the back function reverts the heatmap one step
* *Forward* if *Back* has been used takes the view forward one step

The two tables to the far right of the diagram has the same functions as for the circular diagram
