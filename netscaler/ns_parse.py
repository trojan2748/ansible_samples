#!/usr/bin/env python
# ns_parse.py:
#   Author: adamlandas@gmail.com
#
#   Purpose:
#     * Take current netscaler config (ns.conf)
#       and parse into a wr format
#   Examples:
#     # python -d ns_parse.py
#        # dumps all config
#     # python ns_parse.py
#       SVCGRP-UAT-JBB-API-HTTP-B
#         -> LB-UAT-JBB-API-HTTP
#           -> CS-UAT-JBB-API-HTTP
#             -> QT:DROP_API_ROOT_ACCESS_POL
#             -> QT:HTTP_TO_HTTPS_POL
#           -> CS-UAT-JBB-API-SSL
#             -> REPLACE_IPAD_API_SEARCH_TO_QUERY_POL
#             -> QT:DROP_API_ROOT_ACCESS_POL
#           -> CS-UAT-JBB-API-INT-HTTP
#     # python ns_parse.py -u "www.ten-x.com/commercial/dashboard"
#       cert: www.ten-x.com
#         -> CS-PROD-TDC-SSL
#           -> LB-PROD-TDC-CRE-DASH-HTTP
#              -> ACCESS_TDC_CRE_DASH_PROD
#                 -> TDC_CRE_DASH_PROD_EXP
#                   -> TDC_CRE_DASH_PROD_HTTP_URL_PATH_SW_SET
#
#
#
import argparse

class Policy:
	def __init__(self, name):
		self.dict = {}
                self.dict['name'] = name
                self.dict['type'] = ""
                self.dict['add'] = ""
                self.dict['config'] = []
                self.dict['patset'] = []
                self.dict['acts'] = ""
                self.dict['pols'] = []
                self.dict['rules'] = []
		self.dict['csvs'] = []
		self.dict['lbs'] = []
		

	def __str__(self):
		return self

	def __getitem__(self, key):
		return self.dict[key]

class Server:
        def __init__(self, name):
                self.dict = {}
                self.dict['name'] = name
                self.dict['type'] = ""
                self.dict['add'] = ""
                self.dict['config'] = []
                self.dict['pols'] = []
                self.dict['lbs'] = []
                self.dict['csvs'] = []
                self.dict['groups'] = []
                self.dict['listen'] = ""


        def __str__(self):
                return self

        def __getitem__(self, key):
                return self.dict[key]


def get_args():
	parser = argparse.ArgumentParser()

        parser.add_argument('-v', '--verbose',
                action = 'store',
		default = 1,
                help = "Set verbose 1-3, 1 default")

	parser.add_argument('-u', '--url',
                action = 'store',
                help = "Examples: \
				* https://www.ten-x.com \
				* https://www.ten-x.com/commercial \
				\t* /commercial/")
        parser.add_argument('-d', '--dump',
                action = 'store_true',
                help = "Dumps all config sorted by SVGGROUP's")

	args = parser.parse_args()

	if not args.verbose:
		args.verbose = 1
	return args


with open("ns.conf") as f:
        lines = f.readlines()

