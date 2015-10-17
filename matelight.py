from pybot import irc, plugin_manager, configuration, log
import socket


host = configuration.get("matelight.host")
port = configuration.get("matelight.port") or 1337
host_not_set = "Hostname for matelight in \"matelight.host\" not set."


@plugin_manager.command("matelight")
def matelight_command(command, server):
    """Execute the )matelight command"""

    channel = command.event.args[0]
    if host:
        message = " ".join(command.args)

        s = socket.socket()
        s.connect((host, port))
        s.send(message)
        reply = s.recv(1024)
        s.close()

        server.send_event(irc.Irc_event("PRIVMSG", channel, reply))

    else:
        server.send_event(irc.Irc_event("PRIVMSG", channel, host_not_set))


if not host:
    log.write(host_not_set)
