import pandas as pd
import numpy as np
from collections import OrderedDict
from copy import deepcopy

from tensorflow.python.keras.backend import concatenate

from src.lib.price_history import read_price_history, transform_price_history, PriceHistory
from src.lib.util import trim_nan_rows


from sklearn.preprocessing import StandardScaler

def read_stock_dataset(symbols, target_column, n_time_steps, transform=True, **kwargs):
    data_dir = kwargs.pop("data_dir", None)
    
    price_histories = []
    for symbol in symbols:
        history = read_price_history(symbol, data_dir)
        if transform:
            history = transform_price_history(history, **kwargs)
        price_histories.append(history)
    
    return StockDataset(price_histories, target_column, n_time_steps)


def join_price_histories(price_histories, target_column):
    column_records = OrderedDict()
    target_columns = []

    history_datas = []
    for history in price_histories:
        symbol = history.symbol
        original_columns = history.data.columns
        assert target_column in original_columns, f"History for {symbol} does not contain target column: {target_column}"

        add_symbol = lambda col: f"{symbol}_{col}"
        new_columns = [add_symbol(col) for col in original_columns]
        target_columns.append(add_symbol(target_column))

        history.data.columns = new_columns
        column_records[symbol] = {
            "original": original_columns,
            "new": new_columns
        }

        history_datas.append(history.data)
    
    concatenated = pd.concat(history_datas, axis=1)
    return concatenated, column_records, target_columns

