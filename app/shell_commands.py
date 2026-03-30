import subprocess
import os
from pathlib import Path
from .shell_utils import ShellUtils

class ShellCommandHandler:
    def __init__(self, built_in_commands):
        self.built_in_commands = built_in_commands

    def execute(self, tokens):
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
                tokens = tokens[:tokens.index('>')] 
            
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
                    if token in self.built_in_commands:
                        value.append(f"{token} is a shell builtin")
                        return
                    match, full_path = ShellUtils.check_executable(token)
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
            match, full_path = ShellUtils.check_executable(tokens[0])
            if match:
                result = subprocess.run(tokens, capture_output=True, text=True)
                value = result.stdout
                if value.endswith('\n'):
                    value = value[:-1]
            else:
                value = (f"{tokens[0]}: command not found")
        if value is not None:
            if redirect: 
                with open(output_file, 'w') as file:
                    file.write(str(value))
            else:
                print(value)
