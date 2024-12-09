from typing import List

import pandas as pd
import numpy as np
from tslearn.barycenters import (
    euclidean_barycenter,
    dtw_barycenter_averaging,
    dtw_barycenter_averaging_subgradient,
    softdtw_barycenter,
)


def create_rls(
        ts_data: pd.DataFrame,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        hourly_sum_cols: List[str],
        index_cols: List[str],
        pivot_col: str,
        groupby_cols: List[str],
        percentile: float = 0.95,
        normalize: bool = False,
        customer_type: str = 'residential',
) -> pd.DataFrame:
    """
    This function creates the representative load shape.
    Args:
        ts_data: Time series data.
        start_date: Start date of the load shape (e.g. 2022-01-01)
        end_date: End date of the load shape (e.g. 2022-12-31)
        percentile: value at percentile to replace outliers
        normalize: Whether to normalize the load
        customer_type: Customer type (residential, commercial, industrial)
    returns:
        Dataframe with the representative load shape with shape (9870,2)
    """
    grouped_data = prepare_data_for_rls(
        ts_data=ts_data,
        hourly_sum_cols=hourly_sum_cols,
        index_cols=index_cols,
        pivot_col=pivot_col,
        groupby_cols=groupby_cols,
        percentile=percentile,
        normalize=normalize
    )
    centroids = grouped_data.apply(
        lambda group: calculate_barycentre(
            ts_data=group['hour_values'].values,
            method="euclidean")
    )
    centroids = centroids.reset_index()
    centroids = centroids.rename(columns={0: 'kwh'})

    results = pd.DataFrame(columns=['time', 'kwh'])
    delta = pd.Timedelta(days=1)
    current_date = start_date

    while current_date <= end_date:
        current_result = pd.DataFrame(fill_load_timeseries(
            centroids_df=centroids,
            start_date=current_date,
            customer_type=customer_type)).reset_index()
        current_result.columns = ['time', 'kwh']
        results = pd.concat([results, current_result], ignore_index=True)
        current_date += delta
    return results


def prepare_data_for_rls(
        ts_data: pd.DataFrame,
        hourly_sum_cols: List[str],
        index_cols: List[str],
        pivot_col: str,
        groupby_cols: List[str],
        percentile: float = 0.95,
        normalize: bool = False,
) -> pd.DataFrame:
    """
    This function prepares the data for creating representative load shape.
    It performs the following steps:
    1. Rename columns
    2. Replace outliers with the value at 95th percentile
    3. Whether to normalize the load
    Args:
        ts_data: Time series data (AMI, SCADA, etc.)
        time: datetime like column
        groupby_cols: Columns to group by.
    Returns:
        Dataframe with the time series data for each group.
    """
    ts_data = ts_data.rename(columns={'kWh': 'load'})
    # round time to the nearest hour
    ts_data['rounded_time'] = ts_data['time'].dt.round('H')
    if normalize:
        ts_data = normalize_load(ts_data)
    hourly_sum = ts_data.groupby(
        list(hourly_sum_cols))['load'].sum().reset_index()
    hourly_sum.rename(columns={'rounded_time': 'time'}, inplace=True)
    hourly_sum['date'] = hourly_sum['time'].dt.date
    hourly_sum['weekend'] = hourly_sum['time'].dt.dayofweek.isin([5, 6])
    hourly_sum['hour'] = hourly_sum['time'].dt.hour
    hourly_sum = hourly_sum.groupby('service_point').apply(
        replace_outliers, percentile=percentile).reset_index(drop=True)

    data = hourly_sum.pivot(
        index=index_cols,
        columns=pivot_col,
        values='load').reset_index()
    data.fillna(0, inplace=True)
    data.columns = index_cols + [f'hour{hour}' for hour in range(24)]
    hour_columns = ['hour' + str(i) for i in range(24)]
    # Use the apply function to create arrays for each row
    data['hour_values'] = data.apply(
        lambda row: row[hour_columns].values.tolist(), axis=1)
    grouped = data.groupby(list(groupby_cols))
    return grouped


