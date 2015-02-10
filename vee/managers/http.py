import os
import urllib2
import urlparse
import shutil

from vee.managers.base import BaseManager
from vee.package import Package as BasePackage
from vee.utils import makedirs, colour


class HttpManager(BaseManager):

    name = 'http'

    @property
    def _local_path(self):
        split = urlparse.urlsplit(self.requirement.spec)
        return self.home.abspath(
            'managers',
            self.name,
            split.netloc,
            split.path.strip('/'),
        )

    def fetch(self, package):

        if os.path.exists(self._local_path):
            return

        makedirs(os.path.dirname(self._local_path))

        dst = self._local_path
        tmp = dst + '.downloading'

        print colour('VEE Downloading', 'blue', bright=True), colour(self.requirement.spec, 
            'black') + colour('', reset=True)

        srcfh = None
        dstfh = None
        try:
            srcfh = urllib2.urlopen(self.requirement.spec)
            dstfh = open(tmp, 'wb')
            for chunk in iter(lambda: srcfh.read(16384), ''):
                dstfh.write(chunk)
        finally:
            if srcfh:
                srcfh.close()
            if dstfh:
                dstfh.close()

        shutil.move(tmp, dst)
