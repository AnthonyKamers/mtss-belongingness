# procedure necessary to import from root
import sys

sys.path.append('.')


# https://stackoverflow.com/questions/41383787/round-down-to-2-decimal-in-python
def round_down(value, decimals: int = 4) -> float:
    factor = 1 / (10 ** decimals)
    return (value // factor) * factor


def to_ms(start, end) -> float:
    return round((end - start) * 1000, 2)
