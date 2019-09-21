caps.drop all
#1G memory limit
rlimit-as 1000000000

private-tmp
private-dev

# /mnt, /media, /run/mount, /run/media
disable-mnt
blacklist /srv
blacklist /root
blacklist /lost+found
blacklist /swapfile
blacklist /lib/systemd

blacklist /etc/passwd
blacklist /etc/passwd-
blacklist /etc/shadow
blacklist /etc/shadow-
blacklist /etc/group
blacklist /etc/group-
blacklist /etc/gshadow
blacklist /etc/gshadow-

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
