import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        terminal_input = input()
        if terminal_input == "exit":
            break
        print(f"{terminal_input}: command not found")
    pass


if __name__ == "__main__":
    main()
