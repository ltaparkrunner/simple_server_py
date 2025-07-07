#!/usr/bin/env python3

# Simple modbusTCP server.
# It reads a string from a test file once a second, parses it and sets the result as a sensors' values.
# On a client's modbus TCP respond the server transmits the last read values.

# d: && cd D:\Alex_m\Python\simple_server\ && D:\Alex_m\Python\python3\python.exe simple_server.py
# cd wrk/myproj/python/simple_server/simple_server && python3 simple_server.py

import sys
#sys.path.append('D:\Alex_m\Python\python3\python38')
import curses

import time
import datetime
import threading

unicurses = curses
# def reading_timer_start(win, interval, callback, fn, stop_event):
#     win.addstr(15, 0, "true_cycle:" + str(nc))
#     win.refresh()
#     try:
#         win.addstr(15, 0, "true_cycle:" + str(nc))
#         win.refresh()
#         nc = 0
#         next_execution_time = time.time() + interval
#         print("PreciseTimer try start")
#         with open(fn, "r") as fh:
#             while not se.is_set():

#                 now = time.time()
#                 if now >= next_execution_time:
#                     nc = nc + 1
#                     win.addstr(15, 0, "true_cycle:" + str(nc))
#                     win.refresh()
#                     callback(win, nc, fh)
#                     next_execution_time += interval
#                 else:
#                     time.sleep(max(0, next_execution_time - now))
#     except KeyboardInterrupt:
#         pass
			
class PreciseTimer:
    def __init__(self, win, interval, callback, fn, stop_event):
        self.interval = interval
        self.callback = callback
        self.next_execution_time = time.time() #+ interval
        self.win = win
        self.running = True
        self.nc = 0
        self.fn = fn
        self.se = stop_event
        self.probe = ("0", "0", "0", "0", "0", "0", "0", "0")

    def start(self):
        try:
            with open(self.fn, "r") as fh:
                #while not self.se.is_set():
                while True:
                    now = time.time()
                    if now >= self.next_execution_time:
                        self.nc = self.nc + 1
                        self.win.addstr(12, 0, "line:" + str(self.nc))
                        self.win.refresh()
                        self.probe = self.callback(self.win, self.nc, fh)
                        self.next_execution_time += self.interval
                    else:
                        time.sleep(max(0, self.next_execution_time - now))
        except KeyboardInterrupt:
            self.stop()
			
    def stop(self):
        self.running = False

    def read_probe(self):
        return self.probe

def task(win, nc, fh):
    line = fh.readline()
    str_list = line.split(';')
    
    now = datetime.datetime.now()
    if now.month < 10: sm = "0" + str(now.month)
    else: sm = str(now.mounth)
    if now.day < 10: sd = "0" + str(now.day)
    else: sm = str(now.day)
    win.addstr(2, 0, "Date, time: " + str(now.year ) + "-" + sm + "-" + sd  
        + "   " + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second))
    for i in range(1, 9, 1):
        win.addstr(i + 2, 0, "Probe " + str(i) + " :"+ str_list[i] + "   ")
    win.refresh()
    return str_list[1:9]

import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 502        # Port to listen on (non-privileged ports are > 1023)

def get_b(word):
    try:
        word = word.replace(",", ".")
        num = int(float(word) * 2)

        return num.to_bytes(2, byteorder='big')
    except ValueError:
        print(f"Error: '{word}' cannot be converted to an integer.")

def read_probe():
    return ("510,5", "513,5", "411", "332,5", "634,5", "432", "512", "611,5")

def send_mklp_data_time(rbuf, conn, r_p):
    #Modbus TCP Slave :0001 0000 0009 11 03 06 022B 0064 007F
    wbuf = bytearray(42)
    for k in range(0, 8, 1): wbuf[k] = rbuf[k]
    wbuf[5] = 2 * rbuf[11] + 3
    wbuf[8] = 2 * rbuf[11]
    wdata_len = wbuf[8] + 9

#    for (uint8_t k = 0;k < rbuf[11];k++) {
    cur = r_p()
    for k in range(0, 8, 1):
        temp = get_b(cur[k])
        wbuf[2 * k + 9] = temp[0]
        wbuf[2 * k + 10] = temp[1]
#        wbuf[2 * k + 9] = static_cast<int>(buf[k]) >> 8
#        wbuf[2 * k + 10] = static_cast<int>(buf[k]) & 0x00FF

    conn.sendall(wbuf)


def simple_tcp_server(stop_event, read_probe):
#def simple_tcp_server():
    # Create a socket object using IPv4 and TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
        # Bind the socket to the specified host and port
            s.bind((HOST, PORT))
        # Listen for incoming connections (allow up to 1 client in the queue)
            s.listen()
            #print(f"Server listening on {HOST}:{PORT}")
            
            s.settimeout(1.0)
        # Accept a new connection
            while not stop_event.is_set():
                try: 
                    conn, addr = s.accept()

                    with conn:
                        #print(f"Connected by {addr}")

                        #while True:
                        while not stop_event.is_set():
                            # Receive data from the client, up to 1024 bytes
                            data = conn.recv(1024)
                            if not data:
                                break  # No more data, connection closed by client
                            if data[0] == 1 and data[1] == 1 and data[2] == 0 and data[3] == 0 and \
                            data[4] == 0 and data[5] == 6 and data[6] == 33 and data[7] == 3 and \
                            data[8] == 0 and data[9] == 0 and data[10] == 0 and data[11] == 16:
                                send_mklp_data_time(data, conn, read_probe)
                        #print(f"Connection with {addr} closed.")
                        return True
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            return False

if len(sys.argv) >= 2 and ("--help" in sys.argv[1] or "-h" in sys.argv[1] or "/?"  in sys.argv[1]):
    print("usage: simple_server.py [ip_addr [test_file.csv]]")
    sys.exit()
test_fn = "Test_1.csv"
if len(sys.argv) >= 3:
	test_fn = sys.argv[2]

try:
	with open(test_fn, "r") as fh:	
		fh.close()
except EnvironmentError as err:
	print(err)

ip_addr = "192.168.1.170"
if len(sys.argv) >= 2:
	ip_addr = sys.argv[1]

# import sys
#print("sys.path= ", sys.path)
 
# import csv
# import json
#try:
stdscr = curses.initscr()
curses.curs_set(0)  # Hide cursor

height = 3
width = 10
LINES, COLS = stdscr.getmaxyx()
starty = int((LINES - height) / 2)
startx = int((COLS - width) / 2)
#stdscr.addstr("Simple server that reads data from file " + test_fn + " and transmit it via Ethernet")
#stdscr.refresh()
#time.sleep(2)

se = threading.Event()

timer_rf = PreciseTimer(stdscr, 1, task, test_fn, se)
thread1 = threading.Thread(target=simple_tcp_server, args=(se,timer_rf.read_probe))
thread1.start()

timer_rf.start()
#thread1 = threading.Thread(target=timer_rf.start, args=())
#thread1 = threading.Thread(target=reading_timer_start, args=(stdscr, 1, task, test_fn, se))

#print("Start tcp server")
#time.sleep(10)
#print("Start tcp server")
#cntn = simple_tcp_server()
se.set()
#timer_rf = PreciseTimer(stdscr, 1, task, test_fn)


#thread1.join()

#timer_rf.start()
curses.endwin()


