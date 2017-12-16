import select
import socket
import sys
import time
import math
import msgpack

TICKRATE = 64
ADDRESS = 'localhost'
PORT = 46643

for item in sys.argv:
  if item.startswith('tick='):
    TICKRATE = int(item.split('=')[1])
  elif item.startswith('port='):
    PORT = int(item.split('=')[1])
  elif item.startswith('host='):
    ADDRESS = item.split('=')[1]

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setblocking(0)

server_addr = (ADDRESS, PORT)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_addr)

players = {}
address_book = []
timeouts = {}


def main():
  i = 0

  while True:

    time.sleep(1.0/TICKRATE)
    queue_deletes = []

    readable, writable, exception = select.select([server], [], [], 0)

    for s in readable:

      data, address = s.recvfrom(4096)

      if data:
        try:
          plaintext = data.decode()
        except UnicodeDecodeError:
          plaintext = ''

        if plaintext.startswith('C'): # if a token has been sent through

          if plaintext[1:] in players.keys(): # if the token is already registered (the client is refreshing its presence)
            timeouts[plaintext[1:]] = [time.time(), address]

          elif address not in address_book: # if the token is new (new user connected)
            timeouts[plaintext[1:]] = [time.time(), address]

            players[plaintext[1:]] = {'user' : str(i), 'status' : 'OK'}
            i += 1
            print('received player id {}'.format(plaintext))
            server.sendto(msgpack.packb([d for d in players.values() if d['user'] != str(i - 1)]), address) # this line sends all the current player data to the user on connect
            address_book.append(address)

        else:
          try:
            d = msgpack.unpackb(data, encoding='utf8')
          except TypeError:
            address_book.remove(address)
            print('failed to gain data from client (msgpack decode failed)')
            continue

          uid = d.pop('id')

          if d['status'] == 'discon':
            address_book.remove(address)
            queue_deletes.append(uid)
            print('user disconnected')
          else:

            try:
              player_old = players[uid].copy() # depending on the position in the cycle that a user discons at, it can cause errors here.
            except KeyError:
              address_book.remove(address)
              queue_deletes.append(uid)

            players[uid].update(d)
            player_new = players[uid]

            player_old['user'] = 'N'

            try:
              if round(math.hypot(player_old['x'] - player_new['x'], player_old['y'] - player_new['y']), 4) > 3:
                print('illegal movement. disregarding instruction.')
                players[uid] = player_old
                server.sendto(msgpack.packb(player_old), address)
            except KeyError:
              pass

            broadcast(address, msgpack.packb(players[uid]))

    for user_id, refresh_time in timeouts.items():
      if time.time() - refresh_time[0] > 30:
        try:
          address_book.remove(refresh_time[1])
        except:
          pass

        queue_deletes.append(user_id)
        print('user disconnected (timeout)')

    if queue_deletes:
      for item in queue_deletes:
        del timeouts[item]

        players[item]['status'] = 'discon'

        broadcast(None,msgpack.packb(players[item]))
        del players[item]

def broadcast(address, message):
  for addr in address_book:
    if addr != address:
      server.sendto(message, addr)

main()
