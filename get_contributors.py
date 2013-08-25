#!/usr/bin/env python
import os
import time
from os.path import dirname
import hashlib
import urllib
import requests
import sqlite3
import logging
import json


# Quick & dirty env-based config
# See also: https://developer.github.com/v3/#rate-limiting
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', None)
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', None)
GITHUB_EMAIL_CACHE_AGE = int(os.getenv('GITHUB_EMAIL_CACHE_AGE',
                                       60 * 60 * 24 * 7))
GITHUB_REPOS_CACHE_AGE = int(os.getenv('GITHUB_REPOS_CACHE_AGE',
                                       60 * 60))

CACHE_PATH_TMPL = 'cache/%s/%s'

repos = [
    'codeforamerica/adopt-a-hydrant',
    'codeforamerica/public_art_finder',
    'codeforamerica/blightstatus',
    'codeforamerica/schoolselection',
    'codeforamerica/honolulu_answers',
    'codeforamerica/nsb-mobile',
    'codeforamerica/opencounter',
    'codeforamerica/prepared.ly',
    'codeforamerica/wheresmyschoolbus',
    'codeforamerica/click_that_hood',
    'codeforamerica/streetmix',
    'codeforamerica/textizen',
    'smartchicago/chicago-early-learning',
    'smartchicago/chicago-atlas',
    'smartchicago/wikichicago',
    'smartchicago/TweetCollector',
    'smartchicago/connect-chicago-locator',
    'smartchicago/civic-innovation-summer',
    'smartchicago/civic-user-testing',
    'smartchicago/www.smartchicagoapps.org',
    'smartchicago/foodborne',
    'smartchicago/foodborne_classifier',
    'smartchicago/wasmycartowed',
    'smartchicago/tabula',
    'smartchicago/cutgroup',
    'smartchicago/adopt-a-sidewalk',
    'smartchicago/cutgroup-signups',
    'smartchicago/chicago-health-atlas',
    'smartchicago/311-fm-webapp',
    'smartchicago/311-fm-data',
    'smartchicago/foodborne',
    'LearnSprout/learnsprout.github.com',
    'azavea/Open-Data-Catalog',
    'openplans/shareabouts',
    'open-city/vacant-building-finder',
    'sheltr/sheltr',
    'openplans/OpenTripPlanner',
    'localwiki/localwiki',
    'open-city/look-at-cook',
    'memphis518/Garden-Dating-Service',
    'okfn/ckan'
]
GITHUB_API_HOST = 'https://api.github.com'
base_url = '%s/repos' % GITHUB_API_HOST
commit_levels = [1000,500,250,100, 50, 25, 10, 1, 0]
contributors = {}
contributors_by_level = {}


