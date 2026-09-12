"""Additional malformed-quote cases found by source review after frozen checks."""
import core
failures=[]
for raw in ['label,quantity\nx,"1', 'label,quantity\n"x"junk,1\n']:
    try:
        core.run(raw)
    except ValueError:
        pass
    else:
        failures.append(raw)
assert not failures, ('malformed CSV accepted', failures)
print('postreview-ok')
