caps.drop all
#1G memory limit
rlimit-as 1000000000
private-tmp
whitelist ${HOME}/.config/lxc/config.yml
read-only ${HOME}/.config/lxc/config.yml
