# Install

Below, two ways are explained for installing *pijersi_certu* on your computer:

- As a single file executable, but for Windows platform only ; this is the simplest way.
- As a Python project from source files, for either Windows or Linux platforms ; this is easy thanks to the `pijersi_start.py` script.

## Installing as single executable for Windows and Linux platforms

- From the  [`releases`](../releases) sub-folder of this repository, download the desired version of the executable file `pijersi_certu_version.exe` on your computer where you want. Also the UGI server `pijersi-cmalo` can be found there.
- The latest stable version is `v2.2.0`.
- Check the integrity of the downloaded executable using either `SHA256` or `MD5`algorithms, for example by executing the `Get-FileHash` command, as follows, in the `PowerShell` terminal:
  - `Get-FileHash pijersi_certu_version.exe -Algorithm SHA256`
  - `Get-FileHash pijersi_certu_version.exe -Algorithm MD5`
  - The returned hash value must comply with the following table, otherwise, remove immediately the downloaded executable from your computer.

  | Version     | Hash   | Expected hash value                                          |
  | ----------- | ------ | ------------------------------------------------------------ |
  | v2.3.0.rc1  | SHA256 | D1FE668AA52E5FD3CD2774348B497FA33A1C68A2BE51A769A1CA43F53BD9FED8 |
  | v2.3.0.rc1  | MD5    | D488DE210E511C8052CFE6B31E97EF3A                             |
  | v2.2.0  | SHA256 | A5AE1B59751F11858571EE95A173668B176651340805B99D3D7414C411D886A5 |
  | v2.2.0  | MD5    | FD11005C366326379006951EFA7F8516                             |
  | v2.1.0  | SHA256 | B5EC493FA5C06C9190F8BF01A58759B49736FB7A2345714325912F205945A55E |
  | v2.1.0  | MD5    | 169731954E81B0D8CA2AC4BDE1D4D4BF                             |
  | v2.0.0  | SHA256 | ED5416E03A519D54465896FF6249F203D35E8302252CEB0E71A87D82AE244186 |
  | v2.0.0  | MD5    | 30D26CF1C8798662EC1B6DDEADC54D18                             |
  | v1.3.0  | SHA256 | 66E306910D943F25F090A0CA36580736CEA1EA6349D6A4C04F2E9A5D23447180 |
  | v1.3.0  | MD5    | 562F7DBFE750377ACEA171DE02B65C65                             |
  | v1.2.0  | SHA256 | C75109044E6A71C0133B680CB87639A1BF5022F700E8FBC4D98AB5FAC61129C8 |
  | v1.2.0  | MD5    | 464E1A7F59EF6F4B3702067D0D6A14F3                             |
  | v1.1.0  | SHA256 | 62245ffd476791e12bdfbbf03006edecbd9742a6faa2c14917eee37126e9dbd4 |
  | v1.1.0  | MD5    | 5dbf2450e54a7520d8ed8c72f863c80a                             |
  | v1.0.0  | SHA256 | 57A336F2BC944DF5F230DFC7712C198ED95013C1A2D842DC6F0EDE3FBF985B36 |
  | v1.0.0  | MD5    | 541C8F2A3C70184F04FEA72E8A2222A8                             |
  
  - Linux releases :
  
  | Version     | Hash   | Expected hash value                                          |
  | ----------- | ------ | ------------------------------------------------------------ |
  | v2.3.0.rc1  | SHA256 | BDC4DE68D969629710BFEE964647C89BDF4F23FDE69B564DC42A4F9901079244 |
  | v2.3.0.rc1  | MD5    | 347F7C82E10D68AF1A213D5582B8E303                             |

  - The old release candidates have been removed :

   | Version    | Hash   | Expected hash value                                              |
   | ---------- | ------ | ---------------------------------------------------------------- |
   | v2.0.0.rc5 | SHA256 | 5289992718677000B337405B0D897C3A7A3145883FFAB8E56FC322FAF213D54B |
   | v2.0.0.rc5 | MD5    | 996FDADAC746E408080B44249165F455                                 |
   | v2.0.0.rc4 | SHA256 | FEC7BA9743B6E5A744FA774E2EED9FABBE4C5A8273A4888BDC4DAEC98468FE04 |
   | v2.0.0.rc4 | MD5    | AF9EC3B059F01E934E0E0B97111A6905                                 |
   | v2.0.0.rc3 | SHA256 | 49D7E1A24EB9488B6E44E3B5834EB26E758786DE5C5DD6F7FA1AA8E9D0F56315 |
   | v2.0.0.rc3 | MD5    | 6C871EF9522D714511CA77174A0BBB08                                 |
   | v2.0.0.rc2 | SHA256 | B20B07ABBEAA87D16708C6B4E07353B51ACDE4758871024A45F6979734422100 |
   | v2.0.0.rc2 | MD5    | 7541ACA5DAD55059716953A4C57FE929                                 |
   | v2.0.0.rc1 | SHA256 | 8FAC0C9A5BF4F2B870B1DDCA369B73AEC52714649AD07A5C4F24771A48E59C44 |
   | v2.0.0.rc1 | MD5    | 7215AA83BB353792CC03002455D865BC                                 |
   | v1.3.0-rc3 | SHA256 | 4AC2CD815E97843095C734256B2CF8C381D54F165C86E262E49C627598522E11 |
   | v1.3.0-rc3 | MD5    | AA2A31FE676CB0A9BF43D2C391365631                                 |
   | v1.3.0-rc2 | SHA256 | A9494E334A51EEB29AB56209D1E96A1BD8D50261A2273138A6EEBFA5C146FD0E |
   | v1.3.0-rc2 | MD5    | C1A231F17DB50959DD0A00ED470E7413                                 |
   | v1.3.0-rc1 | SHA256 | 62C6391E9C3A5941C88A6319DFD60ECEA69898C7DE46687C53ADBA614E55F7DE |
   | v1.3.0-rc1 | MD5    | 38D81759DBF813119D3D43D95F433C60                                 |
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


  - The check-sums of the `pijersi-cmalo` UGI servers on `windows` are in the next table; the release candidates have been removed:

   | Version    | Hash   | Expected hash value                                              |
   | ---------- | ------ | ---------------------------------------------------------------- |
   | v2.0.0.rc4 | SHA256 | FB32A4227396FAB783BD0F0488C31A70B6823A82CADF35334287E43A585CBA34 |
   | v2.0.0.rc4 | MD5    | DA8EDD7C8876419CB34063E6DA35A257                                 |
   | v2.0.0.rc3 | SHA256 | 5A67D18A8D2607BAEECDB65B89EA97265A6B05CF8DBDEA6D0268E47E1B7D6470 |
   | v2.0.0.rc3 | MD5    | 0B4C8EEAA237F8DC0C1342440AD5BFEE                                 |
   | v2.0.0.rc2 | SHA256 | 057506A95A5FE649052D52CD6DCE10CDCB2F923DAC2CF3981A4EEE1A3A648114 |
   | v2.0.0.rc2 | MD5    | D7E3432A269BB79263340FEFF53C2ACA                                 |
   | v2.0.0.rc1 | SHA256 | CF922DD3C4263DFA8E3EC3EAB1322B7E19D49471671FF4E0B1FABD494E4A8350 |
   | v2.0.0.rc1 | MD5    | 0E37EDAB469825F423689A7B8B56B587                                 |

  - The check-sums of the `pijersi-cmalo` UGI servers on `linux` are in the next table; the release candidates have been removed:

   | Version    | Hash   | Expected hash value                                              |
   | ---------- | ------ | ---------------------------------------------------------------- |
   | v2.0.0.rc4 | SHA256 | 5ADC9A2ED3C4CEBF15A03FC5C830502BC044F6B629637769A9D6024B951C2B29 |
   | v2.0.0.rc4 | MD5    | 2853CBB2B7FBCA6747EB5A45A2D2339F                                 |

- To start `pijersi-certu` : double-click on the icon of the downloaded executable
- To uninstall  `pijersi-certu` : just remove the downloaded executable.

## Installing from Python sources for Linux and Windows platforms

Latest version of *pijersi_certu* has been developed using Python 3.11. So it is better to have installed such version or some higher version.

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

The package *Mcts* is no longer used.

