import sys
import os
import readline
import subprocess
from pathlib import Path

BUILTINS = {"echo", "exit", "type", "pwd", "cd", "history"}

def get_path_executables():
    path_str = os.environ.get("PATH", "")
    directories = path_str.split(os.pathsep)
    executables = set()

    for directory in directories:
        if os.path.isdir(directory):
            try: 
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    
                    if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                        executables.add(filename)

            except PermissionError:
                continue
    return list(executables)


def check_executable(program):
    for dir_ in os.environ.get("PATH", "").split(os.pathsep):
        full = os.path.join(dir_, program)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


def tokenizer(line):
    tokens, current = [], []
    in_single = in_double = is_backslash = False

    i = 0
    while i < len(line):
        char = line[i]

        if is_backslash:
            current.append(char)
            is_backslash = False
            i += 1
            continue

        # Check for 1> or 2> redirect prefixes
        if char in ("1", "2") and not in_single and not in_double and not current:
            if i + 2 < len(line) and line[i + 1:i + 3 ] == ">>":
                tokens.append(f"{char}>>")
                i += 3
                continue

            if i + 1 < len(line) and line[i + 1] == ">":
                tokens.append(f"{char}>")
                i += 2
                continue

        if char == "\\" and not in_single:
            is_backslash = True
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
        elif char == "|" and not in_single and not in_double:
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append("|")
        elif char == ">" and not in_single and not in_double:
            if current:
                tokens.append("".join(current))
                current = []
            if i + 1 < len(line) and line[i + 1] == ">":
                tokens.append(f">>")
                i += 2
            else:
                tokens.append(">")
        elif char == " " and not in_single and not in_double:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)

        i += 1

    if current:
        tokens.append("".join(current))
    return tokens


def helper_pipeline(tokens):
    result = []
    current_list = []

    for token in tokens:
        if token == "|":
            result.append(current_list)
            current_list = []
        else:
            current_list.append(token)

    if current_list:
        result.append(current_list)

    return result




def get_redirect(tokens, symbol):
    if symbol in tokens:
        idx = tokens.index(symbol)
        if idx + 1 < len(tokens):
            return tokens[:idx], tokens[idx + 1]
    return tokens, None


def write_file(path, text):
    with open(path, "a") as f:
        text = str(text)
        f.write(text if text.endswith("\n") else text + "\n")

def run_pipeline(pipeline):
    prev_read_fd = None
    pids = []

    for i, command_list in enumerate(pipeline):
        is_last = (i == len(pipeline) - 1)
        
        if is_last:
            read_fd, write_fd = None, None
        else:
            read_fd, write_fd = os.pipe()

        pid = os.fork()

        if pid == 0:
            # Wire up stdin from previous stage
            if prev_read_fd is not None:
                os.dup2(prev_read_fd, 0)
                os.close(prev_read_fd)

            # Wire up stdout to next stage (not for last command)
            if write_fd is not None:
                os.dup2(write_fd, 1)
                os.close(write_fd)
            if read_fd is not None:
                os.close(read_fd)

            # Try execvp first for external commands
            executable = check_executable(command_list[0])
            if executable:
                os.execvp(executable, command_list)

            # Fall back to commands() for builtins
            commands(command_list)
            sys.exit(0)

        else:
            pids.append(pid)
            if write_fd is not None:
                os.close(write_fd)
            if prev_read_fd is not None:
                os.close(prev_read_fd)
            if read_fd is not None:
                prev_read_fd = read_fd

    # Wait for all children
    for pid in pids:
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass

