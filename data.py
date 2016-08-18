import sys
import math
import readVCF
import fileinput

#Reads a tab file with name string given by toRead.
#Constructs a list of chromosome items, one per chromosome, and inserts
#chromosome name, start bp, end bp, coverage per 1000 bp in these items.
def readTab(toRead):
    totalReadLines = 0
    tabFileName = toRead
    chromosomes = []
    coverageNorm = 0
    coverageNormLog = 0
    totalBP = 0
    numChr = 0
    with open(toRead, 'r') as tab:
            #Read the first line in the file, should start with #CHR.
        line = tab.readline()
        if (not line.startswith("#CHR")):
            print('TAB file is not in correct format')
            return None
        else:
            print('TAB file seems ok, continuing read')

        #Read the second line and create the first Chromosome object.
        #All following lines should be formatted as: chrName\tstart\tend\tcoverage
        line = tab.readline()
        fields = line.split('\t')
        if (not len(fields) == 4):
            print("TAB file not formatted correctly on line 2")
            return None
        else:
            curChrName = fields[0]
            chrom = Chromosome(curChrName, fields[1])
            chrom.addCoverage(float(fields[3]))
            coverageNorm += float(fields[3])
            if(float(fields[3])) > 0:
                coverageNormLog += math.log(float(fields[3]),2)
            totalReadLines += 1
            lastRead = line
            chromosomes.append(chrom)
            numChr += 1

        #Iterate over the rest of the lines in the file
        for line in tab:
            fields = line.split('\t')
            if (not len(fields) == 4):
                print("TAB file not formatted correctly")
                return -1
            #If we come across a new chromosome, assign end on current chromosome (contained in last read line)
            #Then create a new Chromosome object, assign name & start. Add to list.
            if fields[0] != curChrName:
                chrom.setEnd(lastRead.split('\t')[2])
                curChrName = fields[0]
                chrom = Chromosome(curChrName, fields[1])
                chromosomes.append(chrom)
                numChr += 1
            #Every line contains coverage data of interest, for current chromosome
            chrom.addCoverage(float(fields[3]))
            coverageNorm += float(fields[3])
            if(float(fields[3])) > 0:
                coverageNormLog += math.log(float(fields[3]),2)
            totalReadLines += 1
            #Store last read line and go to next line
            lastRead = line
        chrom.setEnd(lastRead.split('\t')[2])

        coverageNorm = coverageNorm / totalReadLines
        coverageNormLog = coverageNormLog / totalReadLines

    #sum total read bp
    for chromo in chromosomes:
        totalBP += int(chromo.end)
    return (chromosomes,coverageNorm,coverageNormLog,totalBP)

def readCytoTab(toRead):
    cytoTabName = toRead
    cytoTabInfo = []
    with open(toRead, 'r') as tab:

		#Read the first line in the file, should start with #chromosome.
        line = tab.readline()
        if (not line.startswith("chr1")):
            print('TAB file is not in correct format')
            return None
        else:
            print('CytoBandTAB file seems ok, continuing read')
        #The fields are as following: #chromosome, startPos, endPos, cytoband, stain value
        fields = line.split('\t')
        fields[0] = fields[0].strip('chr')
        fields[4] = fields[4].strip('\n')
        cytoTab = [fields[0], fields[1], fields[2], fields[3], fields[4]]
        cytoTabInfo.append(cytoTab)
        for line in tab:
            fields = line.split('\t')
            fields[0] = fields[0].strip('chr')
            fields[4] = fields[4].strip('\n')
            cytoTab = [fields[0], fields[1], fields[2], fields[3], fields[4]]
            cytoTabInfo.append(cytoTab)
    return cytoTabInfo

def readVCFFile(toRead, chromosomes):
    vcfFileName = toRead
    vcfInfoLines = []
    with open(toRead, 'r') as vcf:

        #The first lines should be a number of meta-information lines, prepended by ##.
        #Should begin with fileformat. Store these. Check first line for correct format.
        line = vcf.readline()
        if (not line.startswith("##fileformat=")):
            print("VCF file is not in correct format")
            return None
        else:
            print("VCF file seems ok, continuing read")
        while (line.startswith("##")):
            vcfInfoLines.append(line)
            line = vcf.readline()

        #A header line prepended by # should follow containing 8 fields, tab-delimited.
        #These are in order CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO. Store in info line list.
        fields = line.split('\t')
        if (not (line.startswith('#') or len(fields) == 8) ):
            print("Header columns missing in VCF file")
            return None
        else:
            vcfInfoLines.append(line)

        #All following lines are tab-delmited data lines.
        #Store variant data in chromosome item corresponding to CHROM field
        numvars = 0
        for line in vcf:
            numvars += 1
            #Feed every data line into readVCF, returning: (chrA,posA,chrB,posB,event_type,description,format)
            (chrA,posA,chrB,posB,event_type,description,format) = readVCF.readVCFLine(line)
            #Iterate through chromosome list to find match to insert data into
            for chromo in chromosomes:
                if chromo.name == chrA:
                    chromo.addVariant(chrA,posA,chrB,posB,event_type,description,format)
                    break
        return (chromosomes,vcfInfoLines)

#Reads a general tab delimited file (such as a bed file)
def readGeneralTab(toRead):
    tabLines = []
    with open(toRead, 'r') as tab:
        #Skip first line
        line = tab.readline()
        for line in tab:
            #The fields are as following: #chromosome, startPos, endPos, text
            fields = line.split('\t')
            fields[0] = fields[0].replace("chr","").replace("Chr","").replace("CHR","")
            fields[-1] = fields[-1].strip('\n')
            tabLines.append(fields)
    return tabLines

