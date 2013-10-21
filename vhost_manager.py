""" VHostManager

A module that helps you manage Apache virtual hosts

Features:

- creates apache virtual hosts
- Add/Remove domains
- Add/Remove multiple domains aliases, multiple subdomains
- Sets up the dirs for www, logs for the
- Creates a git bare repo (can be skipped with --skip-bare-repo)
where updates can be pushed to git via ssh: root@ip:/home/domain.com/www.git

License: MIT
Copyright: (c) 2013 [Mardix](https://github.com/mardix)
Python version >= 2.7.5
Platform: Linux (Centos, RHEL, Ubuntu) and OSX

> Usage as script:
You must have root access or use SUDO

vhost_manager.py [--add | --remove] domain.com
vhost_manager.py [--add | --remove] domain.com:8080
vhost_manager.py [--add | --remove] domain.com:8080 --a dev.domain.com -a admin.domain.com
vhost_manager.py --list-domains
vhost_manager.py --list-alias domain.com:8080


> Usage as module

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

"""

import os
import platform


NAME = "VHostManager"
VERSION = 0.1
__author__ = "Mardix"
LICENSE = "MIT"
GIT_REPO = "https://github.com/mardix/vhost-manager"



# DIST CONFIGURATION
# Config for each platform distribution.
# -- Keys:
#    home_dir: The dir where html files will be placed at
#    vhost_file: The file that con
#    restart_cmd: a command to restart apache

DIST_CONF = {
    "rhel": {  # valid for centos, fedora and rhel distribution
        "home_dir": "/home",
        "vhost_file": "/etc/httpd/conf.d/vhost.conf",
        "restart_cmd": "service httpd restart"
    },
    "ubuntu": {
        "home_dir": "/home",
        "vhost_file": "/etc/apache2/sites-enabled/vhost.conf",
        "restart_cmd": "service apache2 restart"
    },
    "osx": {
        "home_dir": "/home",
        "vhost_file": "/etc/apache2/extra/vhost.conf",
        "restart_cmd": "/usr/sbin/apachectl restart"
    },
    "default": {
        "home_dir": "./home",
        "vhost_file": "./conf.d",
        "restart_cmd": ""
    }
}

# Default virtual host port
DEFAULT_PORT = 80

# These directories will be created by default under the /home/domain.com
# www = Where your html file reside
# logs = hold the logs
DOMAIN_DIRS = ["www", "logs"]

# To automatically create a bare repo for you to push docs to your site
CREATE_BARE_REPO = True

# TEMPLATES
#  VHost template file
vhost_template = """<VirtualHost *:{PORT}>
    ServerName {DOMAIN_NAME}
    DocumentRoot {DOMAIN_DIR}/www
    ErrorLog {DOMAIN_DIR}/logs/error.log
    CustomLog {DOMAIN_DIR}/logs/access.log combined
    #DirectoryIndex index.html index.htm index.php
    <Directory {DOMAIN_DIR}/www>
        Options -Indexes +IncludesNOEXEC +SymLinksIfOwnerMatch +ExecCGI
        allow from all
        AllowOverride All Options=ExecCGI,Includes,IncludesNOEXEC,Indexes,MultiViews,SymLinksIfOwnerMatch
        #AddHandler fcgid-script .php
        #FCGIWrapper {DOMAIN_DIR}/fcgi-bin/php.fcgi .php
    </Directory>
    #RemoveHandler .php
</VirtualHost>
"""

# Alias template
vhost_alias_template = "    ServerAlias {ALIAS}"

##########

