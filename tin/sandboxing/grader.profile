caps.drop all
nonewprivs
nogroups
noroot

x11 none
nodvd
nosound
notv
novideo
no3d

shell none

# Resource limits
# 1G memory, 10M files, 500 open file descriptors, 1000 processes
rlimit-as 1000000000
rlimit-fsize 10485760
rlimit-nofile 500
rlimit-nproc 1000

private-tmp
private-dev

# /mnt, /media, /run/mount, /run/media
disable-mnt
blacklist /srv
blacklist /root
blacklist /lost+found
blacklist /swapfile
blacklist /lib/systemd

# localtime for the time, nsswitch.conf for network configuration, and
# profile/skel/bash.bashrc in case they want to start a shell or something
private-etc localtime,nsswitch.conf,profile,skel,bash.bashrc,ssl,lsb-release,arch-release,debian_version,redhat-release,ca-certificates

read-only /etc
read-only /opt
read-only /usr
read-only /lib
read-only /lib64
read-only /var
read-only /bin
read-only /sbin
read-only /dev
read-only /sys
