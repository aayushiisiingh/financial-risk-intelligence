import sys

from src.engine.pipeline import run, summarize

if __name__ == "__main__":
    backend = sys.argv[1] if len(sys.argv) > 1 else None
    evs = run(backend=backend)
    print(summarize(evs))