groups = {}
lbs = {}
csvs = {}
pols = {}
acts = {}
ssl_certKeys = {}
lb_mons = {}
Policies = {}
Servers = {}
lines = [line.strip() for line in lines]
for line in lines:
        if "add serviceGroup" in line or "add service " in line:
                group = line.split()[2]
                groups[group] = {}
                groups[group]["name"] = group
                groups[group]["add"] = line
                groups[group]["lbs"] = []
                groups[group]["mons"] = []
                groups[group]["config"] = []
                groups[group]["servers"] = []
        elif "bind service" in line:
                group = line.split()[2]
                groups[group]["config"].append(line)
                if "-monitorName" in line:
                        mon = line.split()[-1].strip()
                        groups[group]["mons"].append(mon)

	elif "add policy" in line:
		pol = line.split()[3]
		pols[pol] = {}
		cur = Policy(pol)
		cur.type = line.split()[2]
		cur.add = line
		cur.name = pol
		pols[pol]['name'] = pol
		pols[pol]['type'] = line.split()[2]
		pols[pol]['add'] = line
		pols[pol]['config'] = []
		pols[pol]['patset'] = []
		pols[pol]['acts'] = []
		pols[pol]['pols'] = []
		pols[pol]['rules'] = []

		if cur.type == "expression":
			for p in Policies:
				if Policies[p].type == "patset" and Policies[p]["name"] in line:
					cur["patset"].append(p)
					cur["pols"].append(p)
		Policies[pol] = cur


		if pols[pol]['type'] == "expression":
			for p in pols:
				if pols[p]['type'] == "patset" and p in line:
					pols[pol]['patset'].append(p)
					pols[pol]['pols'].append(p)
	elif "bind policy patset" in line:
		pol = line.split()[3]
		pols[pol]['config'].append(line)
		Policies[pol]["config"].append(line)

	elif "add lb vserver" in line:
                lb = line.split()[3]
		ip = line.split()[5] + ":" + line.split()[6]
		cur = Server(lb)
		cur.type = "lb"
		cur.name = lb
		cur.add = line
		cur.listen = ip
		Servers[lb] = cur
                lbs[lb] = {}
                lbs[lb]["add"] = line
                lbs[lb]["config"] = []
                lbs[lb]["name"] = lb
                lbs[lb]["groups"] = []
                lbs[lb]["pols"] = []
                lbs[lb]["csv"] = []
	elif "bind lb vserver" in line:
                lb = line.split()[3]
                lbs[lb]["config"].append(line)
		Servers[lb]["config"].append(line)
                if "-policyName" in line:
                        policy = line.split("-policyName")[1].split()[0]
                        lbs[lb]["pols"].append(policy)
                else:
                        group = line.split()[-1]
                        groups[group]["lbs"].append(lb)
                        lbs[lb]["groups"].append(group)
			Servers[lb]["groups"].append(group)

        elif "add cs vserver" in line:
                csv = line.split()[3]
                cur = Server(csv)
                cur.type = "csv"
                cur.name = csv
                cur.add = line
		ip = line.split()[5] + ":" + line.split()[6]
		cur.listen = ip
                Servers[csv] = cur
                csvs[csv] = {}
                csvs[csv]["add"] = line
                csvs[csv]["name"] = csv
                csvs[csv]["lbs"] = []
                csvs[csv]["config"] = []
                csvs[csv]["pols"] = []
                csvs[csv]["sslconfig"] = []
                csvs[csv]["certs"] = []
        elif "bind cs vserver" in line:
                csv = line.split()[3]
                csvs[csv]["config"].append(line)
		Servers[csv]["config"].append(line)

                if "-lbvserver" in line:
                        lb = line.split()[-1]
                        csvs[csv]["lbs"].append(lb)
                        lbs[lb]["csv"].append(csv)
			Servers[lb]["csvs"].append(csv)
			Servers[csv]["lbs"].append(lb)

                elif "-targetLBVserver" in line:
                        policy = line.split("-policyName")[1].split()[0]
                        lb = line.split("-targetLBVserver")[1].split()[0]
                        csvs[csv]["lbs"].append(lb)
                        lbs[lb]["csv"].append(csv)
                        lbs[lb]["pols"].append(policy)
			Servers[lb]["csvs"].append(csv)
			Servers[lb]["pols"].append(policy)
			Servers[csv]["pols"].append(policy)
			Servers[csv]["lbs"].append(lb)
			Policies[policy]["lbs"].append(lb)
			Policies[policy]["csvs"].append(csv)

                else:
                        policy = line.split("-policyName")[1].split()[0]
                        csvs[csv]["pols"].append(policy)
			Servers[csv]["pols"].append(policy)
			Policies[policy]["csvs"].append(csv)

	elif "add ssl certKey" in line:
                certKey = line.split()[3]
                ssl_certKeys[certKey] = {}
                ssl_certKeys[certKey]["add"] = line
                ssl_certKeys[certKey]["csvs"] = []
                ssl_certKeys[certKey]["config"] = ""
                ssl_certKeys[certKey]["name"] = certKey
		
	elif "link ssl certKey" in line:
		certKey = line.split()[3] 
               	ssl_certKeys[certKey]["config"] = line
        elif "bind ssl vserver" in line:
                csv = line.split()[3]
                if "-certkeyName" in line and "CS" in csv:
                        cert = line.split("-certkeyName")[1].split()[0]
                        csvs[csv]["certs"].append(cert)
                        csvs[csv]["config"].append(line)
			ssl_certKeys[cert]["csvs"].append(csv)

        elif "add cs policy" in line:
                pol = line.split()[3]
		cur = Policy(pol)
		cur.type = "cs"
		cur.add = line
                pols[pol] = {}
                pols[pol]["name"] = pol
		pols[pol]['type'] = "cs"
                pols[pol]["add"] = line
                pols[pol]["rules"] = []
                pols[pol]["config"] = []
		pols[pol]['patset'] = []
                pols[pol]["pols"] = []
                pols[pol]["acts"] = []

		for p in Policies:
			if p != pol and Policies[p]["name"] in line:
				cur["pols"].append(p)
                Policies[pol] = cur

                for a in pols:
			if a in line and a != pol:
				pols[pol]["pols"].append(a)
			
        elif "add rewrite action" in line:
                act = line.split()[3]
                cur = Policy(act)
                cur.type = "action"
                cur.add = line
		Policies[act] = cur
                acts[act] = {}
                acts[act]["name"] = act
                acts[act]["type"] = "rewrite"
                acts[act]["add"] = line
                acts[act]["pols"] = []
        elif "add rewrite policy" in line:
                pol = line.split()[3]
                pols[pol] = {}
		cur = Policy(pol)
                cur.type = "rewrite"
                cur.add = line
                pols[pol]["name"] = pol
                pols[pol]["add"] = line
                pols[pol]["type"] = "rewrite"
		pols[pol]['patset'] = []
                pols[pol]["config"] = []
		pols[pol]["rules"] = []
		pols[pol]["pols"] = []
                pols[pol]["acts"] = []


		for a in Policies:
			if Policies[a].type == "act" and Policies[a]["name"] in line:
				cur["pols"].append(a)
			elif Policies[a].type =="expression" and Policies[a]["name"] in line:
				cur["pols"].append(a)

                Policies[pol] = cur
		for act in acts:
			if act in line:
				pols[pol]["acts"].append(act)
				acts[act]["pols"].append(pol)
                for a in pols:
                        if pols[a]["type"] == "expression" and a in line:
                                pols[pol]["rules"].append(a)
                                pols[pol]["pols"].append(a)
        elif "add responder action" in line:
                act = line.split()[3]
                cur = Policy(act)
                cur.type = "action"
                cur.add = line
                Policies[act] = cur
                acts[act] = {}
                acts[act]["name"] = act
                acts[act]["type"] = "responder"
                acts[act]["add"] = line
		acts[act]["pols"] = []
        elif "add responder policy" in line:
                pol = line.split()[3]
                cur = Policy(pol)
                cur.type = "responder"
                cur.add = line

                pols[pol] = {}
                pols[pol]["name"] = pol
                pols[pol]["add"] = line
                pols[pol]["type"] = "responder"
		pols[pol]['patset'] = []
                pols[pol]["config"] = []
		pols[pol]["rules"] = []
		pols[pol]["pols"] = []
                pols[pol]["acts"] = []

                for a in Policies:
                        if Policies[a].type == "act" and Policies[a]["name"] in line:
                                cur["pols"].append(a)
                        elif Policies[a].type =="expression" and Policies[a]["name"] in line:
                                cur["pols"].append(a)
		Policies[pol] = cur
	

                for act in acts:
                        if act in line:
                                pols[pol]["acts"].append(act)
                                acts[act]["pols"].append(pol)
		for a in pols:
                        if pols[a]["type"] == "expression" and a in line:
                                pols[pol]["rules"].append(a)
                                pols[pol]["pols"].append(a)
        elif "add transform action" in line:
                act = line.split()[3]
                acts[act] = {}
                acts[act]["name"] = act
                acts[act]["type"] = "transform"
                acts[act]["add"] = line
		acts[act]["pols"] = []
        elif "add transform policy" in line:
                pol = line.split()[3]
                cur = Policy(pol)
                cur.type = "responder"
                cur.add = line
		Policies[pol] = cur
                pols[pol] = {}
                pols[pol]["name"] = pol
                pols[pol]["add"] = line
                pols[pol]["type"] = "transform"
		pols[pol]['patset'] = []
                pols[pol]["config"] = []
                pols[pol]["rules"] = []
		pols[pol]["pols"] = []
                pols[pol]["acts"] = []
                for act in acts:
                        if act in line:
                                pols[pol]["acts"].append(act)
                                acts[act]["pols"].append(pol)
        elif "add lb monitor" in line:
                mon = line.split()[3]
                lb_mons[mon] = {}
                lb_mons[mon]["name"] = mon
                lb_mons[mon]["add"] = line


