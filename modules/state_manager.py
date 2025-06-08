import os
import json

STATE_FILE = ".veno_state.json"

def save_state(state, outdir):
    path = os.path.join(outdir, STATE_FILE)
    with open(path, "w") as f:
        json.dump(state, f)

def load_state(outdir):
    path = os.path.join(outdir, STATE_FILE)
    if os.path.isfile(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def clear_state(outdir):
    path = os.path.join(outdir, STATE_FILE)
    try:
        os.remove(path)
    except OSError:
        pass
