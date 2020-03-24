# apersharp
Package to facilitate running SHARPener on APERTIF imaging survey spectral-line cubes. It is intended to be run on spectral-line cubes created by Apercal (https://github.com/apertif/apercal)

## Requirements
- SHARPener: available here: https://github.com/Fil8/SHARPener/

## Instructions

1. Get both sharpener and apersharp. This is just an example of how to set the directories up. At the moment a special branch of SHARPener is necessary.

```
mkdir $HOME/sharp
mkdir $HOME/sharp/apersharp
mkdir $HOME/sharp/sharpener
cd $HOME/sharp/apersharp
git clone https://github.com/rs1701/apersharp.git
cd $HOME/sharp/sharpener
git clone https://github.com/Fil8/SHARPener.git
cd $HOME/sharp/sharpener/SHARPener
git checkout fix_plotting
cd $HOME/sharp
```

2. Set up PYTHONPATH (assuming bash is used)

`export PYTHONPATH=$PYTHONPATH:$HOME/sharp/apersharp/:$HOME/sharp/sharpener/SHARPener/`

3. Make sure miriad is available for example by sourcing MIRRC.sh

4. Run a test

`python2 $HOME/sharp/apersharp/run_apersharp.py --cube="0" --beams="10" <taskid> <output_directory>`

## Overview
(Work in progress)

Apersharp does the following steps by default:
1. Get data from ALTA
2. Set up SHARpener
3. Run the SHARPener from above
4. Collect results from SHARPener (i.e., create the zip files with pdfs and source tables)
5. Create Master table from all cubes
6. Match sources across beams
7. Analyse spectra
8. Clean up by removing cubes and images

This is what SHARPener does in a nutshell:
1. Find the continuum sources
2. Extract absorption spectra
3. Create plots of spectra and continuum images (with sources markers)

## Usage
(Work in progress)

Apersharp comes with a default configuration file. It can be found in `$HOME/sharp/apersharp/apersharp_config/apersharp_default.cfg`. The default configuration will process all beams of cubes 0, 1 and 2 with all steps using 1 core. This can be executed in the following way

`python2 $HOME/sharp/apersharp/run_apersharp.py <taskid> <output_directory>`

When running `run_apersharp.py`, it is possible to overwrite the parameters for the cubes, beams, steps and number of cores. An example would be

`python2 $HOME/sharp/apersharp/run_apersharp.py --steps="get_data,setup_sharpener,run_sharpener,collect_results,get_master_table,match_sources,analyse_sources" --cube="0,1" --beams="10,11" <taskid> <output_directory>`
Note that the clean-up step is left out here.

It is also possible to change the configuration file. To this purpose, it is recommended to copy the default configuration into a different location and edit it there. Apersharp can be executed with a user-specific configuration file like this:

`python2 $HOME/sharp/apersharp/run_apersharp.py --config="/path/to/apersharp/config/file" <taskid> <output_directory>`

SHARPener requires a configuration file, too. Apersharp comes with a default configuration file for SHARPener and adjusts it to its needs. It is possible to provide a user-defined version of the SHARPener configuration file in the Apersharp configuration file (setting `sharpener_configfilename`). Note that the changing the `general`-settings for `workdir`, `cubename`, and `contname` does not have any affect because these are adjusted by Apersharp to the specific file names of the image cube and continuum image.