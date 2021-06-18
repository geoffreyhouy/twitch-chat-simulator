# Twitch Chat Simulator
Twitch Chat Simulator is an IRC chatbot that uses a Markov chain text generator to simulate messages in Twitch chat.

## Getting Started

### Requirements
Twitch Chat Simulator requires Python 3.9 or later. It also requires you to have a [Twitch](https://www.twitch.tv/) account.

### Installation
To install Twitch Chat Simulator, first clone this repository:
```shell
git clone https://github.com/geoffreyhouy/twitch-chat-simulator.git
```
Then install the required project dependencies:
```shell
python -m pip install -r requirements.txt
```
Note: You may want to use a virtual environment to install dependencies because the [IRC](https://github.com/jaraco/irc) library has a handful of dependencies itself.

Twitch Chat Simulator is now ready to be configured!

### Configuration
To configure Twitch Chat Simulator, first open the `settings.py` module.

Then edit the following variables:
- `USERNAME` The Twitch username of your chatbot.
- `OAUTH_TOKEN` The token used to authenticate your chatbot with Twitch servers. You can generate this token using the [Twitch Chat OAuth Password Generator](https://twitchapps.com/tmi/) while logged into your chatbot. For more information, see the [Twitch Developer Documentation](https://dev.twitch.tv/docs/irc).
- `CHANNEL` The Twitch username of the channel whose chat messages you want to simulate.
- `MESSAGES_PER_GENERATION` The number of chat messages used to generate a simulated message.
- `DEBUG` Whether to log all messages seen by your chatbot or not.

Twitch Chat Simulator is now ready to be used!

### Usage
To use Twitch Chat Simulator, run:
```shell
python twitch_chat_simulator.py
```
