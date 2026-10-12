"""
This file serves as a standardized interface for data preprocessing and ensures that any subclass
implements this interface which includes preprocessing steps.
"""

from abc import ABC, abstractmethod

from pandas import DataFrame, concat

from uwqsc_algorithmic_trading.src.common.config import INTERFACE_NOT_IMPLEMENTED_ERROR


class IPreProcessData(ABC):
    """
    This class is an abstract base class, meaning it serves as a blueprint for other classes. It is
    a general class. This approach enforces a structured and consistent way to handle preprocessing
    across different datasets and use cases.
    """

    def __init__(self):
        """
        Initialize the data preprocessor.
        """

        self.__data_history__ = None
        self.__processed_data__ = None

    @abstractmethod
    def missing_values(self):
        """
        Dataset can contain missing values. These values may be indicated by a null value or an
        impossible integer (say -99 in a dataset with heights of people in Canada in cm). It is
        important to remove these missing values in cases where having them is harmful to training
        the model.
        :side-effect: modifies a parquet file.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove_duplicate_timestamps(self):
        """
        Dataset may contain duplicate timestamp values.  It is important to remove the duplicated
        values in cases where having them is harmful to training the model. Note that it is not
        always required, as some indicators benefit from duplications.
        :side-effect: modifies a parquet file.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def remove_outliers(self):
        """
        Dataset may contain stocks that have price spikes. These outliers generally skew the
        training process of an algorithm, and should be accounted for when setting up an algorithm.
        Z-score method will be used to remove price spikes.
        :side-effect: modifies a parquet file.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    def process_data(self, current_data: DataFrame) -> DataFrame:
        """
        Complete pipeline for data preprocessing for a single occurrence of data.
        :returns: DataFrame containing processed data.
        """

        self.__processed_data__ = current_data

        self.missing_values()
        self.remove_duplicate_timestamps()
        self.remove_outliers()

        if self.__data_history__ is None:
            self.__data_history__ = self.__processed_data__
        else:
            self.__data_history__ = concat([self.__data_history__, self.__processed_data__])

        return self.__processed_data__
