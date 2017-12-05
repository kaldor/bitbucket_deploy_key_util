#!/usr/bin/env python2.7

from __future__ import print_function

import argparse
import base64
import collections
import json
import os
import re
import urllib
import urllib2
import subprocess
import tempfile

class Repo():
  def __init__(self, repo):
    if isinstance(repo, collections.Mapping):
      self.owner = repo['owner']
      self.slug = repo['slug']
    elif isinstance(repo, basestring):
      self.owner, self.slug = repo.split('/')
    else:
      raise NotImplementedError()

  def matches(self, regex):
    return regex.search(str(self)) != None

  def keys(self):
    return ['owner', 'slug']

  def __getitem__(self, key):
    return getattr(self, key)

  def __repr__(self):
    return '{}/{}'.format(self.owner, self.slug)

def list_repos(regexes):
  regexes = map(re.compile, regexes)

  req = urllib2.Request('https://api.bitbucket.org/1.0/user/repositories'.format(accountname='nhelke'))
  basicAuthString = base64.standard_b64encode('{}:{}'.format(username, secret))
  req.add_header("Authorization", "Basic {}".format(basicAuthString))
  f = urllib2.urlopen(req)
  repos = json.load(f)
  for repo in map(Repo, repos):
    if any((repo.matches(regex) for regex in regexes)):
      yield repo

class SSHKey():
  def __init__(self, key):
    self.key = key
    with tempfile.TemporaryFile() as tmp:
      tmp.write(self.key)
      tmp.seek(0)
      self.fingerprint = subprocess.check_output(['ssh-keygen', '-E', 'MD5', '-lf', '/dev/stdin'], stdin=tmp).rstrip()

  def __eq__(self, other):
    return self.fingerprint == other.fingerprint

  def __repr__(self):
    return repr(self.key)

  def __str__(self):
    return self.fingerprint

def add_deploy_key(key, label, repos):
  for repo in map(Repo, repos):
    req = urllib2.Request('https://api.bitbucket.org/1.0/repositories/{owner}/{slug}/deploy-keys'.format(**repo))
    basicAuthString = base64.standard_b64encode('{}:{}'.format(username, secret))
    req.add_header("Authorization", "Basic {}".format(basicAuthString))
    d = {'key': SSHKey(key).key}
    if label:
      d['label'] = label
    req.add_data(urllib.urlencode(d))
    f = urllib2.urlopen(req)
    access_key = json.load(f)
    yield SSHKeyEntry(SSHKey(access_key['key']), repo, access_key['pk'], access_key['label'])

class SSHKeyEntry(collections.namedtuple('SSHKeyEntry', ['key', 'repo', 'id', 'label'])):
  def __str__(self):
    return ' '.join(('{}'.format(getattr(self, field)) for field in self._fields))

def list_deploy_keys(repos):
  for repo in map(Repo, repos):
    req = urllib2.Request('https://api.bitbucket.org/1.0/repositories/{owner}/{slug}/deploy-keys'.format(**repo))
    basicAuthString = base64.standard_b64encode('{}:{}'.format(username, secret))
    req.add_header("Authorization", "Basic {}".format(basicAuthString))
    f = urllib2.urlopen(req)
    access_keys = json.load(f)
    for access_key in access_keys:
      yield SSHKeyEntry(SSHKey(access_key['key']), repo, access_key['pk'], access_key['label'])

def remove_deploy_key(key, repos):
  key = SSHKey(key)

  for repo in repos:
    for keyentry in list_deploy_keys([repo]):
      if keyentry.key == key:
        req = urllib2.Request('https://api.bitbucket.org/1.0/repositories/{owner}/{slug}/deploy-keys/{id}'.format(id=keyentry.id, **keyentry.repo))
        basicAuthString = base64.standard_b64encode('{}:{}'.format(username, secret))
        req.get_method = lambda: 'DELETE'
        req.add_header("Authorization", "Basic {}".format(basicAuthString))
        d = {'pk': keyentry.id}
        req.add_data(urllib.urlencode(d))
        f = urllib2.urlopen(req)
        yield keyentry
    else:
      raise LookupError('{} was not found on repo {}'.format(key, repo))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--verbose', action='store_true')

  parser.add_argument('--username')
  parser.add_argument('--secret')

  subparsers = parser.add_subparsers()
  list_repos_parser = subparsers.add_parser('list_repos')
  list_repos_parser.set_defaults(function=list_repos)
  list_repos_parser.add_argument('regexes', metavar='REGEX', nargs='*', help='Disjunction of optional regex(es) to filter list by', default=[''])

  add_deploy_key_parser = subparsers.add_parser('add_deploy_key')
  add_deploy_key_parser.set_defaults(function=add_deploy_key)
  add_deploy_key_parser.add_argument('--key', required=True)
  add_deploy_key_parser.add_argument('--label', help='Optional label to assign to deploy key')
  add_deploy_key_parser.add_argument('repos', metavar='REPO', nargs='+')

  list_deploy_key_parser = subparsers.add_parser('list_deploy_keys')
  list_deploy_key_parser.set_defaults(function=list_deploy_keys)
  list_deploy_key_parser.add_argument('repos', metavar='REPO', nargs='+')
  
  remove_deploy_key_parser = subparsers.add_parser('remove_deploy_key')
  remove_deploy_key_parser.set_defaults(function=remove_deploy_key)
  remove_deploy_key_parser.add_argument('--key', required=True)
  remove_deploy_key_parser.add_argument('repos', metavar='REPO', nargs='+')

  args = parser.parse_args()

  username = os.getenv('BITBUCKET_USERNAME', args.username)
  secret = os.getenv('BITBUCKET_SECRET', args.secret)

  print(username, secret)

  if not username or not secret:
    parser.error('You must specify a username and secret, either by using the BITBUCKET_USERNAME and BITBUCKET_SECRET environment variables, or by using --username and --secret arguments')

  func_args = {k:v for (k, v) in vars(args).iteritems() if k not in set(('function', 'secret', 'username', 'verbose'))}
  map(print, map(repr if args.verbose else str, args.function(**func_args)))