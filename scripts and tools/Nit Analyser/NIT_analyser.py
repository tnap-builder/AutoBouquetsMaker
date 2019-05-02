#!/usr/bin/python

import sys, binascii, os, re
pathstreamfile = "/tmp/nit.bin"
pathnitlog = "/tmp/nit.log"
pathxml = "/tmp/dvbc.xml"
abmpathxml = "/usr/lib/enigma2/python/Plugins/SystemPlugins/AutoBouquetsMaker/providers/dvbc.xml"

def readNIT(actualnetid):
	charpointer = 0L
	strblock = ""
	firstnet = ""
	firstsectionnumber = 0
	firstloop = 0
	topxml = 1
	lcntable = {}
	modulationtype = {0:"Not defined", 1:"16-QAM", 2:"32-QAM", 3:"64-QAM", 4:"128-QAM", 5:"256-QAM"}
	fecoutertype = {0:"Not defined", 1:"No outer FEC coding", 2:"RS204/188"}
	fecinnertype = {0:"Not defined", 1:"1/2", 2:"2/3", 3:"3/4", 4:"5/6", 5:"7/8", 6:"8/9", 7:"3/5", 8:"4/5", 9:"9/10", 15:"no conv."}
	polarizationtype = {0:"horizontal", 1:"vertical", 2:"left", 3:"right"}
	rollofftype = {0:"0.35", 1:"0.25", 2:"0.20", 3:"res"}
	modulationsystemtype = {0:"DVB-S", 1:"DVB-S2"}
	modulationtypetype = {0:"Auto", 1:"QPSK", 2:"8PSK", 3:"16-QAM"}
	bandwidthtype = {0:"8MHz", 1:"7MHz", 2:"6MHz", 3:"5MHZ", 4:"FU", 5:"FU", 6:"FU", 7:"FU"}
	prioritytype = {0:"HP", 1:"LP"}
	constellationtype = {0:"QPSK", 1:"16-QAM", 2:"64-QAM", 3:"FU"}
	coderatetype = {0:"1/2", 1:"2/3", 2:"3/4", 3:"5/6", 4:"7/8", 5:"FU", 6:"FU", 7:"FU"}
	guardintervaltype = {0:"1/32", 1:"1/16", 2:"1/8", 3:"1/4"}
	transmissionmodetype = {0:"2k", 1:"8k", 2:"4k", 3:"FU"}

	with open(pathstreamfile,"rb") as f:
		block = f.read()
		xml_out = []
		while True:
			writelog = 0
			sectionlength = int((binascii.hexlify(block[1 + charpointer]) + binascii.hexlify(block[2 + charpointer]))[1:],16)
			networkid = binascii.hexlify(block[3 + charpointer]) + binascii.hexlify(block[4 + charpointer])
			networkdescriptorlength = int((binascii.hexlify(block[8 + charpointer]) + binascii.hexlify(block[9 + charpointer]))[1:],16)
			sectionnumber =int(binascii.hexlify(block[6 + charpointer]),16)
			if networkid == actualnetid or actualnetid == "":
				writelog = 1
			if networkid == firstnet and sectionnumber == firstsectionnumber and firstloop == 1:	#NIT repeats data
				if writelog == 1:
					flog.write("\nAll sections read.\n")
				break
			print "********************************"
			print "Network id         : ",networkid, int(networkid,16)
			if writelog == 1:
				flog.write("\nNetwork id    : \t%s \t%i \n" % (networkid, int(networkid,16)))
				flog.write("Section       : \t%s \n" % (sectionnumber))
			if firstloop == 0:
				firstnet = networkid
				firstsectionnumber = sectionnumber
				firstloop = 1
			nitbuffer = ""
			for ch in range(charpointer + 8, charpointer + sectionlength + 3):
				nitbuffer += block[ch]
			#Network descriptors
			if networkdescriptorlength > 0:		#Somtimes no NIT content.
				descbuffer = ""
				for ch in range(2 , networkdescriptorlength+2):
					descbuffer += nitbuffer[ch]
				while True:
					descriptor = binascii.hexlify(descbuffer[0])
					if descriptor == "40":	# network_name_descriptor
						networkname = ""
						descbuffer = descbuffer[1:]
						desclength = int(binascii.hexlify(descbuffer[0]),16)
						for ch in range(1, desclength +1):
							#vilidate Network Name, provider sends DLE and EOT here! :(
							networkname += re.sub("[\x00-\x1F]", "", descbuffer[ch])
						print "Network name       : ",networkname
						if writelog == 1:
							flog.write("Network name  : \t%s\n" % (networkname))
						descbuffer = descbuffer[desclength + 1:]
					elif descriptor == "d0":	# 
						descbuffer = descbuffer[1:]
						desclength = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[desclength + 1:]
						#print "Found d0"
					elif descriptor == "83":	# 
						descbuffer = descbuffer[1:]
						desclength = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[desclength + 1:]
						#print "Found 83"
					elif descriptor == "4a":	# Linkage descriptor
						descbuffer = descbuffer[1:]
						desclength = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[desclength + 1:]
						#print "Found 4a"
					else:
						descbuffer = descbuffer[1:]
						desclength = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[desclength + 1:]
						#print "descriptor: " , descriptor
					if descbuffer == "":
						break
			else:
				if sectionnumber == 0:
					print "No network descriptors."
					if writelog == 1:
						flog.write("Network name  : \tUnknown\n")
			#Transport streams
			nitbuffer = nitbuffer[networkdescriptorlength + 2:]	#strip network descriptor part
			transportstreamlooplength = int((binascii.hexlify(nitbuffer[0]) + binascii.hexlify(nitbuffer[1]))[1:],16)
			nitbuffer = nitbuffer[:transportstreamlooplength + 6]
			nitbuffer = nitbuffer[2:]	#length bytes
			while True:
				streamid = (binascii.hexlify(nitbuffer[0]) + binascii.hexlify(nitbuffer[1]))
				originalnetworkid = (binascii.hexlify(nitbuffer[2]) + binascii.hexlify(nitbuffer[3]))
				nitbuffer = nitbuffer[4:]	#streamid & networkid
				descriptorlength = int((binascii.hexlify(nitbuffer[0]) + binascii.hexlify(nitbuffer[1]))[1:],16)
				nitbuffer = nitbuffer[2:]	#descriptorlength
				descbuffer = nitbuffer[:descriptorlength]
				nitbuffer = nitbuffer[len(descbuffer):]
				##print "Stream id          : ",streamid
				##print "Original network id: ",originalnetworkid
				if writelog == 1:
					flog.write("\tStream id    : \t%s\n" % (streamid))
					#flog.write("\tOrg networkid: \t%s\n" % (originalnetworkid))
				while True:	#stream part
					try:
						descriptor = binascii.hexlify(descbuffer[0])
					except:
						break
					if descriptor == "43":	#Satellite delivery system 43
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						frequency = (binascii.hexlify(descbuffer[1])+ binascii.hexlify(descbuffer[2])+ binascii.hexlify(descbuffer[3])+ binascii.hexlify(descbuffer[4]))
						orbital = int(binascii.hexlify(descbuffer[5])+ binascii.hexlify(descbuffer[6]))/10
						bitstr = bin(int(binascii.hexlify(descbuffer[7]),16))[2:].zfill(8)
						westeast = bitstr[:1]
						polarization = bitstr[1:][:2]
						rolloff = bitstr[3:][:2]
						modulationsystem = bitstr[5:][:1]
						modulationtype = bitstr[6:][:2]
						symbolrate = binascii.hexlify(descbuffer[8])+ binascii.hexlify(descbuffer[9])+ binascii.hexlify(descbuffer[10]) + binascii.hexlify(descbuffer[11])[:1]
						fecinner = binascii.hexlify(descbuffer[11])[1:]
						print "FOUND DVB-S 43"
						descbuffer = descbuffer[bytenumber + 1:]
						#frequency			32	1,2,3,4
						#orbital position	16	5,6
						#west-east flag		1	7
						#polarization		2	7
						#roll-off			2	7
						#modulation system	1	7
						#modulation type	2	7
						#symbol rate		28	8,9,10,11(first half)
						#FEC inner			4	11(last half
						if writelog == 1:
							flog.write("\t\tDVB-S.\n")
							flog.write("\t\tFrequency        : \t%s\n" % (frequency))
							flog.write("\t\tOrbital          : \t%s\n" % (orbital))
							flog.write("\t\tWest-East        : \t%s\n" % (westeast))
							flog.write("\t\tPolarization     : \t%s\t%s\n" % (polarization, polarizationtype[int(polarization,2)]))
							flog.write("\t\tRoll-off         : \t%s\t%s\n" % (rolloff, rollofftype[int(rolloff,2)]))
							flog.write("\t\tModulation system: \t%s\t%s\n" % (modulationsystem, modulationsystemtype[int(modulationsystem,2)]))
							flog.write("\t\tModulation type  : \t%s\t%s\n" % (modulationtype, modulationtypetype[int(modulationtype,2)]))
							flog.write("\t\tSymbol rate      : \t%s\n" % (symbolrate))
							flog.write("\t\tFEC inner        : \t%s\t%s\n" % (fecinner, fecinnertype[int(fecinner,16)]))
					elif descriptor == "44":	#cable delivery system 44
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						frequency = binascii.hexlify(descbuffer[1])+ binascii.hexlify(descbuffer[2])+ binascii.hexlify(descbuffer[3])+ binascii.hexlify(descbuffer[4])
						fecouter = binascii.hexlify(descbuffer[6])[1:]
						modulation = binascii.hexlify(descbuffer[7])
						symbolrate = binascii.hexlify(descbuffer[8])+ binascii.hexlify(descbuffer[9])+ binascii.hexlify(descbuffer[10]) + binascii.hexlify(descbuffer[11])[:1]
						fecinner = binascii.hexlify(descbuffer[11])[1:]
						descbuffer = descbuffer[bytenumber + 1:]
						print "FOUND DVB-C 44"
						#frequency			32	1,2,3,4
						#reserved future	12	5,6(first half)
						#FEC outer			4	6(last half)
						#modulation			8	7
						#symbol rate		28	8,9,10,11(first half)
						#FEC inner			4	11(last half)
						if writelog == 1:
							flog.write("\t\tDVB-C.\n")
							flog.write("\t\tFrequency  : \t%s\t\t%s KHz\n" % (frequency, int(frequency)/10))
							flog.write("\t\tFEC outer  : \t%s\t\t\t\t%s\n" % (fecouter, fecoutertype[int(fecouter,16)]))
							flog.write("\t\tModulation : \t%s\t\t\t\t%s\n" % (modulation, modulationtype[int(modulation,16)]))
							flog.write("\t\tSymbol rate: \t%s\t\t\t%s S/s\n" % (symbolrate, int(symbolrate)*100))
							flog.write("\t\tFEC inner  : \t%s\t\t\t\t%s\n" % (fecinner, fecinnertype[int(fecinner,16)]))
						if streamid == "0001" and topxml == 1:
							topxml = 0
							fxml.write("\t<streamtype>dvbc</streamtype>\n")
							fxml.write("\t<protocol>vmuk</protocol>\n")
							fxml.write("\t<dvbcconfigs>\n")
						if streamid == "0001":
							xml_out.append((int(networkid,16),
								"\t\t<configuration key=\"hd_%05d_dvbc_uk\" netid=\"%05d\" bouquettype=\"hd\" frequency=\"%d\" symbol_rate=\"%d\" system=\"0\" modulation=\"%d\">%05d %s</configuration>\n" % (
									int(networkid,16),
									int(networkid,16),
									int(frequency)/10,
									int(symbolrate)*100,
									int(modulation),
									int(networkid,16),
									networkname[:40])))
					elif descriptor == "5a":	#terrestrial delivery system
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "FOUND DVB-T 5A"
						frequency = int((binascii.hexlify(descbuffer[1])+ binascii.hexlify(descbuffer[2])+ binascii.hexlify(descbuffer[3])+ binascii.hexlify(descbuffer[4])),16)*10
						bitstr1 = bin(int(binascii.hexlify(descbuffer[5]),16))[2:].zfill(8)
						bitstr2 = bin(int(binascii.hexlify(descbuffer[6]),16))[2:].zfill(8)
						bitstr3 = bin(int(binascii.hexlify(descbuffer[7]),16))[2:].zfill(8)
						bandwidth = bitstr1[:3]
						priority = bitstr1[3:][:1]
						timeslicing = bitstr1[4:][:1]
						mpefec = bitstr1[5:][:1]
						constellation = bitstr2[:2]
						hierarchy = bitstr2[2:][:3]
						coderatehp = bitstr2[5:][:3]
						coderatelp = bitstr3[:3]
						guardinterval = bitstr3[3:][:2]
						transmissionmode = bitstr3[5:][:2]
						otherfreqflag = bitstr3[7:][:1]
						descbuffer = descbuffer[bytenumber + 1:]
						#centre frequency		32	1,2,3,4
						#bandwidth				3	5
						#priority				1	5
						#time slicing indicator	1	5
						#MPE-FEC indicator		1	5
						#future use				2	5
						#constellation			2	6
						#hierarchy information	3	6
						#code-rate HP stream	3	6
						#code-rate LP stream	3	7
						#guard-interval			2	7
						#transmission mode		2	7
						#other frequency flag	1	7
						#future use				32	
						if writelog == 1:
							flog.write("\t\tDVB-T.\n")
							flog.write("\t\tFrequency          : \t%s\n" % (frequency))
							flog.write("\t\tPriority           : \t%s\t%s\n" % (priority, prioritytype[int(priority,2)]))
							flog.write("\t\tTime slicing ind.  : \t%s\n" % (timeslicing))
							flog.write("\t\tMPE-FEC indicator  : \t%s\n" % (mpefec))
							flog.write("\t\tConstellation      : \t%s\t%s\n" % (constellation, fecoutertype[int(constellation,2)]))
							flog.write("\t\tHierarchy inform.  : \t%s\n" % (hierarchy))
							flog.write("\t\tCode-rate HP stream: \t%s\t%s\n" % (coderatehp, coderatetype[int(coderatehp,2)]))
							flog.write("\t\tCode-rate LP stream: \t%s\t%s\n" % (coderatelp, coderatetype[int(coderatelp,2)]))
							flog.write("\t\tGuard-interval     : \t%s\t%s\n" % (guardinterval, guardintervaltype[int(guardinterval,2)]))
							flog.write("\t\tTransmission mode  : \t%s\t%s\n" % (transmissionmode, transmissionmodetype[int(transmissionmode,2)]))
							flog.write("\t\tOther freq. flag   : \t%s\n" % (otherfreqflag))
					elif descriptor == "41":	#channel information part 41
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[1:]
						#print "FOUND 41 length: " , bytenumber
						for j in range(0,(bytenumber/3)):
							serviceid = binascii.hexlify(descbuffer[0])+ binascii.hexlify(descbuffer[1])
							service_type = binascii.hexlify(descbuffer[2])
							descbuffer = descbuffer[3:]
							##print "Serviceid:", serviceid, "Service type:",service_type
							#flog.write("\t\t\tService id : \t%s\t%s\n" % (serviceid, service_type))
					elif descriptor == "5f":	#
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "FOUND 5F length: ", bytenumber
						descbuffer = descbuffer[bytenumber + 1:]
					elif descriptor == "62":	#Descriptor: frequency_list_descriptor: 0x62 (98)
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "FOUND 62 length: ", bytenumber
						descbuffer = descbuffer[bytenumber + 1:]
					elif descriptor == "7f" and binascii.hexlify(descbuffer[2]) == "04":	#terrestrial2 delivery system
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "FOUND DVB-T2 7F length: ", bytenumber
						print "plp_id:                ", binascii.hexlify(descbuffer[2])
						print "T2_system_id:          ", binascii.hexlify(descbuffer[3]),binascii.hexlify(descbuffer[4])
						if bytenumber > 4:
							print "SISO/MISO ; bandwidth: ", binascii.hexlify(descbuffer[5])
							print "guard_interval etc   : ", binascii.hexlify(descbuffer[6])
							print "cell_id              : ", binascii.hexlify(descbuffer[7]),binascii.hexlify(descbuffer[8])
							print "                       ", binascii.hexlify(descbuffer[9]),binascii.hexlify(descbuffer[10]), binascii.hexlify(descbuffer[11]),binascii.hexlify(descbuffer[12]), binascii.hexlify(descbuffer[13]),binascii.hexlify(descbuffer[14])
						print ""
						descbuffer = descbuffer[bytenumber + 1:]
					elif descriptor == "25":	#Metadata_Pointer_Descriptor
						descbuffer = descbuffer[1:]
						des25length = int(binascii.hexlify(descbuffer[0]),16)
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "FOUND 25 length: ", des25length
						descbuffer = descbuffer[bytenumber + 1:]
					elif descriptor == "83":	#LCN part
						descbuffer = descbuffer[1:]
						lcndeslength = int(binascii.hexlify(descbuffer[0]),16)
						print "LCN part found."
						flog.write("\t\tLCN part found.\n")
						descbuffer = descbuffer[1:]
						for j in range(0,(lcndeslength/4)):
							serviceid = binascii.hexlify(descbuffer[0])+ binascii.hexlify(descbuffer[1])
							logicalchannelnumber = int((binascii.hexlify(descbuffer[2])+ binascii.hexlify(descbuffer[3]))[1:],16)
							lcntable[serviceid] = logicalchannelnumber
							descbuffer = descbuffer[4:]
					elif descriptor == "88":	#HD LCN part
						descbuffer = descbuffer[1:]
						des88length = int(binascii.hexlify(descbuffer[0]),16)
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						print "HD LCN part found."
						if writelog == 1:
							flog.write("\t\tHD LCN part found.\n")
						descbuffer = descbuffer[bytenumber + 1:]
					else:
						descbuffer = descbuffer[1:]
						bytenumber = int(binascii.hexlify(descbuffer[0]),16)
						descbuffer = descbuffer[bytenumber + 1:]
						print "descriptor: " , descriptor
					#descriptor loop
					if descbuffer == "":
						break
				#Transport stream loop
				if len(nitbuffer) < 6:	#min length, there are some bytes left.
					break
			
			#section loop
			charpointer = charpointer + sectionlength + 3
			if charpointer >= len(block):
				break
	f.close()
	fxml.write(''.join([i[1] for i in sorted(xml_out, key=lambda listItem: listItem[0])]))
	#print lcntable
	return


