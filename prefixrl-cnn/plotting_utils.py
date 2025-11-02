from typing import List, Tuple
import sys

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREY = "\033[90m"
RED = "\033[31m"
BOLD_RED = "\033[1m\033[31m"
ORANGE = "\033[38;2;233;84;32m"
PURPLE = "\033[38;2;119;33;111m"
BLUE = "\033[38;2;0;120;255m"


GRAPH_TO_GATES_TITLE: List[str] = [
"   _____                 _       _           _____       _             ",
"  / ____|               | |     | |         / ____|     | |            ",
" | |  __ _ __ __ _ _ __ | |__   | |_ ___   | |  __  __ _| |_ ___  ___  ",
" | | |_ | '__/ _` | '_ \| '_ \  | __/ _ \  | | |_ |/ _` | __/ _ \/ __| ",
" | |__| | | | (_| | |_) | | | | | || (_) | | |__| | (_| | ||  __/\__ \ ",
"  \_____|_|  \__,_| .__/|_| |_|  \__\___/   \_____|\__,_|\__\___||___/ ",
"                  | |                                                  ",
"                  |_|                                                  "
]

SEPARATOR = "=" * len(GRAPH_TO_GATES_TITLE[0])

def print_title_banner(title: List[str]):
    gradient_start_rgb = (0, 120, 255)
    gradient_end_rgb = (255, 40, 130)
    
    for line in title:
        print(apply_gradient(line, gradient_start_rgb, gradient_end_rgb))

def apply_gradient(text: str, start_rgb: Tuple[int, int, int], end_rgb: Tuple[int, int, int]) -> str:
    """Applies a gradient color effect to the given text."""
    length = len(text)
    r_step = (end_rgb[0] - start_rgb[0]) / (max(length - 1, 1))
    g_step = (end_rgb[1] - start_rgb[1]) / (max(length - 1, 1))
    b_step = (end_rgb[2] - start_rgb[2]) / (max(length - 1, 1))

    colored_text = ""
    for i, letter in enumerate(text):
        r = int(start_rgb[0] + (r_step * i))
        g = int(start_rgb[1] + (g_step * i))
        b = int(start_rgb[2] + (b_step * i))
        colored_text += f"\033[38;2;{r};{g};{b}m{letter}{RESET}"
    return colored_text
    
def print_info(message: str) -> None:
    """Prints informational messages with a grey color."""
    print(f"{GREY}{message}{RESET}\n")

def print_info_formatted(label: str, value: str) -> None:
    """Prints informational messages with a grey color."""
    num_spaces = " " * (len(GRAPH_TO_GATES_TITLE[0]) - len(label) - len(value) - 1)
    print(f"{GREY}{label}:{num_spaces}{value}{RESET}\n")

def print_error(message: str, exit_script: bool = True) -> None:
    """Prints an error message in bold red. Exits the script if exit_script is True."""
    print(f"{BOLD_RED}ERROR: {message}{RESET}", file=sys.stderr)
    if exit_script:
        sys.exit(1)


def print_section_header(text: str) -> None:
    """Prints a section header in orange with bold formatting."""
    print(f"{ORANGE}{BOLD}{text.center(len(GRAPH_TO_GATES_TITLE[0]))}{RESET}")


def print_status(text: str) -> None:
    """Prints status messages in purple with bold formatting."""
    print(f"{PURPLE}{BOLD}{text}{RESET}\n")
    
def print_timestamp(text: str) -> None:
    """Prints status messages in purple with bold formatting."""
    print(f"{BLUE}{BOLD}{text}{RESET}\n")