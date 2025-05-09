import json
import sys

sys.path.append("../")
from mtsssigner.cff_builder import get_d


def main():
    """
        Make a table considering different values for q and k, in order to make polynomial CFFs. In polynomial CFFs, we need to
        make the following checks:
        - q must be a prime power
        - k must be >= 2 and smaller than q
        - d = (q-1)/(k-1)
        - n = q^k
        - t = q^2
        Our final result will be a dictionary with 'd' as the key and a tuple: (q, k, n, t)
    """
    q = [7, 8, 9, 11, 13, 16, 17, 19, 23, 25, 27, 29, 31, 32, 37, 41, 43, 47, 49, 53, 61, 64]
    k = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

    table = {}
    for q_ in q:
        for k_ in k:
            d = get_d(q_, k_)
            if d == 0 or d == 1:
                continue

            n = q_ ** k_
            t = q_ ** 2
            if d not in table:
                table[d] = [(q_, k_, n, t)]
            else:
                table[d].append((q_, k_, n, t))

    for d in table:
        print(f"d={d}: {table[d]}")

    # put manually the 63 value into the table, so we use in our article
    table[63] = [(64, 2, 4096, 4096)]

    # save to json
    with open("./d_cff.json", "w") as f:
        json.dump(table, f, indent=4)


if __name__ == "__main__":
    main()