def verbose():
	global res
	for group in groups:
		config = []
		group = groups[group]
                config.append(group["name"])
                config.append("  %s" % group["add"])
                for mon in group["mons"]:
                        try:
                                config.append("  %s" % lb_mons[mon]["add"])
                        except:
                                pass

		for line in group["config"]:
			config.append("     %s" % line)

		for lb in group["lbs"]:
			config.append("  %s" % lbs[lb]["add"])
                        for line in lbs[lb]["config"]:
				if group["name"] in line:
	                                config.append("     %s" % line)

                        lb_pols = lbs[lb]['pols']
                        lb_csvs = lbs[lb]["csv"]
			for pol in lb_pols:
				if pols[pol]["type"] == "cs":
					res = []
					chain = obj_chain(pol)
					for p in reversed(chain):
						config.append("  %s" % pols[p]["add"])
						for line in pols[p]["config"]:
							config.append("     %s" % line)
			for csv in lb_csvs:
				certs = csvs[csv]["certs"]
	                        for cert in certs:
        	                        config.append("  %s" % ssl_certKeys[cert]["add"])
        	                        config.append("  %s" % ssl_certKeys[cert]["config"])
				for pol in csvs[csv]['pols']:
					config.append("  %s" % pols[pol]["add"])
				config.append("  %s" % csvs[csv]["add"])
				for line in csvs[csv]["config"]:
					if lb in line:
                                        	config.append("     %s" % line)
					elif "targetLBVserver" not in line and "lbvserver" not in line:
                                        	config.append("     %s" % line)
				
			
		for line in config:
			print line
		print



