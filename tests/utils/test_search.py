from unittest import TestCase

from taleweave.models.entity import Room, World
from taleweave.utils.search import find_room


class TestFindRoom(TestCase):
    def test_existing_room(self):
        world = World(name="Test World", rooms=[], theme="testing", order=[])
        room = Room(
            name="Test Room",
            description="A test room.",
            characters=[],
            items=[],
            portals=[],
        )
        world.rooms.append(room)
        self.assertEqual(find_room(world, "Test Room"), room)

    def test_missing_room(self):
        world = World(name="Test World", rooms=[], theme="testing", order=[])
        room = Room(
            name="Test Room",
            description="A test room.",
            characters=[],
            items=[],
            portals=[],
        )
        world.rooms.append(room)
        self.assertEqual(find_room(world, "Missing Room"), None)
