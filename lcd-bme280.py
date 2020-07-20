#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smbus
import datetime
import sys

from time import sleep
from time import strftime
from signal import signal,SIGTERM

#read data using BME280
from bme280_python3 import bme280

# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

def termed(signum, frame):
    LCD_BACKLIGHT = 0x00
    lcd_byte(0x01, LCD_CMD)
    sys.exit(0)

def main():

    # Initialise display
    lcd_init()

    while True:

      # get sensor values
      try:
        sensor = bme280()
      except OSError as e:
        print("error:", e.args)
        sleep(1)
        continue
      except Exception as e:
        print("error:", e.args)


      temperture = '{:-6.2f}\xdfC'.format(sensor.getTemperature())
      humidity   = '{:7.2f}%'.format(sensor.getHumidity())
      pressure   = '{:6.2f}hPa'.format(sensor.getPressure())

      local_time = datetime.datetime.now()
      nowtime = local_time.strftime(" %H:%M")

      # Display
      lcd_string(temperture + humidity, LCD_LINE_1)
      lcd_string(pressure + nowtime, LCD_LINE_2)

      sleep(3)

if __name__ == '__main__':
    try:
      signal(SIGTERM, termed)
      main()
    except KeyboardInterrupt:
      pass
    finally:
      LCD_BACKLIGHT = 0x00 # backlight off
      lcd_byte(0x01, LCD_CMD) #LCD Clear
