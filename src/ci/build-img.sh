#!/bin/bash

# exit when any command fails
set -ex

echo user: $(whoami)
echo groups: $(groups)
echo working directory: $(pwd)

echo
ls -hla
echo

wget --no-verbose http://ftp.snt.utwente.nl/pub/os/linux/archlinux/iso/2022.07.01/archlinux-bootstrap-2022.07.01-x86_64.tar.gz
b2sum --check data/b2sums.txt

tar xzf archlinux-bootstrap-*-x86_64.tar.gz --numeric-owner
mv root.x86_64 image

# https://wiki.archlinux.org/title/Install_Arch_Linux_from_existing_Linux#Method_A:_Using_the_bootstrap_image_(recommended)
# https://unix.stackexchange.com/questions/424478/bind-mounting-source-to-itself
mount --bind image image
cd image
cp /etc/resolv.conf etc
mount -t proc none proc
mount --rbind /sys sys
mount --rbind /dev dev
cd ..

# the archlinux-bootstrap data has all pacman mirrors deactivated. need to activate mirrors for pacman to work
# can consider using reflector here?
chroot image /bin/bash -c "sed -i 's/^#Server/Server/' /etc/pacman.d/mirrorlist"

# comment the line "CheckSpace" in pacman.conf
# fixes a pacman error that occurs inside chroot: "error: failed to commit transaction (not enough free disk space)"
# https://gist.github.com/neonb88/5ba848f1aef21ab67c7a4ff28e6d2ea3
chroot image /bin/bash -c "sed -i 's/^CheckSpace/#CheckSpace/' /etc/pacman.conf"

chroot image /bin/bash -c "pacman-key --init"
chroot image /bin/bash -c "pacman-key --populate"

# 3 august 2022: this one fixed keyring error in ci build:
# https://www.reddit.com/r/EndeavourOS/comments/w5bla5/cant_update_invalid_or_corrupted_package/
chroot image /bin/bash -c "pacman -Sy --noconfirm archlinux-keyring"

# install packages
chroot image /bin/bash -c "pacman --sync --refresh --refresh --sysupgrade --sysupgrade --noconfirm"
chroot image /bin/bash -c "pacman --sync --noconfirm sudo dosfstools e2fsprogs squashfs-tools gptfdisk python"

# copy efly source code into chroot and use it to create the img file
cp --recursive --no-target-directory src/efly image/tmp-efly # copy efly python code
rm image/tmp-efly/data; cp --recursive data image/tmp-efly # replace symlink to data with actual data for use inside chroot
chroot image /bin/bash -c "/tmp-efly/efly-img" # run efly-img to create the raw disk image
mv image/out/efly-live.img . # move the created image to a location where it can be found by github actions script

# unmount previously mounted special directories
#umount --lazy image/proc
#umount --lazy image/sys
#umount --lazy image/dev
