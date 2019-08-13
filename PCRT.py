# -*- coding:utf-8 -*-
__author__="sherlly"
__version__="1.1"

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

def str2num(s,n=0):
	if n==4:
		return struct.unpack('!I',s)[0]
	else:
		return eval('0x'+str2hex(s))

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

	def __init__(self,in_file='',out_file='output.png',choices='',mode=0):
		self.in_file=in_file
		self.out_file=out_file
		self.choices=choices
		self.i_mode=mode

	
	def __del__(self):
		try:
			self.file.close()
		except AttributeError:
			pass

	def AddPayload(self,name,payload,way):
		data=self.LoadPNG()
		if data==-1:
			return -1
		self.file=WriteFile(self.out_file)
		if way==1:
			# way1:add ancillary
			payload_chunk=self.MakeAncillary(name,payload)
			pos=data.find('IHDR')
			self.file.write(data[:pos+21])
			self.file.write(payload_chunk)
			self.file.write(data[pos+21:])
		elif way==2:
			# way2:add critical chunk:IDAT
			name='IDAT'
			payload_chunk=self.MakeCritical(name,payload)
			pos=data.find('IEND')
			self.file.write(data[:pos-4])
			self.file.write(payload_chunk)
			self.file.write(data[pos-4:])
		
	def MakeCritical(self,name,payload):
		print Termcolor('Notice','Payload chunk name: %s'%name)
		payload=zlib.compress(payload)
		length=len(payload)
		crc=zlib.crc32(name+payload) & 0xffffffff
		data=struct.pack('!I4s%dsI'%(length),length,name,payload,crc)
		return data

	def MakeAncillary(self,name,payload):
		if name==None:
			name=self.RanAncillaryName()
		name=name[0].lower()+name[1:4].upper()
		print Termcolor('Notice','Payload chunk name: %s'%name)
		length=len(payload)
		crc=zlib.crc32(name+payload) & 0xffffffff
		data=struct.pack('!I4s%dsI'%(length),length,name,payload,crc)
		return data

	def RanAncillaryName(self):
		import random,string
		key = 'abcdefghijklmnopqrstuvwxyz'
		name=''.join(random.sample(string.ascii_lowercase,4))
		return name

	def GetPicInfo(self,ihdr=''):
		'''
		bits: color depth
		mode: 0:gray[1] 2:RGB[3] 3:Indexed[1](with palette) 4:grey & alpha[2] 6:RGBA[4]
		compression: DEFLATE(LZ77+Huffman)
		filter: 0:None 1:sub X-A 2:up X-B 3:average X-(A+B)/2 4:Paeth p = A + B − C
		C B D
		A X
		'''
		data=self.LoadPNG()
		if data==-1:
			return -1
		if ihdr=='':
			pos,IHDR=self.FindIHDR(data)
			if pos==-1:
				print Termcolor('Detected','Lost IHDR chunk')
				return -1
			length=struct.unpack('!I',IHDR[:4])[0]
			ihdr=IHDR[8:8+length]

		self.width,self.height,self.bits,self.mode,self.compression,self.filter,self.interlace=struct.unpack('!iiBBBBB',ihdr)

		self.interlace=str2num(ihdr[12])
		if self.mode==0 or self.mode==3: # Gray/Index
			self.channel=1
		elif self.mode==2: # RGB
			self.channel=3
		elif self.mode==4: #GA
			self.channel=2
		elif self.mode==6: # RGBA
			self.channel=4
		else:
			self.channel=0

		data=self.LoadPNG()
		if data==-1:
			return -1
		self.content=self.FindAncillary(data)

	def PrintPicInfo(self):
		status=self.GetPicInfo()
		if status==-1:
			return -1

		mode_dict={0:'Grayscale',2:'RGB',3:'Indexed',4:'Grayscale with Alpha',6:'RGB with Alpha'}
		compress_dict={0:'Deflate'}
		filter_dict={0:'None',1:'Sub',2:'Up',3:'Average',4:'Paeth'}
		interlace_dict={0:'Noninterlaced',1:'Adam7 interlaced'}
		print '\n-------------------------Image Infomation---------------------------------------'
		print 'Image Width: %d\nImage Height: %d\nBit Depth: %d\nChannel: %d'%(self.width,self.height,self.bits,self.channel)
		print 'ColorType: %s'%(mode_dict[self.mode])
		print 'Interlace: %s\nFilter method: %s\nCompression method: %s'%(interlace_dict[self.interlace],filter_dict[self.filter],compress_dict[self.compression])
		print 'Content: '
		for k in self.content:
			if self.content[k]!=[]:
				text_t='\n'.join(self.content[k]).split('\n')
				text=''
				import re
				for t in text_t:
					if re.match(r'^[ ]+$',t):
						pass
					else:
						text+='\n'+t
				print '%s: '%k,text
		print '--------------------------------------------------------------------------------\n'

	def ClearFilter(self,idat,width,height,channel,bits=8):
		IDAT=''
		if len(idat)==height*width*channel:
			return idat
		filter_unit=bits/8*channel
		for i in range(0,len(idat),width*channel+1):
			line_filter=str2num(idat[i])
			idat_data=idat[i+1:i+width*channel+1]
			if i>=1:
				idat_data_u=tmp
			else:
				idat_data_u=[0]*width*channel

			if line_filter not in [0,1,2,3,4]:
				return -1

			if line_filter==0: #None
				tmp=list(idat_data)
				IDAT+=''.join(tmp)

			elif line_filter==1: #Sub
				k=0
				tmp=list(idat_data)
				for j in range(filter_unit,len(idat_data)):
					tmp[j] = chr((ord(idat_data[j]) + ord(tmp[k])) % 256)
					k+=1
				IDAT+=''.join(tmp)

			elif line_filter==2: # Up
				tmp=''
				for j in range(len(idat_data)):
					tmp += chr((ord(idat_data[j]) + ord(idat_data_u[j])) % 256)
				IDAT+=tmp
				tmp=list(tmp)

			elif line_filter == 3: # Average
				tmp=list(idat_data)
				k=-filter_unit
				for j in range(len(idat_data)):
					if k<0:
						a=0
					else:
						a=ord(tmp[k])
					tmp[j] = chr((ord(idat_data[j]) + (a + ord(idat_data_u[j])) / 2) % 256)
					k+=1
				IDAT+=''.join(tmp)
			
			elif line_filter == 4: #Paeth
				def predictor(a, b, c):
					'''a = left, b = above, c = upper left'''
					p = a + b -c
					pa = abs(p - a)
					pb = abs(p - b)
					pc = abs(p - c)
					if pa <= pb and pa <= pc:
						return a
					elif pb <= pc:
						return b
					else:
						return c
				k=-filter_unit
				tmp=list(idat_data)
				for j in range(len(idat_data)):
					if k<0:
						a=c=0
					else:
						a=ord(tmp[k])
						c=ord(idat_data_u[k])
					tmp[j] = chr((ord(idat_data[j]) + predictor(a, ord(idat_data_u[j]), c)) % 256 )
					k+=1
				IDAT+=''.join(tmp)
		return IDAT
		
	def zlib_decrypt(self,data):
		# Use in IDAT decompress
		z_data=zlib.decompress(data)
		return z_data

	def LoadPNG(self):
		data=ReadFile(self.in_file)
		if data == -1:
			return -1
		status=self.CheckFormat(data)
		if status == -1:
			print Termcolor('Warning','The file may be not a PNG image.')
			return -1
		return data


	def DecompressPNG(self,data,channel=3,bits=8,width=1,height=1):
		# data: array[idat1,idat2,...]
		from PIL import Image
		IDAT_data=''
		for idat in data:
			IDAT_data+=idat
		z_idat=self.zlib_decrypt(IDAT_data)
		length=len(z_idat)

		if width==0 and height == 0:
			# bruteforce
			import shutil
			channel_dict={1:'L',3:'RGB',2:'LA',4:'RGBA'}
			PATH='tmp/'
			if os.path.isdir(PATH)==True:
				shutil.rmtree(PATH)
			os.mkdir(PATH)
			for bits in [8,16]:
				for channel in [4,3,1,2]:
					size_list=[]
					for i in range(1,length):
						if length%i==0:
							if (i-1)%(bits/8*channel)==0:
								size_list.append((i-1)/(bits/8*channel))
								size_list.append(length/i)
							if (length/i-1)%(bits/8*channel)==0:
								size_list.append((length/i-1)/(bits/8*channel))
								size_list.append(i)
					for i in range(0,len(size_list),2):
						width=size_list[i]
						height=size_list[i+1]
						tmp=self.ClearFilter(z_idat,width,height,channel,bits)
						if tmp!=-1:
							img=Image.fromstring(channel_dict[channel],(width,height), tmp)
							# img.show()
							filename=PATH+'test(%dx%d)_%dbits_%dchannel.png'%(width,height,bits,channel)
							img.save(filename)

			# show all possible image
			os.startfile(os.getcwd()+'/'+PATH)
			# final size
			size=raw_input('Input width, height, bits and channel(space to split):').split()
			# remove temporary file
			shutil.rmtree(PATH)

			width=int(size[0])
			height=int(size[1])
			bits=int(size[2])
			channel=int(size[3])
			tmp=self.ClearFilter(z_idat,width,height,channel,bits)
			if tmp==-1:
				print 'Wrong'
				return -1
			img=Image.fromstring(channel_dict[channel],(width,height), tmp)
			img.save('decompress.png')

		else:
			if width==1 and height == 1:
				# load PNG config
				status=self.GetPicInfo()
				if status == -1:
					return -1
				width=self.width
				height=self.height
				channel=self.channel
				bits=self.bits
			else:
				pass
			z_idat=self.ClearFilter(z_idat,width,height,channel,bits)

			mode_dict={0:'L',2:'RGB',3:'P',4:'LA',6:'RGBA'}
			img=Image.fromstring(mode_dict[self.mode],(width,height), z_idat)
			img.show()
			img.save('zlib.png')

		return 0


	def FindAncillary(self,data):
		ancillary=['cHRM','gAMA','sBIT','PLTE','bKGD','sTER','hIST','iCCP','pHYs','sPLT','sRGB','dSIG','eXIf','iTXt','tEXt','zTXt','tIME','tRNS','oFFs','sCAL','fRAc','gIFg','gIFt','gIFx']
		attach_txt=['eXIf','iTXt','tEXt','zTXt']
		content={}
		for text in attach_txt:
			pos=0
			content[text]=[]
			while pos!=-1:
				pos=data.find(text,pos)
				if pos!=-1:
					length=str2num(data[pos-4:pos])
					content[text].append(data[pos+4:pos+4+length])
					pos+=1
		return content


	def CheckPNG(self):
		data=self.LoadPNG()
		if data==-1:
			return -1

		self.file=WriteFile(self.out_file)
		res=self.CheckHeader(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1
		res=self.CheckIHDR(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1

		res,idat=self.CheckIDAT(data)
		if res == -1:
			print '[Finished] PNG check complete'
			return -1
		self.CheckIEND(data)
		print '[Finished] PNG check complete'

		'''check complete'''

		if self.choices != '':
			choice=self.choices
		else:
			msg=Termcolor('Notice','Show the repaired image? (y or n) [default:n] ')
			choice=raw_input(msg)
		if choice == 'y':
			try:
				from PIL import Image
				self.file.close()
				img=Image.open(self.out_file)
				img.show()
			except ImportError,e:
				print Termcolor('Error',e)
				print "Try 'pip install PIL' to use it"
		return 0

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

	def FindIHDR(self,data):
		pos=data.find('IHDR')
		if pos == -1:
			return -1,-1
		idat_begin=data.find('IDAT')
		if idat_begin != -1:
			IHDR=data[pos-4:idat_begin-4]
		else:
			IHDR=data[pos-4:pos+21]
		return pos,IHDR

	def CheckIHDR(self,data):
		# IHDR:length=13(4 bytes)+chunk_type='IHDR'(4 bytes)+chunk_ihdr(length bytes)+crc(4 bytes)
		# chunk_ihdr=width(4 bytes)+height(4 bytes)+left(5 bytes)
		pos,IHDR=self.FindIHDR(data)
		if pos==-1:
			print Termcolor('Detected','Lost IHDR chunk')
			return -1
		length=struct.unpack('!I',IHDR[:4])[0]
		chunk_type=IHDR[4:8]
		chunk_ihdr=IHDR[8:8+length]

		width,height=struct.unpack('!II',chunk_ihdr[:8])
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
						if self.Checkcrc(chunk_type,chunk_ihdr,calc_crc) == None:
							IHDR=IHDR[:8]+chunk_ihdr+calc_crc
							print '[Finished] Successfully fix crc'
							break
				else:
					# fix width
					for w in xrange(width,height):
						chunk_ihdr=struct.pack('!I',w)+IHDR[12:8+length]
						if self.Checkcrc(chunk_type,chunk_ihdr,calc_crc) == None:
							IHDR=IHDR[:8]+chunk_ihdr+calc_crc
							print '[Finished] Successfully fix crc'
							break
		else:
			print '[Finished] Correct IHDR CRC (offset: %s): %s'% (int2hex(pos+4+length),str2hex(crc))
		self.file.write(IHDR)
		print '[Finished] IHDR chunk check complete (offset: %s)'%(int2hex(pos-4))

		# get image information
		self.GetPicInfo(ihdr=chunk_ihdr)

	def CheckIDAT(self,data):
		# IDAT:length(4 bytes)+chunk_type='IDAT'(4 bytes)+chunk_data(length bytes)+crc(4 bytes)
		IDAT_table = []
		idat_begin = data.find('49444154'.decode('hex'))-4
		if idat_begin == -1:
			print Termcolor('Detected','Lost all IDAT chunk!')
			return -1,''
		if self.i_mode == 0:
			# fast: assume both chunk length are true
			idat_size=struct.unpack('!I',data[idat_begin:idat_begin+4])[0]+12
			for i in xrange(idat_begin,len(data)-12,idat_size): 
				IDAT_table.append(data[i:i+idat_size])
			if i < len(data)-12:
				# the last IDAT chunk
				IDAT_table.append(data[i:-12])
		elif self.i_mode == 1:
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
		IDAT_data_table=[]
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
			IDAT_data_table.append(chunk_data)
			offset+=len(chunk_data)+12
		print '[Finished] IDAT chunk check complete (offset: %s)'%(int2hex(idat_begin))
		return 0,IDAT_data_table

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
Version: %s
	"""%(__version__)

	parser = argparse.ArgumentParser()
	parser.add_argument('-q', '--quiet',action='store_true', help="don't show the banner infomation")
	parser.add_argument('-y', '--yes',help='auto choose yes',action='store_true')
	parser.add_argument('-v', '--verbose', help='use the safe way to recover',action='store_true')
	parser.add_argument('-m', '--message',help='show the image information',action='store_true')
	parser.add_argument('-n', '--name', help="payload name [Default: random]")
	parser.add_argument('-p', '--payload', help="payload to hide")
	parser.add_argument('-w', '--way', type=int, default=1, help="payload chunk: [1]: ancillary [2]: critical [Default:1]")

	parser.add_argument('-d', '--decompress', help="decompress zlib data file name")

	parser.add_argument('-i', '--input', help='Input file name (*.png) [Select from terminal]')
	parser.add_argument('-f', '--file', help='Input file name (*.png) [Select from window]',action='store_true')
	parser.add_argument('-o', '--output', default='output.png', help='Output repaired file name [Default: output.png]')
	args = parser.parse_args()

	in_file=args.input
	out_file=args.output
	payload=args.payload
	payload_name=args.name
	z_file=args.decompress

	if args.quiet != True:
		print msg

	if z_file!=None:
		z_data=ReadFile(z_file)
		my_png=PNG()
		my_png.DecompressPNG(z_data,width=0,height=0)
	else:
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
				if args.yes == True:
					my_png=PNG(in_file,out_file,choices='y',mode=mode)
				else:
					my_png=PNG(in_file,out_file,mode=mode)
				if args.message == True:
					my_png.PrintPicInfo()
				elif payload != None:
					way=args.way
					my_png.AddPayload(payload_name,payload,way)
				else:
					my_png.CheckPNG()
			except ImportError,e:
				print Termcolor('Error',e)
				print "Try 'pip install Tkinter' to use it"
		elif in_file!=None:
			if args.yes == True:
				my_png=PNG(in_file,out_file,choices='y',mode=mode)
			else:
				my_png=PNG(in_file,out_file,mode=mode)
			if args.message == True:
				my_png.PrintPicInfo()
			elif payload != None:
				way=args.way
				my_png.AddPayload(payload_name,payload,way)
			else:
				my_png.CheckPNG()
		else:
			parser.print_help()

