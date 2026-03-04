import sys

def commands(terminal_input):
    if terminal_input[0:5] == "echo ":
        print(terminal_input[5:])
    else:
        print(f"{terminal_input}: command not found")



def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        terminal_input = input()
        if terminal_input == "exit":
            break
        else: 
            commands(terminal_input)
    pass


if __name__ == "__main__":
    main()
