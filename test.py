a = {'a': 1, 'b':2, 'c': 3}

def test(iter_val):
    print(next(iter_val))

iter_val = iter(a)
test(iter_val)
test(iter_val)
test(iter_val)
