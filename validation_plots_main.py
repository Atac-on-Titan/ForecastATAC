"""Main script for validation plots."""
import argparse
from pathlib import Path

from validation import plot_avg_error
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Concatenate all validation metric dataframes into a single dataframe with average errors.')
    parser.add_argument('-d', '--data', type=str, required=True, help="The path where the validation metric can be found.")

    parser.add_argument('-o', '--out', type=str, required=True, help="The directory where the files will be saved.")

    # Parse the arguments
    args = parser.parse_args()

    df = pd.read_feather(args.data)

    time_df = df[df.name == "time"]
    weather_df = df[df.name == "weather"]
    day_df = df[df.name == "day"]

    time_df.value = list(map(lambda t: int(t.split("-")[0]), time_df.value))
    time_morning = time_df[time_df.value < 8]
    time_day = time_df[(time_df.value >= 8) & (time_df.value < 16)]
    time_evening = time_df[time_df.value >= 16]

    time_plot_morning = plot_avg_error(time_morning, title="Morning Hours", labels=[f"{start} - {start + 1}" for start in range(0, 8)])
    time_plot_day = plot_avg_error(time_day, title="Day Hours", labels=[f"{start} - {start + 1}" for start in range(8, 16)])
    time_plot_evening = plot_avg_error(time_evening, title="Evening Hours", labels=[f"{start} - {start + 1}" for start in range(16, 24)])

    weather_plot = plot_avg_error(weather_df, title="Weather", labels=["Clear Weather", "Unclear Weather"])
    day_plot = plot_avg_error(day_df, title="Weekday", labels=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    Path(args.out).mkdir(parents=True, exist_ok=True)

    time_out_path = f"{args.out}/time_morning_validation.eps"
    time_plot_morning.savefig(time_out_path, format="eps")

    time_out_path = f"{args.out}/time_day_validation.eps"
    time_plot_day.savefig(time_out_path, format="eps")

    time_out_path = f"{args.out}/time_evening_validation.eps"
    time_plot_evening.savefig(time_out_path, format="eps")

    weather_out_path = f"{args.out}/weather_validation.eps"
    weather_plot.savefig(weather_out_path, format="eps")

    day_out_path = f"{args.out}/day_validation.eps"
    day_plot.savefig(day_out_path, format="eps")
