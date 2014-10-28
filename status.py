from pybot import plugin_manager, irc, shared_data

def afk_command ( command, server ):
    """Execute the )afk command."""

    channel = command.event.args [ 0 ] if not command.event.args [ 0 ] == server.nick else command.event.name
    user = command.event.name

    # Set afk message
    if len ( command.args ) > 0:
        message = " ".join ( command.args )
        server.shared_data.set ( "afk.%s.message" % user, message )

    # Mark user as afk
    server.shared_data.set ( "afk.%s.bool" % user, True )

    # Send announcing message
    announce_event = irc.Irc_event ( "PRIVMSG", channel, "%s is now afk." % user )
    server.send_event ( announce_event )

def status_command ( command, server ):
    """Execute the )status command."""

    channel = command.event.args [ 0 ] if not command.event.args [ 0 ] == server.nick else command.event.name

    # Display afk status for each name
    if len ( command.args ) > 0:
        for name in command.args:
            if server.shared_data.get ( "afk.%s.bool" % name ):
                if server.shared_data.get ( "afk.%s.message" % name ):
                    message = server.shared_data.get ( "afk.%s.message" % name )
                    status_event = irc.Irc_event ( "PRIVMSG", channel, "%s is afk ( %s )" % ( name, message ) )
                    server.send_event ( status_event )

                else:
                    status_event = irc.Irc_event ( "PRIVMSG", channel, "%s is afk" % name )
                    server.send_event ( status_event )

            else:
                status_event = irc.Irc_event ( "PRIVMSG", channel, "%s is not afk" % name )
                server.send_event ( status_event )

def undo_afk ( server, name ):
    """Undo the afk status of the user corresponding to name."""

    server.shared_data.set ( "afk.%s.message" % name, None )
    server.shared_data.set ( "afk.%s.bool" % name, False )

def on_quit ( event, server ):
    """Handle QUIT events."""

    undo_afk ( server, event.name )

def on_part ( event, server ):
    """Handle PART events."""

    # Detect wether user is still in userlist
    if not server.user_data.get_user ( event.name ):
        undo_afk ( server, event.name )

def on_privmsg ( event, server ):
    """Handle PRIVMSG events."""

    # Notify that user is back
    if server.shared_data.get ( "afk.%s.bool" % event.name ):
        undo_afk ( server, event.name )

        back_event = irc.Irc_event ( "PRIVMSG", event.args [ 0 ], "%s is back." % event.name )
        server.send_event ( back_event )

def afk_token ( event, server ):
    channel = server.user_data.get_channel ( event.args [ 0 ] )
    afk_nicks = []

    for user in channel.users:
        if server.shared_data.get ( "afk.%s.bool" % user.nick ):
            afk_nicks.append ( user.nick )

    return ", ".join ( afk_nicks )

plugin_manager.register_command ( "afk", afk_command )
plugin_manager.register_command ( "status", status_command )
plugin_manager.register_event_handler ( "QUIT", on_quit )
plugin_manager.register_event_handler ( "PART", on_part )
plugin_manager.register_event_handler ( "PRIVMSG", on_privmsg )

shared_data.set ( "help.afk", "Mark your self as afk. You can add a message." )
shared_data.set ( "hel.status", "Get the status of a user." )

shared_data.set ( "greeter.tokens.afk", afk_token )
