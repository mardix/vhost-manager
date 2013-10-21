#VHostManager
---

A module that helps you manage Apache virtual hosts

Features:

- creates apache virtual hosts

- Add/Remove domains

- Add/Remove multiple domains aliases, multiple subdomains

- Sets up the dirs for www, logs for the

- Creates a git bare repo (can be skipped with --skip-bare-repo)
where updates can be pushed to git via ssh: root@ip:/home/domain.com/www.git

License: MIT

Copyright: © 2013 [Mardix](https://github.com/mardix)

Python version >= 2.7.5

Platform: Linux (Centos, RHEL, Ubuntu) and OSX

---

###Usage as script:

VHostManager can be used via the command line. It must be executed as root or use sudo to execute ie: 

	python vhost_manager --list-domains 
	or 
	sudo python vhost_manager --list-domains

**Add** or **Remove** a domain. If not specified, the port is 80 by default

	vhost_manager.py [--add | --remove] domain.com

**Add** or **Remove** a domain on the port 8080 for domain.com

	vhost_manager.py [--add | --remove] domain.com:8080

**Add** or **Remove** ***Alias*** (Alias is a full domain name)

	vhost_manager.py [--add | --remove] domain.com:8080 --a mysitealias1.com --a myotheralias.net
	
	
**Add** or **Remove** ***Subdomain*** (Subdomain is a prefix that will be added on the domain, ***admin*** will be prefixed in domain.com -> admin.domain.com)

	vhost_manager.py [--add | --remove] domain.com:8080 --s admin -s www
	
List all the domains

	vhost_manager.py --list-domains

List all alias of a domain

	vhost_manager.py --list-alias domain.com:8080



###Usage as module

Vhost Manager can be used as module in your application. Just import the module to your application and you should be good to go.


	import vhost_manager

	with vhost_manager.VHost() as vhost:

    	# Add domain or alias to a domain
    	vhost.add(domain="domain.com", port="80", alias=["www.domain.com", "admin.domain.com"])

    	# Remove domain
    	vhost.remove(domain="domain.com", port="80")

    	# Remove alias to a domain. In this case it will remove admin.domain.com
    	vhost.remove(domain="domain.com", port="80", alias=["admin.domain.com"])

    	# Get a list of all the domains
    	all_domains = vhost.list_domains()

    	# Get a list of all alias on domain.com
    	all_alias = vhost.list_domains("domain.com", port=80)
    
