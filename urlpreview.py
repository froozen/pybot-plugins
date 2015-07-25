from pybot import irc, plugin_manager
import re
import urllib
import HTMLParser


def valid_url(url):
    """Check wether an URL should be highlighted"""

    valid_filetypes = ["html", "htm", "php"]
    url_split = url.split("/")[2:]

    # Highlight it, if it has no filetype or is the home page
    if len(url_split) == 1 or not "." in url_split[-1]:
        return True

    # Otherwise, check wether it has a valid filetype
    else:
        filetype = url_split[-1].split(".")[-1]
        return filetype in valid_filetypes


def on_privmsg(event, server):
    """Detect urls in messages and reply with their titles"""

    channel = event.args[0]
    message = event.args[1]

    # Find the URLs
    for url_match in re.finditer("http(s)?://.*?( |$)", message):
        url = url_match.group(0)

        # Check wether the URL should be highlighted
        if valid_url(url):
            try:
                html = urllib.urlopen(url).read()
                # Find the title tag
                title_match = re.search("(?s)<title *>(.+?)</title *>", html)
                if title_match:
                    # Reply with the URL's title
                    title = title_match.group(1).strip()
                    title = HTMLParser.HTMLParser().unescape(title)
                    reply = irc.Irc_event(
                        "PRIVMSG", channel, "[%s] - %s" % (title, url))
                    server.send_event(reply)

            # The opening of URLs might fail
            except IOError:
                reply = irc.Irc_event(
                    "PRIVMSG", channel, "Failed to open url: %s" % url)
                server.send_event(reply)

plugin_manager.register_event_handler("PRIVMSG", on_privmsg)
