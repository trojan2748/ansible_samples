

execfile("vcenter_lib.py")

vcm_hosts = {}
vcm_hosts["vcm01lax01us.prod.auction.local"] = {}
vcm_hosts["vcm01sea01us.prod.auction.local"] = {}

args = GetArgs()
vms = []
for vcm in vcm_hosts.keys():
  print "Connecting to %s" % vcm
  vcm_hosts[vcm]["connection"] = Connect(args, vcm)
  vcm_hosts[vcm]["content"] = GetContent(vcm_hosts[vcm]["connection"])
  vcm_hosts[vcm]["vms"] = GetVMs(vcm_hosts[vcm]["content"])
  for vm in vcm_hosts[vcm]["vms"]:
    print vm.config.name
