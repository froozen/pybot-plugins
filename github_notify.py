#!/usr/bin/env python2

from pybot import data_container, plugin_manager, irc, shared_data
from time import sleep
import json
import httplib


def map(key, fun):
    """Apply a function to every element of a list retrieved from a Data_structure."""

    def map_f(data):
        result = []
        for sub in data.get(key):
            sub_data = data_container.Data_container(sub)
            result.append(fun(sub_data))
        return "\n".join(result)
    return map_f


def multiline(*funs):
    """Join the output of multiple functions with '\n'."""
    def multiline_fun(data):
        result = []
        for fun in funs:
            result.append(fun(data))
        return "\n".join(result)
    return multiline_fun


def cond(*conds):
    """Iterate through a list of tuples of conditions and functions.
       If a condition holds, execute the function associated with it."""
    def cond_fun(data):
        for cond, then in conds:
            if cond(data):
                return then(data)
    return cond_fun


def when(cond_, fun):
    """Execute the supplied function, if the condition holds, return a const("") otherwise."""
    return cond(
            (cond_, fun),
            otherwise(const(""))
            )


def elem(key, vals):
    """Check wether a value in a Data_structure is an element of a list."""

    return lambda data: data.get(key) in vals


def eq(key, val):
    """Compare the value in a Data_structure with a value."""

    return elem(key, [val])


def notf(fun):
    """Not the result of a function."""

    return lambda data: not fun(data)


def const(val):
    """Return a function returning a constant value."""

    return lambda _: val


def otherwise(fun):
    """The default case for cond."""

    return (const(True), fun)


def fmt_dt(fmt, *extractors):
    """Format a message, replacing the placeholders with the results of functions."""
    def format_fun(data):
        args = []
        for extractor in extractors:
            args.append(extractor(data))
        return fmt % tuple(args)
    return format_fun


def msg(fmt, *extractors):
    """Format a message, starting with the actors login."""

    return fmt_dt("%%s %s" % fmt, retrieve("actor.login"), *extractors)


def retrieve(identifier):
    """Retrieve something from the data."""

    return lambda data: "%s" % data.get(identifier)


def limit_size(n, fun):
    """Limit the length of the result of a function."""

    return lambda data: fun(data)[:n]


def limit_lines(n, fun):
    """Limit the linecount of the result of a function."""

    return lambda data: "\n".join(fun(data).split("\n")[:n])


# A dispatch table, containing functions that turn github updates into nice
# messages, created by chaining higher order functions
printers = {
        "CommitCommentEvent":
        multiline(
            msg("commented on commit %s of %s",
                limit_size(6, retrieve("payload.comment.commit_id")),
                retrieve("repo.name")
                ),
            retrieve("payload.comment.html_url")
            ),
        "CreateEvent":
        multiline(
            msg("created %s %s: %s",
                cond(
                    (notf(eq("payload.ref_type", "repository")),
                        fmt_dt("%s %s at",
                               retrieve("payload.ref_type"),
                               retrieve("payload.ref")
                               )
                     ),
                    otherwise(const("repository"))
                    ),
                retrieve("repo.name"),
                retrieve("payload.description")
                )
            ),
        "DeleteEvent":
        msg("deleted %s %s from %s",
            retrieve("payload.ref_type"),
            retrieve("payload.ref"),
            retrieve("repo.name")
            ),
        "FollowEvent":
        msg("followed %s: %s",
            retrieve("payload.target.login"),
            retrieve("payload.target.html_url")
            ),
        "ForkEvent":
        multiline(
            msg("forked %s to %s",
                retrieve("repo.name"),
                retrieve("payload.forkee.full_name")
                ),
            retrieve("payload.repository.html_url")
            ),
        "GollumEvent":
        msg("updated the wiki of %s",
            retrieve("repo.name")
            ),
        "IssueCommentEvent":
        multiline(
            msg("commented on issue \"%s\" at %s",
                retrieve("payload.issue.title"),
                retrieve("repo.name")
                ),
            retrieve("payload.comment.html_url")
            ),
        "IssuesEvent":
        multiline(
            when(elem("payload.action", ["assigned", "unassigned", "opened", "closed", "reopened"]),
                 msg("%s %sissue \"%s\" at %s",
                     retrieve("payload.action"),
                     when(elem("payload.action", ["assigned", "unassigned"]),
                          fmt_dt("%s %s ",
                                 cond(
                                     (eq("actor.login", "payload.issue.assignee"),
                                         const("themselves")),
                                     otherwise(retrieve("actor.login"))
                                     ),
                                 cond(
                                     (eq("payload.action", "assigned"), const("to")),
                                     otherwise(const("from"))
                                     )
                                 )
                          ),
                     retrieve("payload.issue.title"),
                     retrieve("repo.name")
                     )
                 ),
            retrieve("payload.issue.html_url")
            ),
        "MemberEvent":
        msg("added %s to %s",
            retrieve("payload.member.login"),
            retrieve("repo.name")
            ),
        "PublicEvent":
        multiline(
            msg("opensourced %s. A time to celebrate: https://www.youtube.com/watch?v=zfAFUd1ZwB8",
                retrieve("repo.name")),
            retrieve("payload.repository.html_url")
            ),
        "PullRequestEvent":
        multiline(
            when(elem("payload.action", ["opened", "closed", "reopened"]),
                 msg("%s pull request \"%s\" at %s",
                     retrieve("payload.action"),
                     retrieve("payload.pull_request.title"),
                     retrieve("repo.name")
                     )
                 ),
            retrieve("payload.pull_request.html_url")
            ),
        "PullRequestReviewCommentEvent":
        multiline(
            msg("commented on pull request \"%s\" at %s",
                retrieve("payload.pull_request.title"),
                retrieve("repo.name")
                ),
            retrieve("payload.comment.html_url")
            ),
        "PushEvent":
        multiline(
            msg("pushed %s to %s",
                cond((eq("payload.size", 1), const("a commit")),
                     otherwise(fmt_dt("%s commits",
                               retrieve("payload.size")))
                     ),
                retrieve("repo.name")
                ),
            map("payload.commits",
                fmt_dt("%s: %s",
                       limit_size(6, retrieve("sha")),
                       limit_lines(1, retrieve("message"))
                       )
                )
            ),
        "RealaeseEvent":
        msg("publised realase %s of %s",
            retrieve("payload.realease.tag_name"),
            retrieve("repo.name")
            ),
        "RepositoryEvent":
        multiline(
            msg("created repository %s",
                retrieve("repo.name")
                ),
            fmt_dt("Description: %s",
                   retrieve("payload.description")
                   ),
            retrieve("payload.html_url")
            ),
        "TeamAddEvent":
        msg("was added to team %s",
            retrieve("payload.team.name")
            ),
        "WatchEvent":
        multiline(
            msg("starred %s",
                retrieve("repo.name")
                ),
            retrieve("payload.html_url")
            )
        }


