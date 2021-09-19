# Usage Guide

## Downloading Data
Run `src.nb.download_data.ipynb`
* Downloads price history data for a list of symbols
* Notebook calls on code implemented in `src.lib.alpaca_historical.py`

## Reading Data
Import from `src.lib.price_history.py`
* `read_price_history(symbol)` function creates a `PriceHistory` object for the given symbol so long as the data for that symbol exists

## Reading and Processing Data
Import from `src.lib.stock_dataset.py`
* `read_stock_dataset(symbols, target_column, n_time_steps)` function creates a `StockDataset` object which combines the `PriceHistory` objects for all the given symbols
* `StockDatset` object can be used to split, preprocess, and batch data

## Training
Run notebooks in `src.nb.train/`
* `1_lstm_msla.ipnby` - 1st nb created, uses an LSTM, Multi-Sharpe-Loss with Allocation
* `2_lstm_hr.ipynb` - 2nd nb created, uses an LSTM, same loss as nb1 with the addition of a Holdings loss that penalizes for number of shares traded

## Paper Trading
`TODO`
## Live Trading
`TODO`
## Performance Evaluating
`TODO`
# Contents

`src`
* `lib`
    * `activations.py`
        * Custom activation functions
    * `alpaca_historical.py`
        * `TODO` Charlie document
    * `alpaca_paper.py`
        * `TODO` Charlie document
    * `losses.py`
        * Custom loss functions
    * `price_history.py`
        * `PriceHistory` class
        * `read_price_history(symbol)` function
            * Creates a `PriceHistory` object for the given symbol so long as the data for that symbol exists
        * Represents timeseries data open, high, low, close, and sometimes TA indicators
        * Includes the underlying symbol
        * Has methods to clean and transform data
    * `stock_dataset.py`
        * `StockDataset` class
        * `read_stock_dataset(symbols, target_column, n_time_steps)` function
            * Creates a `StockDataset` object which combines the `PriceHistory` objects for all the given symbols
            * Uses `target_column` to determine what the `y` values of the data batches should be
            * `n_time_teps` is how many time steps should be in each batch
        * Represents a collection of PriceHistories
        * Has methods to
            * Split data for train/validate/test
            * Z-normalize the data
            * Batch the data
    * `util.py`
        * `makedir_to(file_path)`
            * Given a file path, any non-existant directories to that file
            * Expects the file path to end in a file not a directory
        * `trim_nan_rows(data)`
            * Accepts a `DataFrame` and removes any continuous sections of NaN-containing rows at the beginning and end of the data
* `nb`
    * `data_process`
        * `download_data.ipynb`
            * Downloads price history data for a list of symbols
    * `test`
        * Notebooks to run and examine code output
    * `train`
        * Notebooks that train models
        * `1_lstm_msla.ipnby` - 1st nb created, uses an LSTM, Multi-Sharpe-Loss with Allocation
        * `2_lstm_hr.ipynb` - 2nd nb created, uses an LSTM, same loss as nb1 with the addition of a Holdings loss that penalizes for number of shares traded
* `tests`
    * `test_data`
        * Contains data used to run tests
    * `test_<file_name>.py`
        * Tests functionality of `<file_name>`


# Python Package
## Updaing package
* Make modifications to code
* Modify the version number in `setup.cfg`
* Run `python3 -m build`

## Installing package
* Run `pip3 install .` from the `stockbot_2021` directory
* For Bill's conda environment the command is `/Users/bill/miniforge3/envs/tf_arm/bin/pip3 install .`