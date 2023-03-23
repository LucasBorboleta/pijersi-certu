# Install

Below, two ways are explained for installing *pijersi_certu* on your computer:

- As a single file executable, but for Windows platform only ; this is the simplest way.
- As a Python project from source files, for either Windows or Linux platforms ; this is easy thanks to the `pijersi_start.py` script.

## Installing as single executable for Windows platform

- From the  [`releases`](../releases) sub-folder of this repository, download the desired version of the executable file `pijersi_certu_version.exe` on your computer where you want. The latest version is `v1.1.0-rc5`.
- Check the integrity of the downloaded executable using either `SHA256` or `MD5`algorithms, for example by executing the `Get-FileHash` command, as follows, in the `PowerShell` terminal:
  - `Get-FileHash pijersi_certu_version.exe -Algorithm SHA256`
  - `Get-FileHash pijersi_certu_version.exe -Algorithm MD5`
  - The returned hash value must comply with the following table, otherwise, remove immediately the downloaded executable from your computer.

  | Version    | Hash   | Expected hash value                                              |
  | ---------- | ------ | ---------------------------------------------------------------- |
  | v1.1.0-rc5 | SHA256 | 77A927D80F1335BAC0E0B898BEAF015878D838A4CF0E395805C121FC65C56BA0 |
  | v1.1.0-rc5 | MD5    | 5C48C83228F9D90621AB108717C403A3                                 |
  | v1.1.0-rc4 | SHA256 | 01CEE922B7837ED638D7E69D47B0CE9DA54B4512C9D0059700AF7598B1EE1ECA |
  | v1.1.0-rc4 | MD5    | 6D5DE57F23315355CE8CDE45FA4325C5                                 |
  | v1.1.0-rc3 | SHA256 | C873A790A8F5FFC7FD5A4EE509F6A05EF9C581FBE29335E5047DECE8F7312C28 |
  | v1.1.0-rc3 | MD5    | A15F66E514F557D99516A42B05443111                                 |
  | v1.1.0-rc2 | SHA256 | 7020FF967F3781BBF4C36F7FB45C77C1721212816F6879F63EB80A82D81EAACD |
  | v1.1.0-rc2 | MD5    | E083FC94DB4E8381E10213C6E2E520FE                                 |
  | v1.1.0-rc1 | SHA256 | 0EA219C70E075C253A1B974797D9CCB92531778A7F9FFF4205BEB21F8FA45E28 |
  | v1.1.0-rc1 | MD5    | C0FE98D92EBBE4C3497233F7C281370F                                 |
  | v1.0.0     | SHA256 | 57A336F2BC944DF5F230DFC7712C198ED95013C1A2D842DC6F0EDE3FBF985B36 |
  | v1.0.0     | MD5    | 541C8F2A3C70184F04FEA72E8A2222A8                                 |



- To start `pijersi-certu` : double-click on the icon of the downloaded executable
- To uninstall  `pijersi-certu` : just remove the downloaded executable.

## Installing from Python sources for Linux and Windows platforms

Latest version of *pijersi_certu* has been developed using Python 3.10. So it is better to have installed such version or some higher version.

The following instructions might also work on other platforms, but only Windows and Linux have been tested.

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
- *Mcts* is no longer used.
