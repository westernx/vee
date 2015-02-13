import json
import os
import shlex
import sys

from vee.managers.git import GitManager
from vee.utils import call, makedirs, colour


class HomebrewManager(GitManager):

    name = 'homebrew'

    def __init__(self, *args, **kwargs):
        super(HomebrewManager, self).__init__(*args, **kwargs)

    @property
    def _name_for_platform(self):
        return 'linuxbrew' if sys.platform.startswith('linux') else 'homebrew'

    @property
    def package_path(self):
        return self.home.abspath('packages', self._name_for_platform)

    @property
    def _git_remote_url(self):
        return 'https://github.com/Homebrew/%s.git' % self._name_for_platform

    @property
    def _brew_bin(self):
        return os.path.join(self.package_path, 'bin', 'brew')

    def _brew(self, *cmd, **kwargs):
        package = self.package_path
        env = os.environ.copy()
        env.update(
            # HOMEBREW=prefix,
            HOMEBREW_REPOSITORY=package,
            HOMEBREW_CACHE=os.path.join(package, 'Cache'),
            HOMEBREW_CELLAR=os.path.join(package, 'Cellar'),
            HOMEBREW_PREFIX=package,
            HOMEBREW_TEMP=makedirs(package, 'tmp'),
        )
        return call((self._brew_bin, ) + cmd, env=env, **kwargs)

    _cached_brew_info = None

    def _brew_info(self, name=None, force=False):

        if not os.path.exists(self._brew_bin):
            return {}

        if self._cached_brew_info is None:
            self._cached_brew_info = {}

        name = name or self.requirement.package
        if force or name not in self._cached_brew_info:
            self._cached_brew_info[name] = json.loads(self._brew('info', '--json=v1', name, stdout=True, silent=True))[0]

        return self._cached_brew_info[name]

    def extract(self):
        # Disable BaseManager.extract().
        pass

    def build(self):
        if self.installed:
            print colour('Warning:', 'red', bright=True), colour(self.requirement + ' is already built', 'black', reset=True)
            return
        self._brew('install', self.requirement.package, *(
            shlex.split(self.requirement.configuration) if self.requirement.configuration else ()
        ))

        # Need to force a new installed version number.
        self._brew_info(force=True)

    def _install_name_from_info(self, name=None, info=None):
        info = info or self._brew_info(name)
        return '%s/%s' % (info['name'], info['linked_keg'] or (
            info['installed'][-1]['version']
            if info['installed']
            else info['versions']['stable']
        ))

    @property
    def _build_name(self):
        return self._install_name_from_info()

    @property
    def build_path(self):
        return os.path.join(self.package_path, 'Cellar', self._install_name)

    _install_name = _build_name
    install_path = build_path

    def install(self):
        # Disable BaseManager.install().
        pass

    def link(self, env):
        # We want to link in all dependencies as well.
        for name in self._brew('deps', '-n', self.requirement.package, silent=True, stdout=True).strip().split():
            path = os.path.join(self.package_path, 'Cellar', self._install_name_from_info(name))
            if os.path.exists(path):
                print colour('Linking', 'blue', bright=True), colour('homebrew+%s (homebrew+%s dependency)' % (name, self.requirement.package), 'black', reset=True)
                env.link_directory(path)
        env.link_directory(self.install_path)