def commands(tokens):
    # Parse redirects
    tokens, write_stderr_file = get_redirect(tokens, "2>")
    tokens, write_stdout_file1 = get_redirect(tokens, ">")
    tokens, write_stdout_file2 = get_redirect(tokens, "1>")
    tokens, append_stderr_file = get_redirect(tokens, "2>>")
    tokens, append_stdout_file1 = get_redirect(tokens, ">>")
    tokens, append_stdout_file2 = get_redirect(tokens, "1>>")
   
    write_stdout_file = write_stdout_file1 or write_stdout_file2
    append_stdout_file = append_stdout_file1 or append_stdout_file2
    
    if not tokens:
        return

    # Always create redirect files upfront (even if nothing gets written to them)
    if write_stdout_file:
        open(write_stdout_file, "w").close()
    if append_stdout_file:
        open(append_stdout_file, "a").close()
    if write_stderr_file:
        open(write_stderr_file, "w").close()
    if append_stderr_file:
        open(append_stderr_file, "a").close()

    stderr_file = write_stderr_file or append_stderr_file
    stdout_file = write_stdout_file or append_stdout_file



    cmd = tokens[0]
    value_stdout = None
    value_stderr = None

    if cmd == "echo":
        value_stdout = " ".join(tokens[1:])

    elif cmd == "pwd":
        value_stdout = Path.cwd().resolve()

    elif cmd == "type":
        results = []
        for token in tokens[1:]:
            if token in BUILTINS:
                results.append(f"{token} is a shell builtin")
            elif (path := check_executable(token)):
                results.append(f"{token} is {path}")
            else:
                value_stderr = f"{token}: not found"
        value_stdout = "\n".join(results) if results else None

    elif cmd == "cd":
        target = os.environ.get("HOME", "") if len(tokens) == 1 else tokens[1]
        if target.startswith("~"):
            target = os.path.join(os.environ.get("HOME", ""), target[2:])
        target = Path(target).resolve()
        if target.is_dir():
            os.chdir(target)
        else:
            value_stderr = f"cd: {tokens[1]}: No such file or directory"

    else:
        path = check_executable(cmd)
        if path:
            result = subprocess.run(tokens, capture_output=True, text=True)
            if result.stdout:
                value_stdout = result.stdout.rstrip("\n")
            if result.stderr:
                value_stderr = result.stderr.rstrip("\n")
        else:
            value_stderr = f"{cmd}: command not found"

    if value_stdout:
        if stdout_file:
            write_file(stdout_file, value_stdout)
        else:
            print(value_stdout)
    if value_stderr:
        if stderr_file:
            write_file(stderr_file, value_stderr)
        else:
            print(value_stderr, file=sys.stderr)

def completer(text, state):
    # For optimization implement it such that it's run once at startup 
    # and whenever there's a "PATH=" in the command add the new customs from
    # the given new directories.
    
    if readline.get_begidx() == 0:
        customs = get_path_executables()
        options_commands = [cmd for cmd in BUILTINS | set(customs) if cmd.startswith(text)]

        if state < len(options_commands):
            return options_commands[state] + " "
        else: 
            return None

    else:
        if "/" in text:
            dir_path, prefix = text.rsplit("/", 1)
        else: 
            dir_path, prefix = ".", text

        options_filename = [file for file in os.listdir(dir_path) if file.startswith(prefix)]

        if state < len(options_filename):
            if dir_path == ".":
                if os.path.isdir(os.path.join(dir_path, options_filename[state])):
                    return options_filename[state] + "/"
                return options_filename[state] + " "
            if os.path.isdir(os.path.join(dir_path, options_filename[state])):
                return dir_path + "/" + options_filename[state] + "/"
            else:
                return dir_path + "/" + options_filename[state] + " "
        else:
            return None

def main():
    readline.parse_and_bind("tab:complete")
    readline.set_completer(completer)
    readline.set_completer_delims(" \t\n")
    history = []
    while True:
        line = input("$ ").strip()
        history.append(line)
        if line == "exit":
            break
        if line == "history":
            for i, cmd in enumerate(history):
                print(f"   {i}  {cmd}" )
            continue
        
        tokens = tokenizer(line)
        pipeline = helper_pipeline(tokens)
        if len(pipeline) > 1:
            run_pipeline(pipeline)
        else:
            commands(tokens)

if __name__ == "__main__":
    main()
