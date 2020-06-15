#!/bin/bash -e

# Inspired by https://github.com/cdown/travis-automerge
# See https://github.com/cdown/travis-automerge/blob/90cc2a65a887d0a80f78c098892f29d458b29813/LICENSE

: "${BRANCHES_TO_MERGE_REGEX?}" "${BRANCH_TO_MERGE_INTO?}"
: "${GITHUB_SECRET_TOKEN?}" "${GITHUB_REPO?}"

export GIT_COMMITTER_EMAIL='support@alertlogic.com'
export GIT_COMMITTER_NAME='CI bot'

if ! grep -q "$BRANCHES_TO_MERGE_REGEX" <<< "$TRAVIS_BRANCH"; then
    printf "Current branch %s doesn't match regex %s, exiting\\n" \
        "$TRAVIS_BRANCH" "$BRANCHES_TO_MERGE_REGEX" >&2
    exit 0
fi

# Since Travis does a partial checkout, we need to get the whole thing
repo_temp=$(mktemp -d)
git clone "https://github.com/$GITHUB_REPO" "$repo_temp"

# shellcheck disable=SC2164
cd "$repo_temp"

printf 'Checking out %s\n' "$BRANCH_TO_MERGE_INTO" >&2
git checkout "$BRANCH_TO_MERGE_INTO"

printf 'Merging %s\n' "$TRAVIS_COMMIT" >&2
git merge --ff-only "$TRAVIS_COMMIT"

printf 'Pushing to %s\n' "$GITHUB_REPO" >&2

push_uri="https://$GITHUB_SECRET_TOKEN@github.com/$GITHUB_REPO"

# Redirect to /dev/null to avoid secret leakage
git push "$push_uri" "$BRANCH_TO_MERGE_INTO" >/dev/null 2>&1
git push "$push_uri" :"$TRAVIS_BRANCH" >/dev/null 2>&1
