# PCRT3 (PNG Check & Repair Tool)

[![Static Badge](https://img.shields.io/badge/python-3.12-blue.svg)
](https://www.python.org/downloads/)
[![Version 1.4](https://img.shields.io/badge/Version-1.4-brightgreen.svg)]()

## Description

**PCRT3** (PNG Check & Repair Tool) is a tool to help check if PNG image correct and try to auto fix the error. It's cross-platform, which can run on **Windows**, **Linux** and ~~Mac OS~~ (not tested).

It is python3 compatible fork of PCRT (https://github.com/sherlly/PCRT)

**Works only with Python 3.12!**

It can:

    Show image information
    Fix PNG header error
    Fix wrong IHDR chunk crc due to error picture's width or height
    Fix wrong IDAT chunk data length due to DOS->UNIX conversion
    Fix wrong IDAT chunk crc due to its own error
    Fix lost IEND chunk
    Extract data after IEND chunk (Malware programs like use this way to hide)
    Show the repaired image
    Inject payload into image
    Decompress image data and show the raw image
    ...
    Maybe more in the future :)  

## Installation

- #### **Install Python 3.12**

   - [Python](https://www.python.org/downloads/)

- #### **Clone the repo**

```sh
git clone https://github.com/Etr1x/PCRT3.git
cd PCRT3
```

- #### **Install the requirements**

```sh
pip install -r requirements.txt
```

## Usage

    λ py PCRT.py -h
    usage: PCRT.py [-h] [-q] [-y] [-v] [-m] [-n NAME] [-p PAYLOAD] [-w WAY] [-d DECOMPRESS] [-i INPUT] [-f] [-o OUTPUT]
    
    options:
    -h, --help            show this help message and exit
    -q, --quiet           Don't show the banner infomation
    -y, --yes             Auto choose yes
    -v, --verbose         Use the safe way to recover
    -m, --message         Show the image information
    -n NAME, --name NAME  Payload name [Default: random]
    -p PAYLOAD, --payload PAYLOAD
    						Payload to hide
    -w WAY, --way WAY     Payload chunk: [1]: ancillary [2]: critical [Default:1]
    -d DECOMPRESS, --decompress DECOMPRESS
    						Decompress zlib data file name
    -i INPUT, --input INPUT
    						Input file name (*.png) [Select from terminal]
    -f, --file            Input file name (*.png) [Select from window]
    -o OUTPUT, --output OUTPUT
    						Output repaired file name [Default: output.png]

**[Notice]** without `-v` option means that assume all IDAT chunk length are correct

To check png image:

```sh
py PCRT.py -i image.png
```

To print image info:

```sh
py PCRT.py -m -i image.png
```

## Show

- Windows:

![](https://i.imgur.com/rymuZUk.png)

- Linux:

![](https://i.imgur.com/4JhzjZx.png)

## Known problems:

- Decompress option is not tested, probably not working :)
- -v (verbose) mode is always on bc checking in  checkIDAT() method breaks when -v is off, need fix.

## Release Log

### v1.4

- Updated findAncillary() method, now it finds cHRM, pHYs, gAMA, sBIT, PLTE, bKGD, sTER, hIST, iCCP, sPLT, sRGB, dSIG, tIME, tRNS, oFFs, sCAL, fRAc, gIFg, gIFt, gIFx, eXIf, iTXt, tEXt, zTXt chunks.
- Impoved image info output.

### v1.3:

- Fixed checkIHDR() method

### version 1.2:

- Rewrited to support Python 3.12

### v1.1:

**Add：**

- Show image information (`-m`)
- Inject payload into image (`-p`)
   - add into ancillary chunk (chunk name can be randomly generated or self-defined) (`-w 1`)
   - add into critical chunk (only support IDAT chunk) (`-w 2`)

- decompress image data and show the raw image (`-d`)

### v1.0：

**Feature:**

- Fix PNG header error
- Fix wrong IHDR chunk crc due to error picture's width or height
- Fix wrong IDAT chunk data length due to DOS->UNIX conversion
- Fix wrong IDAT chunk crc due to its own error
- Fix lost IEND chunk
- Extract data after IEND chunk (Malware programs like use this way to hide)
- Show the repaired image

---
