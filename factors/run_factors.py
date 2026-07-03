from factors.momentum import Momentum
from factors.quality import Quality
from factors.size import Size
from factors.value import Value
from factors.volatility import Volatility

FACTORS = [
    (Momentum, 'momentum'),
    (Value, 'value'),
    (Size, 'size'),
    (Quality, 'quality'),
    (Volatility, 'volatility')
]

for cls, name in FACTORS:
    print(f'Running {name}...')
    f = cls(name)
    data = f.compute()
    data = f.normalize(data)
    data = f.assign_quintiles(data)
    f.store(data)
    print(f"  → {len(data)} rows stored")

print('All factors complete.')