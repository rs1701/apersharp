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
```
export PYTHONPATH=$PYTHONPATH:$HOME/sharp/apersharp/:$HOME/sharp/sharpener/SHARPener/
```

3. Make sure miriad is available for example by sourcing MIRRC.sh

4. Run a test
```
python2 $HOME/sharp/apersharp/run_apersharp.py --cube="0" --beams="10" <taskid> <output_directory>
```

## Overview
(Work in progress)

Apersharp does the following steps by default. 
1. `get_data`: Get data from ALTA
2. `setup_sharpener`: Set up the configuration file for SHARpener
3. `run_sharpener`: Run the SHARPener pipeline with the steps set in the configuration file
4. `collect_results`: Collect results from SHARPener (i.e., create the zip files with pdfs and source tables)
5. `get_master_table` Create Master table with the sources from all cubes
6. `match_sources`: Match sources across beams and write the cross-matched source IDs to the master table
7. `analys_sources`: Analyse spectra of all sources and search for candidates of absorption using negative and positive SNR tests
8. `clean_up`: Clean up by removing cubes and images to clear up disk space.
It is possible to leave steps out or run them separately.

This is what SHARPener does in a nutshell:
1. Find the continuum sources
2. Extract absorption spectra
3. Create plots of spectra and continuum images (with sources markers)

## Running Apersharp
(Work in progress)

Apersharp comes with a default configuration file. It can be found in `$HOME/sharp/apersharp/apersharp_config/apersharp_default.cfg`. The default configuration will process all beams of cubes 0, 1 and 2 with all steps using 1 core. This can be executed in the following way
```
python2 $HOME/sharp/apersharp/run_apersharp.py <taskid> <output_directory>
```

When running `run_apersharp.py`, it is possible to overwrite the parameters for the cubes, beams, steps and number of cores. An example would be
```
python2 $HOME/sharp/apersharp/run_apersharp.py --steps="get_data,setup_sharpener,run_sharpener,collect_results,get_master_table,match_sources,analyse_sources" --cube="0,1" --beams="10,11" <taskid> <output_directory>
```
Note that the clean-up step is left out here.

It is also possible to change the configuration file. To this purpose, it is recommended to copy the default configuration into a different location and edit it there. Apersharp can be executed with a user-specific configuration file like this:
```
python2 $HOME/sharp/apersharp/run_apersharp.py --config="/path/to/apersharp/config/file" <taskid> <output_directory>
```

SHARPener requires a configuration file, too. Apersharp comes with a default configuration file for SHARPener and adjusts it to its needs. The default file is located in `$HOME/sharp/apersharp/sharpener_config/sharpener_default.yml`. It includes Apertif-specific settings. It is possible to provide a user-defined version of the SHARPener configuration file in the Apersharp configuration file (setting `sharpener_configfilename`). Note that the changing the `general`-settings for `workdir`, `cubename`, and `contname` does not have any affect because these are adjusted by Apersharp to the specific file names of the image cube and continuum image. It is not recommended to use configuration file that comes with SHARPener itself.

## Using Apersharp output

Steps 5 till 7 of Apersharp will create a master table for the cube that was processed and table with candidates for absorption based on a basic signal-to-noise test. The file locations will be 
```
<output_directory>/<taskid>/cube_<cube_number>/<taskid>_Cube<cube_number>_all_sources.csv
``` 
and 
```
<output_directory>/<taskid>/cube_<cube_number>/<taskid>_Cube<cube_number>_snr_candidates.csv
```
It is strongly recommended to use these files when checking the plots of the spectra and any other further analysis. These files contain all information on the continuuum source location coming from `IMSAD`, in addition to information on a possible SDSS match, match of the source in other beams and quantities derived from the spectrum (more documentation will follow).

It might be useful to run beams separately. In this case the master table `*all_sources.csv` might already exists. The default behaviour is the following: A backup will be created of the table in a new directory `backup_master_table` and the date of the backup will be added to the file name. The existing master table will be appended by the data from the new beams. If there are already data from a "new" beam in the master table, the existing entries will be replaced. See the config file of Apersharp to adjust this behaviour.

In addition, step 4 (`collect_results`) will create zip files with the plots of spectra from each beam 
```
<output_directory>/<taskid>/cube_<cube_number>/<taskid>_cube_<cube_number>_all_plots.zip
```
and a zip file with source information
```
<output_directory>/<taskid>/cube_<cube_number>/<taskid>_cube_<cube_number>_all_sources.zip
``` 
The zip file with source information is no longer necessary, but is helpful for checking that SHARPener worked correctly. The zip file with plots contains pdfs for each beam with the spectra for each source in the beam. The plots of spectra are available in two versions: `*_detailed.pdf` splits the spectra of each source into three panels and `*_compact.pdf` show the spectra in a single panel. 

## To-Do
1. Add better plotting in Apersharp