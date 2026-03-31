# Assemble some helper functions

def floater(x):
    import numpy as np
    try:
        f = float(x)
    except:
        f = np.nan
    return f

def floaterbound(x):
    import numpy as np
    try:
        f = float(x)
    except:
        try:
            f = float(x.replace("<", ""))
        except:
            f = np.nan
    return f

def norm(x):
    import numpy as np
    try:
        n = np.linalg.norm(x)
    except:
        n = np.nan
    return n

def three_vec(x):
    import numpy as np
    try:
        a = np.array(x, dtype=float)
        if a.shape != (3,):
            raise ValueError("Don't understand input as a three-vector")
    except:
        a = np.array([np.nan, np.nan, np.nan])
    return a

def datetime_from_string(x):
    import pandas as pd
    try:
        dt = pd.to_datetime(x)
    except:
        dt = pd.to_datetime("1970-1-1").tz_localize("UTC")
    try:
        dt = dt.tz_convert("UTC")
    except:
        pass  # No timezone information present; assuming UTC
    return dt.tz_localize(None)

def ensure_list(x):
    """Make sure that this field is a list, rather than (say) a single string."""

    return x if isinstance(x, list) else [x]

def str_join_or_None(x):
    """Join an array of strings into a string; or failing that, None"""

    try:
        s = "".join(x)
    except:
        s = None
    return s
