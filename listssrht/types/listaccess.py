from enum import IntFlag

class ListAccess(IntFlag):
    """
    Permissions granted to users of a list.
    """
    none = 0

    browse = 1
    """Permission to subscribe and browse the archives"""
    reply = 2
    """Permission to reply to threads submitted by an authorized user."""
    post = 4
    """Permission to submit new threads."""
    all = browse | reply | post
