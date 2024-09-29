import difflib

def diff(text1, text2, filename1="file1", filename2="file2"):
    """
    Generate a git-style unified diff between two texts with color coding.
    Added lines are green, and deleted lines are red.

    Specifies line ranges + modified files.
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




s1 = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    num = 6  # Changed from 5 to 6
    result = factorial(num)
    print(f"The factorial of {num} is {result}")

if __name__ == "__main__":
    main()
"""

s2 = """def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    num = 5
    result = factorial(num)
    print(f"The factorial of {num} is {result}")

if __name__ == "__main__":
    main()
"""
