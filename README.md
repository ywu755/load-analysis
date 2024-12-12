# Typical Load Shape Analysis
This repository contains code for analyzing electricity load curves.

## Overview
This tool is developed to represent the electricity consumption for a year (8760). It also provides users with the ability to scale the load to a user-defined peak. Users can choose between a winter peak kW scaler or a summer peak kW scaler to customize the load.
This repo includes various methods calculating centroids of time series data, including `The Euclidean barycentre`, `Dynamic Time Warping`, and `Soft Dynamic Time Warping` to get the representative load centroid and create a load shape library.

As suggested by [Luo et al. (2017)](https://www.sciencedirect.com/science/article/abs/pii/S0306261917309819) the load shapes are dominated by factors such as seasons and day of the week. In this project, the data is divided into four seasons: Winter (Dec, Jan, Feb), Spring (Mar, Apr, May), Summer (Jun, Jul, Aug), and Fall (Sep, Oct, Nov). For each season, the data is further divided into weekdays and weekend. This allows us to identify different characteristics of the energy use pattern in each season. 

Moreover, this tool also provides users with the ability to scale the load to a user-defined peak. Users can choose between a winter peak kW scaler or a summer peak kW scaler to customize the load.

## Data Sources
PJM Hourly Energy Consumption Data
PJM Interconnection LLC (PJM) is a regional transmission organization (RTO) in the United States. It is part of the Eastern Interconnection grid operating an electric transmission system serving all or parts of Delaware, Illinois, Indiana, Kentucky, Maryland, Michigan, New Jersey, North Carolina, Ohio, Pennsylvania, Tennessee, Virginia, West Virginia, and the District of Columbia.
The data is availabe to download [here](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption?resource=download&select=COMED_hourly.csv).

## Environment Setup
1) Make a virtual environment.
``` bash
$ sudo apt-get install python-virtualenv
$ virtualenv --python=python3.10 ~/.virtualenvs/loadAnalysis
```
2) Activate the virtual environment.
```
$ source ~/.virtualenvs/loadAnalysis/bin/activate
```
3) Install packages using poetry
```
$ poetry install
```

### How to execute the code:
Run the following command:
``` bash
$  python reference/run_load_profile.py --config_yaml_path reference/load_config.yaml
```
