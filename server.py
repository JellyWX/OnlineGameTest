import select
import socket
import sys
import time
import json

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setblocking(0)

server_addr = ('localhost', 46643)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_addr)

players = {}
address_book = []

def main():
  i = 0

  while True:
    time.sleep(1.0/64)

    readable, writable, exception = select.select([server], [], [], 0)

    for s in readable:

      data, address = s.recvfrom(4096)

      if data:
        plaintext = data.decode()
        if plaintext.startswith('C!') and address not in address_book:
          if plaintext[2:] in players.keys():
            continue
          players[plaintext[2:]] = {'user' : str(i)}
          i += 1
          print('received player id {}'.format(plaintext))
          server.sendto(''.join(json.dumps(d) for d in players.values() if d['user'] != str(i - 1)).encode(), address) # this line sends all the current player data to the user on connect
          address_book.append(address)

        else:
          try:
            d = json.loads(plaintext)
            uid = d.pop('id')
            players[uid].update(d)
          except json.decoder.JSONDecodeError:
            address_book.remove(address)
            print('failed to gain data from client (json decode failed)')

          broadcast(address, json.dumps(players[uid]).encode())


def broadcast(address, message):
  for addr in address_book:
    if addr != address:
      try:
        server.sendto(message, addr)
      except:
        pass

main()
