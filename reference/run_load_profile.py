from argparse import ArgumentParser

from omegaconf import OmegaConf
from pathlib import Path
import pandas as pd


from representative_load_shape.load_profile import (
    create_rls,
)


def query_ts_data(
        data_dir: str,
        customer_class: str = "Residential",
) -> pd.DataFrame:
    """
    This function queries the time series data, assigns the customer class.
    """
    # Load the data from csv
    ts_data = pd.read_csv(data_dir)
    ts_data['customer_class'] = customer_class
    return ts_data


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--config_yaml_path",
        type=Path,
        metavar="",
        help="Path to the yaml file containing the model configs"
        "reference/load_config.yaml",
    )
    args = parser.parse_args()
    config_path = args.config_yaml_path
    conf = OmegaConf.load(config_path)

    data = query_ts_data(
        data_dir=conf.data_dir,
        customer_class=conf.customer_class)

    data['year'] = pd.to_datetime(data.Datetime).dt.year
    data = data[data.year == conf.data.year]

    rls = create_rls(
        ts_data=data,
        start_date=pd.Timestamp("2001-01-01"),
        end_date=pd.Timestamp("2001-12-31"),
        hourly_sum_cols=conf.data.hourly_sum_cols,
        index_cols=conf.data.index_cols,
        pivot_col=conf.data.pivot_col,
        groupby_cols=conf.data.groupby_cols,
        customer_type=conf.customer_class,
    )
