from ._internals.collector import collect_entrypoints

if __name__ == "__main__":
    entrypoints = collect_entrypoints("shortcuts")
