#!/usr/bin/env python3
import requests
from packaging import version
from argparse import ArgumentParser
import re
import os
import datetime
import json
from functools import reduce


def list_github_tags(token, repo):
    auth_headers = {"Authorization": token}
    return requests.get(f"https://api.github.com/repos/{repo}/tags", params=auth_headers).json()


def list_version_tags(github_tags):
    return list(filter(lambda v: isinstance(v, version.Version), map(lambda t: version.parse(t['name']), github_tags)))


def reduce_tag(acc, tag):
    acc[version.parse(tag['name'])] = tag
    return acc


def make_tags_search_hash(github_tags):
    return reduce(reduce_tag, github_tags, {})


def get_latest_version(parsed_tags):
    sorted_tags = sorted(parsed_tags, reverse=True)
    if sorted_tags:
        return sorted_tags[0]
    else:
        return version.parse("0.0.0")


def get_branch_commit_sha(token, repo, branch):
    auth_headers = {"Authorization": token}
    url = f"https://api.github.com/repos/{repo}/branches/{branch}"
    return requests.get(url, params=auth_headers).json()['commit']['sha']


def get_branch_commit_message(token, repo, branch):
    auth_headers = {"Authorization": token}
    url = f"https://api.github.com/repos/{repo}/branches/{branch}"
    return requests.get(url, params=auth_headers).json()['commit']['commit']['message']


def create_new_tag(token, repo, tag_obj):
    auth_headers = {"Authorization": token}
    url = f"https://api.github.com/repos/{repo}/git/tags"
    r = requests.post(url, params=auth_headers, data=tag_obj)
    # meh, just roughly
    if 200 < r.status_code < 300:
        return True
    else:
        print(f"Failed to create tag {json.dumps(tag_obj, indent=4)}, because {r.status_code}")
        return False


def make_tag_object(version, tag_message, sha, tagger='CI Bot', email='travis@travis'):
    date = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    return {
        "tag": f"v{version}",
        "message": tag_message,
        "object": sha,
        "type": "commit",
        "tagger": {
            "name": tagger,
            "email": email,
            "date": date
        }
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Calculates and returns new version based on the version tags of the "
                                        "specified repo, only PEP440 versions are taken into account. "
                                        "If micro version is not passed, "
                                        "version is incremented by --increment, default is 1")
    parser.add_argument("-t", "--token", dest="token",
                        help="github api token, if not set taken from GITHUB_SECRET_TOKEN",
                        default=os.getenv('GITHUB_SECRET_TOKEN'))
    parser.add_argument("-c", "--create_release", action="store_true", default=False,
                        dest="do_release", help="create calculated new release")
    parser.add_argument("-b", "--branch", dest="branch", help="branch to tag", default="master")
    parser.add_argument("-r", "--repo", dest="repo", help="github repo", required=True)
    parser.add_argument("-re", "--commit_message_regex", dest="regex", default=".*",
                        help="commit regex to be tagged, if not set any commit on given branch will be tagged")
    parser.add_argument("-m", "--micro", dest="micro", type=int, help="new micro version <major>.<minor>.<micro>")
    parser.add_argument("-i", "--increment", dest="increment", help="increment minor version by this number",
                        default=1, type=int)
    options = parser.parse_args()
    token = options.token
    if not token:
        print("Secret token is not set neither by parameter nor by environment variable")
        exit(1)
    repo = options.repo
    do_release = options.do_release
    newmicro = options.micro
    increment = options.increment
    branch = options.branch
    regex = options.regex
    tags = list_github_tags(token, repo)
    tag_search = make_tags_search_hash(tags)
    parsed_tags = list_version_tags(tags)
    latest = get_latest_version(parsed_tags)
    latest_sha = tag_search[latest]['commit']['sha']
    ma = latest.major
    mi = latest.minor
    mic = latest.micro
    if newmicro:
        if mic > newmicro:
            print(f"latest micro version {ma}.{mi}.{mic} is bigger than provided, provided {newmicro}")
            exit(1)
        else:
            newrel_version = f"{ma}.{mi}.{newmicro}"
    else:
        newrel_version = f"{ma}.{mi}.{mic + 1}"
    commit_sha = get_branch_commit_sha(token, repo, branch)
    commit_message = get_branch_commit_message(token, repo, branch)
    tag_obj = make_tag_object(newrel_version, commit_message, commit_sha)
    if re.match(regex, commit_message):
        print(f"Commit message {commit_message} matched {regex}, proceeding to release {newrel_version}")
        if do_release:
            if latest_sha == commit_sha:
                print(f"Release aborted release {latest} already created for {commit_sha}")
            else:
                create_new_tag(token, repo, tag_obj)
        else:
            print(f"would create tag if create release is secified \n{json.dumps(tag_obj, indent=4)} \n"
                  f" new commit {latest_sha}, tag {newrel_version}\n"
                  f" old commit {commit_sha}, tag {str(latest)}")
