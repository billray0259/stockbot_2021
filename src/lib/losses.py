import keras.backend as K

def negative_profit_loss(y_true, y_pred):
    """ Loss based on the negative profit achieved given a positioning and a price movement

    Args:
        y_true (float): Percent return over next time step
        y_pred (float): Positioning where -1 represents 100% short, and 1 represents 100% long

    Returns:
        float: Negative profit from holdings descroibed by y_pred 
    """

    return -y_pred * y_true


def single_negative_sharpe_ratio_loss(y_true, y_pred):
    rets = y_pred * y_true
    rets_std = K.std(rets)
    benchmark = K.mean(y_true)
    return (benchmark - rets) / (rets_std + K.epsilon())


def multi_negative_sharpe_ratio_loss(y_true, y_pred):
    """ Loss based on the sharpe ratio

    Args:
        y_true (tensor): Shape (batch_size, n_symbols) Returns for every stock being observed
        y_pred (tensor): Shape (batch_size, n_symbols) Positioning percentages for every stock being observed

    Returns:
        float: Sharp ratio of the given training batch
    """
    rets = K.sum(y_pred * y_true, axis=-1) # Shape (batch_size,)
    rets_std = K.std(rets)

    benchmark = K.mean(y_true)
    # benchmark = K.mean(buy_and_hold_rets)
    # print(benchmark)
    
    return (benchmark - rets) / (rets_std + K.epsilon())