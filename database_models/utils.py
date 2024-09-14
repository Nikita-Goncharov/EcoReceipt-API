import string


def check_hex_digit(hex_string: str) -> bool:
    return len(hex_string) == 8 and all((symbol in string.hexdigits) for symbol in hex_string)
