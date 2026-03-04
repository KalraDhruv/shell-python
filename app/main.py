import sys
import os 
import subprocess

built_in_commands  = ["echo", "exit", "type"]

def check_executable(program):
    path = os.environ.get('PATH')
    individual_paths = path.split(os.pathsep)
    for path in individual_paths:
        if not os.path.isdir(path):
            continue
        full_path = os.path.join(path, program)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return True, full_path
    return False, None


def commands(terminal_input):
    if terminal_input[0:5] == "echo ":
        print(terminal_input[5:])
    elif terminal_input[0:5] == "type ":
        if terminal_input[5:] in built_in_commands:
            print(f"{terminal_input[5:]} is a shell builtin")
            return
        match, full_path = check_executable(terminal_input[5:])
        if match:
            print(f"{terminal_path[5:]} is {full_path}")
        else:
            print(f"{terminal_input[5:]}: not found") 
    else:
        individual_inputs = terminal_input.split(" ")
        match, full_path = check_executable(individual_inputs[0])
        if match:
            subprocess.run([full_path] + individual_inputs[1:])
        else:
            print(f"{terminal_input}: command not found")



def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        terminal_input = input()
        terminal_input = terminal_input.strip()
        if terminal_input == "exit":
            break
        else: 
            commands(terminal_input)
    pass


if __name__ == "__main__":
    main()
