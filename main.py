import sys
import os.path
import re
import json

# write a default config if it's not found
if not os.path.exists(os.path.join(os.getcwd(), "OrphanRadarConfig.json")):
    print("Couldn't find config file, writing a default one")
    defaultConfig = {"language code": "ru",
                     "jump one directory upwards": False,
                     "translation strings to skip": [""]}
    with open("OrphanRadarConfig.json", "w") as configFile:
        json.dump(defaultConfig, configFile, indent = 2)
        print("Default config file created")
    if str(input("Input y to proceed with default settings,\nanything else to quit: ")) != "y":
        sys.exit()

# open config file & load all config vars
config = open("OrphanRadarConfig.json", "r")
config = json.load(config)
LangCode = config["language code"]
jumpOneDirUp = config["jump one directory upwards"]
TLStringsToSkip = []
for string in config["translation strings to skip"]:
    TLStringsToSkip.append(string)

# jump 1-dir upwards
if jumpOneDirUp:
    os.chdir("..")

DirGame = os.getcwd()

DirTL = os.getcwd() + "\\tl" + "\\" + LangCode

# safety
print("Working directory, MUST be 'YourProjectName\\game':", os.getcwd())
print("Translation directory:", DirTL)
if not os.path.isdir(DirTL):
    print("Translation directory not found! Make sure the language code is correct.")
    input("\nPress any key to quit.")
    sys.exit()
if "\\game" not in os.getcwd():
    input("\n'game' not found in the working directory path.\nProceed at yer own risk.")
if str(input("Input y to proceed: ")) != "y":
    sys.exit()

# step #1
# grab all game rpy files and translation rpy files
AllFilePaths_GameRpys = set()
AllFilePaths_TLRpys = set()

print("---------")
print("gathering all .rpy files in /game dir")
for path, subdirs, files in os.walk(DirGame, topdown = False):
    for name in files:
        if name.endswith(".rpy"):
            AllFilePaths_GameRpys.add(path + "\\" + name)
print(f"game rpy files: {len(AllFilePaths_GameRpys)}")

print("---------")
print(f"gathering all .rpy files in tl/{LangCode} dir")
for path, subdirs, files in os.walk(DirTL, topdown = False):
    for name in files:
        # yea trippy i know
        if name.endswith(".rpy") and not name.endswith("common.rpy"):
            AllFilePaths_TLRpys.add(path + "\\" + name)

print(f"translation rpy files: {len(AllFilePaths_TLRpys)}")


# step #2
# gather all oldnew blocks
print("---------")
print("gathering all old-new blocks")
AllOldNewBlocks = []
class OldNewBlock:
    def __init__(self, OldLineNumber, OldString, FilePath):
        self.OldLineNumber = OldLineNumber
        self.OldString = OldString
        self.FilePath = FilePath

for fileindex, filepath in enumerate(AllFilePaths_TLRpys):
    # open a file
    rpyfile = open(filepath, "r", encoding = "utf-8")
    FileLines = rpyfile.readlines()
    # hax
    FileLines.insert(0, "")
    # read through all strings in file
    for num, string in enumerate(FileLines):
        # grab an oldnew block
        if FileLines[num].startswith("    old") and FileLines[num + 1].startswith("    new"):
            QuoteFirst = string.find("\"")
            QuoteLast = string.rfind("\"")
            StringToSave = string[QuoteFirst + 1:QuoteLast]
            ONBlock = OldNewBlock(num, StringToSave, filepath)
            AllOldNewBlocks.append(ONBlock)

    print(f"{round(fileindex / len(AllFilePaths_TLRpys) * 100, 2)}%", end = "\r")
    # close rpy file we've checked, we're not monsters
    rpyfile.close()

print(f"old-new blocks: {len(AllOldNewBlocks)}")

# step 3
# gather all _()-wrapped strings
# its a set bc we dont care bout dupes here
print("---------")
print("gathering all _()-wrapped or menu choice strings in the game")
AllTLStrings = set()
for fileindex, filepath in enumerate(AllFilePaths_GameRpys):
    rpyfile = open(filepath, "r", encoding = "utf-8")
    FileLines = rpyfile.readlines()
    for FileLine in FileLines:
        Line = FileLine.strip()
        # check if its a menu string
        IsMenuString = None
        # there must be a : in a choice
        if ":" in Line:
            # and they must be on the very start of the line
            if any([Line.startswith("'"), Line.startswith('"')]):
                # split in two by the :
                SplitLine = Line.split(":")
                # split right part further by the #, see if the remainer is nothing
                if len(SplitLine[1].split("#")[0].strip()) == 0:
                    QuoteType = Line[0]
                    StringEndIndex = SplitLine[0].find(QuoteType, 1)
                    IsMenuString = SplitLine[0][1:StringEndIndex]

        # if it is, fix it's first string as the only one
        if IsMenuString is not None:
            AllTLStrings.add(IsMenuString)
            #print(f"found translate entry: {IsMenuString}")

        # if it isnt, do the double-parse (for _(strings))
        else:
            MatchesDoubleQuote = re.findall(r'[_][(][\"](.+?)[\"][)]', Line)
            MatchesSingleQuote = re.findall(r"[_][(][\'](.+?)[\'][)]", Line)
            for Entry in MatchesDoubleQuote + MatchesSingleQuote:
                AllTLStrings.add(Entry.replace('"', '\\"'))

    print(f"{round(fileindex / len(AllFilePaths_GameRpys) * 100, 2)}%", end = "\r")
    rpyfile.close()

print(f"_()-wrapped or menu choice strings: {len(AllTLStrings)}")

print("---------")
print("looking for orphaned old-new blocks")
# compare each oldnew block to tl-strings if it exists in there
OrphanedONBlocks = 0
for ONBlock in AllOldNewBlocks:
    if ONBlock.OldString not in AllTLStrings and ONBlock.OldString not in TLStringsToSkip:
        print("orphaned old-new block found:")
        print(f"{ONBlock.OldString}")
        print("File path:", ONBlock.FilePath)
        print("Line:", ONBlock.OldLineNumber)
        print("\n")
        OrphanedONBlocks += 1


if OrphanedONBlocks > 0:
    print("\n")
    print(f"orphaned old-new blocks: {OrphanedONBlocks}")
else:
    print("no orphan old-new blocks found. naisu!")
    print("---------")

input("\nPress any key to quit.")