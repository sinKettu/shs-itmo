import os


def check_path(abs_path):
    """
        Checking URL to avoid LFI
    """
    return (not os.path.exists(abs_path) or
            not abs_path.startswith(os.path.abspath(os.getcwd())) or
            any([abs_path.startswith(i) for i in deprecated]) or
            os.path.isdir(abs_path))