def query_thread(server, channel):
    """A thread regularily querying github for the messages to send to a channel."""

    delay = 60
    while True:
        targets = server.persistent_data.get("gh.%s.targets" % channel)

        for user, user_data in targets.iteritems():
            if user_data:
                etag = user_data["etag"]
                last_id = user_data["last_id"]

                # Query github
                data, n_etag, n_delay, changed, id = query_data(user, etag, last_id)

                # Update the data with the results
                delay = n_delay
                server.persistent_data.set("gh.%s.targets.%s" % (channel, user), {
                    "etag": n_etag,
                    "last_id": id
                    })

                # Send messages, if changed
                if changed:
                    for message in generate_messages(data):
                        server.send_event(irc.Irc_event("PRIVMSG", channel, message))

        sleep(delay)


def query_data(user, etag, last_id):
    """Query the github API for a users data"""

    # Assemble the headers
    headers = {"User-Agent": "pybot"}
    if etag:
        headers["If-None-Match"] = etag

    # Connect and send the request
    http_connection = httplib.HTTPSConnection("api.github.com")
    http_connection.connect()
    http_connection.request("GET",
                            "/users/%s/events" % user,
                            headers=headers)

    # Extract all the relevant data
    resp = http_connection.getresponse()
    response_text = resp.read()
    n_etag = resp.getheader("ETag")
    n_delay = float(resp.getheader("X-Poll-Interval", 60))
    changed = resp.status == 200

    # Close the connection AFTER extracting the data
    http_connection.close()

    if changed:
        # Parse the data and extract the new updates
        data = json.loads(response_text)
        data = list(reversed(filter(lambda update: update["id"] > last_id, data)))
        return data, n_etag, n_delay, changed, data[-1]["id"]
    else:
        return None, n_etag, n_delay, changed, last_id


def generate_messages(updates):
    """Given a list of updates, generate a list of lines to be sent via IRC."""
    result = []

    for update in updates:
        # Try to execute the corresponding printer and extend the result list
        # with it's output
        type = update["type"]
        if type in printers:
            update_data = data_container.Data_container(update)
            lines = printers[type](update_data).split("\n")
            result.extend(lines)

    # Don't send empty lines
    return filter(lambda line: not line == "", result)


@plugin_manager.event_handler("JOIN")
def on_join(event, server):
    channel = event.args[0]
    running = server.shared_data.get("gh.%s.running" % channel)

    if not running:
        server.shared_data.set("gh.%s.running" % channel, True)
        plugin_manager._dispatch(query_thread(server, channel))


@plugin_manager.command("gh_add")
def gh_add_cmd(command, server):
    """Execute the )gh_add command."""

    channel = command.event.args[0]

    if len(command.args) == 1:
        user = command.args[0]

        # Query for the first time
        _, etag, _, _, last_id = query_data(user, None, "0")

        # Already set etag and last_id, so the channel isn't spammend with 30
        # updates on the next query
        server.persistent_data.set("gh.%s.targets.%s" % (channel, user), {
            "etag": etag,
            "last_id": last_id
            })
        server.send_event(irc.Irc_event("PRIVMSG", channel, "Started watching %s" % user))

    else:
        server.send_event(irc.Irc_event("PRIVMSG", channel, "Usage: )gh_add <user> to start watching a user on github"))


@plugin_manager.command("gh_del")
def gh_del_cmd(command, server):
    """Execute the )gh_del command."""

    channel = command.event.args[0]

    if len(command.args) == 1:
        user = command.args[0]
        server.persistent_data.set("gh.%s.targets.%s" % (channel, user), None)
        server.send_event(irc.Irc_event("PRIVMSG", channel, "Stopped watching %s" % user))

    else:
        server.send_event(irc.Irc_event("PRIVMSG", channel, "Usage: )gh_del <user> to stop watching a user on github"))


shared_data.set("help.gh_add", "Start watching a user on github")
shared_data.set("help.gh_del", "Stop watching a user on github")
