from pybot import irc, plugin_manager
import re
import httplib
import urllib
import HTMLParser


def valid_content(url):
    """Check wether an URL should be highlighted by checking the Content-Type
       header"""

    url_split = url.split('/')[2:]
    host = url_split[0]
    path = '/'.join(url_split[1:])

    http_connection = None
    connection_type = url.split(':')[0]
    if connection_type == "https":
        http_connection = httplib.HTTPSConnection(host)
    else:
        http_connection = httplib.HTTPConnection(host)

    http_connection.connect()
    http_connection.request("HEAD", path)
    resp = http_connection.getresponse()

    content_type = resp.getheader("Content-Type")
    if content_type:
        return content_type.split(';')[0] == "text/html"
    else:
        return False


@plugin_manager.event_handler("PRIVMSG")
def on_privmsg(event, server):
    """Detect urls in messages and reply with their titles"""

    channel = event.args[0]
    message = event.args[1]

    # Find the URLs
    for url_match in re.finditer("(http(?:s)?://.*?)( |\\?|$)", message):
        url = url_match.group(1)

        # Check wether the URL should be highlighted
        if valid_content(url):
            try:
                html = urllib.urlopen(url).read()
                # Find the title tag
                title_match = re.search("(?s)<title *>(.+?)</title *>", html)
                if title_match:
                    # Reply with the URL's title
                    title = title_match.group(1).strip()
                    title = HTMLParser.HTMLParser().unescape(title)
                    title = title.replace("\n", " ")
                    reply = irc.Irc_event(
                        "PRIVMSG", channel, "[%s] - %s" % (title, url))
                    server.send_event(reply)

            # The opening of URLs might fail
            except IOError:
                reply = irc.Irc_event(
                    "PRIVMSG", channel, "Failed to open url: %s" % url)
                server.send_event(reply)
