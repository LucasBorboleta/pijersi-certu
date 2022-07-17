## Install

*pijersi_certu* has been developed using Python 3.8.5. So it is better to have installed such version or some higher version. 

The following instructions might also work on other platforms, but only Windows and Linux have been tested.

### Instructions for Linux and Windows platforms

1. Make an installation directory by either cloning this *git* repository or downloading it as a zip archive and unzipping it.

2. Move into the installation directory, where the `README.md` file seats.

3. Execute `python pijersi_start.py` on Linux and  double-click on`pijersi_start.py` on Windows:

   - On Windows, if needed, the first time, use `Open with ...` in order to associate `.py` file with your installed `python` interpreter.

   - The first time a Python virtual environment is created and the required dependencies are downloaded and installed; then the GUI is started. 
   - The next times, the GUI is just started.

4. For un-installing *pijersi_certu* just remove the installation directory.


### Used dependencies

For information, *pijersi_certu* relies on the following packages:

- *Pillow* : for converting and resizing images used in the GUI;
- *MCTS*  : for implementing experimental AI agents.
