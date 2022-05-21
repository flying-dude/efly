#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="efly-live"
iso_label="EFLY_$(date +%Y%m)"
iso_publisher="Efly Linux <https://github.com/flying-dude/efly>"
iso_application="Efly Live Medium"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
#airootfs_image_tool_options=('-comp' 'gzip' '-Xcompression-level' '1')
file_permissions=(
  ["/etc/shadow"]="0:0:0400"
  ["/etc/gshadow"]="0:0:0400"

  ["/root"]="0:0:750"

  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"

  ["/usr/local/share/efly/autorun"]="0:0:755"

  ["/home/efly/Desktop/Keyboard.desktop"]="0:0:755"
  ["/home/efly/Desktop/GParted.desktop"]="0:0:755"
  ["/home/efly/Desktop/TigerVNC Viewer.desktop"]="0:0:755"

  ["/home/efly/Desktop/GVim.desktop"]="0:0:755"
  ["/home/efly/Desktop/Emacs.desktop"]="0:0:755"
  ["/home/efly/Desktop/Geany.desktop"]="0:0:755"

  ["/home/efly/Desktop/Chromium.desktop"]="0:0:755"
  ["/home/efly/Desktop/NetSurf Web Browser.desktop"]="0:0:755"

  ["/home/efly/Desktop/Installation Guide.desktop"]="0:0:755"
)
