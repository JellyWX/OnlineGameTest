import select
import socket
import sys
import time
import json

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

server_addr = ('localhost', 46643)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_addr)


socks = [server]

players = {}

def main():
  i = 0

  while socks:
    time.sleep(1.0/64)

    readable, writable, exception = select.select(socks, [], [], 0)

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
            players[plaintext[2:]] = {'user' : str(i)}
            i += 1
            print('received player id {}'.format(plaintext))
            s.send(''.join(json.dumps(d) for d in players.values() if d['user'] != str(i - 1)).encode()) # this line sends all the current player data to the user on connect

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

            broadcast(s, json.dumps(players[uid]).encode())

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


def broadcast(sock, message):
  for s in socks:
    if s not in [sock, server]:
      try:
        s.send(message)
      except:
        s.close()
        if s in socks:
          socks.remove(s)


main()
