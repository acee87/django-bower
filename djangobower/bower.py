from . import conf, shortcuts
import os
import subprocess
import sys
import json


class BowerAdapter(object):
    """Adapter for working with bower"""

    def __init__(self, bower_path, components_root):
        self._bower_path = bower_path
        self._components_root = components_root

    def is_bower_exists(self):
        """Check is bower exists"""
        if shortcuts.is_executable(self._bower_path)\
                or shortcuts.which(self._bower_path):
            return True
        else:
            return False

    def create_components_root(self):
        """Create components root if need"""
        if not os.path.exists(self._components_root):
            os.mkdir(self._components_root)

    def install(self, packages):
        """Install package from bower"""
        proc = subprocess.Popen(
            [self._bower_path, 'install'] + list(packages),
            cwd=self._components_root,
        )
        proc.wait()

    def _get_package_name(self, line):
        """Get package name#version from line in old bower"""
        prepared_line = line.decode(
            sys.getfilesystemencoding(),
        )
        if '#' in prepared_line:
            for part in prepared_line.split(' '):
                if '#' in part and part:
                    return part[:-1]

        return False

    def _accumulate_dependencies(self, data):
        """Accumulate dependencies"""
        for name, params in data['dependencies'].items():
            self._packages.append('{}#{}'.format(
                name, params.get('pkgMeta', {}).get('version', ''),
            ))
            self._accumulate_dependencies(params)

    def _parse_package_names(self, output):
        """Get package names in bower >= 1.0"""
        data = json.loads(output)
        self._packages = []
        self._accumulate_dependencies(data)
        return self._packages

    def freeze(self):
        """Yield packages with versions list"""
        proc = subprocess.Popen(
            [self._bower_path, 'list', '-j', '--offline', '--no-color'],
            cwd=conf.COMPONENTS_ROOT,
            stdout=subprocess.PIPE,
        )
        proc.wait()

        output = proc.stdout.read().decode("utf-8")

        try:
            packages = self._parse_package_names(output)
        except ValueError:
            # legacy support
            packages = filter(bool, map(
                self._get_package_name, output.split('\n'),
            ))

        return iter(set(packages))


bower_adapter = BowerAdapter(conf.BOWER_PATH, conf.COMPONENTS_ROOT)
