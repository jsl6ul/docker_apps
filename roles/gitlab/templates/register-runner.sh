#!/bin/sh

#TOKEN=<runner-token>
RUNNER_CONTAINER=gitlab_runner_1
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
       --builds-dir "/tmp/builds"

# Optional, but recommended: Set the builds directory to /tmp/builds, so job
# artifacts are periodically purged from the runner host. If you skip this step,
# you must clean up the default builds directory (/builds) yourself.
