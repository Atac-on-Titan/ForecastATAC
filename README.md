# ForecastATAC
Working project on forecasting delays in ATAC, i.e., the public transportation services of Rome.

# Trend Filtering
The `trend_filtering_validation` is a script that 

* downloads the processed gathered live data and static data from an AWS S3 bucket
* creates a graph of the routes
* runs convex optimisation
* stores the results of the optimisation and validation in local storage

## How to run

### Command Line
From the command line, you need to install the necessary packages in `requirements.txt` and then run:
```bash
python trend_filtering_validation.py
```

### Docker
Make sure you have Docker and docker-compose installed, then you can simply run the `docker-compose.yaml` file from the
root directory of the project:
```bash
docker-compose up
```