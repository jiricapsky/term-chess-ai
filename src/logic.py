import numpy as np


def chooseComputerMove(moves):
    return np.random.choice(moves, size=1, replace=False)