#!/usr/bin/env python3
from distutils.core import setup
import subprocess
import glob
import os

subprocess.call(["make"])

ver = os.environ.get("PKGVER") or subprocess.run(['git', 'describe', '--tags'],
      stdout=subprocess.PIPE).stdout.decode().strip()

setup(
  name = 'listssrht',
  packages = [
      'listssrht',
      'listssrht.types',
      'listssrht.blueprints'
  ],
  version = ver,
  description = 'lists.sr.ht website',
  author = 'Drew DeVault',
  author_email = 'sir@cmpwn.com',
  url = 'https://git.sr.ht/~sircmpwn/lists.sr.ht',
  install_requires = ['srht', 'flask-login', 'aiosmtpd'],
  license = 'AGPL-3.0',
  package_data={
      'listssrht': [
          'templates/*.html',
          'static/*'
      ]
  },
  scripts = [
      'lists-srht-lmtp'
  ],
)
