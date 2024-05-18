from adventure.models.entity import Attributes, Room


def hot_room(room: Room, attributes: Attributes):
    """
    If the room is hot, actors should get hotter.
    """

    for actor in room.actors:
        actor.attributes["hot"] = "hot"

    return attributes


def cold_room(room: Room, attributes: Attributes):
    """
    If the room is cold, actors should get colder.
    """

    for actor in room.actors:
        actor.attributes["cold"] = "cold"

    return attributes
