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
    is_backslash = False
    is_space = False
    one_encountered_for_redirect = False
    tokens = []
    current_token = [] 
    for char in terminal_input:

        if is_backslash:
            current_token.append(char)
            is_backslash = False
            continue
        if char == "1" and not in_single_quotes and not in_double_quotes:
            one_encountered_for_redirect = True
            continue
        if (one_encountered_for_redirect and char == ">") or char == ">":
            one_encountered_for_redirect = False
            if len(current_token)!=0:
                tokens.append("".join(current_token))
            current_token = []
            tokens.append(">")
            continue
        elif one_encountered_for_redirect and char != ">":
            one_encountered_for_redirect = False
            current_token.append("1")

        if char == "\\":
            if in_single_quotes:
                current_token.append(char)
            else:
                is_backslash = True
            continue
        if char == "\"" and not in_single_quotes:
            if not in_double_quotes:
                in_double_quotes = True
                continue
            elif in_double_quotes:
                in_double_quotes = False
                continue

        if char == "'" and not in_double_quotes:
            if not in_single_quotes:
                in_single_quotes = True
                continue
            elif in_single_quotes:
                in_single_quotes = False
                continue
        
            
        if char != " ":
            current_token.append(char)
            is_space = False
        elif in_double_quotes or in_single_quotes:
            current_token.append(char)
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
    value = None
    redirect = False
    if len(tokens) == 0:
        print("")
        return
    if '>' in tokens: 
        redirect = True
        output_index = tokens.index('>') + 1
        if output_index < len(tokens):
            output_file = tokens[output_index]
            tokens = tokens[:tokens.index('>')] + tokens[output_index + 1:]
        
    if tokens[0]  == "echo":
        if len(tokens) == 1:
            value = ""
        else: 
            value = " ".join(tokens[1:])
    elif tokens[0] == "pwd":
        value = Path.cwd().resolve()
    elif tokens[0] == "type":
        if len(tokens) == 1:
            value = ""
        else:
            value = []
            for token in tokens[1:]:
                if token in built_in_commands:
                    value.append(f"{token} is a shell builtin")
                    return
                match, full_path = check_executable(token)
                if match:
                    value.append(f"{token} is {full_path}")
                else:
                    value.append(f"{token}: not found") 
            value = "\n".join(value)
    elif tokens[0] == "cd":
        if len(tokens) == 1:
            target = os.environ.get('HOME')
            os.chdir(target)
        else: 
            target = None
            if tokens[1][0] == "~":
                home = os.environ.get('HOME')
                target = Path(os.path.join(home, tokens[1][2:])).resolve()
            
            else:
                target = Path(tokens[1]).resolve()

            if target.resolve().is_dir():
                os.chdir(target.resolve())
            else: 
                print(f"cd: {tokens[1]}: No such file or directory")
            
    else:
        match, full_path = check_executable(tokens[0])
        if match:
            subprocess.run(tokens)
        else:
            value = (f"{tokens[0]}: command not found")
    if redirect: 
        with open(output_file, 'w') as file:
            file.write(value)
    else:
        print(value)



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
