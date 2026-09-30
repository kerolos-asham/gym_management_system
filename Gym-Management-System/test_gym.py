import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gym_system import FileManager
from gym_system import Gym


class GymTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gym = Gym(FileManager(self.temp_dir.name))
        self.member = self.gym.add_member("Ahmed Ali", "01000000000", 22)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_member(self):
        self.assertEqual(self.member.name, "Ahmed Ali")
        self.assertEqual(self.member.person_id, 1)

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            self.gym.add_member("Bad", "010", 10)

    def test_zero_payment(self):
        with self.assertRaises(ValueError):
            self.gym.add_payment(self.member.person_id, 0, "Cash")

    def test_active_membership_allows_attendance(self):
        today = date.today()
        self.gym.create_membership(self.member.person_id, today.isoformat(), (today + timedelta(days=30)).isoformat(), 500)
        attendance = self.gym.record_attendance(self.member.person_id)
        self.assertEqual(attendance.member_id, self.member.person_id)

    def test_expired_membership_blocks_attendance(self):
        start = date.today() - timedelta(days=30)
        end = date.today() - timedelta(days=1)
        self.gym.create_membership(self.member.person_id, start.isoformat(), end.isoformat(), 500)
        with self.assertRaises(ValueError):
            self.gym.record_attendance(self.member.person_id)

    def test_two_active_memberships_blocked(self):
        today = date.today()
        end = today + timedelta(days=30)
        self.gym.create_membership(self.member.person_id, today.isoformat(), end.isoformat(), 500)
        with self.assertRaises(ValueError):
            self.gym.create_membership(self.member.person_id, today.isoformat(), end.isoformat(), 600)

    def test_search_partial_name(self):
        self.gym.add_member("Mohamed Hassan", "01111111111", 30)
        results = self.gym.search_members("hass")
        self.assertEqual(len(results), 1)

    def test_save_and_load(self):
        self.gym.save_data()
        loaded = Gym(FileManager(self.temp_dir.name))
        self.assertEqual(len(loaded.members), 1)
        self.assertEqual(loaded.members[0].name, "Ahmed Ali")


if __name__ == "__main__":
    unittest.main()
