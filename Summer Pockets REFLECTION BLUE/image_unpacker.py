# It's using LucaSystemTools to convert unpacked textures to PNG format
# https://github.com/wetor/LucaSystemTools
#
# LucaSystemTools can also unpack PAKs (without automatic conversion to readable image formats), 
# but it crashes when trying to handle PAK in patch format, which is not an issue for this script
# Put script so next to it is folder "LucaSystemTool" with "LucaSystemTools.exe" inside

import sys
import numpy
import os
import glob
import subprocess

def readString(myfile):
    chars = []
    while True:
        c = myfile.read(1)
        if c == b'\x00':
            return str(b"".join(chars).decode("UTF-8"))
        chars.append(c)

try:
    os.mkdir("%s" % (sys.argv[1][:-4]))
except:
    pass

file = open(sys.argv[1], "rb")

header_size = numpy.fromfile(file, dtype=numpy.int32, count=1)[0]

file_count = numpy.fromfile(file, dtype=numpy.int32, count=1)[0]
unk2_int32 = numpy.fromfile(file, dtype=numpy.int32, count=1)[0]
round_to = numpy.fromfile(file, dtype=numpy.int32, count=1)[0]
reserved0 = file.read(0x10)
flag0 = numpy.fromfile(file, dtype=numpy.int8, count=1)[0]
flag1 = numpy.fromfile(file, dtype=numpy.int8, count=1)[0]
flag2 = numpy.fromfile(file, dtype=numpy.int8, count=1)[0]
flag3 = numpy.fromfile(file, dtype=numpy.int8, count=1)[0]
offset_start_file_names = numpy.fromfile(file, dtype=numpy.uint32, count=1)[0]

file_table = {}
file_table['offset'] = []
file_table['size'] = []

for i in range(0, file_count):
    file_table['offset'].append(numpy.fromfile(file, dtype=numpy.uint32, count=1)[0]*round_to)
    file_table['size'].append(numpy.fromfile(file, dtype=numpy.uint32, count=1)[0])

filename_table = []

for i in range(0, file_count):
    filename_table.append(readString(file))

chapter_names = open("%s_filenames.txt" % (sys.argv[1][:-4]), "w", encoding="UTF-8")

file_extracted = 0
dummy_files = 0
for i in range(0, file_count):
    if (file_table['offset'][i] == 0):
        dummy_files += 1
        continue
    file.seek(file_table['offset'][i], 0)
    file_new = open("%s\%s.dat" % (sys.argv[1][:-4], filename_table[i]), "wb")
    file_new.write(file.read(file_table['size'][i]))
    chapter_names.write("%s\n" % (filename_table[i]))
    file_new.close()
    file_extracted += 1

print("Extracted %d/%d files." % (file_extracted, file_count))
print("Counted %d dummies" % dummy_files)

files = glob.glob("%s/*.dat" % os.path.basename(sys.argv[1])[:-4])

for i in range(0, len(files)):
    print(files[i])
    file = open(files[i], "rb")
    magic = file.read(4)
    file.close()
    if (magic[0:2] == b"CZ"):
        print(subprocess.run(["LucaSystemTool/LucaSystemTools.exe", "-t", magic[0:3].decode("ascii").lower(), "-m", "export", "-f", files[i]], capture_output=True))
    elif (magic[1:4] == b"PNG"):
        os.rename(files[i], "%s.png" % files[i][:-4])
    else:
        print("UNKNOWN FORMAT")