#MAIN
cmd = 'dvbsnoop -s sec -tn -timeout 3000 -b -f 0x40 -n 400 0x10 > /tmp/nit.bin'
os.system(cmd)	
flog = open(pathnitlog, 'w')
fxml = open(pathxml, 'w')
fxml.write("<provider>\n")
fxml.write("<name>Virgin adhoc</name>\n")
flog.write("NIT content.\n")

readNIT("")

fxml.write("\t</dvbcconfigs>\n")
fxml.write("\t<sections>\n")
sections = """
		<section number="100">Entertainment</section>
		<section number="245">Factual</section>
		<section number="278">Lifestyle</section>
		<section number="300">Music</section>
		<section number="400">Movies</section>
		<section number="500">Sports</section>
		<section number="601">News</section>
		<section number="700">Kids</section>
		<section number="740">Shopping</section>
		<section number="801">International</section>
		<section number="851">Audio Description</section>
		<section number="861">Local</section>
		<section number="969">Adult</section>
		<section number="990">BBC Interactive</section>
		<section number="997">Information</section>
		<section number="1000">Red button</section>
		<section number="1020">BT Sport Interactive</section>
"""
fxml.write(sections)
fxml.write("\t</sections>\n")
fxml.write("\t<servicehacks>\n<![CDATA[\n")

