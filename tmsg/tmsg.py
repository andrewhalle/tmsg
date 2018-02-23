import sys
import os
import curses
import time
import threading
import logging
from getpass import getpass
from fbchat import Client
from fbchat.models import *

class Tmsg:
    def __init__(self, client):
        self.client = client
        self.stdscr = None
        self.threads = []
        self.messages = {}
        self.thread_unread = []
        self.threads_lock = threading.Lock()
        self.keep_fetching = True
        self.fetch()
        self.active_thread_uid = self.threads[0].uid
        self.thread_display_limit = 4
        self.name_display_limit = 20
        self.typing = False
        self.message_buffer = ""
        return

    def set_stdscr(self, stdscr):
        self.stdscr = stdscr

    def main(self):
        curses.curs_set(False)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
        self.stdscr.clear()
        fetcher = threading.Thread(target=self.fetch_infinite)
        fetcher.start()
        while True:
            self.refresh()
            cmd = self.stdscr.getkey()
            if cmd in ["1", "2", "3", "4"]:
                self.set_active_thread(int(cmd) - 1)
            elif cmd == "q":
                self.keep_fetching = False
                fetcher.join()
                self.client.logout()
                break
            elif cmd == "s":
                self.type_message()
                self.send_buffer()

    def fetch(self):
        threads_temp = self.client.fetchThreadList()
        messages_temp = {}
        thread_unread_temp = []
        for thread in threads_temp:
            messages_temp[thread] = self.client.fetchThreadMessages(thread.uid)
            thread_unread_temp.append(not messages_temp[thread][0].is_read)
        self.threads_lock.acquire()
        self.threads = threads_temp
        self.messages = messages_temp
        self.thread_unread = thread_unread_temp
        self.threads_lock.release()

    def fetch_infinite(self):
        while self.keep_fetching:
            self.fetch()
            self.refresh()
            time.sleep(0.1)

    def refresh(self):
        self.threads_lock.acquire()
        self.stdscr.clear()
        curses.curs_set(False)
        height, width = self.stdscr.getmaxyx()
        for row in range(height):
            self.stdscr.addstr(row, width // 4, "|")
        for col in range(width // 4):
            for i in range(4):
                row = ((i + 1) * 5) - 1
                self.stdscr.addstr(row, col, "_")
        for col in range((width // 4) + 1, width):
            self.stdscr.addstr(height - 3, col, "_")

        for i in range(self.thread_display_limit):
            row = (i * 5) + 2
            if len(self.threads[i].name.strip()) > self.name_display_limit:
                name_to_display = self.threads[i].name[0:self.name_display_limit].strip() + "..."
            else:
                name_to_display = self.threads[i].name 
            self.stdscr.addstr(row, 4, name_to_display)
            if self.thread_unread[i]:
                self.stdscr.addstr(row, 2, " ", curses.color_pair(2))

        for i in range(5):
            active_thread_index = next(i for i, t in enumerate(self.threads) if t.uid == self.active_thread_uid)
            row = (active_thread_index * 5) + i
            col = (width // 4) - 1
            self.stdscr.addstr(row, col, " ", curses.color_pair(1))

        max_messages = (height // 3) - 1
        max_message_width = (3 * width // 4) // 2
        messages = self.messages[next(t for t in self.threads if t.uid == self.active_thread_uid)]
        for i in range(min(len(messages), max_messages)):
            message = messages[i]
            row = height - ((i * 3) + 5)
            if message.author == self.client.uid:
                col = (3 * width // 4) // 2 + (width // 4)
            else:
                col = (width // 4) + 1
            remaining_text = message.text
            curr = 0
            while remaining_text != "":
                self.stdscr.addstr(row, col, remaining_text[0:max_message_width - 1])
                remaining_text = remaining_text[max_message_width:]
                curr += 1
                if curr == 2 and len(remaining_text) > max_message_width:
                    remaining_text = remaining_text[0:max_message_width-4] + "..."
                row += 1
                if message.author == self.client.uid:
                    col = (3 * width // 4) // 2 + (width // 4)
                else:
                    col = (width // 4) + 1

        if self.typing:
            row = height - 2
            col = (width // 4) + 1
            self.stdscr.addstr(row, col, self.message_buffer)
            curses.curs_set(True)

        self.stdscr.refresh()
        self.threads_lock.release()

    def set_active_thread(self, new_thread_index):
        self.threads_lock.acquire()
        new_thread = self.threads[new_thread_index].uid
        self.active_thread_uid = new_thread
        self.threads_lock.release()
        self.refresh()

    def type_message(self):
        self.typing = True
        next_char = self.stdscr.getkey()
        while next_char != "\n":
            self.message_buffer += next_char
            next_char = self.stdscr.getkey()
            self.refresh()
        self.typing = False

    def send_buffer(self):
        thread = next(t for t in self.threads if t.uid == self.active_thread_uid)
        self.client.send(Message(text=self.message_buffer), thread_id=self.active_thread_uid, thread_type=thread.type)
        self.message_buffer = ""
        self.refresh()

# Console entry point `tmsg`
def start_cli():
    email = input("Email: ")
    password = getpass()
    print("Attempting login of %s" % email)
    client = Client(email, password, logging_level=logging.CRITICAL)
    print("Login successful!")
    print("Setting up...")
    app = Tmsg(client)

    def curses_main(stdscr):
        app.set_stdscr(stdscr)
        app.main()

    curses.wrapper(curses_main)

