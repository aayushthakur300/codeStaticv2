from typing import Final

# Practical safety limit to prevent CPU / memory exhaustion
MAX_FACTORIAL_INPUT: Final[int] = 10_000


def factorial(n: int) -> int:
    """
    Compute the factorial of a non-negative integer within safe limits.

    Args:
        n (int): A non-negative integer not exceeding MAX_FACTORIAL_INPUT.

    Returns:
        int: The factorial of n.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative or exceeds MAX_FACTORIAL_INPUT.
    """

    if not isinstance(n, int):
        raise TypeError("Factorial is only defined for integers.")

    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")

    if n > MAX_FACTORIAL_INPUT:
        raise ValueError(
            f"Input too large. Maximum supported value is {MAX_FACTORIAL_INPUT}."
        )

    # Base cases
    if n in (0, 1):
        return 1

    result = 1
    for value in range(2, n + 1):
        result *= value

    return result


def _safe_read_integer(prompt: str) -> int:
    """
    Safely read an integer from user input.

    Raises:
        ValueError: If input is not a valid integer.
    """
    user_input = input(prompt).strip()
    return int(user_input)


if __name__ == "__main__":
    try:
        number = _safe_read_integer("Enter a non-negative integer: ")

        # Defensive pre-check before heavy computation
        if number > MAX_FACTORIAL_INPUT:
            raise ValueError(
                f"Input exceeds safe limit ({MAX_FACTORIAL_INPUT}). Aborting."
            )

        result = factorial(number)
        print(f"Factorial of {number} is {result}")

    except (ValueError, TypeError) as exc:
        print(f"Error: {exc}")
