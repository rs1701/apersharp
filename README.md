# apersharp
Package to facilitate running SHARPener on APERTIF imaging survey spectral-line cubes. It is intended to be run on spectral-line cubes created by Apercal (https://github.com/apertif/apercal)

## Requirements
- SHARPener: available here: https://github.com/Fil8/SHARPener/

## Instructions

1. Get both sharpener and apersharp. This is just an example of how to set the directories up. At the moment a special branch of SHARPener is necessary.

- mkdir $HOME/sharp
- mkdir $HOME/sharp/apersharp
- mkdir $HOME/sharp/sharpener
- cd $HOME/sharp/apersharp
- git clone https://github.com/rs1701/apersharp.git
- cd $HOME/sharp/sharpener
- git clone https://github.com/Fil8/SHARPener.git
- cd $HOME/sharp/sharpener/SHARPener
- git checkout fix_plotting
- cd $HOME/sharp

2. Set up PYTHONPATH (assuming bash is used)
- export PYTHONPATH=$PYTHONPATH:$HOME/sharp/apersharp/:$HOME/sharp/sharpener/SHARPener/

3. Make sure miriad is available for example by sourcing MIRRC.sh

4. Run a test
python2 $HOME/sharp/apersharp/run_apersharp.py --cube="0" --beams="10" <taskid> <output_directory>

## Overview

What does Apersharp does:
1. Get data from ALTA
2. Set up SHARpener
3. Run the SHARPener from above
4. Collect results (i.e., create the zip files with pdfs and source tables)
5. Clean up by removing cubes and images
6. Match sources across beams
7. Analyse spectra

This is what SHARPener does in a nutshell:
1. Find the continuum sources
2. Extract absorption spectra
3. Create plots of spectra and continuum images (with sources markers)