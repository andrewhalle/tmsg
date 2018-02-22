import os
import sys
import curses
import logging
from curses import wrapper
from fbchat import Client
from fbchat.models import *
from classes import Tmsg


def main(stdscr):
    client = login(stdscr)
    app = Tmsg(client, stdscr)
    app.main()

def login(stdscr):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    row = height // 2
    col = width // 2
    stdscr.addstr(row + 1, col, "Password: ")
    stdscr.addstr(row, col, "Email: ")
    stdscr.refresh()
    next_char = stdscr.getkey()
    email = ""
    while next_char != "\n":
        email += next_char
        stdscr.addstr(next_char)
        stdscr.refresh()
        next_char = stdscr.getkey()
    stdscr.move(row + 1, col + 10)
    stdscr.refresh()
    password = ""
    next_char = stdscr.getkey()
    while next_char != "\n":
        password += next_char
        stdscr.addstr("*")
        stdscr.refresh()
        next_char = stdscr.getkey()

    client = Client(email, password, logging_level=logging.CRITICAL)

    stdscr.clear()
    return client

wrapper(main)