class VHost:
    content = ""
    file = None
    __write_file = False
    dist = "default"

    def __init__(self):

        self.dist = self.__get_dist()

        vhost_file = DIST_CONF[self.dist]["vhost_file"]

        if not os.path.isfile(vhost_file):  # Force the creation of the file
            open(vhost_file, "a").close()

        self.file = open(vhost_file, "r+")
        self.content = self.file.read()
        self.__write_file = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.save()
        self.file.close()

    def save(self):
        if self.__write_file:
            self.__write_file = False
            self.file.seek(0)
            self.file.write(self.content)
            self.file.truncate()

    @staticmethod
    def __get_dist():
        """ Return the current distribution: rhel (for centos, fedora, rhel), ubuntu, osx or default for unknown """

        dist = platform.dist()[0]
        system = platform.system()

        if dist.lower() in ["centos", "rhel", "fedora"]:
            dist = "rhel"

        if not dist:
            if system == "Darwin":
                dist = "OSX"
            else:
                dist = "default"
        return dist.lower()

    def has_domain(self, domain, port=DEFAULT_PORT):
        """ Checks if a domain exist on a port """
        
        vhost_tag_open = False

        for line in self.content.split("\n"):
            if self.__get_vhost_line(port) in line:
                vhost_tag_open = True

            if "</VirtualHost>" in line:
                vhost_tag_open = False

            if vhost_tag_open and self.__get_servername_line(domain) in line:  # Add alias
                return True

        return False

    def add(self, domain, port=DEFAULT_PORT, alias=[]):
        """ Add a new domain or alias to a domain by port"""

        if self.has_domain(domain, port) is not True:
            self.content += "\n" + vhost_template.format(DOMAIN_NAME=domain, DOMAIN_DIR=self.get_domaindir(domain), PORT=port)

        new_content = []
        vhost_tag_open = False
        for line in self.content.split("\n"):
            new_content.append(line)
            if self.__get_vhost_line(port) in line:
                vhost_tag_open = True

            if "</VirtualHost>" in line:
                vhost_tag_open = False

            if vhost_tag_open and self.__get_servername_line(domain) in line:  # Add alias
                for alias_ in alias:
                    if alias_ not in self.content:
                        new_content.append(vhost_alias_template.format(ALIAS=alias_))

        self.content = "\n".join(new_content)
        self.__write_file = True

    def remove(self, domain, port, alias=[]):
        """ Remove a domain or alias of a domain by port """

        if self.has_domain(domain, port):
            tmp_content = []
            new_content = []
            vhost_tag_open = False
            in_vhost = False
            remove_alias = False

            if len(alias) > 0:
                remove_alias = True

            for line in self.content.split("\n"):
                if self.__get_vhost_line(port) in line:
                    vhost_tag_open = True

                if vhost_tag_open:
                    tmp_content.append(line)

                    if self.__get_servername_line(domain) in line:
                        in_vhost = True

                    if vhost_tag_open and in_vhost and not remove_alias:
                        tmp_content = []

                    # Remove alias
                    if remove_alias and "ServerAlias" in line:
                        if self.__get_serveralias(line) in alias:
                            tmp_content.pop()

                    if "</VirtualHost>" in line:
                        if remove_alias or not in_vhost and len(tmp_content) > 0:
                            new_content = new_content + tmp_content

                        tmp_content = []
                        in_vhost = False
                        vhost_tag_open = False
                else:
                    new_content.append(line)

            self.content = "\n".join(new_content)
            self.__write_file = True


    def list_domains(self, domain=None, port=DEFAULT_PORT):
        """ Returns the list domain names of each vhost:port
        or the alias of the domain if domain and port is provided
        """
        domains = []
        vhost_tag_open = False
        in_vhost = False
        _port = ""

        for line in self.content.split("\n"):

            if self.__get_vhost_line(port) in line:
                vhost_tag_open = True

            if "<VirtualHost" in line:
                _port = line.split("*:")[1].replace(">", "").strip()

            if "</VirtualHost>" in line:
                vhost_tag_open = False
                in_vhost = False

            if domain:
                if self.__get_servername_line(domain) in line:
                    in_vhost = True
                if vhost_tag_open and in_vhost:
                    if "ServerAlias" in line:
                        domains.append(self.__get_serveralias(line))
            else:
                if "ServerName" in line:
                    domains.append(self.__get_servername(line) + ":" + _port)

        return domains

    def create_dir(self, domain):
        """ Create all domain related directories """
        domain_dir = self.get_domaindir(domain)
        if not os.path.exists(domain_dir):
            os.makedirs(domain_dir)

        for dir in DOMAIN_DIRS:
            dir_ = domain_dir + "/" + dir
            if not os.path.exists(dir_):
                os.makedirs(dir_)

    @staticmethod
    def __get_vhost_line(port):
        return "<VirtualHost *:" + str(port) + ">"

    @staticmethod
    def __get_servername_line(domain):
        return "ServerName " + domain

    @staticmethod
    def __get_serveralias(str):
        return str.replace("ServerAlias", "").strip()
    
    @staticmethod
    def __get_servername(str):
        return str.replace("ServerName", "").strip()

    def get_domaindir(self, domain):
        return DIST_CONF[self.dist]["home_dir"] + "/" + domain

    def restart_apache(self):
        os.system(DIST_CONF[self.dist]["restart_cmd"])

    def create_bare_repo(self, domain, with_crontab=False):
        """ Create a bare repo, will allow you to update the site with git """

        domain_dir = self.get_domaindir(domain)
        www_dir = domain_dir + "/www"
        www_git = domain_dir + "/www.git"
        hook_post_receive_file = www_git + "/hooks/post-receive"

        if not os.path.exists(www_git):
            os.makedirs(www_git)
            git_init_command = "cd " + www_git
            git_init_command += " && git init --bare"
            os.system(git_init_command)

        if not os.path.isfile(hook_post_receive_file):
            with open(hook_post_receive_file, "w") as file:
                post_receive_content = "#!/bin/sh"
                post_receive_content += "\nGIT_WORK_TREE=" + www_dir + " git checkout -f"
                file.write(post_receive_content)
            os.system("chmod +x " + hook_post_receive_file)


