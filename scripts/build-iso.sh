#!/bin/bash

# exit when any command fails
set -e

echo user: $(whoami)
echo groups: $(groups)
echo working directory: $(pwd)

echo
ls -hla
echo

wget --no-verbose http://ftp.snt.utwente.nl/pub/os/linux/archlinux/iso/2022.05.01/archlinux-bootstrap-2022.05.01-x86_64.tar.gz
b2sum --check b2sums.txt

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

chroot image /bin/bash -c "pacman-key --init"
chroot image /bin/bash -c "pacman-key --populate archlinux"

# the mkosi-created image has all pacman mirrors deactivated. need to activate mirrors for pacman to work
chroot image /bin/bash -c "sed -i 's/^#Server/Server/' /etc/pacman.d/mirrorlist"

# comment the line "CheckSpace" in pacman.conf
# fixes a pacman error that occurs inside chroot: "error: failed to commit transaction (not enough free disk space)"
# https://gist.github.com/neonb88/5ba848f1aef21ab67c7a4ff28e6d2ea3
chroot image /bin/bash -c "sed -i 's/^CheckSpace/#CheckSpace/' /etc/pacman.conf"

# install the "archiso" package
chroot image /bin/bash -c "pacman --sync --refresh --refresh --sysupgrade --sysupgrade --noconfirm"
chroot image /bin/bash -c "pacman --sync --noconfirm archiso"

# create the iso file
cp --recursive iso/ image/ # copy archiso config into chroot
chroot image /bin/bash -c "mkarchiso -v /iso" # image/out/efly-live-2022.05.13-x86_64.iso
mv image/out/*.iso efly-live.iso

# unmount previously mounted special directories
umount --lazy image/proc
umount --lazy image/sys
umount --lazy image/dev
