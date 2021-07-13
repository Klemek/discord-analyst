from unittest import TestCase
from unittest.mock import MagicMock
from src.scanners import FirstScanner
from datetime import datetime, timedelta

from tests.utils import AsyncTestCase, fake_message


class TestFirstScanner(AsyncTestCase):
    def test_help(self):
        self.assertGreater(len(FirstScanner.help()), 0)
        self.assertIn("%first", FirstScanner.help())

    def test_empty_no_messages(self):
        scanner = FirstScanner()

        command_msg = MagicMock()
        self._await(scanner.init(command_msg, []))

        results = self._await(scanner.get_results(""))
        self.assertListEqual(["There was no messages matching your filters"], results)

    def test_empty_filtered(self):
        scanner = FirstScanner()
        scanner.raw_members = [1]

        self._await(scanner.init(fake_message(), []))

        messages = [fake_message(author=2), fake_message(author=3)]

        for msg in messages:
            scanner.compute_message(msg.channel, msg)

        results = self._await(scanner.get_results(""))
        self.assertListEqual(["There was no messages matching your filters"], results)

    def test_normal(self):
        scanner = FirstScanner()

        self._await(scanner.init(fake_message(), []))

        messages = [
            fake_message(id=1, created_at=timedelta(days=-2)),
            fake_message(id=2, created_at=timedelta(days=-3)),
            fake_message(id=3, created_at=timedelta(days=-1)),
        ]

        for msg in messages:
            scanner.compute_message(msg.channel, msg)

        results = self._await(scanner.get_results(""))

        expected = messages[1]
        self.assertListEqual(
            [
                "First message out of 3",
                f"{expected.created_at.strftime('%H:%M, %d %b. %Y')} (2 days ago) <@1> said:",
                f"> {expected.content}",
                "<https://discord.com/channels/1/1/2>",
            ],
            results,
        )

    def test_filtered(self):
        scanner = FirstScanner()
        scanner.raw_members = [1]

        self._await(scanner.init(fake_message(), []))

        messages = [
            fake_message(id=1, author=1, created_at=timedelta(days=-2)),
            fake_message(id=2, author=2, created_at=timedelta(days=-3)),
            fake_message(id=3, author=1, created_at=timedelta(days=-1)),
        ]

        for msg in messages:
            scanner.compute_message(msg.channel, msg)

        results = self._await(scanner.get_results(""))

        expected = messages[0]
        self.assertListEqual(
            [
                "First message out of 2",
                f"{expected.created_at.strftime('%H:%M, %d %b. %Y')} (yesterday) <@1> said:",
                f"> {expected.content}",
                "<https://discord.com/channels/1/1/1>",
            ],
            results,
        )
