import sys
import os
import re

# these types of lines will improve readability in source code
# which is whole point of this
def should_ignore_line(line):
    return not line or line.isspace() or line[0] == "#"

def raise_error(message):
    print(message)
    exit()

def get_file_paths():
    if len(sys.argv) <= 1:
        raise_error("Enter file as arguement")
    source_file_path = sys.argv[1]
    if not os.path.exists(source_file_path):
        raise_error("Source file doesn't exist")
    compiled_file_path = source_file_path + ".ytmux"  # yagna tmux
    return source_file_path, compiled_file_path


# TODO: add more than one line for loop?
def expand_for_loops(code):
    """
    Coverts the line ["for 4: cmd "] into just ["cmd", "cmd", "cmd", "cmd"]
    """
    iterations_per_line = [ 1 for i in range(len(code)) ]
    for_loop_pattern = re.compile(r"^for (?P<iterations>\d+): (?P<command>.+)")
    for lineno, line in enumerate(code):
        if match := for_loop_pattern.match(line):
            iterations, line = int(match.group("iterations")), match.group("command")
            code[lineno], iterations_per_line[lineno] = line, iterations
        elif "for" in line:
            raise_error("Syntax error with for loop")

    expanded_code = []
    for lineno, line in enumerate(code):
        for i in range(iterations_per_line[lineno]):
            expanded_code.append(line)
    return expanded_code

def parse_pane_commands(code):
    """
    Parsed code of the format "pane-number: some-shell-command"

    E.g. ["1: do this; do that; then this"] becomes [
        select-pane -t 1,
        send-keys "do this; do that; then this",
        send-keys Enter,
    ]
    """
    parsed_code = []
    pane_command_pattern = re.compile("(?P<paneno>\d+): (?P<command>.+)")
    for line in code:
        if match := pane_command_pattern.match(line):
            paneno, command = match.group("paneno"), match.group("command")
            parsed_code.append(f"select-pane -t {paneno}")
            parsed_code.append(f"send-keys \"{command}\"")
            parsed_code.append(f"send-keys Enter")
        else:
            parsed_code.append(line)
    return parsed_code


source_file_path, compiled_file_path = get_file_paths()
with open(source_file_path, 'r') as source_file, open(compiled_file_path, 'w+') as compiled_file:
    # removes \n from end of lines and \t in lines after for loop 
    source_code = [
        line.strip() for line in source_file if not should_ignore_line(line)
    ]
    if not source_code:
        raise_error("Found no code to compile :>\(")

    source_code[0] = f"tmux {source_code[0]}"  # only first line needs to prepend cmd with tmux
    source_code = expand_for_loops(source_code)
    source_code = parse_pane_commands(source_code)
    # TODO allow for regular bash commands e.g. variable names, sleep commands
    compiled_code = "#!/bin/bash\n"  # always required for bash scripts obv
    line_seperator = r" \; "
    compiled_code += line_seperator.join(source_code)
    compiled_file.write(compiled_code)

