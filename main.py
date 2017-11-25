from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty, ReferenceListProperty
from kivy.uix.widget import Widget
from kivy.core.window import Window

import socket
import select
import sys
import uuid
import json
import random


class Player(Widget):

  user = None
  p_color = ListProperty([1, 0, 0])

  def __init__(self,*args,**kwargs):
    super(Player,self).__init__(*args,**kwargs)


class Content(Widget):
  user = ObjectProperty(None)
  user2 = ObjectProperty(None)
  user3 = ObjectProperty(None)
  user4 = ObjectProperty(None)
  user5 = ObjectProperty(None)

  player_objects = ReferenceListProperty(user2, user3, user4, user5)

  keysdown = set([])

  def __init__(self,*args,**kwargs):
    super(Content,self).__init__(*args,**kwargs)

    self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.client.settimeout(2)

    self.uuid = uuid.uuid1()
    self.sent_id = False

    self.d = {}

    self.players = {}

    self.user.p_color = [random.random(), random.random(), random.random()]

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

    Clock.schedule_interval(self.loop, 1.0/32)

  def keyDown(self,window,key,*largs):
    self.keysdown.add(key)

  def keyUp(self,window,key,*largs):
    self.keysdown.remove(key)

  def catch_mouse(self,etype,pos):
    self.mouse_pos = pos

  def loop(self,t):
    self.get_network()

    all_users = [u.user for u in self.player_objects]

    for player, data in self.players.items():
      if player not in all_users:
        for user in self.player_objects:
          if user.user == None:
            user.user = player
            break

    for user in self.player_objects:
      if user.user != None:
        user.x = self.players[user.user]['x']
        user.y = self.players[user.user]['y']
        user.p_color = self.players[user.user]['p_color']

    if 119 in self.keysdown:
      self.user.y += 2
    if 115 in self.keysdown:
      self.user.y -= 2
    if 100 in self.keysdown:
      self.user.x += 2
    if 97 in self.keysdown:
      self.user.x -= 2

  def get_network(self):

    if not self.sent_id:
      self.client.send('C!{}'.format(self.uuid).encode())
      self.sent_id = True
      return

    self.ex_d = self.d

    self.d = {
      'id' : str(self.uuid),
      'x' : self.user.x,
      'y' : self.user.y,
      'p_color' : self.user.p_color
    }

    if self.d != self.ex_d:
      self.client.send(json.dumps(self.d).encode())

    readable, writable, exception = select.select([self.client], [], [], 0)

    if self.client in readable:
      data = self.client.recv(4096)
      if not data:
        print('Connection terminated')
        sys.exit(0)

      str_d = data.decode()

      sep_d = str_d.split('{')[1]

      for data in sep_d:
        dict_d = json.loads('{' + sep_d)

        self.players[dict_d['user']] = dict_d


class Main(App):
  def on_start(self):
    Window.bind(on_key_down=self.content.keyDown,on_key_up=self.content.keyUp,mouse_pos=self.content.catch_mouse)

  def build(self):
    self.content = Content()
    return self.content


Main().run()
