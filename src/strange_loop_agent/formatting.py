class color:
   MAGENTA = '\033[35m'
   DARKCYAN = '\033[36m'
   DARKGREY = '\033[90m'
   RED = '\033[91m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   BLUE = '\033[94m'
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   RESET = '\033[0m'

userassistant_format = color.BOLD

def print_system(string):
    print(color.GREEN+string+color.RESET)

def input_user():
    string = input(color.PURPLE)
    print(color.RESET, end='')
    return string

def print_assistant(string):
    print(color.BLUE+string+color.RESET)

def print_code(string):
    print(color.DARKGREY+string+color.RESET)

def print_ua(string):
    print(color.BOLD+string+color.RESET)

def print_internal_error(string):
    print(color.RED+string+color.RESET)
