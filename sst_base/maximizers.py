from databroker.core import SingleRunCache
import bluesky.preprocessors as bpp
from bluesky.plan_stubs import mv
import numpy as np

def find_max(plan, dets, *args, invert=False):
    """
    invert turns find_max into find_min
    """
    src = SingleRunCache()

    @bpp.subs_decorator(src.callback)
    def inner_maximizer():
        yield from plan(dets, *args)
        run = src.retrieve()
        table = run.primary.read()
        motor_names = run.metadata['start']['motors']
        motors = [m for m in args if getattr(m, 'name', None) in motor_names]
        detname = dets[0].name
        if invert:
            max_idx = int(table[detname].argmin())
            print(f"Minimum found at step {max_idx} for detector {detname}")
        else:
            max_idx = int(table[detname].argmax())
            print(f"Maximum found at step {max_idx} for detector {detname}")
        ret = []
        for m in motors:
            max_val = float(table[m.name][max_idx])
            print(f"setting {m.name} to {max_val}")
            ret.append([m, max_val])
            yield from mv(m, max_val)
        return ret
    return (yield from inner_maximizer())


def find_min(plan, dets, *args):
    return (yield from find_max(plan, dets, *args, invert=True))


def find_max_deriv(plan, dets, *args):
    src = SingleRunCache()

    @bpp.subs_decorator(src.callback)
    def inner_maximizer():
        yield from plan(dets, *args)
        run = src.retrieve()
        table = run.primary.read()
        motor_names = run.metadata['start']['motors']
        motors = [m for m in args if getattr(m, 'name', None) in motor_names]
        if len(motors) > 1:
            print("Derivative with multiple motors unsupported, \
            taking first motor")

        detname = dets[0].name
        motname = motors[0].name
        max_idx = np.argmax(np.abs(np.gradient(table[detname], table[motname])))
        print(f"Maximum derivative found at step {max_idx} for detector {detname}")
        ret = []
        for m in motors:
            max_val = float(table[m.name][max_idx])
            print(f"setting {m.name} to {max_val}")
            ret.append([m, max_val])
            yield from mv(m, max_val)
        return ret
    return (yield from inner_maximizer())
