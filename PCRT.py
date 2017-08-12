# -*- coding:utf-8 -*-
__author__="sherlly"
__version__="1.0"

import zlib
import struct
import re
import os
import argparse
import itertools
import platform
import sys


if platform.system() == "Windows":
	import ctypes
	STD_OUTPUT_HANDLE = -11
	FOREGROUND_BLUE = 0x09
	FOREGROUND_GREEN = 0x0a
	FOREGROUND_RED = 0x0c
	FOREGROUND_SKYBLUE = 0x0b
	std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

	def set_cmd_text_color(color, handle=std_out_handle):
		status = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
		return status

	def resetColor():
		set_cmd_text_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)

	def printRed(msg):
		set_cmd_text_color(FOREGROUND_RED)
		sys.stdout.write(msg)
		resetColor()

	def printSkyBlue(msg):
		set_cmd_text_color(FOREGROUND_SKYBLUE)
		sys.stdout.write(msg)
		resetColor()

	def printGreen(msg):
		set_cmd_text_color(FOREGROUND_GREEN)
		sys.stdout.write(msg)
		resetColor()	

def str2hex(s):
	return s.encode('hex').upper()

def int2hex(i):
	return '0x'+hex(i)[2:].upper()

def WriteFile(filename):
	if os.path.isfile(filename)==True:
		os.remove(filename)
	file = open(filename,'wb+')
	return file

def ReadFile(filename):
	try:
		with open(filename,'rb') as file:
			data=file.read()
	except IOError,e:
		print Termcolor('Error',e[1]+': '+filename)
		return -1
	return data


def Termcolor(flag,sentence):
	# check platform
	system=platform.system()
	if system == 'Linux' or system == 'Darwin':
		if flag=='Notice':
			return "\033[0;34m[%s]\033[0m %s" % (flag,sentence)
		elif flag=='Detected':
			return "\033[0;32m[%s]\033[0m %s" % (flag,sentence)
		elif flag=='Error' or flag == 'Warning' or flag == 'Failed':
			return "\033[0;31m[%s]\033[0m %s" % (flag,sentence)
	elif system=='Windows':
		try:
			import ctypes
			if flag=='Notice':
				printSkyBlue('[%s] '%flag)
				return sentence
			elif flag=='Detected':
				printGreen('[%s] '%flag)
				return sentence
			elif flag=='Error' or flag == 'Warning' or flag == 'Failed':
				printRed('[%s] '%flag)
				return sentence
		except ImportError,e:
			print '[Error]',e
			print 'Using the normal color to show...'
			return "[%s] %s" % (flag,sentence)
	else:
		return "[%s] %s" % (flag,sentence)



