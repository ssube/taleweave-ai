from adventure.models.entity import Attributes, Room


def hot_room(room: Room, attributes: Attributes):
    """
    If the room is hot, characters should get hotter.
    """

    for character in room.characters:
        character.attributes["hot"] = "hot"

    return attributes


def cold_room(room: Room, attributes: Attributes):
    """
    If the room is cold, characters should get colder.
    """

    for character in room.characters:
        character.attributes["cold"] = "cold"

    return attributes
