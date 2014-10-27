from pybot import plugin_manager, shared_data, irc

def help_command ( command, server ):
    """Execute the )help command."""

    channel = command.event.args [ 0 ] if not command.event.args [ 0 ] == server.nick else command.event.name
    help_data = shared_data.get ( "help" )

    if help_data:
        # Display all available topics
        if len ( command.args ) == 0:
            if len ( help_data.keys () ) > 0:
                help_message = "Available topics: %s" % ", ".join ( help_data.keys () )
                help_event = irc.Irc_event ( "PRIVMSG", channel, help_message )
                server.send_event ( help_event )

        # Display help for the topics
        else:
            for topic in command.args:
                if topic in help_data:
                    topic_event = irc.Irc_event ( "PRIVMSG", channel, "%s: %s" % ( topic, help_data [ topic ] ) )
                    server.send_event ( topic_event )

plugin_manager.register_command ( "help", help_command )

shared_data.set ( "help.help", "Display information about a topic." )
