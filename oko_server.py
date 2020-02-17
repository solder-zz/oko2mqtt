#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import paho.mqtt.publish as publish
import json
import configparser
from _thread import *
import threading

config = configparser.ConfigParser()
config.read("setting.ini")

imei = config["device"]["imei"]

mqtt_login = config["mqtt"]["login"]
mqtt_pass = config["mqtt"]["pass"]
mqtt_host = config["mqtt"]["host"]

def server():
  print ('Starting server ...')
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.bind((config["socket"]["host"], int(config["socket"]["port"])))
  sock.listen(5)
  while True:
    conn, addr = sock.accept()
    t = threading.Thread(target=handle_client, args=(conn, addr))
    t.daemon = True
    t.start()

events = {
  0: 'восстановление входа - 1',
  1: 'нарушение входа - 1',
  2: 'восстановление входа - 2',
  3: 'нарушение входа - 2',
  16: 'включение выхода - 2',
  17: 'отключение выхода - 2',
  23: '12В АКБ заряженый',
  25: 'начало снятия с охраны',
  32: 'постановка в охрану',
  33: 'снятие с охраны',
  34: 'внешнее питание 220 включилось',
  35: 'внешнее питание 220 отключилось',
  36: 'разряд 12В АКБ',
  40: 'включение выхода - 1',
  41: 'отключение выхода - 1',
  62: 'служебное Android',
  63: 'служебное Android',
  240: 'инициализация GSM-модуля',
  249: 'переодические данные',
  250: 'перезапуск устройства',
  254: 'запрос на передачу данных на сервер',
  255: 'включение устройства'
}

states = {
  6: 'состояние охраны',
  5: 'состояние выхода - 2',
  4: 'состояние выхода - 1',
  3: 'состояние 12В АКБ',
  2: 'состояние внешнего питания',
  1: 'состояние входа - 2',
  0: 'состояние входа - 1'
}

def handle_client(conn, addr):
  print ('Connected from:', addr)
  while True:
    data = conn.recv(1024).decode()
    if not data:
      break
    data = data.replace("{", "").replace("}", "")
    mass = data.split(',')
    if mass[0] == imei:
      event = int(mass[1], 16)
      state = int(mass[2], 16)
      state = bin(state).replace("0b", "")
      statemass = list(state)
      statemass.reverse()
      napr = int(mass[3], 16)
      napr = 3.28 * 10 * napr / 4095
      napr = round(napr, 1)
      temp = int(mass[7], 16)
      print (events[event], statemass[0], states[0], temp, napr)
      if event != 62 and event != 63:
        event_msg = json.dumps({"id": event, "name": events[event]})
        msg = [{'topic': "oko/messages/event", 'payload': event_msg},
               {'topic': "oko/messages/state/0/id", 'payload': statemass[0]},
               {'topic': "oko/messages/state/0/name", 'payload': states[0]},
               {'topic': "oko/messages/state/1/id", 'payload': statemass[1]},
               {'topic': "oko/messages/state/1/name", 'payload': states[1]},
               {'topic': "oko/messages/state/2/id", 'payload': statemass[2]},
               {'topic': "oko/messages/state/2/name", 'payload': states[2]},
               {'topic': "oko/messages/state/3/id", 'payload': statemass[3]},
               {'topic': "oko/messages/state/3/name", 'payload': states[3]},
               {'topic': "oko/messages/state/4/id", 'payload': statemass[4]},
               {'topic': "oko/messages/state/4/name", 'payload': states[4]},
               {'topic': "oko/messages/state/5/id", 'payload': statemass[5]},
               {'topic': "oko/messages/state/5/name", 'payload': states[5]},
               {'topic': "oko/messages/state/6/id", 'payload': statemass[6]},
               {'topic': "oko/messages/state/6/name", 'payload': states[6]},
               {'topic': "oko/messages/temperature", 'payload': temp},
               {'topic': "oko/messages/volt", 'payload': napr}]
        publish.multiple(msg, hostname=mqtt_host, auth={'username':mqtt_login, 'password':mqtt_pass})
  conn.shutdown(socket.SHUT_RDWR)
  conn.close()
  print ('Conection close')

def main():
  server()

if __name__ == '__main__':
  main()
