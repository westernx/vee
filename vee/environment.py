import errno
import os

from vee.utils import makedirs


IGNORE_DIRS = frozenset(('.git', '.svn'))
IGNORE_FILES = frozenset(('.DS_Store', ))


class Environment(object):

    def __init__(self, name, home):
        self.home = home
        if name.startswith('/'):
            self.path = name
            self.name = os.path.basename(name)
        else:
            self.name = name
            self.path = home.abspath('environments', name)
        self._db_id = None

    def db_id(self):
        if self._db_id is None:
            cur = self.home.db.cursor()
            row = cur.execute('SELECT * FROM environments WHERE path = ?', [self.path]).fetchone()
            if row:
                self._db_id = row['id']
            else:
                cur.execute('INSERT INTO environments (name, path) VALUES (?, ?)', [
                    self.name, self.path,
                ])
                self._db_id = cur.lastrowid
        return self._db_id

    def link_directory(self, dir_to_link):
        
        # TODO: Be like Homebrew, and be smarter about what we link, and what
        # we copy.

        for old_dir_path, dir_names, file_names in os.walk(dir_to_link):
            
            rel_dir_path = os.path.relpath(old_dir_path, dir_to_link)
            new_dir_path = os.path.abspath(os.path.join(self.path, rel_dir_path))

            # Ignore AND skip these directories.
            dir_names[:] = [x for x in dir_names if x not in IGNORE_DIRS]
            for dir_name in dir_names:
                makedirs(os.path.join(new_dir_path, dir_name))

            for file_name in file_names:
                if file_name in IGNORE_FILES:
                    continue
                try:
                    os.symlink(
                        os.path.join(old_dir_path, file_name),
                        os.path.join(new_dir_path, file_name),
                    )
                except OSError as e:
                    # TODO: have a vee-link-history.txt in each environment
                    # so that we can quickly check what is already linked there.
                    if e.errno != errno.EEXIST:
                        raise

