caps.drop all

noroot
x11 none

# Resource limits
# 1G memory, 10M files, 500 open file descriptors, 500 processes
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

# localtime for the time, nsswitch.conf/resolv.conf for nameserver configuration, and
# profile/skel/bash.bashrc in case they want to start a shell or something
private-etc localtime,nsswitch.conf,resolv.conf,profile,skel,bash.bashrc,ssl,lsb-release,arch-release,debian_version,redhat-release,ca-certificates

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