class StockDataset:

    def __init__(self, price_histories, target_column, n_time_steps):
        self.target_columns = []
        self.n_time_steps = n_time_steps

        concatenated, self.column_records, self.target_columns = join_price_histories(price_histories, target_column)

        data = trim_nan_rows(concatenated)
        self.y = data[self.target_columns][1:]
        self.X = data[:-1]
        self.y.index = self.X.index
        

    def __deepcopy__(self, memo):
        # https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result


    def __getitem__(self, symbol):
        if symbol not in self.column_records:
            raise KeyError(f"StockDataset does not contain {symbol}")
        
        original_columns = self.column_records[symbol]["original"]
        new_columns = self.column_records[symbol]["new"]

        history_df = self.X[new_columns]
        history_df.columns = original_columns
        return PriceHistory(history_df, symbol)
    

    def swap_data(self, new_X, new_y=None):
        assert set(new_X.columns) == set(self.X.columns), "Can not change columns of StockDataset"
        copy = deepcopy(self)
        copy.X = new_X
        if new_y is not None:
            assert set(new_y.columns) == set(self.y.columns), "Can not change columns of StockDataset"
            copy.y = new_y
        
        return copy
    

    # def swap_data(self, new_X, new_y=None):
    #     assert set(new_X.columns) == set(self.X.columns), "Can not change columns of StockDataset"

    #     copy = deepcopy(self)
    #     copy.X = new_X

    #     if new_y is not None:
    #         assert set(new_y.columns) == set(self.y.columns), "Can not change columns of StockDataset"
    #         copy.y = new_y
    

    def train_valid_test_split(self, valid_time, test_time, scaled):
        end_train_time = self.X.index[-1] - test_time - valid_time
        end_valid_time = self.X.index[-1] - test_time

        assert end_train_time > self.X.index[0], "No training data. All data selected for validation and testing"

        train_X = self.X[:end_train_time]
        train_y = self.y[:end_train_time]
        
        valid_X = self.X[end_train_time: end_valid_time]
        valid_y = self.y[end_train_time: end_valid_time]

        test_X = self.X[end_valid_time:]
        test_y = self.y[end_valid_time:]

        train = self.swap_data(train_X, train_y)
        valid = self.swap_data(valid_X, valid_y)
        test = self.swap_data(test_X, test_y)

        if scaled:
            scaler = train.fit_standard_scaler()

            train = train.apply_standard_scaler(scaler)
            valid = valid.apply_standard_scaler(scaler)
            test = test.apply_standard_scaler(scaler)
        
        return train, valid, test, scaler


    def fit_standard_scaler(self):
        scaler = StandardScaler()
        scaler.fit(self.X)
        return scaler

    
    def apply_standard_scaler(self, scaler):
        X = scaler.transform(self.X)
        new_X = pd.DataFrame(X, self.X.index, self.X.columns)
        return self.swap_data(new_X)


    def get_batchable_index(self, trade_market_open=True):
        batchable_index = np.arange(self.n_time_steps, len(self.X))
        if not trade_market_open:
            def during_market_open(time):
                seconds = time.hour * 60**2 + time.minute * 60
                return seconds > 9 * 60**2 + 30 * 60 + self.n_time_steps
            bool_index = self.X.index.apply(during_market_open)
            batchable_index = np.where(bool_index)[0]

        return batchable_index


    def get_batch(self, batch_size, int_index, shuffle=True, replace=True):
        n_features = len(self.X.columns)
        n_symbols = len(self.y.columns)
        X_batch = np.zeros((batch_size, self.n_time_steps, n_features))
        y_batch = np.zeros((batch_size, n_symbols))

        if shuffle:
            inds = np.random.choice(int_index, batch_size, replace=replace)
        else:
            start_ind = np.random.randint(0, len(int_index)-batch_size+1)
            inds = int_index[start_ind:start_ind+batch_size]
            
        for i, random_index in enumerate(inds):
            X_sample = self.X.iloc[random_index - self.n_time_steps: random_index]
            y_sample = self.y.iloc[random_index - 1]
            X_batch[i, :] = X_sample
            y_batch[i] = y_sample
        
        return X_batch, y_batch
    

    def get_paired_batch(self, batch_size, int_index, shuffle=True, replace=True):
        n_features = len(self.X.columns)
        n_symbols = len(self.y.columns)
        X_batch = np.zeros((batch_size, 2, self.n_time_steps, n_features))
        y_batch = np.zeros((batch_size, 2, n_symbols))

        if shuffle:
            inds = np.random.choice(int_index[:-1], batch_size, replace=replace)
        else:
            start_ind = np.random.randint(0, len(int_index[:-1])-batch_size+1)
            inds = int_index[start_ind:start_ind+batch_size]
        
        inds_final = inds + 1
        
        for i, random_index in enumerate(inds):
            X_sample = self.X.iloc[random_index - self.n_time_steps: random_index]
            y_sample = self.y.iloc[random_index - 1]
            X_batch[i, 0, :] = X_sample
            y_batch[i, 0] = y_sample
        
        for i, random_index in enumerate(inds_final):
            X_sample = self.X.iloc[random_index - self.n_time_steps: random_index]
            y_sample = self.y.iloc[random_index - 1]
            X_batch[i, 1, :] = X_sample
            y_batch[i, 1] = y_sample
        
        return X_batch, y_batch

    # y: (batch_size, n_trades, n_symbols, 2)
    # X: (batch_size, n_time_steps + n_trades - 1, n_features)
    # def get_batch(self, batch_size, n_trades, int_index, shuffle=True, replace=True):
    #     n_features = len(self.X.columns)
    #     n_symbols = len(self.y.columns)
    #     adj_n_time_steps = self.n_time_steps + n_trades - 1
    #     X_batch = np.zeros((batch_size, adj_n_time_steps, n_features)) # (batch_size, adj_n_time_steps n_features)
    #     y_batch = np.zeros((batch_size, n_trades, n_symbols, 2)) # (batch_size, n_trades, n_symbols, 2)

    #     if shuffle:
    #         inds = np.random.choice(int_index, batch_size, replace=replace) # (batch_size,)
    #     else:
    #         start_ind = np.random.randint(0, len(int_index)-batch_size+1)
    #         inds = int_index[start_ind:start_ind+batch_size] # (batch_size,)
            
    #     for i, random_index in enumerate(inds):
    #         X_sample = self.X.iloc[random_index - adj_n_time_steps: random_index] # (adj_n_time_steps, n_features)
    #         y_sample = self.y.iloc[random_index - 1] # (n_symbols,)
    #         X_batch[i, :] = X_sample
    #         y_batch[i] = y_sample
        
    #     return X_batch, y_batch

    def __len__(self):
        return len(self.X)
    
    
    @property
    def n_features(self):
        return len(self.X.columns)
    
    @property
    def n_symbols(self):
        return len(self.y.columns)
    
    @property
    def index(self):
        return self.X.index
    
    @property
    def symbols(self):
        return list(self.column_records.keys())