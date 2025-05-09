import json


def main():
    def iterate_item(key_now, value_now, num_iterate=1):
        if isinstance(value_now, dict):
            if key_now is not None:
                print(f'{num_iterate * "-"} {key_now}')

            for key_now in value_now.keys():
                iterate_item(key_now, value_now[key_now], num_iterate + 1)

        elif isinstance(value_now, list):
            print(f'{num_iterate * "-"} {key_now}')

            for item in value_now:
                iterate_item(None, item, num_iterate + 1)
        elif isinstance(value_now, str):
            print(f'{num_iterate * "-"} {key_now} {value_now}')

    # start code
    with open("test.json") as file:
        data = json.load(file)

    for key, value in data.items():
        iterate_item(key, value, 1)


if __name__ == "__main__":
    main()