class PNG(object):
	
	def __init__(self,in_file,out_file='output.png',choices='',mode=0):
		self.in_file=in_file
		self.out_file=out_file
		self.choices=choices
		self.mode=mode
	
	def __del__(self):
		try:
			self.file.close()
		except AttributeError:
			pass

	def CheckPNG(self):
		data=ReadFile(self.in_file)
		if data == -1:
			return -1
		status=self.CheckFormat(data)
		if status == -1:
			print Termcolor('Warning','The file may be not a PNG image.')
		self.file=WriteFile(self.out_file)
		res=self.CheckHeader(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1
		res=self.CheckIHDR(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1
		res=self.CheckIDAT(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1
		self.CheckIEND(data)
		print '[Finished] PNG check complete'
		if self.choices != '':
			choice=self.choices
		else:
			msg=Termcolor('Notice','Show the repaired image? (y or n) [default:y] ')
			choice=raw_input(msg)
		if choice == 'y' or choice == '':
			try:
				from PIL import Image
				self.file.close()
				img=Image.open(self.out_file)
				img.show()
			except ImportError,e:
				print Termcolor('Error',e)
				print "Try 'pip install PIL' to use it"
		return 0


	def zlib_decrypt(self,data):
		# Use in IDAT decompress
		z_data=zlib.decompress(data)
		return z_data

	def Checkcrc(self,chunk_type,chunk_data, checksum):
		# CRC-32 computed over the chunk type and chunk data, but not the length
		calc_crc = zlib.crc32(chunk_type+chunk_data) & 0xffffffff
		calc_crc = struct.pack('!I', calc_crc)
		if calc_crc != checksum:
			return calc_crc
		else:
			return None

	def CheckFormat(self,data):
		png_feature=['PNG','IHDR','IDAT','IEND']
		status = [True for p in png_feature if p in data]
		if status == []:
			return -1
		return 0

	def CheckHeader(self,data):
		# Header:89 50 4E 47 0D 0A 1A 0A   %PNG....
		Header=data[:8]
		if str2hex(Header)!='89504E470D0A1A0A':
			print Termcolor('Detected','Wrong PNG header!')
			print 'File header: %s\nCorrect header: 89504E470D0A1A0A'%(str2hex(Header))
			if self.choices != '':
				choice=self.choices
			else:
				msg = Termcolor('Notice','Auto fixing? (y or n) [default:y] ')
				choice=raw_input(msg)
			if choice == 'y' or choice == '':
				Header='89504E470D0A1A0A'.decode('hex')
				print '[Finished] Now header:%s'%(str2hex(Header))
			else:
				return -1
		else:
			print '[Finished] Correct PNG header'
		self.file.write(Header)
		return 0

	def CheckIHDR(self,data):
		# IHDR:length=13(4 bytes)+chunk_type='IHDR'(4 bytes)+chunk_ihdr(length bytes)+crc(4 bytes)
		# chunk_ihdr=width(4 bytes)+height(4 bytes)+left(5 bytes)
		pos=data.find('IHDR')
		if pos == -1:
			print Termcolor('Detected','Lost IHDR chunk')
			return -1
		idat_begin=data.find('IDAT')
		if idat_begin != -1:
			IHDR=data[pos-4:idat_begin-4]
		else:
			IHDR=data[pos-4:pos+21]
		length=struct.unpack('!I',IHDR[:4])[0]
		chunk_type=IHDR[4:8]
		chunk_ihdr=IHDR[8:8+length]
		width=struct.unpack('!I',chunk_ihdr[:4])[0]
		height=struct.unpack('!I',chunk_ihdr[4:8])[0]
		crc=IHDR[8+length:12+length]
		# check crc
		calc_crc = self.Checkcrc(chunk_type,chunk_ihdr,crc)
		if calc_crc != None:
			print Termcolor('Detected','Error IHDR CRC found! (offset: %s)\nchunk crc: %s\ncorrect crc: %s'%(int2hex(pos+4+length),str2hex(crc),str2hex(calc_crc)))
			if self.choices != '':
				choice=self.choices
			else:
				msg = Termcolor('Notice','Try fixing it? (y or n) [default:y] ')
				choice = raw_input(msg)
			if choice == 'y' or choice=='':
				if width > height:
					# fix height
					for h in xrange(height,width):
						chunk_ihdr=IHDR[8:12]+struct.pack('!I',h)+IHDR[16:8+length]
						if self.Checkcrc(chunk_type,chunk_ihdr,crc) == None:
							IHDR=IHDR[:8]+chunk_ihdr+crc
							print '[Finished] Successfully fix crc'
							break
				else:
					# fix width
					for w in xrange(width,height):
						chunk_ihdr=struct.pack('!I',w)+IHDR[12:8+length]
						if self.Checkcrc(chunk_type,chunk_ihdr,crc) == None:
							IHDR=IHDR[:8]+chunk_ihdr+crc
							print '[Finished] Successfully fix crc'
							break
		else:
			print '[Finished] Correct IHDR CRC (offset: %s): %s'% (int2hex(pos+4+length),str2hex(crc))
		self.file.write(IHDR)
		print '[Finished] IHDR chunk check complete (offset: %s)'%(int2hex(pos-4))


	def CheckIDAT(self,data):
		# IDAT:length(4 bytes)+chunk_type='IDAT'(4 bytes)+chunk_data(length bytes)+crc(4 bytes)
		IDAT_table = []
		idat_begin = data.find('49444154'.decode('hex'))-4
		if idat_begin == -1:
			print Termcolor('Detected','Lost all IDAT chunk!')
			return -1
		if self.mode == 0:
			# fast: assume both chunk length are true
			idat_size=struct.unpack('!I',data[idat_begin:idat_begin+4])[0]+12
			for i in xrange(idat_begin,len(data)-12,idat_size): 
				IDAT_table.append(data[i:i+idat_size])
			if i < len(data)-12:
				# the last IDAT chunk
				IDAT_table.append(data[i:-12])
		elif self.mode == 1:
			# slow but safe
			pos_IEND=data.find('IEND')
			if pos_IEND != -1:
				pos_list = [g.start() for g in re.finditer('IDAT',data) if g.start() < pos_IEND]
			else:
				pos_list = [g.start() for g in re.finditer('IDAT',data)]
			for i in range(len(pos_list)):
				# split into IDAT
				if i+1 == len(pos_list):
					# IEND
					pos1=pos_list[i]
					if pos_IEND != -1:
						IDAT_table.append(data[pos1-4:pos_IEND-4])
					else:
						IDAT_table.append(data[pos1-4:])
					break
				pos1=pos_list[i]
				pos2=pos_list[i+1]
				IDAT_table.append(data[pos1-4:pos2-4])

		offset=idat_begin
		for IDAT in IDAT_table:
			length=struct.unpack('!I',IDAT[:4])[0]
			chunk_type=IDAT[4:8]
			chunk_data=IDAT[8:-4]
			crc=IDAT[-4:]
			# check data length
			if length != len(chunk_data):
				print Termcolor('Detected','Error IDAT chunk data length! (offset: %s)'%(int2hex(offset)))
				print 'chunk length:%s\nactual length:%s'%(int2hex(length)[2:],int2hex(len(chunk_data))[2:])
				if self.choices != '':
					choice=self.choices
				else:				
					msg = Termcolor('Notice','Try fixing it? (y or n) [default:y] ')
					choice=raw_input(msg)
				if choice == 'y' or choice == '':
					print Termcolor('Warning','Only fix because of DOS->Unix conversion')
					# error reason:DOS->Unix conversion
					chunk_data=self.FixDos2Unix(chunk_type,chunk_data,crc,count=abs(length-len(chunk_data)))
					if chunk_data == None:
						print Termcolor('Failed','Fixing failed, auto discard this operation...')
						chunk_data=IDAT[8:-4]
					else:
						IDAT=IDAT[:8]+chunk_data+IDAT[-4:]
						print '[Finished] Successfully recover IDAT chunk data'
			else:
				print '[Finished] Correct IDAT chunk data length (offset: %s length: %s)'%(int2hex(offset),int2hex(length)[2:])
				# check crc
				calc_crc = self.Checkcrc(chunk_type,chunk_data,crc)
				if calc_crc != None:
					print Termcolor('Detected','Error IDAT CRC found! (offset: %s)\nchunk crc: %s\ncorrect crc: %s'%(int2hex(offset+8+length),str2hex(crc),str2hex(calc_crc)))
					if self.choices != '':
						choice=self.choices
					else:		
						msg = Termcolor('Notice','Try fixing it? (y or n) [default:y] ')
						choice = raw_input(msg)
					if choice == 'y' or choice == '':
						IDAT=IDAT[:-4]+calc_crc
						print '[Finished] Successfully fix crc'

				else:
					print '[Finished] Correct IDAT CRC (offset: %s): %s'% (int2hex(offset+8+length),str2hex(crc))

			# write into file
			self.file.write(IDAT)
			offset+=len(chunk_data)+12
		print '[Finished] IDAT chunk check complete (offset: %s)'%(int2hex(idat_begin))
		return 0

	def FixDos2Unix(self,chunk_type,chunk_data,crc,count):
		pos=-1
		pos_list=[]
		while True:
			pos=chunk_data.find('\x0A',pos+1)
			if pos == -1:
				break
			pos_list.append(pos)
		fix='\x0D'
		tmp=chunk_data
		for pos_all in itertools.combinations(pos_list,count): 
			i=0
			chunk_data=tmp
			for pos in pos_all:
				chunk_data=chunk_data[:pos+i]+fix+chunk_data[pos+i:]
				i+=1
			# check crc
			if self.Checkcrc(chunk_type,chunk_data,crc) == None:
				# fix success
				return chunk_data
		return None


	def CheckIEND(self,data):
		# IEND:length=0(4 bytes)+chunk_type='IEND'(4 bytes)+crc=AE426082(4 bytes)
		standard_IEND='\x00\x00\x00\x00IEND\xae\x42\x60\x82'
		pos=data.find('IEND')
		if pos == -1:
			print Termcolor('Detected','Lost IEND chunk! Try auto fixing...')
			IEND=standard_IEND
			print '[Finished] Now IEND chunk:%s'%(str2hex(IEND))
		else:
			IEND=data[pos-4:pos+8]
			if IEND != standard_IEND:
				print Termcolor('Detected','Error IEND chunk! Try auto fixing...')
				IEND=standard_IEND
				print '[Finished] Now IEND chunk:%s'%(str2hex(IEND))
			else:
				print '[Finished] Correct IEND chunk'
			if data[pos+8:] != '':
				print Termcolor('Detected','Some data (length: %d) append in the end (%s)'%(len(data[pos+8:]),data[pos+8:pos+18]))
				while True:
					msg = Termcolor('Notice','Try extracting them in: <1>File <2>Terminal <3>Quit [default:3] ')
					choice=raw_input(msg)
					if choice == '1':
						filename = raw_input('[File] Input the file name: ')
						file=WriteFile(filename)
						file.write(data[pos+8:])
						print '[Finished] Successfully write in %s'%(filename)
						os.startfile(os.getcwd())
					elif choice == '2':
						print 'data:',data[pos+8:]
						print 'hex(data):',data[pos+8:].encode('hex')
					elif choice == '3' or choice == '':
						break
					else:
						print Termcolor('Error','Illegal choice. Try again.')

		self.file.write(IEND)
		print '[Finished] IEND chunk check complete'
		return 0

if __name__=='__main__':
	
	msg="""
	 ____   ____ ____ _____ 
	|  _ \ / ___|  _ \_   _|
	| |_) | |   | |_) || |  
	|  __/| |___|  _ < | |  
	|_|    \____|_| \_\|_|  

	PNG Check & Repair Tool 

Project address: https://github.com/sherlly/PCRT
Author: sherlly
Version: 1.0
	"""

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', action='store_true', help="don't show the banner infomation")
	parser.add_argument('-y', help='auto choose yes',action='store_true')
	parser.add_argument('-v', '--verbose', help='use the safe way to recover',action='store_true')
	parser.add_argument('-i', '--input', help='Input file name (*.png) [Select from terminal]')
	parser.add_argument('-f', '--file', help='Input file name (*.png) [Select from window]',action='store_true')
	parser.add_argument('-o', '--output', default='output.png', help='Output repaired file name [Default: output.png]')
	args = parser.parse_args()

	in_file=args.input
	out_file=args.output
	
	if args.q != True:
		print msg
	if args.verbose == True:
		mode=1
	else:
		mode=0

	if args.file == True:
		try:
			import Tkinter
			import tkFileDialog
			root=Tkinter.Tk()
			in_file=tkFileDialog.askopenfilename()
			root.destroy()
			if args.y == True:
				my_png=PNG(in_file,out_file,choices='y',mode=mode)
			else:
				my_png=PNG(in_file,out_file,mode=mode)
			my_png.CheckPNG()
		except ImportError,e:
			print Termcolor('Error',e)
			print "Try 'pip install Tkinter' to use it"
	elif in_file!=None:
		if args.y == True:
			my_png=PNG(in_file,out_file,choices='y',mode=mode)
		else:
			my_png=PNG(in_file,out_file,mode=mode)
		my_png.CheckPNG()
	else:
		parser.print_help()

