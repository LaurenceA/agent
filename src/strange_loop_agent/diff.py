import difflib

def diff(text1, text2, filename1="file1", filename2="file2"):
    """
    Generate a git-style unified diff between two texts with color coding.
    Added lines are green, and deleted lines are red.
    """
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

    diff = difflib.unified_diff(
        text1.splitlines(keepends=True),
        text2.splitlines(keepends=True),
        fromfile=filename1,
        tofile=filename2,
    )

    colored_diff = []
    for line in diff:
        if line.startswith('+'):
            colored_diff.append(f"{GREEN}{line}{RESET}")
        elif line.startswith('-'):
            colored_diff.append(f"{RED}{line}{RESET}")
        else:
            colored_diff.append(line)

    return ''.join(colored_diff)
