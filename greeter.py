from pybot import irc, plugin_manager, shared_data

def on_join ( event, server ):
    """Handle JOIN events."""

    channel = event.args [ 0 ]

    # Don't greet the bot
    if not server.nick == event.name:
        greet_event = irc.Irc_event ( "PRIVMSG", channel, _generate_greeting ( event, server ) )
        server.send_event ( greet_event )

def _generate_greeting ( event, server ):
    # No welcomemsg set
    if not server.persistent_data.get ( "greeter.%s.welcomemsgs" % event.name ):
        return "Welcome on %s, %s." % ( channel, event.name )

    if shared_data.get ( "greeter.tokens" ):
        tokens = shared_data.get ( "greeter.tokens" )
        welcomemsg = server.persistent_data.get ( "greeter.%s.welcomemsgs" % event.name )

        for token in tokens:
            while "%%%s%%" % token in welcomemsg:
                try:
                    insert = tokens [ token ] ( event, server )
                    welcomemsg = welcomemsg.replace ( "%%%s%%" % token, insert )
                except:
                    raise
                    welcomemsg = welcomemsg.replace ( "%%%s%%" % token, "Failed" )

        return welcomemsg

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

def tokens_command ( command, server ):
    channel = command.event.args [ 0 ] if not command.event.args [ 0 ] == server.nick else command.event.name

    if shared_data.get ( "greeter.tokens" ):
        tokens = shared_data.get ( "greeter.tokens" )
        tokens_list = ", ".join ( tokens.keys () )

        tokens_event = irc.Irc_event ( "PRIVMSG", channel, "Available tokens: %s" % tokens_list )
        server.send_event ( tokens_event )

    else:
        no_tokens_event = irc.Irc_event ( "PRIVMSG", channel, "No tokens available." )
        server.send_event ( no_tokens_event )

def channel_token ( event, server ):
    return event.args [ 0 ]

plugin_manager.register_event_handler ( "JOIN", on_join )
plugin_manager.register_command ( "welcomemsg", welcomemsg_command )
plugin_manager.register_command ( "tokens", tokens_command )

shared_data.set ( "help.welcomemsg", "Change the bots greeting." )
shared_data.set ( "help.tokens", "List all tokens available for use in welcome messages." )

shared_data.set ( "greeter.tokens.channel", channel_token )
