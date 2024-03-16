# Gitlab initial root password

You can get the initial root password using: `docker exec -it gitlab_app_1 grep 'Password:' /etc/gitlab/initial_root_password`

https://docs.gitlab.com/ee/install/docker.html#install-gitlab-using-docker-engine

# Gitlab runner

Create a gitlab runner for your project, (Project settings, CI/CD, Runners, New project runner, Create runner)
Copy token and run `register-runner.sh`

```
$ ssh dockeruser@host

dockeruser@host:~$ export TOKEN=glrt-PrevWbdG-bgagaLsZ5sk

dockeruser@host:~$ docker/gitlab/register-runner.sh 
Runtime platform arch=amd64 os=linux pid=18 revision=782c6ecb version=16.9.1
Running in system-mode.
Verifying runner... is valid
Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded!
Configuration (with the authentication token) was saved in "/etc/gitlab-runner/config.toml" 
```

