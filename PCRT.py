import argparse
import binascii
import itertools
import os
import re
import struct
import zlib

from termcolor import colored

__author__ = "sherlly"
__version__ = "1.4"


def str2hex(s):
    return binascii.hexlify(s).decode().upper()


def int2hex(i):
    return "0x" + hex(i)[2:].upper()


def str2num(s, n=0):
    if n == 4:
        return struct.unpack("!I", s)[0]
    else:
        return int(str2hex(s), 16)


def readImage(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f'{colored('[Error]', 'red')} {e}')
        return -1
    return data


def writeImage(file):
    if os.path.isfile(file) is True:
        os.remove(file)
    file = open(file, "wb+")
    return file


class PNG:
    def __init__(self, in_file="", out_file="output.png", choices="", mode=0) -> None:
        self.in_file = in_file
        self.out_file = out_file
        self.choices = choices
        self.i_mode = mode

    def __del__(self) -> None:
        try:
            self.file.close()
        except AttributeError:
            pass

    def checkFormat(self, data):
        png_feature = [b"PNG", b"IHDR", b"IDAT", b"IEND"]
        status = [True for p in png_feature if p in data]
        if status == []:
            return -1
        return 0

    def loadImage(self):
        data = readImage(self.in_file)
        if data == -1:
            return -1
        status = self.checkFormat(data)
        if status == -1:
            print(
                f'{colored('[Warning]', 'red')
                     } The file may be not a PNG image.'
            )
            return -1
        return data

    def checkHeader(self, data):
        # Header:89 50 4E 47 0D 0A 1A 0A   %PNG....
        header = data[:8]
        if str2hex(header) != "89504E470D0A1A0A":
            print(f'{colored('[Detected]', 'green')} Wrong PNG header!')
            print(f"File header {str2hex(header)}")
            print("Correct header: 89504E470D0A1A0A")
            if self.choices != "":
                choice = self.choices
            else:
                msg = f'{colored('[Notice]', 'yellow')
                         } Auto fixing? (y or n) [default:y] '
                choice = input(msg)
            if choice == "y" or choice == "":
                header = binascii.unhexlify("89504E470D0A1A0A")
                print(f"[Finished] Now header: {str2hex(header)}")
            else:
                return -1
        else:
            print("[Finished] Correct PNG header")
        self.file.write(header)
        return 0

    def findIHDR(self, data):
        pos = data.find(b"IHDR")
        if pos == -1:
            return -1, -1
        idat_begin = data.find(b"IDAT")
        if idat_begin != -1:
            IHDR = data[pos - 4 : idat_begin - 4]
        else:
            IHDR = data[pos - 4 : pos + 21]
        return pos, IHDR

    def getPicInfo(self, ihdr=""):
        """bits: color depth
        mode: 0:gray[1] 2:RGB[3] 3:Indexed[1](with palette) 4:grey & alpha[2] 6:RGBA[4]
        compression: DEFLATE(LZ77+Huffman)
        filter: 0:None 1:sub X-A 2:up X-B 3:average X-(A+B)/2 4:Paeth p = A + B − C
        C B D
        A X.
        """  # noqa: D205
        data = self.loadImage()
        if data == -1:
            return -1
        if ihdr == "":
            pos, IHDR = self.findIHDR(data)
            if pos == -1:
                print(f'{colored('[Detected]', 'green')} Lost IHDR chunk')
                return -1
            length = struct.unpack("!I", IHDR[:4])[0]
            ihdr = IHDR[8 : 8 + length]

        (
            self.width,
            self.height,
            self.bits,
            self.mode,
            self.compression,
            self.filter,
            self.interlace,
        ) = struct.unpack("!iiBBBBB", ihdr)

        self.interlace = int(ihdr[12])
        if self.mode == 0 or self.mode == 3:  # Gray/Index
            self.channel = 1
        elif self.mode == 2:  # RGB
            self.channel = 3
        elif self.mode == 4:  # GA
            self.channel = 2
        elif self.mode == 6:  # RGBA
            self.channel = 4
        else:
            self.channel = 0

        data = self.loadImage()
        if data == -1:
            return -1
        self.txt_content, self.image_content, self.crcs = self.findAncillary(data)

    def printPicInfo(self):
        status = self.getPicInfo()
        if status == -1:
            return -1

        mode_dict = {
            0: "Grayscale",
            2: "RGB",
            3: "Indexed",
            4: "Grayscale with Alpha",
            6: "RGB with Alpha",
        }
        compress_dict = {0: "Deflate"}
        filter_dict = {0: "None", 1: "Sub", 2: "Up", 3: "Average", 4: "Paeth"}
        interlace_dict = {0: "Noninterlaced", 1: "Adam7 interlaced"}
        print(
            "\n-------------------------Image Infomation-------------------------------"
        )
        print(
            f"Image Width: {self.width}\nImage Height: {
                self.height}\nBit Depth: {self.bits}\nChannel: {self.channel}"
        )
        print(f"ColorType: {mode_dict[self.mode]}")
        print(
            f"Interlace: {interlace_dict[self.interlace]}\nFilter method: {
                filter_dict[self.filter]}\nCompression method: {compress_dict[self.compression]}"
        )

        for k in self.image_content:
            if self.image_content[k] != []:
                if k == b"pHYs":
                    print(
                        f"Chunk {k.decode()}: {self.image_content[k][0]}x{self.image_content[k][1]} {self.image_content[k][2]}"
                    )
                elif k == b"gAMA":
                    print(f"Chunk {k.decode()}: {self.image_content[k]}")
                elif k == b"sRGB":
                    print(f"Chunk {k.decode()}: {self.image_content[k]}")
                elif k == b"tIME":
                    print(f"Chunk {k.decode()}: {self.image_content[k]}")
                else:
                    print(f"Chunk {k.decode()}: {str2hex(self.image_content[k][0])}")
            if self.crcs[k] != []:
                if self.crcs[k][1] is not None:
                    print(
                        f"CRC error in chunk {k.decode()} (computed {str2hex(self.crcs[k][0])}, found {str2hex(self.crcs[k][1])})"
                    )

        print("\nContent: ")
        for k in self.txt_content:
            if self.txt_content[k] != []:
                text = ""
                for v in self.txt_content[k]:
                    text_t = v.decode()
                    import re

                    if re.match(r"^[ ]+$", text_t):
                        pass
                    else:
                        text += "\n" + text_t
                print(k.decode() + ": ", text)
        print(
            "------------------------------------------------------------------------"
        )

    def makeCritical(self, name, payload):
        print(
            f'{colored('[Notice]', 'yellow')
                 } Payload chunk name: {name}'
        )
        payload = zlib.compress(payload)
        length = len(payload)
        crc = zlib.crc32((name + payload).encode()) & 0xFFFFFFFF
        data = struct.pack(
            "!I4s%dsI" % (length), length, name.encode(), payload.encode(), crc
        )
        return data

    def ranAncillaryName(self):
        import random
        import string

        name = "".join(random.sample(string.ascii_lowercase, 4))
        return name

    def MakeAncillary(self, name, payload):
        if name is None:
            name = self.ranAncillaryName()
        name = name[0].lower() + name[1:4].upper()
        print(
            f'{colored('[Notice]', 'yellow')
                 } Payload chunk name: {name}'
        )
        length = len(payload)
        crc = zlib.crc32((name + payload).encode()) & 0xFFFFFFFF
        data = struct.pack(
            "!I4s%dsI" % (length), length, name.encode(), payload.encode(), crc
        )
        return data

    def addPayload(self, name, payload, way):
        data = self.loadImage()
        if data == -1:
            return -1
        self.file = writeImage(self.out_file)
        if way == 1:
            # way1:add ancillary
            payload_chunk = self.MakeAncillary(name, payload)
            pos = data.find(b"IHDR")
            self.file.write(data[: pos + 21])
            self.file.write(payload_chunk)
            self.file.write(data[pos + 21 :])
        elif way == 2:
            # way2:add critical chunk:IDAT
            name = b"IDAT"
            payload_chunk = self.MakeCritical(name, payload)
            pos = data.find(b"IEND")
            self.file.write(data[: pos - 4])
            self.file.write(payload_chunk)
            self.file.write(data[pos - 4 :])

    def findAncillary(self, data):
        ancillary = [
            b"cHRM",
            b"pHYs",
            b"gAMA",
            b"sBIT",
            b"PLTE",
            b"bKGD",
            b"sTER",
            b"hIST",
            b"iCCP",
            b"sPLT",
            b"sRGB",
            b"dSIG",
            b"tIME",
            b"tRNS",
            b"oFFs",
            b"sCAL",
            b"fRAc",
            b"gIFg",
            b"gIFt",
            b"gIFx",
        ]
        attach_txt = [b"eXIf", b"iTXt", b"tEXt", b"zTXt"]
        image_content = {}
        crcs = {}
        for data_i in ancillary:
            pos = 0
            image_content[data_i] = []
            crcs[data_i] = []
            while pos != -1:
                pos = data.find(data_i, pos)
                if pos != -1:
                    length = str2num(data[pos - 4 : pos])
                    image_content[data_i].append(data[pos + 4 : pos + 4 + length])
                    crcs[data_i] = data[pos + 4 + length : pos + 4 + length + 4]
                    calculatedcrc = self.checkcrc(
                        data_i, image_content[data_i][0], crcs[data_i]
                    )
                    if calculatedcrc is not None:
                        crcs[data_i] = calculatedcrc, crcs[data_i]
                    else:
                        crcs[data_i] = []
                    pos = pos + 4 + length
                    if data_i == b"pHYs":
                        p_h = struct.unpack(">I", image_content[data_i][0][:4])[0]
                        p_w = struct.unpack(">I", image_content[data_i][0][4:8])[0]
                        unit = image_content[data_i][0][8]
                        if unit == 1:
                            unit = "pixels/meter"
                        else:
                            unit = "unknown unit"
                        image_content[data_i] = p_h, p_w, unit
                    elif data_i == b"sRGB":
                        srgb = image_content[data_i][0]
                        if srgb == b"\x00":
                            srgb = "Perceptual"
                        elif srgb == b"\x01":
                            srgb = "Relative Colorimetric"
                        elif srgb == b"\x02":
                            srgb = "Saturation"
                        elif srgb == b"\x03":
                            srgb = "Absolute Colorimetric"
                        image_content[data_i] = srgb
                    elif data_i == b"gAMA":
                        gama = struct.unpack(">I", image_content[data_i][0][:4])[0]
                        image_content[data_i] = gama / 100000
                    elif data_i == b"tIME":
                        png_timestamp = image_content[data_i][0]
                        year = str2num(png_timestamp[:2])
                        month = png_timestamp[2]
                        day = png_timestamp[3]
                        hour = png_timestamp[4]
                        minute = png_timestamp[5]
                        second = png_timestamp[6]
                        image_content[
                            data_i
                        ] = f"{str(year)}:{str(month).zfill(2)}:{str(day).zfill(2)} {str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"

                    pos += 1

        txt_content = {}
        for text in attach_txt:
            pos = 0
            txt_content[text] = []
            while pos != -1:
                pos = data.find(text, pos)
                if pos != -1:
                    length = str2num(data[pos - 4 : pos])
                    txt_content[text].append(data[pos + 4 : pos + 4 + length])
                    pos += 1
        return txt_content, image_content, crcs

    def checkcrc(self, chunk_type, chunk_data, checksum):
        # check crc
        calc_crc = zlib.crc32(chunk_type + chunk_data)
        calc_crc = struct.pack("!I", calc_crc)
        if calc_crc != checksum:
            return calc_crc
        else:
            return None

    def checkIHDR(self, data):
        # IHDR:length=13(4 bytes)+chunk_type='IHDR'(4 bytes)+chunk_ihdr(length bytes)+crc(4 bytes)
        # chunk_ihdr=width(4 bytes)+height(4 bytes)+left(5 bytes)
        pos, IHDR = self.findIHDR(data)
        if pos == -1:
            print(f'{colored('[Detected]', 'green')} Lost IHDR chunk')
            return -1
        length = struct.unpack("!I", IHDR[:4])[0]
        chunk_type = IHDR[4:8]
        chunk_ihdr = IHDR[8 : 8 + length]

        width, height = struct.unpack("!II", chunk_ihdr[:8])
        crc = IHDR[8 + length : 12 + length]
        # check crc

        calc_crc = self.checkcrc(chunk_type, chunk_ihdr, crc)
        if calc_crc is not None:
            print(
                f'{colored("[Detected]", "green")} Error IHDR CRC found!',
                end="",
            )
            print(f" (offset: {int2hex(pos+4+length)})")
            print(f"Chunk crc: {str2hex(crc)}")
            print(f"Correct crc: {str2hex(calc_crc)}")
            if self.choices != "":
                choice = self.choices
            else:
                msg = f'{colored("[Notice]", "yellow")
                         } Try fixing it? (y or n) [default:y] '
                choice = input(msg)
            crcFound = False
            if choice == "y" or choice == "":
                print("Bruteforcing dimensions...")
                for w in range(width + height + 1000):
                    for h in range(width + height + 1000):
                        chunk_ihdr = (
                            struct.pack(">I", w) + struct.pack(">I", h) + IHDR[16:21]
                        )
                        if self.checkcrc(chunk_type, chunk_ihdr, crc) is None:
                            crcFound = True
                            IHDR = IHDR[:8] + chunk_ihdr + crc
                            print(
                                f"[Finished] Found correct dimensions:\nWidth: {w}\nHeight: {h}"
                            )
                            print("[Finished] Successfully fix crc")
                            break
            if not crcFound:
                print(
                    f"{colored('[Error]', 'red')} Exhausted all dimensions up to ({width+height+1000}, {width+height+1000})"
                )
        else:
            print(
                f"[Finished] Correct IHDR (offset: {int2hex(
                    pos+4+length)}): {str2hex(crc)}"
            )

        self.file.write(IHDR)
        print(f"[Finished] IHDR chunk check complete (offset: {int2hex(pos-4)})")

        self.getPicInfo(ihdr=chunk_ihdr)

    def fixDos2Unix(self, chunk_type, chunk_data, crc, count):
        pos = -1
        pos_list = []
        while True:
            pos = chunk_data.find(b"\x0A", pos + 1)
            if pos == -1:
                break
            pos_list.append(pos)
        fix = b"\x0D"
        tmp = chunk_data
        for pos_all in itertools.combinations(pos_list, count):
            i = 0
            chunk_data = tmp
            for pos in pos_all:
                chunk_data = chunk_data[: pos + i] + fix + chunk_data[pos + i :]
                i += 1
            # check crc
            if self.checkcrc(chunk_type, chunk_data, crc) is None:
                # fix success
                return chunk_data
        return None

    def checkIDAT(self, data):
        # IDAT:length(4 bytes)+chunk_type='IDAT'(4 bytes)+chunk_data(length bytes)+crc(4 bytes)
        IDAT_table = []
        idat_begin = data.find(b"IDAT") - 4
        if idat_begin == -1:
            print(f'{colored("[Detected]", "green")} Lost all IDAT chunk!')
            return -1, ""
        # breaking idk why need fix
        # if self.i_mode == 0:
        #     # fast: assume both chunk length are true
        #     idat_size = struct.unpack('!I', data[idat_begin:idat_begin+4])[0]+12
        #     for i in range(idat_begin, len(data) - 12, idat_size):
        #         datalen = len(data)
        #         if i > len(data):
        #             # the last IDAT chunk
        #             IDAT_table.append(data[i:-12])
        #             break

        #         IDAT_table.append(data[i:i+idat_size])

        elif self.i_mode == 1 or self.i_mode == 0:
            # slow but safe
            pos_IEND = data.find(b"IEND")
            if pos_IEND != -1:
                pos_list = [
                    g.start()
                    for g in re.finditer(b"IDAT", data)
                    if g.start() < pos_IEND
                ]
            else:
                pos_list = [g.start() for g in re.finditer(b"IDAT", data)]
            for i in range(len(pos_list)):
                # split into IDAT
                if i + 1 == len(pos_list):
                    # IEND
                    pos1 = pos_list[i]
                    if pos_IEND != -1:
                        IDAT_table.append(data[pos1 - 4 : pos_IEND - 4])
                    else:
                        IDAT_table.append(data[pos1 - 4 :])
                    break
                pos1 = pos_list[i]
                pos2 = pos_list[i + 1]
                IDAT_table.append(data[pos1 - 4 : pos2 - 4])

        offset = idat_begin
        IDAT_data_table = []
        for IDAT in IDAT_table:
            length = struct.unpack("!I", IDAT[:4])[0]
            chunk_type = IDAT[4:8]
            chunk_data = IDAT[8:-4]
            crc = IDAT[-4:]
            # check data length
            if length != len(chunk_data):
                print(
                    f'{colored("[Detected]", "green")} Error IDAT chunk data length! (offset: {
                        int2hex(offset)})'
                )
                print(f"chunk length: {int2hex(length)}")
                print(f"correct chunk length: {int2hex(len(chunk_data))}")
                if self.choices != "":
                    choice = self.choices
                else:
                    msg = f'{colored("[Notice]", "yellow")
                             } Try fixing it? (y or n) [default:y] '
                    choice = input(msg)
                if choice == "y" or choice == "":
                    print(
                        f'{colored('[Warning]', 'red')
                           } Only fix because of DOS->Unix conversion'
                    )
                    # error reason:DOS->Unix conversion
                    chunk_data = self.fixDos2Unix(
                        chunk_type,
                        chunk_data,
                        crc,
                        count=abs(length - len(chunk_data)),
                    )
                    if chunk_data is None:
                        print(
                            f'{colored(
                                "[Failed]", "red")} Fix IDAT chunk failed, auto discard this operation... '
                        )
                        chunk_data = IDAT[8:-4]
                    else:
                        IDAT = IDAT[:8] + chunk_data + IDAT[-4:]
                        print("[Finished] Successfully recover IDAT chunk data")
            else:
                print(
                    f"[Finished] Correct IDAT chunk data length (offset: {int2hex(offset)}, length: {
                        int2hex(length)[2:]})"
                )
                # check crc
                calc_crc = self.checkcrc(chunk_type, chunk_data, crc)
                if calc_crc is not None:
                    print(
                        f'{colored("[Detected]", "green")} Error IDAT CRC found! (offset: {
                            int2hex(offset+8+length)}'
                    )
                    print(f"chunk crc: {str2hex(crc)}")
                    print(f"correct crc: {str2hex(calc_crc)}")
                    if self.choices != "":
                        choice = self.choices
                    else:
                        msg = f'{colored("[Notice]", "yellow")
                                 } Try fixing it? (y or n) [default:y] '
                        choice = input(msg)
                    if choice == "y" or choice == "":
                        IDAT = IDAT[:-4] + calc_crc
                        print("[Finished] Successfully fix CRC")

                else:
                    print(
                        f"[Finished] Correct IDAT CRC (offset: {int2hex(
                            offset+8+length)}): {str2hex(crc)}"
                    )

            # write into file
            self.file.write(IDAT)
            IDAT_data_table.append(chunk_data)
            offset += len(chunk_data) + 12
        print(
            f"[Finished] IDAT chunk check complete (offset: {
              int2hex(idat_begin)})"
        )
        return 0, IDAT_data_table

    def checkIEND(self, data):
        # IEND:length=0(4 bytes)+chunk_type='IEND'(4 bytes)+crc=AE426082(4 bytes)
        standard_IEND = b"\x00\x00\x00\x00IEND\xae\x42\x60\x82"
        pos = data.find(b"IEND")
        if pos == -1:
            print(
                f'{colored('[Detected]', 'green')
                   } Lost IEND chunk! Try auto fixing...'
            )
            IEND = standard_IEND
            print(f"[Finished] Now IEND chunk: {str2hex(IEND)}")
        else:
            IEND = data[pos - 4 : pos + 8]
            if IEND != standard_IEND:
                print(
                    f'{colored("[Detected]", "green")
                       } Error IEND chunk! Try auto fixing...'
                )
                IEND = standard_IEND
                print(f"[Finished] Now IEND chunk: {str2hex(IEND)}")
            else:
                print("[Finished] Correct IEND chunk")
            data[pos + 8 :]

            if data[pos + 8 :] != b"":
                print(
                    f'{colored('[Detected]', 'green')} Some data (length: {
                        len(data[pos+8:])}) append in the end ({data[pos+8:pos+18]})'
                )
                while True:
                    msg = f'{colored(
                        "[Notice]", "yellow")} Try extracting them in: <1>File <2>Terminal <3>Quit [default:3] '
                    choice = input(msg)
                    if choice == "1":
                        filename = input("[File] Input the file name: ")
                        file = writeImage(filename)
                        file.write(data[pos + 8 :])
                        file.close()
                        print(f"[Finished] Successfully write in {filename}")
                        # os.startfile(os.getcwd())
                    elif choice == "2":
                        print(f"data: {data[pos+8:]}")
                        print(
                            f"hex(data): {
                              binascii.hexlify(data[pos+8:]).decode()}"
                        )
                    elif choice == "3" or choice == "":
                        break
                    else:
                        print(
                            f'{colored("[Error]", "red")
                                 } Invalid choice! Try again.'
                        )

        self.file.write(IEND)
        print("[Finished] IEND chunk check complete")
        return 0

    def checkPNG(self):
        data = self.loadImage()
        if data == -1:
            return -1

        self.file = writeImage(self.out_file)

        res = self.checkHeader(data)
        if res == -1:
            print("[Finished] PNG check complete")
            return -1
        res = self.checkIHDR(data)
        if res == -1:
            print("[Finished] PNG check complete")
            return -1
        res, idat = self.checkIDAT(data)
        if res == -1:
            print("[Finished] PNG check complete")
            return -1
        self.checkIEND(data)
        print("[Finished] PNG check complete")

        """check complete"""

        if self.choices != "":
            choice = self.choices
        else:
            msg = f'{colored("[Notice]", "yellow")
                     } Show the repaired image? (y or n) [default:n] '
            choice = input(msg)
        if choice == "y":
            try:
                from PIL import Image

                img = Image.open(self.out_file)
                img.show()
            except ImportError as e:
                print(f'{colored("[Error]", "red")} {e}')
                print("Try 'pip install PIL' to use it")
        return 0

    def zlib_decrypt(self, data):
        # Use in IDAT decompress
        z_data = zlib.decompress(data)
        return z_data

    def clearFilter(self, idat, width, height, channel, bits=8):
        IDAT = ""
        tmp = []
        if len(idat) == height * width * channel:
            return idat

        filter_unit = bits / 8 * channel
        for i in range(0, len(idat), width * channel + 1):
            line_filter = str2num(idat[i])
            idat_data = idat[i + 1 : i + width * channel + 1]
            if i >= 1:
                idat_data_u = tmp
            else:
                idat_data_u = [0] * width * channel

            if line_filter not in [0, 1, 2, 3, 4]:
                return -1

            if line_filter == 0:  # None
                tmp = list(idat_data)
                IDAT += "".join(tmp)

            elif line_filter == 1:  # Sub
                k = 0
                tmp = list(idat_data)
                for j in range(filter_unit, len(idat_data)):
                    tmp[j] = chr((ord(idat_data[j]) + ord(tmp[k])) % 256)
                    k += 1
                IDAT += "".join(tmp)

            elif line_filter == 2:  # Up
                tmp = ""
                for j in range(len(idat_data)):
                    tmp += chr((ord(idat_data[j]) + ord(idat_data_u[j])) % 256)
                IDAT += tmp
                tmp = list(tmp)

            elif line_filter == 3:  # Average
                tmp = list(idat_data)
                k = -filter_unit
                for j in range(len(idat_data)):
                    if k < 0:
                        a = 0
                    else:
                        a = ord(tmp[k])
                    tmp[j] = chr(
                        (ord(idat_data[j]) + (a + ord(idat_data_u[j])) / 2) % 256
                    )
                    k += 1
                IDAT += "".join(tmp)

            elif line_filter == 4:  # Paeth

                def predictor(a, b, c):
                    """A = left, b = above, c = upper left."""
                    p = a + b - c
                    pa = abs(p - a)
                    pb = abs(p - b)
                    pc = abs(p - c)
                    if pa <= pb and pa <= pc:
                        return a
                    elif pb <= pc:
                        return b
                    else:
                        return c

                k = -filter_unit
                tmp = list(idat_data)
                for j in range(len(idat_data)):
                    if k < 0:
                        a = c = 0
                    else:
                        a = ord(tmp[k])
                        c = ord(idat_data_u[k])
                    tmp[j] = chr(
                        (ord(idat_data[j]) + predictor(a, ord(idat_data_u[j]), c)) % 256
                    )
                    k += 1
                IDAT += "".join(tmp)
        return IDAT

    def decompressPNG(self, data, channel=3, bits=8, width=1, height=1):
        # data: array[idat1, idat2, ...]
        from PIL import Image

        IDAT_data = b""
        for idat in data:
            IDAT_data += idat.to_bytes(1, "big")
        z_idat = self.zlib_decrypt(IDAT_data)
        length = len(z_idat)

        if width == 0 and height == 0:
            # bruteforce
            import shutil

            channel_dict = {1: "L", 3: "RGB", 2: "LA", 4: "RGBA"}
            PATH = "tmp/"
            if os.path.isdir(PATH) is True:
                shutil.rmtree(PATH)
            os.mkdir(PATH)
            for bits in [8, 16]:
                for channel in [4, 3, 1, 2]:
                    size_list = []
                    for i in range(1, length):
                        if length % i == 0:
                            if (i - 1) % (bits / 8 * channel) == 0:
                                size_list.append((i - 1) / (bits / 8 * channel))
                                size_list.append(length / i)
                            if (length / i - 1) % (bits / 8 * channel) == 0:
                                size_list.append(
                                    (length / i - 1) / (bits / 8 * channel)
                                )
                                size_list.append(i)
                    for i in range(0, len(size_list), 2):
                        width = size_list[i]
                        height = size_list[i + 1]
                        tmp = self.ClearFilter(z_idat, width, height, channel, bits)
                        if tmp != -1:
                            img = Image.frombytes(
                                channel_dict[channel], (width, height), tmp
                            )
                            # img.show()
                            filename = PATH + "test(%dx%d)_%dbits_%dchannel.png" % (
                                width,
                                height,
                                bits,
                                channel,
                            )
                            img.save(filename)

            # show all possible image
            os.startfile(os.getcwd() + "/" + PATH)
            # final size
            size = input(
                "Input width, height, bits and channel(space to split):"
            ).split()
            # remove temporary file
            shutil.rmtree(PATH)

            width = int(size[0])
            height = int(size[1])
            bits = int(size[2])
            channel = int(size[3])
            tmp = self.clearFilter(z_idat, width, height, channel, bits)
            if tmp == -1:
                print("Wrong")
                return -1
            img = Image.frombytes(channel_dict[channel], (width, height), tmp)
            img.save("decompress.png")