def replace_outliers(
        service_point_ts: pd.DataFrame,
        percentile: float = 0.95,
) -> pd.DataFrame:
    """
    This function replaces outliers with the value at 95th percentile.
    Args:
        service_point_ts: Time series data at the atomic level
        (e.g. service point, premise)
        percentile: Percentile to replace outliers
    Returns:
        Dataframe with outliers replaced for each service point.
    """
    load_95th_percentile = service_point_ts['load'].quantile(percentile)
    service_point_ts['load'] = service_point_ts['load'].clip(
        upper=load_95th_percentile)
    return service_point_ts


def normalize_load(
        ts_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    This function removed outliers and normalize the load.
    Replace outlier with the value at 95th percentile.
    Normalize load by dividing the load by the 95th percentile.
    The normalized load will be between 0 and 1.
    Args:
        ts_data: Time series data (AMI, SCADA, etc.)
        percentile: Percentile to normalize the time series data.
    Returns:
        Dataframe with the normalized time series data.
    """
    load_max = ts_data['load'].max()
    ts_data['normalized_load'] = (
        ts_data['load'] / load_max
    )
    return ts_data


def calculate_barycentre(
        ts_data: np.ndarray,
        method: str,
        gamma: float = 0.4,
) -> np.array:
    """
    This function calculates the centroids of the time series data.
    Args:
        ts_data: time series array
        method: method of computing the typical representation.
        gamma: regularization parameter for softdtw. Lower is less smoothed
            (closer to true DTW).

    Returns:
        The centroid representation of the samples. Array shape (24, 1)
    """
    if method == "euclidean":
        centroid = euclidean_barycenter(ts_data)
    elif method == "dtw":
        centroid = dtw_barycenter_averaging(ts_data)
    elif method == "dtw_subgradient":
        centroid = dtw_barycenter_averaging_subgradient(ts_data)
    elif method == "softdtw":
        centroid = softdtw_barycenter(ts_data, gamma=gamma)
    else:
        raise ValueError(f"{method} is not a valid load profiling method")
    return centroid.transpose()[0]


def fill_load_timeseries(
        centroids_df: pd.DataFrame,
        start_date: pd.Timestamp,
        customer_type: str = 'residential',
) -> pd.DataFrame:
    """
    This function fills a time series load data for a given date.
    Args:
        centroids_df: The centroids for each group.
        start_date: Date to fill the time series data
        customer_type: Customer type (residential, commercial, industrial)
    Returns:
        Dataframe with the time series data for 24 hours. Data shape (24, 2)
    """

    ts_index = pd.date_range(start=start_date, periods=24, freq='H')

    season = get_season(start_date.month)
    weekend = start_date.dayofweek in ([5, 6])

    filtered_data = centroids_df[
        (centroids_df['customer_class'] == customer_type)
        & (centroids_df['season'] == season)
        & (centroids_df['weekend'] == weekend)
    ].values[0]

    ts = pd.DataFrame(
        data=filtered_data[3],
        index=ts_index
    )
    return ts


def get_season(month):
    if 3 <= month <= 5:
        return "spring"
    elif 6 <= month <= 8:
        return "summer"
    elif 9 <= month <= 11:
        return "fall"
    else:
        return "winter"


def scale_load(
        load_profile: np.ndarray,
        scale_for_season: bool,
        desired_peak: float,
        season_months: List[int] = None,
) -> pd.Series:
    """
    Args:
        load_profile: Load profile from time series data
        scale_for_season: Boolean to determine if the load profile should be
        scaled for a particular season. If it sets to False, it will scale for
        the entire year.
        season_months: Months to represent a particular season
        desired_peak: User input peak MW for that particular season

    Returns:
        Load curve scaled based on the seasonal peaks
    """
    if scale_for_season:
        season_curve = load_profile.copy()
        season_curve.loc[~season_curve.index.month.isin(season_months)] = 0.0
        season_max = season_curve.max()
        normalized_season_load = season_curve / season_max
        scaled_curve = normalized_season_load * desired_peak
        scaled_curve.loc[~scaled_curve.index.month.isin(season_months)] = (
            load_profile.loc[~scaled_curve.index.month.isin(season_months)]
        )
    else:
        year_max = load_profile.max()
        normalized_year_load = load_profile / year_max
        scaled_curve = normalized_year_load * desired_peak
    return scaled_curve
