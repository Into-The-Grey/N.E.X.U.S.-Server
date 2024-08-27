import random
"""
    The `strict_format` function randomly selects a variation and combines it with a response in a
    specific format.
    
    :param response: The `response` parameter is the input text or message that you want to format in a
    specific way
    :param variations: The `variations` parameter in the `strict_format` function is a list of strings
    that represent different variations of a message or response. When the function is called, it
    randomly selects one of these variations and combines it with the provided `response` parameter in a
    specific format
    :return: The function `strict_format` takes two parameters: `response` and `variations`. It randomly
    selects a variation from the list of variations and then returns a formatted string that includes
    the chosen variation and the response.
"""

def strict_format(response, variations):
    chosen_variation = random.choice(variations)
    return f"({chosen_variation} {response})"
