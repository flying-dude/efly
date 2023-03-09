# Custom Profiles

`efly` provides the possibility to create custom profiles based on which to create disk images.
If no profile is specified, it will use the
[default](https://github.com/flying-dude/efly/tree/main/data/profiles/efly-live)
profile automatically.
You can create your own profile and invoke `efly` using it with the `--profile` flag:

```
efly rom --profile path/to/profile
```

The above command will place the build data into a subdirectory `./out` relative to the current working directory, from which you invoked `efly`.

A profile currently consists of the following components:

* [`packages.txt`](https://github.com/flying-dude/efly/blob/main/data/profiles/efly-live/packages.txt):
The list of packages to install on the image.
* [`extra`](https://github.com/flying-dude/efly/tree/main/data/profiles/efly-live/extra):
A folder with extra data that will be copied to location `/` of the root filesystem after installing the specified packages with
[`pacstrap`](https://man.archlinux.org/man/pacstrap.8). You can put your personal configuration and additional scripts into that folder.
* [`postinst`](https://github.com/flying-dude/efly/blob/main/data/profiles/efly-live/postinst):
A script that will be executed inside a chroot after copying the `extra` files. Use this script for some additional tweaking of our disk image.

There are two install modes, in which efly profiles can be built:
[`efly-rom`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-rom),
[`efly-dd`](https://github.com/flying-dude/efly/blob/main/src/efly/efly-dd).

## The `postinst` Script

The
[`postinst`](https://github.com/flying-dude/efly/blob/main/data/profiles/efly-live/postins)
file is an executable (typically a script in bash, python, etc.), that will be
[executed](https://github.com/flying-dude/efly/blob/8aaed9b3ff3b7e4f0af2dc372d23a306f08d6097/src/efly/efly-rom#L210)
inside a chroot environment after setting up a new system with `pacstrap`.

The working directory is simply the root `/` of the new file system.
Use this script to execute commands for further customization of your image.

For `efly-rom`, this script will run before compression of the root file system with squashfs.
That means changes made with this script are stored on the compressed squashfs partition.
Since `efly-dd` and `efly-img` have no squashfs partition, all data except EFI boot partition is stored on the same `ext4` partition.
