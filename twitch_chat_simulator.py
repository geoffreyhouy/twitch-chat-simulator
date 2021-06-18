import logging
import re
import statistics
import sys

import irc.bot
import irc.client
import markovify

import settings

TWITCH_IRC_SERVER_HOST = "irc.chat.twitch.tv"
TWITCH_IRC_SERVER_PORT = 6667
TWITCH_IRC_SERVER_CAPABILITIES = (
    "twitch.tv/membership",
    "twitch.tv/tags",
    "twitch.tv/commands",
)
TWITCH_IRC_MESSAGE_CHAR_LIMIT = 500
# UTF-8 uses 1 to 4 bytes per character.
TWITCH_IRC_MESSAGE_BYTE_LIMIT = 4 * TWITCH_IRC_MESSAGE_CHAR_LIMIT

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

logger = logging.getLogger("twitch_chat_simulator")


class TwitchIRCServerConnection(irc.client.ServerConnection):
    def _prep_message(self, string: str) -> bytes:
        if "\r" in string or "\n" in string:
            raise irc.client.InvalidCharacters(
                "Messages must not contain newline characters."
            )
        bytes_ = self.encode(f"{string}\r\n")
        if len(bytes_) > TWITCH_IRC_MESSAGE_BYTE_LIMIT:
            raise irc.client.MessageTooLong(
                f"Messages must not exceed {TWITCH_IRC_MESSAGE_BYTE_LIMIT} bytes "
                "in length, including the appended CRLF."
            )
        return bytes_


class TwitchIRCReactor(irc.client.Reactor):
    connection_class = TwitchIRCServerConnection


class TwitchChatSimulator(irc.bot.SingleServerIRCBot):
    reactor_class = TwitchIRCReactor

    def __init__(
        self,
        username: str,
        oauth_token: str,
        channel: str,
        *,
        messages_per_generation: int,
    ) -> None:
        if not username:
            raise ValueError("username must be provided.")
        username = username.lower()

        if not oauth_token:
            raise ValueError("oauth_token must be provided.")
        oauth_token_prefix = "oauth:"
        if oauth_token == oauth_token_prefix:
            raise ValueError("oauth_token is incomplete.")
        if not oauth_token.startswith(oauth_token_prefix):
            oauth_token = f"{oauth_token_prefix}{oauth_token}"

        if not channel:
            raise ValueError("channel must be provided.")
        channel = channel.lower()
        channel_prefix = "#"
        if not channel.startswith(channel_prefix):
            channel = f"{channel_prefix}{channel}"

        super().__init__(
            [(TWITCH_IRC_SERVER_HOST, TWITCH_IRC_SERVER_PORT, oauth_token)],
            username,
            username,
        )
        self._channel = channel
        self.corpus = []
        self.messages_per_generation = messages_per_generation

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def messages_per_generation(self) -> int:
        return self._messages_per_generation

    @messages_per_generation.setter
    def messages_per_generation(self, messages_per_generation: int) -> None:
        if messages_per_generation < 2:
            raise ValueError("messages_per_generation must be at least 2.")
        self._messages_per_generation = messages_per_generation

    def on_welcome(
        self, connection: irc.client.ServerConnection, event: irc.client.Event
    ) -> None:
        logger.info(
            f"{connection.username} connected to {connection.server}:{connection.port}"
        )
        connection.cap("REQ", *TWITCH_IRC_SERVER_CAPABILITIES)
        connection.join(self.channel)

    def on_join(
        self, connection: irc.client.ServerConnection, event: irc.client.Event
    ) -> None:
        if connection.username == event.source.user:
            logger.info(f"{connection.username} joined {self.channel[1:]}'s chat room")

    def on_disconnect(
        self, connection: irc.client.ServerConnection, event: irc.client.Event
    ) -> None:
        logger.warning(f"{connection.username} disconnected")

    def on_pubnotice(
        self, connection: irc.client.ServerConnection, event: irc.client.Event
    ) -> None:
        logger.warning(event.arguments[0])

    def on_pubmsg(
        self, connection: irc.client.ServerConnection, event: irc.client.Event
    ) -> None:
        message = event.arguments[0]
        if message.startswith("!"):
            # Ignore messages intended for other bots.
            return
        # Remove URLs to reduce the chances of moderation flagging generated messages.
        message = re.sub(URL_RE, "", message)
        self.corpus.append(message)
        logger.debug(f"{event.source.user}: {message}")
        if len(self.corpus) >= self.messages_per_generation:
            self.send_generated_message(connection)

    def generate_message(self) -> str:
        message_lengths = [len(message) for message in self.corpus]
        message_length_mean = int(statistics.mean(message_lengths))
        # Use a second-order Markov chain to make potentially longer generated messages
        # look less like spam.
        state_size = 1 if message_length_mean < 100 else 2
        model = markovify.NewlineText(
            "\n".join(self.corpus), state_size=state_size, retain_original=False
        )
        # Limit the generated message length to within two standard deviations of the
        # corpus message length mean to better represent an average message.
        message_length_stdev = int(
            statistics.stdev(message_lengths, message_length_mean)
        )
        generated_message_max_length = min(
            TWITCH_IRC_MESSAGE_CHAR_LIMIT,
            message_length_mean + 2 * message_length_stdev,
        )
        generated_message_min_length = max(
            0,
            message_length_mean - 2 * message_length_stdev,
        )
        return model.make_short_sentence(
            generated_message_max_length, generated_message_min_length
        )

    def send_generated_message(
        self, connection: irc.client.ServerConnection, *, clear_corpus: bool = True
    ) -> None:
        message = self.generate_message()
        if clear_corpus:
            self.corpus.clear()
        connection.privmsg(self.channel, message)
        logger.info(f"{connection.username}: {message}")


def configure_logging(debug: bool = False) -> None:
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.DEBUG if debug else logging.INFO,
        stream=sys.stdout,
    )
    logging.getLogger("irc").setLevel(logging.WARNING)


def main() -> None:
    configure_logging(settings.DEBUG)

    bot = TwitchChatSimulator(
        settings.USERNAME,
        settings.OAUTH_TOKEN,
        settings.CHANNEL,
        messages_per_generation=settings.MESSAGES_PER_GENERATION,
    )

    print("Quit Twitch Chat Simulator with CTRL-C.")
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.die("")


if __name__ == "__main__":
    main()
