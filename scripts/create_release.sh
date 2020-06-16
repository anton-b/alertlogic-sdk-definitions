#!/bin/bash -e

: "${RELEASE_BRANCH?}" "${GITHUB_TOKEN?}"

function is_in_remote() {
    local branch=${1}
    local existed_in_remote=$(git ls-remote --heads origin ${branch})

    if [[ -z ${existed_in_remote} ]]; then
        echo 0
    else
        echo 1
    fi
}

is_in_remote _release_lock_
if [ "$?" -eq 0 ]; then
    repo_temp=$(mktemp -d)
    git clone "https://github.com/$GITHUB_REPO" "$repo_temp"
    cd "$repo_temp"

    LATEST_TAG=`curl -H "Authorization: token $TOK" https://api.github.com/repos/anton-b/alertlogic-sdk-definitions/tags | jq '.[0].name'`
    printf "Latest release determined %s" \ "$LATEST_TAG"
end