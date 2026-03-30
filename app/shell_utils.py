import os

class ShellUtils:
    BUILT_IN_COMMANDS = ["echo", "exit", "type", "pwd"]

    @staticmethod
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
