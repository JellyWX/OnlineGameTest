from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, ReferenceListProperty
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.vector import Vector

import socket
import select
import sys
import uuid
import random
import time
import math
import umsgpack


class Player(Widget):

  user = None
  p_color = ListProperty([1, 0, 0])
  d_color = ListProperty([1, 0, 0])

  vel_x = NumericProperty(0)
  vel_y = NumericProperty(0)
  vel = ReferenceListProperty(vel_x, vel_y)

  rotation = NumericProperty(0)

  firing = False
  weapon = None

  def __init__(self,*args,**kwargs):
    super(Player,self).__init__(*args,**kwargs)

  def move(self):
    self.pos = Vector(self.vel).normalize() * 3 + self.pos


class Content(Widget):

  user = ObjectProperty(None)

  player_objects = []

  keysdown = set([])

  mouse_pos = [0, 0]
  mouse_pressed = False

  def __init__(self,*args,**kwargs):
    super(Content,self).__init__(*args,**kwargs)

    self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.client.settimeout(2)

    self.uuid = uuid.uuid1().hex

    self.d = {}
    self.time_since_token = 0

    self.players = {}

    li = [round(random.random(),3), round(random.random(),3), round(random.random(),3)]

    self.user.p_color = list(li)
    self.user.d_color = list(li)

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

  def on_touch_down(self,e):
    self.mouse_pressed = True

  def on_touch_up(self,e):
    self.mouse_pressed = False

  def loop(self,t):
    self.get_network()

    all_users = [u.user for u in self.player_objects]

    for player, data in self.players.items():
      if player not in all_users:
        new_user = Player()
        new_user.user = player
        new_user.width = 25
        new_user.height = 25
        self.player_objects.append(new_user)
        self.add_widget(new_user)

    for user in self.player_objects:
      if user.user != None:
        user.x = self.players[user.user]['x']
        user.y = self.players[user.user]['y']
        user.p_color = self.players[user.user]['col']
        user.rotation = self.players[user.user]['rot'] * 4 # rotation is sent as a smaller number to save like 7 bits smh
        user.firing = self.players[user.user]['fire']

        if user.firing:
          user.d_color = [1, 1, 0]
        else:
          user.d_color = user.p_color

        if self.players[user.user]['status'] != 'OK':
          self.remove_widget(user)
          self.player_objects.remove(user)
          del self.players[user.user]

    self.user.vel_x = 0
    self.user.vel_y = 0

    if 119 in self.keysdown:
      self.user.vel_y = 1
    if 115 in self.keysdown:
      self.user.vel_y = -1
    if 100 in self.keysdown:
      self.user.vel_x = 1
    if 97 in self.keysdown:
      self.user.vel_x = -1

    try:
      self.user.rotation = round(math.degrees(math.atan2(self.mouse_pos[0] - self.user.center_x, self.mouse_pos[1] - self.user.center_y)))
    except ZeroDivisionError:
      pass

    self.user.move()
    self.user.firing = self.mouse_pressed

    if self.user.firing:
      self.user.d_color = [1, 1, 0]
    else:
      self.user.d_color = self.user.p_color

  def get_network(self):

    if time.time() - self.time_since_token > 8:
      self.client.send('C{}'.format(self.uuid).encode())
      self.time_since_token = time.time()

    self.ex_d = self.d

    self.d = {
      'x' : self.user.x,
      'y' : self.user.y,
      'col' : self.user.p_color,
      'rot' : int(self.user.rotation / 4),
      'fire' : self.user.firing
    }

    self.differences = {x: self.d[x] for x in self.d.keys() if x not in self.ex_d.keys() or self.d[x] != self.ex_d[x]}

    if self.differences:
      self.differences['id'] = self.uuid
      self.differences['status'] = 'OK'
      self.client.send(umsgpack.packb(self.differences))

    readable, writable, exception = select.select([self.client], [], [], 0)

    if self.client in readable:
      data_b = self.client.recv(4096)
      d = umsgpack.unpackb(data_b)

      if type(d) == dict:

        if d['user'] == 'N':
          self.user.x = data['x']
          self.user.y = data['y']

        else:
          self.players[d['user']] = d

      elif type(d) == list:
        for data in d:
          self.players[data['user']] = data

      print(self.players)

  def disconnect_signal(self):
    self.client.send(umsgpack.packb({'id' : self.uuid, 'status' : 'discon'}))
    sys.exit(0)


class Main(App):
  def on_start(self):
    Window.bind(on_key_down=self.content.keyDown, on_key_up=self.content.keyUp, mouse_pos=self.content.catch_mouse)

  def build(self):
    self.content = Content()
    return self.content

  def on_stop(self):
    self.content.disconnect_signal()


m = Main()
try:
  m.run()
except KeyboardInterrupt:
  m.content.disconnect_signal()
# program ends naturally

m.content.disconnect_signal()
