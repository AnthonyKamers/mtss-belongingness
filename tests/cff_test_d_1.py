from mtsssigner.cff_builder import create_1_cff
from timeit import default_timer as timer

n_s = [64, 256, 512, 1024, 4096, 8192, 16384, 32768]


def main():
    for n in n_s:
        start = timer()
        create_1_cff(n)
        end = timer()

        print(n, end=" ", flush=True)
        print(end - start, flush=True)


if __name__ == "__main__":
    main()
