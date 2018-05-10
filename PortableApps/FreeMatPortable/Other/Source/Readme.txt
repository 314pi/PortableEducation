FreeMat Portable Launcher
==========================
Copyright 2004-2013 John T. Haller
Copyright 2008-2013 Bart.S

Website: http://PortableApps.com/FreeMatPortable

This software is OSI Certified Open Source Software.
OSI Certified is a certification mark of the Open Source Initiative.

This program is free software; you can redistribute it and/or 
modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation; either version 2 
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program; if not, write to the Free Software 
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


ABOUT FREEMAT PORTABLE
=======================
The FreeMat Portable Launcher allows you to run FreeMat from a removable drive whose 
letter changes as you move it to another computer. The program can be entirely self-
contained on the drive and then used on any Windows computer.


LICENSE
========
This code is released under the GPL. The source is included with this package as 
FreeMatPortable.nsi.


INSTALLATION / DIRECTORY STRUCTURE
===================================
By default, the program expects the following directory structure:

-\ <--- Directory with FreeMatPortable.exe
	+\App\
		+\FreeMat\
	+\Data\
		+\settings\

It can be used in other directory configurations by including the FreeMatPortable.ini 
file in the same directory as FreeMatPortable.exe and configuring it as details in the 
INI file section below.


FREEMATPORTABLE.INI CONFIGURATION
==================================
The FreeMat Portable Launcher will look for an ini file called FreeMatPortable.ini 
within its directory (see the Installation/Directory Structure section above for more 
details). If you are happy with the default options, it is not necessary, though. The 
INI file is formatted as follows:

[FreeMatPortable]
FreeMatDirectory=App\FreeMat
SettingsDirectory=Data\settings
FreeMatExecutable=FreeMat.exe
AdditionalParameters=
DisableSplashScreen=false
AllowMultipleInstances=true


The FreeMatDirectory and SettingsDirectory entries should be set to the *relative* path to the 
appropriate directories from the current directory. They must be a subdirectory (or multiple 
subdirectories) of the directory containing FreeMatPortable.exe. The default entries for these are 
described in the installation section above.

The FreeMatExecutable entry allows you to set the FreeMat Portable Launcher to use an alternate EXE 
call to launch FreeMat. This is helpful if you are using a machine that is set to deny FreeMat.exe 
from running. You'll need to rename the FreeMat.exe file and then enter the name you gave it on 
the FreeMatExecutable= line of the INI.

The AdditionalParameters entry allows you to pass additional commandline parameter entries to 
FreeMat.exe. Whatever you enter here will be appended to the call to FreeMat.exe.

The DisableSplashScreen entry allows you to run the FreeMat Portable Launcher without the 
splash screen showing up. The default is false.

The AllowMultipleInstances entry allows you to run multiple instances of FreeMat Portable. 
The default is true.