def print_objs(objs):
	spacer = ""
	for obj in objs:
		print "%s -> %s" % (spacer, obj)
		spacer += "  "



def search(url):
	global res
	domain = ""
	if "//" in url:
		domain = url.split("//")[1].split("/")[0]
		url = url.split(domain)[-1]
        elif ".com" in url and "/" in url:
                domain = url.split("/")[0]
                url = url.split("/", 1)[1]
	print domain + "/" +url

	if domain in ssl_certKeys.keys():
		print "cert: " + ssl_certKeys[domain]["name"]
		csv_list = ssl_certKeys[domain]["csvs"]
	else:
		csv_list = csvs.keys() 
	for csv in csv_list:
		for lb in csvs[csv]["lbs"]:
			for pol in lbs[lb]["pols"]:
				if url in pols[pol]['add'] or any(url in s for s in pols[pol]['config']):
					print csvs[csv]["certs"]
					print_objs([csv,lb,pol])
				for a in pols[pol]['pols']:
					if url in pols[a]['add'] or any(url in s for s in pols[a]['config']):
						print csvs[csv]["certs"]
						print_objs([csv,lb,pol,a])
					for b in pols[a]['pols']:
						if url in pols[b]['add'] or any(url in s for s in pols[b]['config']):
							print csvs[csv]["certs"]
							print_objs([csv,lb,pol,a,b])

res = []
i = 0
def obj_chain(obj, search = ""):
	global res
	res.append(obj)
	if search == "":

		if pols[obj]['pols'] == []:
			return res
		for pol in pols[obj]['pols']:
			return obj_chain(pol)
	else:
		for pol in pols[obj]['pols']:
			if any(search in s for s in pols[pol]["config"]) or search in pols[pol]["add"]:
				if pol not in res:
					i = 1
					res.append(pol)
					return obj_chain(pol, search)
			else:
				if i == 0:
					res.append(pol)
					return obj_chain(pol, search)
		if pols[obj]['pols'] == []:
			if i == 1:
                        	return res
			else:
				return []
def obj_chain2(obj, search = ""):
        global res
        res.append(obj)
        if search == "":

                if Policies[obj]['pols'] == []:
                        return res
                for pol in Policies[obj]['pols']:
                        return obj_chain2(pol)


def default():
	global res
	for group in groups:
		print group
		for lb in groups[group]['lbs']:
			print "  ->  %s (%s)" % (lb, Servers[lb].listen)
			for csv in Servers[lb]['csvs']:
				print "    ->  %s (%s)" % (csv, Servers[csv].listen)
				for pol in Policies:
					if (lb in Policies[pol]["lbs"] or Policies[pol]["lbs"] == []) and csv in Policies[pol]["csvs"]:
						res = []
						print "      ->  " + "  ->  ".join(obj_chain2(pol))
				
		print
								

def main():
        global args
        args = get_args()

	if args.dump == True:
		verbose()
	elif args.url != None:
		search(args.url)
	else:
		default()
if __name__ == "__main__":
        main()

