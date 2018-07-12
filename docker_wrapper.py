#!/usr/bin/env python3

import os
import sys
import subprocess

def check_type(name, value, types):
    # WAR for python2
    if sys.version_info[0] == 2:
        if str in types:
            types.append(unicode)

    if type(value) not in types:
        raise RuntimeError("%s cannot be type %s" % (name, str(type(value))))

class DockerExec:
    def __init__(self, docker_exec='docker', name=None, image=None, work_path=None, uid=None, gid=None, **kwargs):
        self.docker_options = {}
        self.use_paths = {}
        self.environmentals = {}

        self.set_container_name(name)
        self.set_image(image)
        self.set_docker_exec(docker_exec)
        self.set_work_path(work_path)
        self.set_user(uid, gid)

        self.set_autoremove()
        self.set_interactive()
        self.set_allocate_tty()

    def run(self, args, stdin=sys.stdin, stdout=sys.stdout, shell=True, blocking=True, **kwargs):
        assert(type(args) == list)
        assert(self.image is not None)

        docker_args = [ self.docker_exec, 'run' ]

        if self.name is not None:
            docker_args.extend([ '--name', self.name ])

        for opt, value in self.docker_options.items():
            if type(value) == bool:
                if value == True:
                    docker_args.append(opt)
            elif type(value) == str:
                docker_args.extend([ opt, value ])
            elif type(value) == list:
                for v in value:
                    docker_args.extend([ opt, v ])
            else:
                raise TypeError("Unexpected option type: %s for option" % (str(type(value)), opt))

        for src_path, dst_path in self.use_paths.items():
            docker_args.extend([ '-v', '%s:%s' % (src_path, dst_path) ])

        for name, val in self.environmentals.items():
            docker_args.extend([ '-e', '%s=%s' % (name, val) ])

        if self.work_path is not None:
            docker_args.extend([ '-w', self.work_path ])

        if self.uid is not None:
            user = str(self.uid)
            if self.gid is not None:
                user += ":" + str(self.gid)
            docker_args.extend([ '-u', user])

        docker_args.append(self.image)
        docker_args.extend(args)

        cmd = " ".join(docker_args)
        print("[Running with docker]")
        print(cmd)

        process = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, shell=shell, **kwargs)
        if blocking:
            process.wait()
        return process

    def set_container_name(self, name):
        check_type("name", name, [ str, type(None) ])

        self.name = name

    def set_image(self, image):
        check_type("image", image, [ str ])

        self.image = image

    def set_docker_exec(self, docker_exec):
        check_type("docker_exec", docker_exec, [ str ])

        self.docker_exec = docker_exec

    def set_work_path(self, path):
        check_type("workpath", path, [ str, type(None) ])

        self.work_path = path

    def set_user(self, uid, gid=None):
        check_type("uid", uid, [ int, type(None) ])
        check_type("gid", gid, [ int, type(None) ])

        self.uid = uid
        self.gid = gid

    def use_path(self, path, container_path=None):
        check_type("path", path, [ str ])
        check_type("container_path", container_path, [ str, type(None) ])

        if path == "":
            raise RuntimeError("Cannot map empty path")

        if container_path is None:
            self.use_paths[path] = path
        else:
            self.use_paths[path] = container_path

    def set_envar(self, name, value):
        check_type("name", name, [ str ])
        check_type("value", value, [ str ])

        self.environmentals[name] = value

    # Overwrite option if exists
    def set_option(self, opt, value=None):
        check_type("opt", opt, [ str ])
        check_type("value", value, [ bool, str, type(None) ])

        self.docker_options[opt] = value

    # Support specifying same option multiple times with different value
    def add_option(self, opt, value):
        check_type("opt", opt, [ str ])
        check_type("value", value, [ str ])

        if opt in self.docker_options.keys():
            val = self.docker_options[opt]
            if type(val) != list:
                self.docker_options[opt] = [ val ]
        else:
            self.docker_options[opt] = []

        self.docker_options[opt].append(value)

    def unset_option(self, opt, value=None):
        check_type("opt", opt, [ str ])
        check_type("value", value, [ str ])

        if value is None:
            del self.docker_options[opt]
            return
        else:
            if type(self.docker_options[opt]) == dict:
                self.docker_options[opt].remove(value)
                return
            else:
                if self.docker_options[opt] == value:
                    del self.docker_options[opt]
                    return
                else:
                    raise RuntimeError("Value of [%s] does not match")

        raise RuntimeError("Control reaches unexpected location")

    def set_autoremove(self, enable=True):
        return self.set_option('--rm', enable)

    def set_interactive(self, enable=True):
        return self.set_option('-i', enable)

    def set_allocate_tty(self, enable=True):
        return self.set_option('-t', enable)

class NvidiaDockerExec(DockerExec):
    def __init__(self, **kwargs):
        DockerExec.__init__(self, docker_exec='nvidia-docker', **kwargs)

        self.set_option('--shm-size', '1g')
        self.add_option('--ulimit', 'memlock=-1')
        self.add_option('--ulimit', 'stack=67108864')
