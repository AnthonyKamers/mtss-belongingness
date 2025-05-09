from timeit import default_timer as timer
from mtsssigner.cff_builder import *

# values are tuples where (q, k, n)
values = [
    [2, 2, 4],
    [3, 3, 27],
    [4, 3, 64],
    [5, 4, 625],
    [5, 5, 3125],
    # [7, 5, 16807],
    # [8, 5, 32768],
    # [7, 6, 117649],
    # [8, 6, 262144],
    # [9, 6, 531441],
    # [7, 7, 823543],
    # [8, 7, 2097152],
    # [9, 7, 4782969],
    # [8, 8, 16777216],
    # [11, 7, 19487171],
    # [9, 8, 43046721],
    # [11, 8, 214358881],
    # [9, 9, 387420489],
    # [11, 9, 2357947691],
    # [11, 10, 25937424601],
    # [11, 11, 285311670611],
]


def main():
    qtd_tests = len(values)
    sperner_sum = 0
    polynomial_sum = 0
    for q, k, n in values:
        # first generate using 1-cff
        start_sperner = timer()
        create_1_cff(n)
        end_sperner = timer()
        diff_sperner = end_sperner - start_sperner

        # second, generate using polynomial construction
        start_polynomial = timer()
        create_cff(q, k)
        end_polynomial = timer()
        diff_polynomial = end_polynomial - start_polynomial

        # put into sums, so we take the average at the end
        sperner_sum += diff_sperner
        polynomial_sum += diff_polynomial

        print(diff_sperner, diff_polynomial)

    average_sperner = sperner_sum / qtd_tests
    average_polynomial = polynomial_sum / qtd_tests
    print(f'Sperner: {average_sperner}')
    print(f'Polynomial: {average_polynomial}')

    print(f'Polynomial takes {average_polynomial / average_sperner} times more to execute')


if __name__ == "__main__":
    main()
