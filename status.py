from pybot import plugin_manager, irc, shared_data


@plugin_manager.command("afk")
def afk_command(command, server):
    """Execute the )afk command."""

    channel = command.event.args[0] if not command.event.args[
        0] == server.nick else command.event.name
    user = command.event.name

    # Set afk message
    if len(command.args) > 0:
        message = " ".join(command.args)
        server.shared_data.set("afk.%s.message" % user, message)

    # Mark user as afk
    server.shared_data.set("afk.%s.bool" % user, True)

    # Send announcing message
    announce_event = irc.Irc_event("PRIVMSG", channel, "%s is now afk." % user)
    server.send_event(announce_event)


@plugin_manager.command("status")
def status_command(command, server):
    """Execute the )status command."""

    channel = command.event.args[0] if not command.event.args[
        0] == server.nick else command.event.name

    # Display afk status for each name
    if len(command.args) > 0:
        for name in command.args:
            if not name == "":
                mark_type = None
                if server.shared_data.get("afk.%s.bool" % name):
                    mark_type = "afk"
                if server.shared_data.get("afk.%s.probably" % name):
                    mark_type = "proposed as afk by %s" % server.shared_data.get(
                        "afk.%s.proposer" % name)

                if mark_type == None:
                    status_event = irc.Irc_event(
                        "PRIVMSG", channel, "%s is not afk" % name)
                    server.send_event(status_event)
                else:
                    if server.shared_data.get("afk.%s.message" % name):
                        message = server.shared_data.get(
                            "afk.%s.message" % name)
                        status_event = irc.Irc_event(
                            "PRIVMSG", channel, "%s is %s ( %s )" % (name, mark_type, message))
                        server.send_event(status_event)
                    else:
                        status_event = irc.Irc_event(
                            "PRIVMSG", channel, "%s is %s" % (name, mark_type))
                        server.send_event(status_event)


@plugin_manager.command("afkPropose")
def afkPropose_command(command, server):
    """Execute the )afkPropose command."""

    channel = command.event.args[0] if not command.event.args[
        0] == server.nick else command.event.name

    if len(command.args) < 1:
        return  # Ignore.

    proposer = command.event.name
    target = command.args[0]

    if server.shared_data.get("afk.%s.bool" % target):
        reject_event = irc.Irc_event(
            "PRIVMSG", channel, "%s is already afk." % target)
        server.send_event(reject_event)
        return

    # Set afk message
    if len(command.args) > 1:
        message = " ".join(command.args[1:])
        server.shared_data.set("afk.%s.message" % target, message)

    # Mark user as possibly afk
    server.shared_data.set("afk.%s.probably" % target, True)
    server.shared_data.set("afk.%s.proposer" % target, proposer)

    # Send announcing message
    announce_event = irc.Irc_event(
        "PRIVMSG", channel, "%s is now probably afk." % target)
    server.send_event(announce_event)


def undo_afk(server, name):
    """Undo the afk status of the user corresponding to name."""

    server.shared_data.set("afk.%s.message" % name, None)
    server.shared_data.set("afk.%s.bool" % name, False)
    server.shared_data.set("afk.%s.probably" % name, False)
    server.shared_data.set("afk.%s.proposer" % name, False)


@plugin_manager.event_handler("QUIT")
def on_quit(event, server):
    """Handle QUIT events."""

    undo_afk(server, event.name)


@plugin_manager.event_handler("PART")
def on_part(event, server):
    """Handle PART events."""

    # Detect wether user is still in userlist
    if not server.user_data.get_user(event.name):
        undo_afk(server, event.name)


@plugin_manager.event_handler("PRIVMSG")
def on_privmsg(event, server):
    """Handle PRIVMSG events."""

    is_marked = server.shared_data.get(
        "afk.%s.bool" % event.name) or server.shared_data.get("afk.%s.probably" % event.name)

    if is_marked:
        undo_afk(server, event.name)

        # Notify that user is back
        back_event = irc.Irc_event(
            "PRIVMSG", event.args[0], "%s is back." % event.name)
        server.send_event(back_event)


def afk_token(event, server):
    channel = server.user_data.get_channel(event.args[0])
    afk_nicks = []

    for user in channel.users:
        if server.shared_data.get("afk.%s.bool" % user.nick):
            afk_nicks.append(user.nick)
        if server.shared_data.get("afk.%s.probably" % user.nick):
            afk_nicks.append("~" + user.nick)

    return ", ".join(afk_nicks)

shared_data.set("help.afk", "Mark your self as afk. You can add a message.")
shared_data.set(
    "help.afkPropose", "Mark somebody else as probably afk. You can add a message.")
shared_data.set("help.status", "Get the status of a user.")

shared_data.set("greeter.tokens.afk", afk_token)
