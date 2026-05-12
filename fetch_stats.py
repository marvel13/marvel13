#!/usr/bin/env python3
"""
Fetch GitHub stats (repos, stars, commits, followers, lines of code)
and write them to stats.json. Per-repo LOC is cached in cache/ so
unchanged repos are not re-fetched.
"""
import hashlib, json, os, sys
from pathlib import Path
import requests

TOKEN = os.environ.get('ACCESS_TOKEN') or os.environ.get('GITHUB_TOKEN')
USER  = os.environ.get('USER_NAME', 'marvel13')
CACHE_FILE = Path('cache') / (hashlib.sha256(USER.encode()).hexdigest() + '.txt')
GRAPHQL = 'https://api.github.com/graphql'
HEADERS = {'Authorization': f'bearer {TOKEN}'}


def gql(query, variables=None):
    r = requests.post(GRAPHQL, json={'query': query, 'variables': variables or {}}, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    if 'errors' in data:
        raise Exception(data['errors'])
    return data['data']


def get_user_id():
    data = gql('query($l:String!){user(login:$l){id}}', {'l': USER})
    return data['user']['id']


def get_repos(affiliations):
    edges, cursor = [], None
    while True:
        data = gql('''
        query($l:String!,$a:[RepositoryAffiliation],$c:String){
          user(login:$l){
            repositories(first:100,after:$c,ownerAffiliations:$a){
              totalCount
              edges{node{nameWithOwner stargazers{totalCount}
                defaultBranchRef{target{...on Commit{history{totalCount}}}}}}
              pageInfo{endCursor hasNextPage}
            }
          }
        }''', {'l': USER, 'a': affiliations, 'c': cursor})
        repo_data = data['user']['repositories']
        edges += repo_data['edges']
        if not repo_data['pageInfo']['hasNextPage']:
            return edges, repo_data['totalCount']
        cursor = repo_data['pageInfo']['endCursor']


def loc_for_repo(owner, repo, owner_id, cursor=None, adds=0, dels=0, commits=0):
    data = gql('''
    query($o:String!,$r:String!,$c:String){
      repository(owner:$o,name:$r){
        defaultBranchRef{target{...on Commit{
          history(first:100,after:$c){
            edges{node{additions deletions author{user{id}}}}
            pageInfo{endCursor hasNextPage}
          }
        }}}
      }
    }''', {'o': owner, 'r': repo, 'c': cursor})
    ref = data['repository']['defaultBranchRef']
    if not ref:
        return adds, dels, commits
    history = ref['target']['history']
    for edge in history['edges']:
        node = edge['node']
        if node['author']['user'] and node['author']['user']['id'] == owner_id:
            commits += 1
            adds += node['additions']
            dels += node['deletions']
    if history['pageInfo']['hasNextPage']:
        return loc_for_repo(owner, repo, owner_id, history['pageInfo']['endCursor'], adds, dels, commits)
    return adds, dels, commits


def load_cache():
    try:
        result = {}
        for line in CACHE_FILE.read_text().splitlines():
            parts = line.split()
            if parts:
                result[parts[0]] = parts[1:]
        return result
    except FileNotFoundError:
        return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(exist_ok=True)
    lines = [f"{k} {' '.join(v)}" for k, v in cache.items()]
    CACHE_FILE.write_text('\n'.join(lines) + '\n')


def main():
    print(f'Fetching GitHub stats for {USER}...')
    owner_id = get_user_id()

    owner_edges, repo_count = get_repos(['OWNER'])
    all_edges, contrib_count  = get_repos(['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])

    stars     = sum(e['node']['stargazers']['totalCount'] for e in owner_edges)
    followers = gql('query($l:String!){user(login:$l){followers{totalCount}}}',
                    {'l': USER})['user']['followers']['totalCount']

    cache = load_cache()
    total_adds = total_dels = total_commits = 0

    for edge in all_edges:
        node  = edge['node']
        name  = node['nameWithOwner']
        key   = hashlib.sha256(name.encode()).hexdigest()
        ref   = node.get('defaultBranchRef')
        cur_count = ref['target']['history']['totalCount'] if ref else 0

        if key in cache:
            cached_count, my_commits, adds, dels = cache[key]
            if int(cached_count) == cur_count:
                total_adds    += int(adds)
                total_dels    += int(dels)
                total_commits += int(my_commits)
                continue

        owner, repo = name.split('/', 1)
        print(f'  LOC: {name}')
        adds, dels, my_commits = loc_for_repo(owner, repo, owner_id)
        cache[key] = [str(cur_count), str(my_commits), str(adds), str(dels)]
        total_adds    += adds
        total_dels    += dels
        total_commits += my_commits

    save_cache(cache)

    stats = {
        'repos':      repo_count,
        'contributed': contrib_count,
        'stars':      stars,
        'commits':    total_commits,
        'followers':  followers,
        'loc_add':    total_adds,
        'loc_del':    total_dels,
        'loc_total':  total_adds - total_dels,
    }
    Path('stats.json').write_text(json.dumps(stats, indent=2))
    print('Done:', stats)


if __name__ == '__main__':
    main()
