# ForecastATAC
Working project on forecasting delays in ATAC, i.e., the public transportation services of Rome.

# Trend Filtering
The `trend_filtering_validation` is a script that 

* downloads the processed gathered live data and static data from an AWS S3 bucket
* creates a graph of the routes
* runs convex optimisation
* stores the results of the optimisation and validation in local storage

## How to run
```bash
python trend_filtering_validation.py
```