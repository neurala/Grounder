
## Prerequisites:

Needed: Qt5 and KF5 development versions.

On OpenSuSE 13.2 the required package list is:

~~~~~~~~~~~~~~~{.bash}
gettext-tools

extra-cmake-modules
kconfig-devel
kconfigwidgets-devel
kcoreaddons-devel
kwidgetsaddons-devel
kxmlgui-devel
ki18n-devel
kf5-filesystem
~~~~~~~~~~~~~~~

Possibly needed:
`kauth-devel`


## How To Build This Application:

~~~~~~~~~~~~~~~{.bash}
cd Grounder
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$KDEDIRS -DCMAKE_BUILD_TYPE=Debug ..
make
~~~~~~~~~~~~~~~

Then `make install`  or  `su -c 'make install' ` or  `sudo make install`


**IMPORTANT:** Note the `..` at the end of cmake command. Without it cmake will try to find its files in the build directory (which is obviously empty...)

`$KDEDIRS` should point to your KDE installation prefix.

**Note:** you can use another build path. Then `cd` into your build dir and:

~~~~~~~~~~~~~~~{.bash}
export Grounder_SRC=path_to_Grounder_src
cmake $Grounder_SRC -DCMAKE_INSTALL_PREFIX=$KDEDIRS -DCMAKE_BUILD_TYPE=Debug
~~~~~~~~~~~~~~~

**Note:** `-DCMAKE_INSTALL_PREFIX=$KDEDIRS` is optional, if not given the application
will be installed in the `/usr/local` tree


## Usage:

Grounder allows to load a sequence of video frames named as:

~~~~~~~~~~~~~~~{.bash}
someVideo-0.jpg
...
someVideo-9797.jpg
~~~~~~~~~~~~~~~

That are residing in the same directory.  Number of frames is not limited (except that it is represented as `uint` internally). To load the sequence any file in the sequence shall be selected, the system loads all others automatically.



## Future:

Looking into loading videos instead of/in addition to sequaences of frames
