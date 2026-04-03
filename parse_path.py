import sys


def parse_path(filename: str) -> None:
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line[0] == "#":
                    pass

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
