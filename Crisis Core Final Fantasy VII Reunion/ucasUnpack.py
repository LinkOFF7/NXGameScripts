# Script decompressing ucas archives with help of json file generated by UnrealPakViewer.
# It was made just to understand how archives are storing data. It's slower than UnrealPakViewer, but it unpacks whole files
# My goal is to make it working without json file so I can start working on ucas/utoc repacker
# It requires Oodle.exe in the same folder, you can compile it with Oodle.cpp in the same repo folder
# Confirmed that it's unpacking fully without issues all pakchunks

import subprocess
import json
import sys
import os

def Sort(key):
    return key["Offset"]

json_file = open(f"{sys.argv[1]}.json", "r", encoding="UTF-8")
DUMP = json.load(json_file)["Files"]
json_file.close()

DUMP.sort(key=Sort)

FilteredList = []

all_dec_size = 0

offset = 0
for i in range(len(DUMP)):
    entry = {}
    entry["filepath"] = DUMP[i]["Path"]
    entry["offset"] = offset
    entry["com_size"] = DUMP[i]["Compressed Size"]
    offset += DUMP[i]["Compressed Size"]
    entry["dec_size"] = DUMP[i]["Size"]
    all_dec_size += DUMP[i]["Size"]
    entry["block_count"] = DUMP[i]["Compressed Block Count"]
    FilteredList.append(entry)

DUMP = []

print("Unpacked files will take space of: %d B, %.2f MB" % (all_dec_size, all_dec_size/1024/1024))
print("To continue, press ENTER")
input()

ucas_file = open(f"{sys.argv[1]}.ucas", "rb")

FilteredListLen = len(FilteredList)

for i in range(len(FilteredList)):
    os.makedirs(os.path.dirname(FilteredList[i]["filepath"]), exist_ok=True)
    ucas_file.seek(FilteredList[i]["offset"])
    file_pos = ucas_file.tell()
    if (FilteredList[i]["block_count"] == 1):
        print("File: %6d/%d  %s" % (i+1, FilteredListLen, FilteredList[i]["filepath"]))
        oodle_magic = int.from_bytes(ucas_file.read(1), "big")
        oodle_compressor = int.from_bytes(ucas_file.read(1), "big") #idk, just guessing what this is
        ucas_file.seek(-2, 1)
        if (oodle_magic != 0x8C or oodle_compressor > 0x10):
            temp_file = open(FilteredList[i]["filepath"], "wb")
            temp_file.write(ucas_file.read(FilteredList[i]["dec_size"]))
            temp_file.close()
            continue
        catch = subprocess.run(["Oodle.exe", "-d", "%d" % FilteredList[i]["dec_size"], "stdin=%d" % FilteredList[i]["com_size"], FilteredList[i]["filepath"]], input=ucas_file.read(FilteredList[i]["com_size"]), capture_output=True, text=False)
        if (catch.stderr != b""):
            print(catch.stderr.decode("ascii"))
            print("Error while decompressing file at offset: 0x%X!" % file_pos)
            os.remove(FilteredList[i]["filepath"])
            if (os.path.exists("temp.oodle") == True):
                os.remove("temp.oodle")
            sys.exit(1)
        
    else:
        print("File: %6d/%d  %s, size: %.2f MB" % (i+1, FilteredListLen, FilteredList[i]["filepath"], FilteredList[i]["dec_size"]/1024/1024))
        chunks = []
        for x in range(FilteredList[i]["block_count"]):
            print("Chunk: %d/%d" % (x+1, FilteredList[i]["block_count"]), end="\r")
            if (ucas_file.tell() % 0x10 != 0):
                ucas_file.seek(ucas_file.tell() + 0x10 - (ucas_file.tell() % 0x10))
            oodle_magic = int.from_bytes(ucas_file.read(1), "big")
            oodle_compressor = int.from_bytes(ucas_file.read(1), "big") #idk, just guessing what this is
            if (oodle_magic != 0x8C or oodle_compressor > 0x10):
                ucas_file.seek(-2, 1)
                if (x+1 < FilteredList[i]["block_count"]):
                    chunks.append(ucas_file.read(262144))
                else:
                    chunks.append(ucas_file.read(FilteredList[i]["dec_size"] - (x * 262144)))
                continue
            block_size = int.from_bytes(ucas_file.read(3), "big") + 6
            flag = int.from_bytes(ucas_file.read(1), "big")
            ucas_file.seek(-6, 1)
            chunk_pos = ucas_file.tell()
            if (flag != 0):
                bytedata = ucas_file.read(block_size)
            else:
                bytedata = ucas_file.read(6)
            if (x+1 < FilteredList[i]["block_count"]):
                catch = subprocess.run(["Oodle.exe", "-d", "262144", "stdin=%d" % len(bytedata), "stdout"], input=bytedata, capture_output=True, text=False)
                if (catch.stderr != b""):
                    print(catch.stderr.decode("ascii"))
                    print("Chunk: %d/%d" % (x+1, FilteredList[i]["block_count"]))
                    print("Error while decompressing chunk at offset: 0x%X!" % chunk_pos)
                    print("File offset: 0x%X" % file_pos)
                    sys.exit(1)
            else:  
                catch = subprocess.run(["Oodle.exe", "-d", "%d" % (FilteredList[i]["dec_size"] - (x * 262144)), "stdin=%d" % len(bytedata), "stdout"], input=bytedata, capture_output=True, text=False)
                if (catch.stderr != b""):
                    print(catch.stderr.decode("ascii"))
                    print("Chunk: %d/%d" % (x+1, FilteredList[i]["block_count"]))
                    print("Error while decompressing chunk at offset: 0x%X!" % chunk_pos)
                    print("File offset: 0x%X" % file_pos)
                    sys.exit(1)
            chunks.append(catch.stdout)
        conc_file = open(FilteredList[i]["filepath"], "wb")
        conc_file.write(b"".join(chunks))
        end_size = conc_file.tell()
        conc_file.close()
        if (end_size != FilteredList[i]["dec_size"]):
            print("Decompressed file has wrong size!")
            print("Expected: %dB" % FilteredList[i]["dec_size"])
            print("Got: %dB" % end_size)
            os.remove(FilteredList[i]["filepath"])
            sys.exit(1)

ucas_file.close()