hacks = """

try:
	is_assigned
except:
	is_assigned = True

	dxNoSDT = 0x1 # details of lamedb flags are in README.txt
	dxHoldName = 0x8 # details of lamedb flags are in README.txt

	flags = dxNoSDT | dxHoldName
	provider = "Virgin Media"

	#Channel names have quotes, channel numbers do not. Example: ['ITV HD', 250, 500]
	blacklist = [295,650,651,743,744,745,746,947,'BT Events HD','Channel Moved','Channel Closed','hayu','ITVEvents HD','L Pack Tier 4','M Pack Tier 1','More TV Pack Tier 2','motorsport.tv','M+ Pack Tier 3','Netflix','PIN Protection Help','S4C HD','XL Pack Tier 5','Vevo','Worldbox','YouTube']

	bt_sports_xtra = ["BT Sport Extra 0","BT Sport Extra 1","BT Sport Extra 2","BT Sport Extra 3","BT Sport Extra 4","BT Sport Extra 5","BT Sport Extra 6"]

	fta_corrections = []

	netID = int(bouquet_key[3:8])
	netID_whitelist = [41047,
	]

	# Remove some services unless in netID whitelist
	# Channel names have quotes, channel numbers do not. Example: ['ITV HD', 250, 500]
	selective_blacklist = [501, 502, 503, 504, 505, 506, 507, 508,]

if (service["service_name"] in selective_blacklist or service["number"]  in selective_blacklist) and netID not in netID_whitelist:
	skip = True

# Correct service type of HD channels not marked as such
if service["service_type"] in DvbScanner.VIDEO_ALLOWED_TYPES and service["service_type"] not in DvbScanner.HD_ALLOWED_TYPES and service["service_name"][-2:] == 'HD':
	service["service_type"] = 25

for number in service["numbers"]:
	if number in blacklist:
		skip = True
		break
	elif number >= 50 and number <= 60:
		service["numbers"] = [number + 952]
		break
	elif number == 40:
		service["numbers"] = [number + 961]
		break
	elif number == 43:
		service["numbers"] = [number + 957]
		break
	elif number < 100 and service["service_name"] in bt_sports_xtra:
		service["numbers"] = [1021 + bt_sports_xtra.index(service["service_name"])]
		break

if service["service_name"] in blacklist:
	skip = True

if service["service_name"].startswith("DL_") or service["service_name"].startswith("Hidden"):
	skip = True

if service["service_name"].startswith("SptsETV"):
	service["free_ca"] = 1

#Some encrypted channels are wrongly flagged as FTA.
if service["service_name"] in fta_corrections:
	service["free_ca"] = 1

service["service_flags"] = flags
service["provider_name"] = provider

"""
fxml.write(hacks)
fxml.write("\n]]>\n\t</servicehacks>\n")
fxml.write("</provider>\n")
fxml.close()
flog.close()

f = open(abmpathxml, 'w')
f.write(open(pathxml).read())
f.close()
