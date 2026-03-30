import sys
import os
import subprocess
from pathlib import Path

BUILTINS = {"echo", "exit", "type", "pwd", "cd"}


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
        elif char == ">" and not in_single and not in_double:
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


def get_redirect(tokens, symbol):
    """Extract redirect file for a given symbol, return (cleaned_tokens, filepath_or_None)."""
    if symbol in tokens:
        idx = tokens.index(symbol)
        if idx + 1 < len(tokens):
            return tokens[:idx], tokens[idx + 1]
    return tokens, None


def write_file(path, text):
    with open(path, "a") as f:
        text = str(text)
        f.write(text if text.endswith("\n") else text + "\n")


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





def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        line = input().strip()
        if line == "exit":
            break
        commands(tokenizer(line))


if __name__ == "__main__":
    main()
