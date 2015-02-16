import argparse
import os
import re
import shlex

from vee.exceptions import AlreadyInstalled


class Requirement(object):

    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('-n', '--name')
    arg_parser.add_argument('-r', '--revision')
    arg_parser.add_argument('-e', '--environ', action='append', default=[])
    arg_parser.add_argument('--install-name')
    arg_parser.add_argument('--configuration')
    arg_parser.add_argument('package')


    def __init__(self, args, home=None):

        if isinstance(args, basestring):
            args = shlex.split(args)
        if isinstance(args, (list, tuple)):
            args = self.arg_parser.parse_args(args)
            
        # Extract the manager type. Usually this is of the form:
        # type+specification. Otherwise we assume it is a simple URL or file.
        m = re.match(r'^(\w+)\+(.+)$', args.package)
        if m:
            self.manager_name = m.group(1)
            self.package = m.group(2)
        elif re.match(r'^https?://', args.package):
            self.manager_name = 'http'
            self.package = args.package
        else:
            self.manager_name = 'file'
            self.package = os.path.abspath(os.path.expanduser(args.package))

        self._args = args

        self.configuration = args.configuration
        self.install_name = args.install_name
        self.name = args.name
        self.revision = args.revision

        self.environ = {}
        for x in args.environ:
            parts = re.split(r'(?:^|,)(\w+)=', x)
            for i in xrange(1, len(parts), 2):
                self.environ[parts[i]] = parts[i + 1]

        self.home = home or args.home
        self.manager = self.home.get_manager(requirement=self)


    def __str__(self):
        package = self.manager_name + ('+' if self.manager_name else '') + self.package
        args = []
        for name in (
            'configuration',
            'environ',
            'install_name',
            'name',
            'revision',
        ):
            value = getattr(self, name)
            if value:
                if isinstance(value, dict):
                    value = ','.join('%s=%s' % (k, v) for k, v in sorted(value.iteritems()))
                if isinstance(value, (list, tuple)):
                    value = ','.join(value)
                args.append('--%s %s' % (name, value))
        return package + (' ' if args else '') + ' '.join(sorted(args))

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, str(self))

    def _reinstall_check(self, force):
        if self.manager.installed:
            if force:
                self.manager.uninstall()
            else:
                raise AlreadyInstalled(str(self))

    def resolve_environ(self, source=None):

        source = source or os.environ
        diff = {}

        def rep(m):
            a, b, c, orig = m.groups()
            abc = a or b or c
            if abc:
                return source.get(abc, '')
            if orig:
                return source.get(k)

        for k, v in self.environ.iteritems():
            v = re.sub(r'\$\{(\w+)\}|\$(\w+)|%(\w+)%|(@)', rep, v)
            diff[k] = v

        return diff

    def install(self, force=False):

        self._reinstall_check(force)

        self.manager.fetch()
        self._reinstall_check(force)
    
        self.manager.extract()
        self._reinstall_check(force)

        self.manager.build()
        self.manager.install()


class AbstractManager(object):

    def dependencies(self):
        return []

    def provisions(self):
        return []


class AbstractRequirement(object):

    def __init__(self, package):
        self.package = package
        self.manager = AbstractManager()

    def __str__(self):
        return self.package

