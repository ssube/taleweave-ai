from adventure.models.entity import Attributes, AttributeValue


def add_attribute(attributes: Attributes, name: str, value: int | float) -> Attributes:
    """
    Add an attribute to a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            raise ValueError(f"Cannot add a number to a string attribute: {name}")

        attributes[name] = value + previous_value
    else:
        attributes[name] = value

    return attributes


def subtract_attribute(
    attributes: Attributes, name: str, value: int | float
) -> Attributes:
    """
    Subtract an attribute from a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            raise ValueError(
                f"Cannot subtract a number from a string attribute: {name}"
            )

        attributes[name] = value - previous_value
    else:
        attributes[name] = -value

    return attributes


def multiply_attribute(
    attributes: Attributes, name: str, value: int | float
) -> Attributes:
    """
    Multiply an attribute in a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            raise ValueError(f"Cannot multiply a string attribute: {name}")

        attributes[name] = previous_value * value
    else:
        attributes[name] = 0

    return attributes


def divide_attribute(
    attributes: Attributes, name: str, value: int | float
) -> Attributes:
    """
    Divide an attribute in a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            raise ValueError(f"Cannot divide a string attribute: {name}")

        attributes[name] = previous_value / value
    else:
        attributes[name] = 0

    return attributes


def set_attribute(
    attributes: Attributes, name: str, value: AttributeValue
) -> Attributes:
    """
    Set an attribute in a set of attributes.
    """
    attributes[name] = value

    return attributes


def append_attribute(attributes: Attributes, name: str, value: str) -> Attributes:
    """
    Append a string to an attribute in a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            attributes[name] = previous_value + value
        else:
            raise ValueError(
                f"Cannot append a string to a non-string attribute: {name}"
            )
    else:
        attributes[name] = value

    return attributes


def prepend_attribute(attributes: Attributes, name: str, value: str) -> Attributes:
    """
    Prepend a string to an attribute in a set of attributes.
    """
    if name in attributes:
        previous_value = attributes[name]
        if isinstance(previous_value, str):
            attributes[name] = value + previous_value
        else:
            raise ValueError(
                f"Cannot prepend a string to a non-string attribute: {name}"
            )
    else:
        attributes[name] = value

    return attributes
