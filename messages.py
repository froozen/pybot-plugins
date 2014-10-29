from pybot import plugin_manager, irc, shared_data
import time

def msg_command ( command, server ):
    """Execute the )msg command."""

    # This command needs a receipent and a message -> args > 1
    if len ( command.args ) > 1:
        message = "Message from %s: %s" % ( command.event.name, " ".join ( command.args [ 1: ] ) )
        receipent = command.args [ 0 ]

        # Receipent is online
        if server.user_data.get_user ( receipent ):
            # Send it directly to receipent
            message_event = irc.Irc_event ( "PRIVMSG", receipent, message )
            server.send_event ( message_event )

        else:
            # Create list if it doesn't already exist
            if not server.persistent_data.get ( "messages.%s.inbox" % receipent ):
                server.persistent_data.set ( "messages.%s.inbox" % receipent, [] )

            # Put message in inbox
            server.persistent_data.append ( "messages.%s.inbox" % receipent, message )
            server.persistent_data.set ( "messages.%s.unseen" % receipent, True )

def cm_command ( command, server ):
    """Execute the )cm command."""

    user = command.event.name

    # There are messages
    if server.persistent_data.get ( "messages.%s.inbox" % user ):
        messages = server.persistent_data.get ( "messages.%s.inbox" % user )
        if len ( messages ) > 0:
            messages_header_event = irc.Irc_event ( "PRIVMSG", user, "Your current inbox:" )
            server.send_event ( messages_header_event )

            index = 0
            for message in messages:
                message_event = irc.Irc_event ( "PRIVMSG", user, "%d. %s" % ( index, message ) )
                server.send_event ( message_event )
                index += 1

                # Prevent flooding protection to kick in
                if len ( messages ) > 3:
                    time.sleep ( 0.5 )

                if server.persistent_data.get ( "messages.%s.autoremove" % user ):
                    server.persistent_data.remove ( "messages.%s.inbox" % user, message )

            server.persistent_data.set ( "messages.%s.unseen" % user, False )
            return

    # Catch both cases for no messages
    no_messages_event = irc.Irc_event ( "PRIVMSG", user, "You don't have any messages." )
    server.send_event ( no_messages_event )

def rm_command ( command, server ):
    """Execute the )rm command."""

    user = command.event.name

    if len ( command.args ) > 0:
        # Delete all messages
        if "all" in command.args:
            server.persistent_data.set ( "messages.%s.inbox" % user, [] )
            return

        # Delete all listed messages
        if server.persistent_data.get ( "messages.%s.inbox" % user ):
            messages = server.persistent_data.get ( "messages.%s.inbox" % user )

            for arg in command.args:
                if not arg == "":
                    try:
                        server.persistent_data.remove ( "messages.%s.inbox" % user, messages [ int ( arg ) ] )
                    except ValueError:
                        number_error_event = irc.Irc_event ( "PRIVMSG", user, "\"%s\" is no valid number." % arg )
                        server.send_event ( number_error_event )
                    except IndexError:
                        index_error_event = irc.Irc_event ( "PRIVMSG", user, "%s is no valid index." % arg )
                        server.send_event ( index_error_event )

def autoremove_command ( command, server ):
    """Execute the )autoremove command."""

    user = command.event.name

    # Set the autoremove option
    if len ( command.args ) > 0:
        if command.args [ 0 ] == "on":
            server.persistent_data.set ( "messages.%s.autoremove" % user, True )
        elif command.args [ 0 ] == "off":
            server.persistent_data.set ( "messages.%s.autoremove" % user, False )
        else:
            invalid_option_event = irc.Irc_event ( "PRIVMSG", user, "\"%s\" is not valid option." % command.args [ 0 ] )
            server.send_event ( invalid_option_event )

    # Display the autoremove option
    else:
        if server.persistent_data.get ( "messages.%s.autoremove" % user ):
            display_event = irc.Irc_event ( "PRIVMSG", user, "You set autoremove to \"on\"." )
            server.send_event ( display_event )
        else:
            display_event = irc.Irc_event ( "PRIVMSG", user, "You set autoremove to \"off\"." )
            server.send_event ( display_event )

def on_join ( event, server ):
    """Handle JOIN events."""

    # There are unseen messages
    if server.persistent_data.get ( "messages.%s.unseen" % event.name ):
        # Notify user
        unseen_messages_event = irc.Irc_event ( "PRIVMSG", event.name, "You have unseen messages." )
        server.send_event ( unseen_messages_event )

plugin_manager.register_command ( "msg", msg_command )
plugin_manager.register_command ( "cm", cm_command )
plugin_manager.register_command ( "rm", rm_command )
plugin_manager.register_command ( "autoremove", autoremove_command )
plugin_manager.register_event_handler ( "JOIN", on_join )

shared_data.set ( "help.msg", "Send a message to a user that is afk or offline." )
shared_data.set ( "help.cm", "Check your inbox." )
shared_data.set ( "help.rm", "Remove message at index; use rm all to remove all messages." )
shared_data.set ( "help.autoremove", "Remove messages as soon as you've seen them. Valid options: on, off" )
