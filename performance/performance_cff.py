import sys
from timeit import default_timer as timer

sys.path.append("../")
from mtsssigner.cff_builder import __create_polynomial_cff

OUTPUT_FILE = 'output/q_k_cff_ms.txt'
QTD_ITERATION = 100


def main():
    q_values = [2, 3, 4, 5, 7, 8, 9, 11, 13]
    k_values = [2, 3, 4, 5]

    # Limpa o conteúdo do arquivo no início
    open(OUTPUT_FILE, "w").close()

    for q_ in q_values:
        for k_ in k_values:
            times = []
            for _ in range(QTD_ITERATION):
                try:
                    start = timer()
                    __create_polynomial_cff(q_, k_)
                    end = timer()
                    times.append((end - start) * 1000)  # em ms
                except:
                    times = []
                    break

            if times:
                avg_time = sum(times) / len(times)
                line = f"{q_} {k_} {avg_time:.6f}"
                print(line)
                with open(OUTPUT_FILE, "a") as f:
                    f.write(line + "\n")


if __name__ == "__main__":
    main()
