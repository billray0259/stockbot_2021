import keras.backend as K
from keras.activations import softmax


def negative_softmax(x):
    absx = K.abs(x)
    return x / absx * softmax(absx, axis=-1)