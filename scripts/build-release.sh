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
mount --make-rslave --rbind /sys sys
mount --make-rslave --rbind /dev dev
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
chroot image /bin/bash -c "pacman --sync --refresh --refresh"
chroot image /bin/bash -c "pacman --sync --noconfirm archiso"

# create the actual build output. this is a bootable iso file located inside folder "image/out/"
cp --recursive efly-live/ image/
chroot image /bin/bash -c "mkarchiso -v /efly-live" # image/out/efly-linux-2022.05.13-x86_64.iso

mv image/out/*.iso efly-live.iso
b2sum efly-live.iso > efly-live.iso.b2sum

# unmount previously mounted special directories
#umount image/proc
#umount image/sys
#umount image/dev
