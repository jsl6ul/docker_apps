#!/bin/bash

#TOKEN=<runner-token>
if [ "$TOKEN" == "" ]; then
    echo "Error, runner authentication token undefined."
    exit 1
fi

if [ "$RUNNER_CONTAINER" == "" ]; then
    RUNNER_CONTAINER=gitlab-runner-1
fi

GITLAB_URL=https://gitlab.{{ common_apps_domain }}
DOCKER_NETWORK=bridge

# register runner
docker exec -it ${RUNNER_CONTAINER} \
       gitlab-runner register \
       --non-interactive \
       --token ${TOKEN} \
       --url ${GITLAB_URL} \
       --description "Docker Runner" \
       --executor docker \
       --docker-image docker:stable \
       --docker-network-mode ${DOCKER_NETWORK} \
       --docker-allowed-pull-policies always \
       --docker-allowed-pull-policies if-not-present \
       --docker-allowed-pull-policies never \
       --docker-volumes "/cache" \
       --docker-volumes "/run/user/{{ docker_rootless_user.uid }}/docker.sock:/var/run/docker.sock" \
       --docker-volumes "/tmp/builds:/tmp/builds" \
       --docker-volumes "{{ docker_rootless_user.home }}/{{ docker_project_dir }}/Dockerfile:/root/Dockerfile" \
       --builds-dir "/tmp/builds"

# Optional, but recommended: Set the builds directory to /tmp/builds, so job
# artifacts are periodically purged from the runner host. If you skip this step,
# you must clean up the default builds directory (/builds) yourself.
