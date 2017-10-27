#!/usr/bin/python
import socket
import sys
import telnetlib
import re
import time

import bottle
import os
from bottle import Bottle
from BottleServer import BottleServer

import wemoTelnet


rootApp = Bottle()

@rootApp.route('/')
def rootIndex():
    return 'ok'

@rootApp.route('/image')
def image():
    root = os.path.dirname(os.path.realpath(__file__))
    print("image requested")
    return bottle.static_file("lede-ramips-rt305x-f7c027-squashfs-sysupgrade.bin", root=root, download=True)


def getLocalIp(targetIp,targetPort):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.25)
    s.connect((targetIp, targetPort))
    ret = s.getsockname()[0]
    s.close()
    return ret

def isOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def tnExec(tn,cmd):
    tn.write(cmd+"\n")
    return tn.read_until("# ")

def tnRegex(tn,cmd,regex):
    t = tnExec(tn, cmd )
    m = re.search(regex , t , re.M)
    if (m):
        return m.group(1)
    return ""

def main():
    if len(sys.argv) < 2:
        print("usage: wemotool <target ip address>")
        exit(1)

    targetIp = sys.argv[1];
    targetPort = 49153

    sourceIp = getLocalIp(targetIp, targetPort);
    sourcePort = 8080

    server = BottleServer(rootApp, sourceIp, sourcePort)

    retry = True

    while retry:
        retry = False

        wemoTelnet.run(targetIp, server)

        print("telnet ready on " + targetIp + ":23")

        tn = telnetlib.Telnet(targetIp, 23, timeout=1)
        tn.read_until("# ")

        fwversion = tnRegex(tn,"cat /etc/ver.txt","^(WeMo.*)$")
        print("fw version: "+fwversion)

        bootstate = tnRegex(tn, "uboot_env getenv bootstate", "^getenv : bootstate with ([0-9]).*$")
        print("bootstate: " + bootstate)

        check_boot = tnRegex(tn, "uboot_env getenv check_boot", "^getenv : check_boot with ([0-9]).*$")
        print("check_boot: " + check_boot)

        if bootstate=="0" or bootstate == "1":
            print("bootstate is "+bootstate+", running from slot 1")
            print("changing boot slot and rebooting")

            tnExec(tn,"uboot_env setenv bootstate 2")
            tnExec(tn,"uboot_env setenv check_boot 0")
            tn.write("reboot\n")

            print("waiting for wemo to reboot")
            while isOpen(targetIp,targetPort):
                sys.stdout.write(".")
                time.sleep(0.5)

            print("booting up...")

            while not isOpen(targetIp,targetPort):
                sys.stdout.write(".")
                time.sleep(0.5)

            print("wemo rebooted, starting over...")
            retry = True
        elif bootstate=="2" or bootstate == "3":
            print("bootstate is " + bootstate + ", running from slot 2")
            print("preparing firmware update")

            print tnExec(tn,"wget -O /tmp/image http://"+server.host+":"+str(server.port)+"/image")
            print("writing firmware update")
            print tnExec(tn,"fwupgrade image")

            bootstate = tnRegex(tn, "uboot_env getenv bootstate", "^getenv : bootstate with ([0-9]).*$")
            print("bootstate: " + bootstate)

            check_boot = tnRegex(tn, "uboot_env getenv check_boot", "^getenv : check_boot with ([0-9]).*$")
            print("check_boot: " + check_boot)

            print("rebooting")
            time.sleep(2)
            tn.write("reboot\n")
            time.sleep(2)


        tn.close()
        print("telnet closed")


    server.stop()


if __name__ == '__main__':
    main()

'''
~ # fwupgrade image
Firmware upgrade uses [image]
DisableSoftWatchDog
remove softdog...
Gemtek_Success

bootstate is 2, update firmware to A...
Erase Length: 0x00350000 Bytes
Erasing ......
Erasing ......success
Writing 3408041 bytes......
Writing 3408041 bytes......success
Upgrade Success
Set_bootstate_to_env...
Reading 4096 bytes......success
Uboot CRC is AC628FBD, Uboot env CRC is AC628FBD
Set_bootstate_to_env : bootstate is [1]
Erase Length: 0x00010000 Bytes
Erasing ......
Erasing ......success
Writing 4096 bytes......
Writing 4096 bytes......success

'''