if __name__ == "__main__":
    msg = rf"""
     ____   ____ ____ _____
    |  _ \ / ___|  _ \_   _|
    | |_) | |   | |_) || |
    |  __/| |___|  _ < | |
    |_|    \____|_| \_\|_|

    PNG Check & Repair Tool

Project address: https://github.com/Etr1x/PCRT3
Original Author: sherlly
Python3 support by: etr1x
Version: {__version__}
"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Don't show the banner infomation",
    )
    parser.add_argument("-y", "--yes", help="Auto choose yes", action="store_true")
    parser.add_argument(
        "-v",
        "--verbose",
        help="Use the safe way to recover",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Show the image information",
        action="store_true",
    )
    parser.add_argument("-n", "--name", help="Payload name [Default: random]")
    parser.add_argument("-p", "--payload", help="Payload to hide")
    parser.add_argument(
        "-w",
        "--way",
        type=int,
        default=1,
        help="Payload chunk: [1]: ancillary [2]: critical [Default:1]",
    )

    parser.add_argument("-d", "--decompress", help="Decompress zlib data file name")

    parser.add_argument(
        "-i", "--input", help="Input file name (*.png) [Select from terminal]"
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Input file name (*.png) [Select from window]",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.png",
        help="Output repaired file name [Default: output.png]",
    )
    args = parser.parse_args()

    in_file = args.input
    out_file = args.output
    payload = args.payload
    payload_name = args.name
    z_file = args.decompress

    if args.quiet is not True:
        print(msg)

    if z_file is not None:
        z_data = readImage(z_file)
        my_png = PNG()
        my_png.decompressPNG(z_data, width=0, height=0)
    else:
        if args.verbose is True:
            mode = 1
        else:
            mode = 0
        if args.file is True:
            try:
                import tkinter
                import tkinter.filedialog

                root = tkinter.Tk()
                in_file = tkinter.filedialog.askopenfilename()
                root.destroy()
                if args.yes is True:
                    my_png = PNG(in_file, out_file, choices="y", mode=mode)
                else:
                    my_png = PNG(in_file, out_file, mode=mode)
                if args.message is True:
                    my_png.printPicInfo()
                elif payload is not None:
                    way = args.way
                    my_png.addPayload(payload_name, payload, way)
                else:
                    my_png.checkPNG()
            except ImportError as e:
                print(f"{colored('[Error]', 'red')} {e[1]})")
                print("Try 'pip install Tkinter' to use it")
        elif in_file is not None:
            if args.yes is True:
                my_png = PNG(in_file, out_file, choices="y", mode=mode)
            else:
                my_png = PNG(in_file, out_file, mode=mode)
            if args.message is True:
                my_png.printPicInfo()
            elif payload is not None:
                way = args.way
                my_png.addPayload(payload_name, payload, way)
            else:
                my_png.checkPNG()
        else:
            parser.print_help()
