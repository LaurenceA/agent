import difflib
d = difflib.Differ()

def diff(original, updated):
    diff_lines = list(d.compare(original.splitlines(), updated.splitlines()))

    #Extracts the line numbers corresponding to modified code.
    modified_lines = [i for (i, line) in enumerate(diff_lines) if line[0] in ['+', '-']]

    #Extracts ranges of line numbers, rather than individual line numbers.
    modified_regions = []
    for line in modified_lines:
        if (0<len(modified_regions)) and (modified_regions[-1].stop == line):
            #If the previous modified line was the previous line, then
            #we're in the same block, and we should extend it by 1.
            modified_regions[-1] = range(modified_regions[-1].start, line+1)
        else:
            #If the previous modified line was not the previous line, then
            #we're starting a new block.
            modified_regions.append(range(line, line+1))

    #Expands the ranges
    expand = 2
    expanded_regions = []
    for region in modified_regions:
        start = max(0, region.start-expand)
        stop = min(len(diff_lines), region.stop+expand)
        expanded_regions.append(range(start, stop))

    #Merges the ranges
    merge = 3
    merged_regions = []
    for region in expanded_regions:
        if (0<len(merged_regions)) and (region.start <= (merged_regions[-1].stop + merge)):
            #Regions are close, so merge them.
            merged_regions[-1] = range(merged_regions[-1].start, region.stop)
        else:
            #Regions are far, so add prev_region
            merged_regions.append(region)

    region_text = []
    for region in merged_regions:
        region_text.append('\n'.join([line for (i, line) in enumerate(diff_lines) if i in region]))

    #breakpoint()

    return '\n\n\n\n\n'.join(region_text)





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
