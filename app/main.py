import sys

built_in_commands  = ["echo", "exit", "type"]

def commands(terminal_input):
    if terminal_input[0:5] == "echo ":
        print(terminal_input[5:])
    elif terminal_input[0:5] == "type ":
        if terminal_input[5:] in built_in_commands:
            print(f"{terminal_input[5:]} is a shell builtin")
        else:
            print(f"{terminal_input[5:]}: not found") 
            
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