if __name__ == "__main__":
    import argparse

    def parse_domain(domain):
        """ Parse a domain:port return a list [domain, port] """
        d = domain.split(":", 1)
        if len(d) == 1:
            d.append(DEFAULT_PORT)
        return d

    try:
        with VHost() as vhost:
            parser = argparse.ArgumentParser()
            parser.add_argument("--add",
                                help="Create new domain or add alias|subdomain associated to it. ie [--add domain.com:80]",
                                metavar="")
            parser.add_argument("--remove",
                                help="Remove domain or alias|subdomain associated to it. ie [--remove domain.com:80]",
                                metavar="")
            parser.add_argument("-a", "--alias",
                                help="Alias name. For multiple alias: [-a new-domain.com -a another.com]",
                                metavar="",
                                action="append")
            parser.add_argument("-s", "--subdomain",
                                help="Subdomain name prefix for the domain. dev = dev.domain.com "
                                     "For multiple subdomain: [-s dev -s admin -s intranet]",
                                metavar="",
                                action="append")
            parser.add_argument("--list-domains", help="List all domains", action="store_true")
            parser.add_argument("--list-alias", help="List all alias under a domain [--ls-alias domain.com:8080]",
                                metavar="")
            parser.add_argument("--restart-apache", help="To manually restart apache", action="store_true")
            parser.add_argument("--skip-bare-repo", help="To skip the creation of a git bare repo", action="store_true")

            arg = parser.parse_args()

            with VHost() as vhost:
                print ("*" * 80)
                print (NAME + " " + str(VERSION) + \
                      " [ " + __author__ + " - " + GIT_REPO + " ]")

                """ Add or Remove domains/alias """
                if arg.add or arg.remove:
                    if arg.add:
                        _d = arg.add
                        _action = "Add"
                    elif arg.remove:
                        _d = arg.remove
                        _action = "Remove"

                    domain, port = parse_domain(_d)

                    alias = []
                    if arg.alias and len(arg.alias) > 0:
                        alias += arg.alias
                    if arg.subdomain and len(arg.subdomain) > 0:
                        alias += [s+"."+domain for s in arg.subdomain]

                    print ("")
                    print ("Domain: " + domain + ":" + str(port))
                    print ("Action: " + _action)
                    if len(alias) > 0:
                        print ("Alias: ")
                        for _alias in alias:
                            print (" - " + _alias)

                    if arg.add: # Add domains/alias
                        vhost.add(domain, port, alias)
                        vhost.create_dir(domain)
                        if CREATE_BARE_REPO and not arg.skip_bare_repo:
                            vhost.create_bare_repo(domain)

                    elif arg.remove:  # Remove domain/alias
                        vhost.remove(domain, port, alias)

                    vhost.restart_apache()

                """ List domains alias """
                if arg.list_alias:
                    domain, port = parse_domain(arg.list_alias)

                    print ("")
                    print ("List Alias: " + domain + ":" + str(port))
                    for domain in vhost.list_domains(domain, port):
                        print (" - " + domain)

                """ List all domains """
                if arg.list_domains:
                    print ("")
                    print ("List Domains:")
                    for domain in vhost.list_domains():
                        print (" - " + domain)

                """ Restart Apache """
                if arg.restart_apache:
                    print ("Restart Apache Server")
                    vhost.restart_apache()

    except Exception as ex:
        print (NAME + " " + str(VERSION) + " encounters an error")
        print (ex)



