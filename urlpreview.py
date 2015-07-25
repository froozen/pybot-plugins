from pybot import irc, plugin_manager
import re
import urllib
import HTMLParser

def on_privmsg ( event, server ):
    """Detect urls in messages and reply with their titles"""

    channel = event.args [ 0 ]
    message = event.args [ 1 ]

    # Find the URLs
    for url_match in re.finditer( "http(s)?://.*?( |$)", message ):
        url = url_match.group( 0 )

        try:
            html = urllib.urlopen( url ).read ()
            # Find the title tag
            title_match = re.search( "(?s)<title *>(.*?)</title *>", html )
            if title_match:
                # Reply with the URL's title
                title = title_match.group( 1 ).strip ()
                title = HTMLParser.HTMLParser().unescape( title )
                reply = irc.Irc_event ( "PRIVMSG", channel, "[%s] - %s" % ( title, url ) )
                server.send_event ( reply )

        # The opening of URLs might fail
        except IOError:
            reply = irc.Irc_event ( "PRIVMSG", channel, "Failed to open url: %s" % url )
            server.send_event ( reply )

plugin_manager.register_event_handler ( "PRIVMSG", on_privmsg )
