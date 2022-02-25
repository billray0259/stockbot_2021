# Contents
configs

`src`
* `lib`
    * `activations.py`
        * Custom activation functions
            *  Negative Softmax
                * Maps values to the range -1 to 1
                * Ensures the absolute value of its outputs sums to 1
                * Used to make trading decisions over a list of symbols where postive values indicate a "buy" signal and negative values inidcate a "short" signal
                * Because the absolute values sum to 1, the signals limit exposure to 100%
                * Ex:
                    * Symbols: [FB, AMZN, NTFLX, GOOG]
                    * Negative Softmax output: [-0.2, 0.3, -0.1, 0.4]
                    * Portfolio size: $100k
                    * Actions: Short $20k of FB, long $30k of AAPL, short $10k of NTFLX, long $40k of GOOG.
    * `losses.py`
        * Custom loss functions
            * Negative Profit Loss
                * Loss based on the negative profit achieved given a positioning and a price movement
                * When this loss is minimized, profit is maximized
            * Negative Sharpe Ratio Loss
                * Calculates the sharpe ratio over the training batch
                * When this loss is minimized the sharpe ratio is maximized
                * Proved much more effective than the negative profit loss
    * `price_history.py`
        * 
    * `stock_dataset.py`
* `nb`

tests

