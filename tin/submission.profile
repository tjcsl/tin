caps.drop all
noroot
net none
seccomp
#500M memory limit
rlimit-as 500000000
blacklist /tmp
