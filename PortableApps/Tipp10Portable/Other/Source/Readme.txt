Tipp10 Portable Launcher
=========================
Copyright 2004-2015 John T. Haller
Copyright 2008-2011 Bart.S

Website: http://PortableApps.com/Tipp10Portable

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


ABOUT TIPP10 PORTABLE
======================
The Tipp10 Portable Launcher allows you to run Tipp10 from a removable drive whose 
letter changes as you move it to another computer. The program can be entirely self-
contained on the drive and then used on any Windows computer.


LICENSE
========
This code is released under the GPL. The source is included with this package as 
Tipp10Portable.nsi.


INSTALLATION / DIRECTORY STRUCTURE
===================================
By default, the program expects the following directory structure:

-\ <--- Directory with Tipp10Portable.exe
	+\App\
		+\Tipp10\
	+\Data\
		+\settings\

It can be used in other directory configurations by including the Tipp10Portable.ini
file in the same directory as Tipp10Portable.exe and configuring it as details in the
INI file section below.


TIPP10PORTABLE.INI CONFIGURATION
=================================
The Tipp10 Portable Launcher will look for an ini file called Tipp10Portable.ini 
within its directory (see the Installation/Directory Structure section above for more
details). If you are happy with the default options, it is not necessary, though. The 
INI file is formatted as follows:

[Tipp10Portable]
Tipp10Directory=App\Tipp10
SettingsDirectory=Data\settings
Tipp10Executable=tipp10.exe
AdditionalParameters=
DisableSplashScreen=false
AllowMultipleInstances=false


The Tipp10Directory and SettingsDirectory entries should be set to the *relative* path to the 
appropriate directories from the current directory. They must be a subdirectory (or multiple 
subdirectories) of the directory containing Tipp10Portable.exe. The default entries for these are 
described in the installation section above.

The Tipp10Executable entry allows you to set the Tipp10 Portable Launcher to use an alternate EXE
call to launch Tipp10. This is helpful if you are using a machine that is set to deny tipp10.exe 
from running. You'll need to rename the tipp10.exe file and then enter the name you gave it on 
the Tipp10Executable= line of the INI.

The AdditionalParameters entry allows you to pass additional commandline parameter entries to 
tipp10.exe. Whatever you enter here will be appended to the call to tipp10.exe.

DisableSplashScreen allows you to disable the splash screen when set to true.

The AllowMultipleInstances entry allows you to run multiple instances of Tipp10 Portable.
The default is false.