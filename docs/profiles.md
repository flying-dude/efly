# Custom Profiles

`efly` provides the possibility to create custom profiles based on which to create disk images.
If no profile is specified, it will use the
[default](https://github.com/flying-dude/efly/tree/main/data/img)
profile automatically.
You can create your own profile and invoke `efly` using it with the `--profile` flag:

```
efly img --profile path/to/myprofile
```

The above command will place the build data into a subdirectory `./out` relative to the current working directory, from which you invoked `efly`.

A profile currently consists of the following components:

* [`packages.txt`](https://github.com/flying-dude/efly/blob/main/data/img/packages.txt): The list of packages to install on the image.
* [`extra`](https://github.com/flying-dude/efly/blob/main/data/img/extra): A folder with extra data that will be copied to location `/` of the root filesystem after installing the specified packages with
[`pacstrap`](https://man.archlinux.org/man/pacstrap.8). You can put your personal configuration and additional scripts into that folder.
* [`postinst`](https://github.com/flying-dude/efly/blob/main/data/img/postinst): A script that will be executed inside a chroot after copying the `extra` files. Use this script for some additional tweaking of our disk image.

## Install Modes

There are three install modes, in which efly profiles can be built:
[`efly-img`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-img),
[`efly-dd`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-dd),

When used with
[`efly-img`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-img),
a graphical live medium with persistent storage is created.
The live medium uses an overlayfs, that combines a compressed, read-only squashfs partition with a read-write `ext4` partition.
The squashfs partition contains all changes made up until running the `postinst` script (see next paragraph). And the `ext4` partition stores file system changes made after that; when actually running the system.
That means you can do changes like install software, change configuration, download files etc. and they will be written to the `ext4` partition.
These changes do not get lost after rebooting the system, which is often the case for live systems.

The second mode is
[`efly-dd`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-dd),
where all data except `/boot` is written to a single `ext4` partition.
There is no overlayfs nor squashfs.
Use this mode to quickly set up a fresh, preconfigured Arch Linux system, that boots directly into a graphical environment with shell, browser, etc. immediately available.

## The `postinst` Script

The
[`postinst`](https://github.com/flying-dude/efly/blob/main/data/profiles/img/postinst)
file is an executable (typically a script in bash, python, etc.), that will be
[executed](https://github.com/flying-dude/efly/blob/fd1cb258f547aa6bdd536f2a80ea53169be78820/src/efly/efly-img#L238)
inside a chroot environment after setting up a new system with `pacstrap`.

The working directory is simply the root `/` of the new file system.
Use this script to execute commands for further customization of your image.

For `efly-rom`, this script will run before compression of the root file system with squashfs.
That means changes made with this script are stored on the compressed squashfs partition.
Since `efly-dd` and `efly-img` have no squashfs partition, all data except EFI boot partition is stored on the same `ext4` partition.
