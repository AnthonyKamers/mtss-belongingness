import sys
from timeit import default_timer as timer

sys.path.append('.')

from mtsssigner.cff_builder import *
from mtsssigner.utils.file_and_block_utils import write_cff_to_file

k_s = [2, 3, 4, 5]
q_s = [2, 3, 4, 5, 7, 8, 9, 11, 13, 16]


def cff_test(q, k):
    try:
        start = timer()
        cff = create_cff(q, k)
        end = timer()

        t = len(cff)
        n = len(cff[0])

        print(q, end=" ", flush=True)
        print(k, end=" ", flush=True)
        print(end - start, flush=True)
        sys.stdout.flush()

        # write cff to disk
        write_cff_to_file(t, n, k, cff)
    except Exception as e:
        print(f"({q},{k}) error in", str(e))


def main():
    for k in k_s:
        for q in q_s:
            cff_test(q, k)


if __name__ == "__main__":
    main()
