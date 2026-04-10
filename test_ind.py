from strategy import IndicatorCalculator
import numpy as np

def test():
    closes = np.random.rand(100) * 1000 + 60000
    volumes = np.random.rand(100) * 10
    
    calc = IndicatorCalculator()
    res = calc.calculate_sync(closes, volumes)
    
    print("ema_9:", res['ema_9'][-1])
    print("ema_20:", res['ema_20'][-1])
    print("rsi_14:", res['rsi_14'][-1])

if __name__ == "__main__":
    test()
