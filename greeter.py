from pybot import irc, plugin_manager, shared_data

def on_join ( event, server ):
    """Handle JOIN events."""

    channel = event.args [ 0 ]

    # Don't greet the bot
    if not server.nick == event.name:
        # There is a customized welcome message
        if server.persistent_data.get ( "greeter.%s.welcomemsgs" % event.name ):
            greet_event = irc.Irc_event ( "PRIVMSG", channel, server.persistent_data.get ( "greeter.%s.welcomemsgs" % event.name ) )
            server.send_event ( greet_event )

        else:
            greet_event = irc.Irc_event ( "PRIVMSG", channel, "Welcome on %s, %s." % ( channel, event.name ) )
            server.send_event ( greet_event )

def welcomemsg_command ( command, server ):
    """Execute the )welcomemsg command."""

    user = command.event.name

    # Set welcome message
    if len ( command.args ) > 0:
        server.persistent_data.set ( "greeter.%s.welcomemsgs" % user, " ".join ( command.args ) )

    # Output current welcome message
    else:
        if server.persistent_data.get ( "greeter.%s.welcomemsgs" % user ):
            message = "Your welcome message is: \"%s\"" % server.persistent_data.get ( "greeter.%s.welcomemsgs" % user )
            output_event = irc.Irc_event ( "PRIVMSG", user, message )
            server.send_event ( output_event )

        else:
            output_event = irc.Irc_event ( "PRIVMSG", user, "No welcome message set." )
            server.send_event ( output_event )

plugin_manager.register_event_handler ( "JOIN", on_join )
plugin_manager.register_command ( "welcomemsg", welcomemsg_command )

shared_data.set ( "help.welcomemsg", "Change the bots greeting." )
