from pybot import plugin_manager, irc, shared_data
import random


@plugin_manager.command("roll")
def roll_command(command, server):
    """Execute the )roll command."""

    channel = command.event.args[0] if not command.event.args[
        0] == server.nick else command.event.name

    # Roll a number within the given range
    if len(command.args) > 0:
        for arg in command.args:
            if not arg == "":
                try:
                    number = random.randint(0, int(arg))
                    roll_event = irc.Irc_event(
                        "PRIVMSG", channel, "You rolled %d." % number)
                    server.send_event(roll_event)

                except ValueError:
                    error_event = irc.Irc_event(
                        "PRIVMSG", channel, "%s is no valid number." % arg)
                    server.send_event(error_event)

    # Roll a number from 0 trough 1
    else:
        number = random.random()
        roll_event = irc.Irc_event(
            "PRIVMSG", channel, "You rolled %f." % number)
        server.send_event(roll_event)

shared_data.set("help.roll", "Roll a random number.")
