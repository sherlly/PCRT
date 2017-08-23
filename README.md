# PCRT (PNG Check & Repair Tool)
[![Python 2.7](https://img.shields.io/badge/Python-2.7-blue.svg)](https://www.python.org/downloads/) 
[![Version 1.1](https://img.shields.io/badge/Version-1.1-brightgreen.svg)]() 

## Description

**PCRT** (PNG Check & Repair Tool) is a tool to help check if PNG image correct and try to auto fix the error. It's cross-platform, which can run on **Windows**, **Linux** and **Mac OS**. 

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


## Install

- #### **Install Python 2.7**
	- [Python 2.7](https://www.python.org/downloads/)

- #### **Install Python dependency packages**
	- Tkinter
	- [PIL](https://pypi.python.org/pypi/PIL/1.1.6)
	- ctypes (For Windows)


- #### **Clone the source code**

		git clone https://github.com/sherlly/PCRT.git
		cd PCRT
		python PCRT.py

## Usage

	> python PCRT.py -h
	usage: PCRT.py [-h] [-q] [-y] [-v] [-m] [-n NAME] [-p PAYLOAD] [-w WAY]
                 [-d DECOMPRESS] [-i INPUT] [-f] [-o OUTPUT]

	optional arguments:
    -h, --help            show this help message and exit
    -q, --quiet           don't show the banner infomation
    -y, --yes             auto choose yes
    -v, --verbose         use the safe way to recover
    -m, --message         show the image information
    -n NAME, --name NAME  payload name [Default: random]
    -p PAYLOAD, --payload PAYLOAD
                          payload to hide
    -w WAY, --way WAY     payload chunk: [1]: ancillary [2]: critical
                          [Default:1]
    -d DECOMPRESS, --decompress DECOMPRESS
                          decompress zlib data file name
    -i INPUT, --input INPUT
                          Input file name (*.png) [Select from terminal]
    -f, --file            Input file name (*.png) [Select from window]
    -o OUTPUT, --output OUTPUT
                          Output repaired file name [Default: output.png]

**[Notice]** without `-v` option means that assume all IDAT chunk length are correct


## Show

- Window:

![](http://i.imgur.com/Ksk2ctV.png)

- Linux:

![](http://i.imgur.com/ZXnPqYD.png)

- Mac OS:

![](http://i.imgur.com/re4gQux.png)

## Some Problem:

- For Window:

> Can't show the repaired image

1. Find the file named `ImageShow.py` under the path like `X:\Python27\lib\site-packages\PIL\ImageShow.py`
2. Find the code `return "start /wait %s && ping -n 2 127.0.0.1 >NUL && del /f %s" % (file, file)` around line 100 and commented it
3. Add the new code: `return "start /wait %s && PING 127.0.0.1 -n 5 > NUL && del /f %s" % (file, file)` and save
4. Restart the python IDE

## Release Log

### version 1.1:


**Add：**

- Show image information (`-m`)
- Inject payload into image (`-p`)
	- add into ancillary chunk (chunk name can be randomly generated or self-defined) (`-w 1`)
	- add into critical chunk (only support IDAT chunk) (`-w 2`)
- decompress image data and show the raw image (`-d`)

### version 1.0：

**Feature:**

- Fix PNG header error
- Fix wrong IHDR chunk crc due to error picture's width or height
- Fix wrong IDAT chunk data length due to DOS->UNIX conversion
- Fix wrong IDAT chunk crc due to its own error
- Fix lost IEND chunk
- Extract data after IEND chunk (Malware programs like use this way to hide)
- Show the repaired image
---

## 项目描述

**PCRT** (PNG Check & Repair Tool) 工具旨在实现检查并自动化修复损坏的PNG图像。 支持在**Windows/Linux/Mac OS**平台使用。

它可以实现：

	显示图片文件信息
	修复PNG文件头错误
	修复由于错误的图片长度或宽度导致的IHDR块crc校验出错
	修复由于DOS->UNIX平台自动格式转换导致的部分IDAT块数据长度出错
	修复由于自身错误导致的IDAT块crc校验出错
	修复丢失的IEND块
	提取追加在IEND块后的数据（恶意程序常使用的传播方式）
	自动显示修复后的图片
	添加payload到图片文件
	解析图片压缩数据并显示
	...
	更多功能有待开发：）
	


## 安装

- #### **安装 Python 2.7**
	- [Python 2.7](https://www.python.org/downloads/)

- #### **安装需要的Python 依赖包**
	- Tkinter
	- [PIL](https://pypi.python.org/pypi/PIL/1.1.6)
	- ctypes (For Windows)


- #### **拷贝源码到本地**

		git clone https://github.com/sherlly/PCRT.git
		cd PCRT
		python PCRT.py

## 使用方法

	> python PCRT.py -h
	usage: PCRT.py [-h] [-q] [-y] [-v] [-m] [-n NAME] [-p PAYLOAD] [-w WAY]
                 [-d DECOMPRESS] [-i INPUT] [-f] [-o OUTPUT]

	optional arguments:
    -h, --help            show this help message and exit
    -q, --quiet           don't show the banner infomation
    -y, --yes             auto choose yes
    -v, --verbose         use the safe way to recover
    -m, --message         show the image information
    -n NAME, --name NAME  payload name [Default: random]
    -p PAYLOAD, --payload PAYLOAD
                          payload to hide
    -w WAY, --way WAY     payload chunk: [1]: ancillary [2]: critical
                          [Default:1]
    -d DECOMPRESS, --decompress DECOMPRESS
                          decompress zlib data file name
    -i INPUT, --input INPUT
                          Input file name (*.png) [Select from terminal]
    -f, --file            Input file name (*.png) [Select from window]
    -o OUTPUT, --output OUTPUT
                          Output repaired file name [Default: output.png]

**[注意]** 如果不添加 `-v` 选项则默认所有IDAT块长度均合法， 即不出现声明的IDAT数据块长度和实际数据长度不符合的情况。


## 示例

- Window:

![](http://i.imgur.com/Ksk2ctV.png)

- Linux:

![](http://i.imgur.com/ZXnPqYD.png)

- Mac OS:

![](http://i.imgur.com/re4gQux.png)

## 可能出现的一些问题

- Window下：

> 出现修复后图片无法显示时：

1. 找到Python安装路径下的文件 `X:\Python27\lib\site-packages\PIL\ImageShow.py`
2. 将在100行左右的代码`return "start /wait %s && ping -n 2 127.0.0.1 >NUL && del /f %s" % (file, file)`注释掉
3. 添加代码：`return "start /wait %s && PING 127.0.0.1 -n 5 > NUL && del /f %s" % (file, file)`并保存
4. 重启运行python的IDE

## 更新日志

### version 1.1:


**增加：**

- 显示图片文件信息（`-m`）
- 添加payload到图片文件（`-p`）
	- 支持添加到辅助块（块名可随机生成或自定义）（`-w 1`）
	- 支持添加到关键块（仅支持IDAT）(`-w 2`)
- 解析图片压缩数据并显示（`-d`）

### version 1.0：

**特性：**

- 实现修复PNG文件头错误
- 实现修复由于错误的图片长度或宽度导致的IHDR块crc校验出错
- 实现修复由于DOS->UNIX平台自动格式转换导致的部分IDAT块数据长度出错
- 实现修复由于自身错误导致的IDAT块crc校验出错
- 实现修复丢失的IEND块
- 实现提取追加在IEND块后的数据（恶意程序常使用的传播方式）
- 实现自动显示修复后的图片