"Helper functions for parsing user input."


def ask_yes_or_no(message, remaining_attempts=10):
    "Prompt a message and return True if the user confirms, False else."
    YES_VALUES = ["Y", "y", "yes", "YES", "Yes", "O", "o", "oui", "OUI", "Oui"]
    NO_VALUES = ["N", "n", "no", "NO", "No", "non", "NON", "Non"]
    user_input = str(input(message))

    if user_input in YES_VALUES:
        return True
    elif user_input in NO_VALUES:
        return False
    elif remaining_attempts == 0:
        raise ValueError("Input not undersood.")
    else:
        print("Input not understood, [Y/n] ?")
        return ask_yes_or_no("", remaining_attempts=remaining_attempts - 1)
