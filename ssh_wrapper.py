#!/usr/bin/env python3

import os
import sys
import subprocess

def check_output(cmd, **kwargs):
    return subprocess.check_output(cmd, **kwargs).decode("UTF-8").rstrip("\n")

def which(exe_name):
    return check_output("which %s" % exe_name, shell=True)

class Remote():
    def __init__(self, host, port=None, user=None, ssh_exec="ssh", rsync_exec="rsync", scp_exec="scp", **kwargs):
        self.host = host
        self.port = port
        self.user = user

        self.ssh_exec = ssh_exec
        self.rsync_exec = rsync_exec
        self.scp_exec = scp_exec

    def get_remote_desc(self):
        desc = "{user}@{host}".format(user=self.user, host=self.host)
        return desc.lstrip('@')

    def run(self, remote_cmd, options=[], method=subprocess.run, **kwargs):
        ssh_cmd = self.ssh_exec

        if self.port:
            ssh_cmd += " -p" + str(self.port)

        if options:
            ssh_cmd += " ".join(options)

        ssh_cmd += " "
        if self.user:
            ssh_cmd += self.user + "@"
        ssh_cmd += self.host

        cmd = "{ssh_cmd} '{remote_cmd}'".format(ssh_cmd=ssh_cmd, remote_cmd=remote_cmd)
        print(cmd)
        return method(cmd, shell=True, **kwargs)

    def check_output(self, remote_cmd, options=[], **kwargs):
        return self.run(remote_cmd, options, method=check_output, **kwargs)

    def mkdir(self, path, **kwargs): 
        self.run("mkdir -p %s" % path, **kwargs)

    def rmdir(self, path, **kwargs):
        if not path or path.strip(" ") == "/":
            raise ValueError("invalid path for remote 'rm'")

        self.run("rm -r %s" % path, **kwargs)

    def sync(self, from_path, to_path, options, method, **kwargs):
        sync_cmd = self.rsync_exec

        sync_cmd += " " + " ".join(options)
        sync_cmd += " " + from_path
        sync_cmd += " " + to_path

        print(sync_cmd)
        method(sync_cmd, shell=True, **kwargs)

    def push(self, lpath, rpath, options=['-avz'], method=subprocess.run, **kwargs):
        to_path = "{remote_desc}:{rpath}".format(remote_desc=self.get_remote_desc(), rpath=rpath)

        if self.port:
            options.append("--port %s" % str(self.port))

        if os.path.isdir(lpath):
            lpath = lpath.rstrip("/") + "/"
            to_path = to_path.rstrip("/")

        self.mkdir(os.path.dirname(rpath))
        self.sync(lpath, to_path, options, method, **kwargs)
        
    def pull(self, rpath, lpath, options=['-avz'], method=subprocess.run, **kwargs):
        from_path = "{remote_desc}:{rpath}".format(remote_desc=self.get_remote_desc(), rpath=rpath)

        if self.port:
            options.append("--port %s" % str(self.port))

        if os.path.isdir(lpath):
            from_path = from_path.rstrip("/") + "/"
            lpath = lpath.rstrip("/")

        self.mkdir(os.path.dirname(rpath))
        self.sync(from_path, lpath, options, method, **kwargs)
