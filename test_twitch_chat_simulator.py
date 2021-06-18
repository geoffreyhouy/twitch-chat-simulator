import unittest

import irc.client

import twitch_chat_simulator


class TestTwitchIRCServerConnection(unittest.TestCase):
    def test_prep_message_with_newline_characters(self):
        connection = twitch_chat_simulator.TwitchIRCServerConnection(None)
        with self.assertRaises(irc.client.InvalidCharacters):
            connection._prep_message("message\r\n")

    def test_prep_message_with_overlong_message(self):
        connection = twitch_chat_simulator.TwitchIRCServerConnection(None)
        with self.assertRaises(irc.client.MessageTooLong):
            connection._prep_message(
                "a" * twitch_chat_simulator.TWITCH_IRC_MESSAGE_BYTE_LIMIT
            )


class TestTwitchChatSimulator(unittest.TestCase):
    def test_init_with_empty_username(self):
        with self.assertRaises(ValueError):
            twitch_chat_simulator.TwitchChatSimulator(
                "", "oauth:abcd1234", "channel", messages_per_generation=2
            )

    def test_init_with_empty_oauth_token(self):
        with self.assertRaises(ValueError):
            twitch_chat_simulator.TwitchChatSimulator(
                "username", "", "channel", messages_per_generation=2
            )

    def test_init_with_oauth_token_prefix_only(self):
        with self.assertRaises(ValueError):
            twitch_chat_simulator.TwitchChatSimulator(
                "username", "oauth:", "channel", messages_per_generation=2
            )

    def test_init_with_empty_channel(self):
        with self.assertRaises(ValueError):
            twitch_chat_simulator.TwitchChatSimulator(
                "username", "oauth:abcd1234", "", messages_per_generation=2
            )

    def test_init_with_less_than_two_messages_per_generation(self):
        with self.assertRaises(ValueError):
            twitch_chat_simulator.TwitchChatSimulator(
                "username", "oauth:abcd1234", "channel", messages_per_generation=1
            )


if __name__ == "__main__":
    unittest.main()
