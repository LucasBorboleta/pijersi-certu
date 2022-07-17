#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""pijersi_build_app.py builds a one-file executable for Windows OS."""


_COPYRIGHT_AND_LICENSE = """
PIJERSI-CERTU implements a GUI and a rule engine for the PIJERSI boardgame.

Copyright (C) 2022 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""


import glob
import os
import shutil
import subprocess
import sys


_product_home = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
_venv_home = os.path.join(_product_home, ".env")

print("Checking virtual environment ...")
assert os.path.isdir(_venv_home)
print("Checking virtual environment done")


print()
print("Determining the python executable ...")
if os.name == 'nt':
    _venv_python_executable = os.path.join(_venv_home, "Scripts", "python.exe")

elif os.name == 'posix':
    _venv_python_executable = os.path.join(_venv_home, "bin", "python")

else:
    _venv_python_executable = glob.glob(os.path.join(_venv_home, "*/python*"))[0]

print("    _venv_python_executable = ", _venv_python_executable)
print("Determining the python executable done")


print()
print("Installing PyInstaller ...")

if os.name == 'nt':
    # windows fix of "import _ssl" failure after "import ssl" during "pip" execution
    _sys_python_path = os.path.dirname(sys.executable)

    if 'PATH' in os.environ:
        os.environ['PATH'] =  (_sys_python_path + os.pathsep +
                              os.path.join(_sys_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_sys_python_path, 'Library', 'bin') + os.pathsep +
                              os.environ['PATH'] )
    else:
        os.environ['PATH'] = (_sys_python_path + os.pathsep +
                              os.path.join(_sys_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_sys_python_path, 'Library', 'bin') )

subprocess.run(args=[_venv_python_executable, "-m", "ensurepip", "--upgrade"], shell=False, check=True)
subprocess.run(args=[_venv_python_executable, "-m", "pip", "install", "--upgrade", "pip"], shell=False, check=True)
subprocess.run(args=[_venv_python_executable, "-m", "pip", "install", "pyinstaller"], shell=False, check=True)
print()
print("Installing PyInstaller done")


print()
print("Building pijersi_certu application ...")
os.chdir(os.path.join(_product_home, "pijersi_certu"))

if os.path.isdir("tmp_dist"):
   shutil.rmtree("tmp_dist") 

if os.path.isdir("tmp_build"):
   shutil.rmtree("tmp_build") 

if os.path.isfile("pijersi_certu.spec"):
   os.remove("pijersi_certu.spec") 

subprocess.run(args=[_venv_python_executable, 
                     "-m", "PyInstaller", 
                     "--distpath",  "tmp_dist",
                     "--workpath", "tmp_build",
                     "--add-data", "pictures;pictures",
                     "-n", "pijersi_certu",
                     "-i", "pictures\pijersi.ico",
                     "pijersi_gui.py"], 
               shell=False, check=True)

if os.path.isdir("tmp_build"):
   shutil.rmtree("tmp_build") 

if os.path.isfile("pijersi_certu.spec"):
   os.remove("pijersi_certu.spec") 

print()
print("Building pijersi_certu application done")


