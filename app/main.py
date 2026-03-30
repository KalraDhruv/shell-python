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
    tokens, stderr_file = get_redirect(tokens, "2>")
    tokens, stdout_file1= get_redirect(tokens, ">")
    tokens, stdout_file2 = get_redirect(tokens, "1>")
    stdout_file = stdout_file1 or stdout_file2

    if not tokens:
        return

    # Always create redirect files upfront (even if nothing gets written to them)
    if stdout_file:
        open(stdout_file, "w").close()
    if stderr_file:
        open(stderr_file, "w").close()

    cmd = tokens[0]
    value_stdout = None
    value_stderr = None

    if cmd == "echo":
        value_stdout = " ".join(tokens[1:])

    elif cmd == "pwd":
        value_stdout = Path.cwd().resolve()

    elif cmd == "type":
        for token in tokens[1:]:
            if token in BUILTINS:
                value_stdout = f"{token} is a shell builtin"
            elif (path := check_executable(token)):
                value_stdout = f"{token} is {path}"
            else:
                value_stderr = f"{token}: not found"

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
