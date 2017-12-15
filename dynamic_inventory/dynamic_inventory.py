#!/usr/bin/env python
# Usage:
#   * ./dynamic_inventory.py -s "ansible_product_uuid|ansible_distribution_version"
#     Creates custom inventory ini file with these ansible vars
#   * ./dynamic_inventory.py -s "address%10.1.15"
#     Create an inventory file for any value that has '10.1.15' in it
#   * ./dynamic_inventory.py -s "mtu>9000"
#     Create an inventory file where any mtu value is greater then 9000
import argparse
import commands
import glob
import json
import objectpath
import yaml

from jsonpath_rw import jsonpath, parse
from pprint import pprint

servers = {}
multi = {}
m = 0

def GetArgs():
    parser = argparse.ArgumentParser(
        description='Script to produce dynamic inventories')
    parser.add_argument('-f', '--facts', required=False, action='store',
        help='Path to ansible fact cache')
    parser.add_argument('-p', '--perhost', required=False, action='store_true',
        help='Produce per host inventory files, or one all.yml. Default: False')
    parser.add_argument('-s', '--search', required=False, action='store',
        help='Enter search string: ie: "-s dockerthin"   ie: -s "address%10.1.15"  ie: "-s "ansible_distribution_version=7.4')
    parser.add_argument('-d', '--dir', required=False, action='store',
        help='Directory for output')
    parser.add_argument('-y', '--yaml', required=False, action='store_true',
        help='Output in yaml')
    parser.set_defaults(perhost=False)
    parser.set_defaults(search="")
    parser.set_defaults(facts="/tmp/fact.cache/")
    parser.set_defaults(output=".")
    parser.set_defaults(yaml=False)

    args = parser.parse_args()
    return args

def find2(search_string, m=0):
  fact_path = "%s/*" % args.facts
  files = glob.glob(fact_path)
  global filename
  for f in files:
    server = f.split("/")[-1]
    s = {}
    s["results"] = []
    found = 0
    
    data = json.load(open(f))
    tree_obj = objectpath.Tree(data)

    if "=" in search_string:
      l = search_string.split("=")[0]
      r = search_string.split("=")[1]
      filename = "%s-eq-%s" % (l, r)
      jsonpath_expr = parse('$..%s' % l)
      parents = [str(match.full_path) for match in jsonpath_expr.find(data)]
      for parent in parents:
        try:
          result = list(tree_obj.execute('$..%s[@ is str(\"%s\")]' % (parent, r)))
        except:
          result = []
        if len(result) > 0:
          found = 1
          try:
            s["results"].append((parent, result[0]))
          except:
            s["results"] = []
            s["results"].append((parent, result[0]))

    elif "%" in search_string:
      l = search_string.split("%")[0]
      r = search_string.split("%")[1]
      filename = "%s-like-%s" % (l, r)
      jsonpath_expr = parse('$..%s' % l)
      parents = [str(match.full_path) for match in jsonpath_expr.find(data)]
      for parent in parents:
        try:
          result = list(tree_obj.execute('$..%s[str(\"%s\") in str(@.%s)]' % (parent, r, l)))
        except:
          result = []
        if len(result) > 0:
          found = 1
          try:
            s["results"].append((parent, result[0]))
          except:
            s["results"] = []
            s["results"].append((parent, result[0]))


    elif ">" in search_string or "<" in search_string:
      if ">" in search_string:
        l = search_string.split(">")[0]
        r = search_string.split(">")[1]
        filename = "%s-gt-%s" % (l, r)
        jsonpath_expr = parse('$..%s' % l)
        parents = [str(match.full_path) for match in jsonpath_expr.find(data)]
        for parent in parents:
          result = list(tree_obj.execute('$..%s[@ > int(\"%s\")]' % (parent, r)))
          if len(result) > 0:
            found = 1
            try:
              s["results"].append((parent, result[0]))
            except:
              s["results"] = []
              s["results"].append((parent, result[0]))
      else:
        l = search_string.split("<")[0]
        r = search_string.split("<")[1]
        filename = "%s-lt-%s" % (l, r)
        jsonpath_expr = parse('$..%s' % l)
        parents = [str(match.full_path) for match in jsonpath_expr.find(data)]
        for parent in parents:
          result = list(tree_obj.execute('$..%s[@ < int(\"%s\")]' % (parent, r)))
          if len(result) > 0:
            found = 1
            try:
              s["results"].append((parent, result[0]))
            except:
              s["results"] = []
              s["results"].append((parent, result[0]))


    else:
      filename = "custom"
      if "|" in search_string:
        search = search_string.split("|")
      else:
        search = [search_string]
      for l in search:
        result = list(tree_obj.execute('$..%s' % l))
        for r in result:
          found = 1
          s["results"].append((l, r))

    if found == 1:
      if server not in servers.keys():
        ip = list(objectpath.Tree(data).execute('$..ansible_default_ipv4'))
        s["ip"] = ip[0]["address"]
        servers[server] = s
      else:
        for r in s["results"]:
          servers[server]["results"].append(r)

      if m == 1:
        try:
          servers[server]["finds"].append(l)
        except:
          servers[server]["finds"] = []
          servers[server]["finds"].append(l)

  return servers


def write(ss):
  count = len(ss.keys())
  if args.yaml == True:
    print "Writing to: %s.yml" % (filename)
    output = open("./%s.yml" % filename, "w")
    output.write("---\n\nall:\n  hosts:\n")
    for server in sorted(ss.keys()):
      s = ss[server]
      string = "    {0}:\n".format(server)
      string += "      ansible_host: {0}\n".format(s["ip"])
      for r in s["results"]:
        if type(r[1]) == dict:
          string += "      %s:\n" % str(r[0])
          y = yaml.safe_dump(r[1], default_flow_style=False)
          for line in y.split("\n"):
            string += "        %s\n" % line
        else:
          string += "      %s: %s\n" % (r[0], r[1])
      output.write("%s" % (string))
    output.close()
  else:
    print "Writing to: %s" % (filename)
    output = open("./%s" % filename, "w")
    output.write("# %s\n\n[all]\n" % args.search)
    for server in sorted(ss.keys()):
      res = ""
      s = ss[server]
      for r in s["results"]:
        res += " %s=%s " % (r[0], r[1])
      string = "{0:<45} ansible_host={1:<15} {2}\n".format(server, s["ip"], res)
      output.write(string)
    output.close()


def main():
  global args
  global filename
  args = GetArgs()

  if "&" in args.search:
    m = 1 
    items = args.search.split("&")
    s = {}
    for item in items:
      find2(item, m)
    for server in servers:
      if len(servers[server]["finds"]) == len(items):
        s[server] = servers[server]

  else:
    s = find2(args.search)

  if len(s.keys()) > 0:
    write(s)


if __name__ == "__main__":
  main()
