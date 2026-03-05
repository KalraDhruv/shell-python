import sys
import os 
import subprocess
from pathlib import Path

built_in_commands  = ["echo", "exit", "type", "pwd"]

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


def tokenizer(terminal_input):
    index = 0
    in_single_quotes = False
    in_double_quotes = False
    is_space = False
    tokens = []
    current_token = [] 
    for char in terminal_input:
        if char == "'" and not in_single_quotes:
            in_single_quotes = True
            continue
        elif char == "'" and in_single_quotes:
            in_single_quotes = False
            continue
            
        if char != " " or in_single_quotes:
            current_token.append(char)
            is_space = False
        elif in_single_quotes:
            tokens.append(current_token.append(char))
        else: 
            if is_space == False:
                tokens.append("".join(current_token))
                current_token = []
            is_space = True
            continue
    if len(current_token) > 0:
        tokens.append("".join(current_token))
    return tokens


def commands(tokens):
    if len(tokens) == 0:
        print("")
        return
    if tokens[0]  == "echo":
        if len(tokens) == 1:
            print("")
        else: 
            print(" ".join(tokens[1:]))
    elif tokens[0] == "pwd":
        print(Path.cwd().resolve())
    elif tokens[0] == "type":
        if len(tokens) == 1:
            print("")
        else:
            for token in tokens[1:]:
                if token in built_in_commands:
                    print(f"{token} is a shell builtin")
                    return
                match, full_path = check_executable(token)
                if match:
                    print(f"{token} is {full_path}")
                else:
                    print(f"{token}: not found") 
    elif tokens[0] == "cd":
        if len(tokens) == 1:
            target = Path(os.environ.get('HOME'))
        else: 
            if tokens[1][0] == "~":
                target = os.environ.get('HOME')
            elif tokens[1].startswith("~/"):
                home = os.environ.get('HOME')
                target = os.path.join(home, tokens[1][2:])  
            else:
                target = Path(tokens[1]) 

            try:
                if target.resolve().exists() and target.resolve().is_dir():
                    os.chdir(target.resolve())
                else: 
                    print(f"cd: {tokens[1]}: No such file or directory")
            except Exception:
                print(f"cd: {tokens[1]}: No such file or directory")
            
    else:
        match, full_path = check_executable(tokens[0])
        if match:
            subprocess.run(tokens)
        else:
            print(f"{tokens[0]}: command not found")



def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        terminal_input = input()
        terminal_input = terminal_input.strip()
        if terminal_input == "exit":
            break
        else: 
            commands(tokenizer(terminal_input))
    pass


if __name__ == "__main__":
    main()
