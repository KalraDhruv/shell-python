import sys
import os 

built_in_commands  = ["echo", "exit", "type"]

def commands(terminal_input):
    if terminal_input[0:5] == "echo ":
        print(terminal_input[5:])
    elif terminal_input[0:5] == "type ":
        if terminal_input[5:] in built_in_commands:
            print(f"{terminal_input[5:]} is a shell builtin")
        match = False
        path = os.environ.get('PATH')
        individual_paths = path.split(os.pathsep)
        for path in individual_paths:
            if not os.path.isdir(path):
                continue
            full_path = os.path.join(path, terminal_input[5:])
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                print(f"{terminal_input[5:]} is {full_path}")
                match = True
                break
        if not match:
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
