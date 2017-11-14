from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock

import socket
import select
import sys
import uuid


class Content(Widget):
  def __init__(self,*args,**kwargs):
    super(Content,self).__init__(*args,**kwargs)

    self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.client.settimeout(2)

    self.uuid = uuid.uuid1()
    self.sent_id = False

    try:
      ip = sys.argv[1].split(':')[0]
      port = int(sys.argv[1].split(':')[1])
    except ValueError:
      print('`port` Must be an integer')
      sys.exit(0)
    except IndexError:
      print('Please use `python3 main.py ip:port`')
      sys.exit(0)

    try:
      self.client.connect((ip,port))

    except:
      print('Couldn\'t establish connection to {}:{}'.format(ip,port))
      sys.exit(0)

    Clock.schedule_interval(self.get_network, 1.0/32)

  def get_network(self,t):

    readable, writable, exception = select.select([self.client], [], [], 0)

    if self.client in readable:
      data = self.client.recv(4096)
      if not data:
        print('Connection terminated')
        sys.exit(0)


      data.decode()

    if not self.sent_id:
      self.client.send('C!{}'.format(self.uuid).encode())
      self.sent_id = True

class Main(App):
  def build(self):
    return Content()

Main().run()
