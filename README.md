# SciVis

# Overview
SciVis is a visualization tool for genomic data, especially structural variants, using the VCF file format. Currently four different visualization modes are supported, see below. Multiple concurrent visualizations of different datasets are supported through a tabbed view, and can be exported as images. The program is not to be seen as a very finished product, but is still under development.

SciVis is built on PySide and Python 3.

![Circle](/Screenshots/Circle.png)

# Installation
Either try running one of the following binaries:

Windows (10): to be added

OS X (10.11): to be added

Linux (Debian Stretch): to be added

Or install PySide and run app.py through python.

#Settings
User settings are located in the userSettings.conf file and can be customized either before running the program or during.

# Circular diagram
The circular diagram reads data from a vcf-file (for variant data) and a tab-file (for coverage data) and arranges chromosomes in a circle divided into circle sectors. The variants are visualized as lines between the start and end position on corresponding chromosomes.
The diagram is constructed by circular layers. The innermost layer is a coverage graph followed by the chromosome layer. Additional layers can be added as tab-delimited files and these will always be added as the outermost layer.

# Coverage diagram
The coverage diagram is an interactive plot of the coverage data in the genome. Bed tracks can be added, as well as tab delimited files for excluding regions. Positions of variants can be marked in the plot, and settings such as base pair resolution and deletion and duplication limits can be customized.

# Karyotype diagram
This diagram visualizes variants as lines between cytobands in a karyotype. Only variants where the start and end positions are located on different cytobands are shown.

# Heatmap
The heatmap visualizes the position of specific varianttypes on two chromosomes (it can be the same chromosome twice). 
Many variants close together gives a lighter color compared to surrounding areas.  