def readConfig(toRead):
    circularConfig = {}
    coverageConfig = {}
    karyoConfig = {}
    heatmapConfig = {}
    colorConfig = {}
    with open(toRead, 'r') as config:
        activeSection = "CIRCULAR"
        for line in config:
            if line.startswith('#'):
                continue
            if line.startswith('['):
                if line.startswith('[CIRCULAR]'):
                    activeSection = 'CIRCULAR'
                elif line.startswith('[COVERAGE]'):
                    activeSection = 'COVERAGE'
                elif line.startswith('[KARYOGRAM]'):
                    activeSection = 'KARYOGRAM'
                elif line.startswith('[HEATMAP]'):
                    activeSection = 'HEATMAP'
                elif line.startswith('[COLORS]'):
                    activeSection = 'COLORS'
            else:
                if activeSection == "CIRCULAR":
                    fields = line.split('=')
                    circularConfig[fields[0]] = fields[1].strip('\n')
                elif activeSection == "COVERAGE":
                    fields = line.split('=')
                    coverageConfig[fields[0]] = fields[1].strip('\n')
                elif activeSection == "KARYOGRAM":
                    fields = line.split('=')
                    karyoConfig[fields[0]] = fields[1].strip('\n')
                elif activeSection == "HEATMAP":
                    fields = line.split('=')
                    heatmapConfig[fields[0]] = fields[1].strip('\n')
                elif activeSection == 'COLORS':
                    fields = line.split('=')
                    fields[1] = fields[1]
                    colorConfig[fields[0]] = fields[1].strip('\n')
    return (circularConfig,coverageConfig,karyoConfig,heatmapConfig,colorConfig)

def saveConfig(fileName,circularConfig,coverageConfig,karyoConfig,heatmapConfig,colorConfig):

    with open(fileName,'r+') as config:
        configData = config.readlines()
        activeSection = "CIRCULAR"
        newData = []
        for line in configData:
            if line.startswith('#'):
                line = line.strip('\n')
                newData.append(line)
                continue
            if line.startswith('['):
                if line.startswith('[CIRCULAR]'):
                    activeSection = 'CIRCULAR'
                elif line.startswith('[COVERAGE]'):
                    activeSection = 'COVERAGE'
                elif line.startswith('[KARYOGRAM]'):
                    activeSection = 'KARYOGRAM'
                elif line.startswith('[HEATMAP]'):
                    activeSection = 'HEATMAP'
                elif line.startswith('[COLORS]'):
                    activeSection = 'COLORS'
            else:
                if activeSection == "CIRCULAR":
                    fields = line.split('=')
                    line = line.replace(fields[1],circularConfig[fields[0]])
                elif activeSection == "COVERAGE":
                    fields = line.split('=')
                    line = line.replace(fields[1],coverageConfig[fields[0]])
                elif activeSection == "KARYOGRAM":
                    fields = line.split('=')
                    line = line.replace(fields[1],karyoConfig[fields[0]])
                elif activeSection == "HEATMAP":
                    fields = line.split('=')
                    line = line.replace(fields[1],heatmapConfig[fields[0]])
                elif activeSection == 'COLORS':
                    pass
            line = line.strip('\n')
            newData.append(line)
        config.seek(0)
        config.truncate()
        for line in newData:
            config.write(line + '\n')

class Chromosome():

    def __init__(self, name, start):
        self.name = name
        self.start = start
        self.coverage = []
        self.coverageLog = []
        self.display = False
        self.variants = []
        self.connections = []
        self.display_connections = False
        self.display_cytoBandNames = False

    def addCoverage(self, coverageValue):
        self.coverage.append(coverageValue)
        if(coverageValue > 0):
            self.coverageLog.append(math.log(coverageValue,2))
        else:
            self.coverageLog.append(0)

    def setEnd(self,end):
        self.end = end

    def addVariant(self,chrA,posA,chrB,posB,event_type,description,format):
        #The variants are by default set to be shown
        display_variant = True
        marked = False
        #For every variant we would like the genes in CSQ, if this exists
        if "CSQ" in description:
            csqField = description["CSQ"]
            #The CSQ field has several sub-fields, each separated with ','
            subList = csqField.split(',')
            geneList = []
            for subIndex in range(len(subList)):
                #The gene name field is always the fourth element in the CSQ field separated with '|'
                subSubList = subList[subIndex].split('|')
                geneList.append(subSubList[3])
            #Convert the list to a set to remove any duplicates
            geneSet = set(geneList)
            s = ', '
            allGenes = s.join(geneSet)
        else:
            allGenes = ""
        #We would also like the CYTOBAND field, if this exists
        if "CYTOBAND" in description:
            cband = description["CYTOBAND"]
        else:
            cband = None
        if "RankScore" in description:
            rankScore = description["RankScore"]
        else:
            rankScore = None
        #Add the variant data to this chromosome
        variant = [chrA,posA,chrB,posB,event_type,description,format,allGenes,cband,display_variant,rankScore, marked]
        self.variants.append(variant)

    def createConnections(self):
        #These corresponding values for the variant are added to the list: CHRA,CHRB,WINA,WINB,CYTOBAND
        self.connections = []
        for variant in self.variants:
            if not variant[9]:
                continue
            else:
                description = variant[5]
                if "CYTOBAND" in description:
                    cband = description["CYTOBAND"]
                else:
                    cband = None
                if variant[0] is not variant[2]:
                    connection = [variant[0],variant[2],description["WINA"],description["WINB"],cband]
                    self.connections.append(connection)
                else:
                    connection = [variant[0], variant[2], str(variant[1]) + "," + str(variant[1]), str(variant[3]) + "," + str(variant[3]), cband]
                    self.connections.append(connection)