def main():
    # Figure out the number of contributions per contributor:
    for repo in repos:
        print "Fetching contributors for %s" % repo
        repo_url = '%s/repos/%s' % (GITHUB_API_HOST, repo)

        repocontributors = api_get('%s/contributors' % repo_url, None,
                                   'repocontributors', GITHUB_REPOS_CACHE_AGE)
        for repocontributor in repocontributors:
            username = repocontributor['login']
            contributions = repocontributor['contributions']
            contributor = contributors.setdefault(username, {
                "username": username,
                "name": None,
                "email": None,
                "location": None,
                "public_repos": 0,
                "followers": 0,
                "hireable": True,
                "company": None
            })
            contributor['contributions'] = (
                contributor.get('contributions', 0) + contributions)
            contributor.setdefault('repos', []).append(repo)
            if not contributor['email']:
                print "Fetching email for %s" % (username,)
                commits = api_get('%s/commits' % repo_url,
                                  dict(author=username),
                                  'email', GITHUB_EMAIL_CACHE_AGE)
                try:
                    first = commits[0]['commit']
                    contributor['email'] = first['author']['email']
                except:
                    pass
            print "Fetching location for %s" % (username,)
            user = api_get('%s/users/%s' % (GITHUB_API_HOST, username),
                           None, 'user', GITHUB_EMAIL_CACHE_AGE)
            contributor['location'] = user.get('location', None)
            contributor['name'] = user.get('name', None)
            contributor['public_repos'] = user.get('public_repos', 0)
            contributor['followers'] = user.get('followers', 0)
            contributor['hireable'] = user.get('hireable', True)
            contributor['company'] = user.get('company', None)

        print "Fetching forkers of %s" % repo
        forks = api_get('%s/forks' % repo_url, None, 'forks',
                        GITHUB_REPOS_CACHE_AGE)
        for fork in forks:
            if type(fork) != dict:
                import ipdb; ipdb.set_trace()
            else:
                username = fork['owner']['login']
                contributor = contributors.setdefault(username, {
                    "username": username, "email": None
                })
                contributor.setdefault('repos', []).append(repo)
                if not contributor['email']:
                    print "Fetching email for %s" % username
                    forker = api_get('%s/users/%s' % (GITHUB_API_HOST, username))
                    try:
                        contributor['email'] = forker['email']
                    except:
                        pass


    # Group the contributors into levels by number of contributions:
    for user, contributor in contributors.items():
        if 'contributions' in contributor:
            contributions = contributor['contributions']
        else:
            contributions = 0
        for level in commit_levels:
            if contributions >= level:
                contributors_by_level.setdefault(level, []).append(contributor)
                break

    print_contributors_by_level()


def print_contributors():
    """Output contributors and their number of contributions."""
    for user, contributor in contributors.items():
        print '%s, %s, %s' % (
            user, contributor['contributions'], ' '.join(contributor['repos']))


def print_contributors_by_level():
    """Output contributors, based on their contribution levels."""
    for level in commit_levels:
        print '========== %s+ ==========' % level
        print '---- %s contributors ----' % len(contributors_by_level[level])
        for contributor in contributors_by_level[level]:
            print '%s, %s, %s, %s, %s, %s, %s, %s' % (
                contributor['username'],
                contributor.get('name', ''),
                contributor.get('email', ''),
                contributor.get('location', ''),
                contributor.get('public_repos', 0),
                contributor.get('followers', 0),
                contributor.get('hireable', False),
                contributor.get('company', '')
            )


def load_contributors_by_level():
    """Load contributors into sqlite db."""
    for level in commit_levels:
        for contributor in contributors_by_level[level]:
            conn = sqlite3.connect('contributors.db')
            pass


def api_url(url, params=None):
    """Append the GitHub client details, if available"""
    if not params:
        params = {}
    if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        params.update(dict(
            client_id = GITHUB_CLIENT_ID,
            client_secret = GITHUB_CLIENT_SECRET
        ))
    if params:
        url = '%s?%s' % (url, urllib.urlencode(params))
    return url


def api_get(path, params=None, cache_name=False, cache_timeout=86400):
    """Cached HTTP GET to GitHub repos API"""
    url = api_url(path, params)
    
    # If no cache name, then cache is disabled.
    if not cache_name:
        return requests.get(url).json()

    # Build a cache path based on MD5 of URL
    path_hash = hashlib.md5(url).hexdigest()
    cache_path = CACHE_PATH_TMPL % (cache_name, path_hash)
    
    # Create the cache path, if necessary
    cache_dir = dirname(cache_path)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Attempt to load up data from cache
    data = None
    if os.path.exists(cache_path) and file_age(cache_path) < cache_timeout:
        try:
            data = json.load(open(cache_path, 'r'))
        except ValueError:
            pass

    # If data was missing or stale from cache, finally perform GET
    if not data:
        print "GET %s" % url
        data = requests.get(url).json()
        json.dump(data, open(cache_path, 'w'))

    return data


def file_age(fn):
    """Get the age of a file in seconds"""
    return time.time() - os.stat(fn).st_mtime


if __name__ == '__main__':
    main()
