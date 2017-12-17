import atexit
import argparse
import getpass
import requests
import ssl
import sys
import time

from datetime import tzinfo, timedelta, datetime
from pyVmomi import vim, vmodl
from pyVim.task import WaitForTask
from pyVim import connect
from pyVim.connect import Disconnect, SmartConnect, GetSi

###
# Editble vars
###
vcm_hosts = {}
vcm_hosts["vcm01lax01us.prod.auction.local"] = {}
#vcm_hosts["vcm01sea01us.prod.auction.local"] = {}
#vcm_hosts = ["vcm01lax01us.prod.auction.local"]

###
# Fixes SSL issues, namely having a self signed cert
###
requests.packages.urllib3.disable_warnings()
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE

MAX_DEPTH=10
content = None
class UTC(tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO

utc = UTC()


def GetArgs():
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')
    parser.add_argument('-u', '--user', required=False, action='store',
        help='Enter prod username')
    parser.add_argument('-p', '--password', required=False, action='store',
        help='Enter prod password')
    parser.add_argument('-m', '--md', required=False, action='store_true',
        help='Output markdown')
    parser.add_argument('-s', '--search', required=False, action='store',
        help='Search: ex: name=apm01lax01us   uuid=234u23904823904823904')
    parser.add_argument('-w', '--wildcard', required=False, action='store_true',
        help='Whether search should return first match or all')
    parser.set_defaults(color=False)
    parser.set_defaults(wildcard=True)
    parser.set_defaults(user="alandas")
    parser.set_defaults(md=False)
    args = parser.parse_args()


    if args.user != None:
        user = args.user
    else:
        args.user = getpass.getpass(prompt='Enter username for prod')

    if args.password != None:
        password = args.password
    else:
        args.password = getpass.getpass(prompt='Enter password for prod\%s: ' % (args.user))

    return args


def GetVMs(content):
  container = content.rootFolder
  viewType = [vim.VirtualMachine]
  recursive = True

  containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

  children = containerView.view
  return children


def Connect(args, vcm):
  try:
    si = SmartConnect(host=vcm,
            user=args.user,
            pwd=args.password,
            port=443,
            sslContext=context)

    atexit.register(Disconnect, si)

  except vim.fault.InvalidLogin:
    print "Username/password not correct"
    sys.exit(1)

  return si

def GetContent(si):
  content = si.RetrieveContent()
  return content


def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


