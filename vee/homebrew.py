import json
import os
import sys

from vee.git import GitRepo
from vee.subproc import call
from vee.utils import  cached_property


class Homebrew(object):

    def __init__(self, path=None, repo=None, home=None):
        self.name = 'linuxbrew' if sys.platform.startswith('linux') else 'homebrew'
        if repo:
            self.repo = repo
        else:
            work_tree = (
                path or
                os.environ.get('VEE_HOMEBREW') or
                home._abs_path('packages', self.name)
            )
            remote_url = 'https://github.com/Homebrew/%s.git' % self.name
            self.repo = GitRepo(work_tree=work_tree, remote_url=remote_url)
        self._info = {}

    @cached_property
    def cellar(self):
        return os.path.join(self.repo.work_tree, 'Cellar')

    def __call__(self, cmd, *args, **kwargs):
        self.repo.clone_if_not_exists()
        bin = os.path.join(self.repo.work_tree, 'bin', 'brew')
        
        # We need to own the homebrew cache so that we can control permissions.
        kwargs['env'] = env = kwargs.get('env', os.environ).copy()
        env.setdefault('HOMEBREW_CACHE', os.path.join(self.repo.work_tree, 'Cache'))
        
        res = call((bin, cmd) + args, _frame=1, **kwargs)
        if cmd in ('install', 'uninstall'):
            self._info.pop(args[0], None)
        return res

    def info(self, name, force=False):
        if self._info is None:
            self._info = {}
        if force or name not in self._info:
            self._info[name] = json.loads(self('info', '--json=v1', name, stdout=True))[0]
        return self._info[name]
