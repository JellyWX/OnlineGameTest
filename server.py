import select
import socket
import sys
import time
import json

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

server_addr = ('localhost',46643)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_addr)

server.listen(12)

socks = [server]

players = {}

def main():
  i = 0

  while socks:
    time.sleep(1.0/64)

    readable, writable, exception = select.select(socks,[],[],0)

    for s in readable:

      if s is server:
        sock, addr = server.accept()
        socks.append(sock)
        print('{} connected to server'.format(addr))

      else:

        try:
          data = s.recv(4096)
        except ConnectionResetError:
          print('{} killed the connection'.format('nicknames[s]'))
          if s in socks:
            socks.remove(s)
          s.close()
          continue

        if data:
          plaintext = data.decode()
          if plaintext.startswith('C!'):
            if plaintext[2:] in players.keys():
              if s in socks:
                socks.remove(s)
              s.close()
            players[plaintext[2:]] = {'user' : i}
            i += 1
            print('received player id {}'.format(plaintext))

          else:
            try:
              d = json.loads(plaintext)
              uid = d.pop('id')
              players[uid].update(d)
            except json.decoder.JSONDecodeError:
              if s in socks:
                socks.remove(s)
              s.close()
              print('failed to gain data from client (json decode failed)')

            broadcast(players[uid])

        else:
          print('{} killed the connection'.format(s.getpeername()))
          if s in socks:
            socks.remove(s)
          s.close()

    for s in exception:
      print('{} killed the connection (exception detected)'.format(s.getpeername()))
      if s in socks:
        socks.remove(s)
      s.close()


def broadcast(message):
  for s in socks:
    if s != server:
      try:
        s.send(message)
      except:
        s.close()
        if s in socks:
          socks.remove(s)


main()
