import sys
import math
import readVCF

class Reader():

    def __init__(self):
        self.numChr = 0
        self.chromosomes = []
        self.totalBP = 0
        self.vcfInfoLines = []
        self.coverageNorm = 0
        self.coverageNormLog = 0
        self.colorTabInfo = []
        self.cytoTabInfo = []

    #Reads a tab file with name string given by toRead.
    #Constructs a list of chromosome items, one per chromosome, and inserts
    #chromosome name, start bp, end bp, coverage per 1000 bp in these items.
    def readTab(self,toRead):
        totalReadLines = 0
        self.tabFileName = toRead
        with open(toRead, 'r') as tab:

            #Read the first line in the file, should start with #CHR.
            line = tab.readline()
            if (not line.startswith("#CHR")):
                print('TAB file is not in correct format')
                return -1
            else:
                print('TAB file seems ok, continuing read')

            #Read the second line and create the first Chromosome object.
            #All following lines should be formatted as: chrName\tstart\tend\tcoverage
            line = tab.readline()
            fields = line.split('\t')
            if (not len(fields) == 4):
                print("TAB file not formatted correctly on line 2")
                return -1
            else:
                curChrName = fields[0]
                chrom = Chromosome(curChrName, fields[1])
                chrom.addCoverage(float(fields[3]))
                self.coverageNorm += float(fields[3])
                if(float(fields[3])) > 0:
                    self.coverageNormLog += math.log(float(fields[3]),2)
                totalReadLines += 1
                lastRead = line
                self.chromosomes.append(chrom)
                self.numChr += 1

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
                    self.chromosomes.append(chrom)
                    self.numChr += 1
                #Every line contains coverage data of interest, for current chromosome
                chrom.addCoverage(float(fields[3]))
                self.coverageNorm += float(fields[3])
                if(float(fields[3])) > 0:
                    self.coverageNormLog += math.log(float(fields[3]),2)
                totalReadLines += 1
                #Store last read line and go to next line
                lastRead = line
            chrom.setEnd(lastRead.split('\t')[2])

            self.coverageNorm = self.coverageNorm / totalReadLines
            self.coverageNormLog = self.coverageNormLog / totalReadLines

            #DEBUG: print read data (and also sum total bp, move elsewhere later maybe)
            #print("%d chromosomes read: " % (self.numChr))
            for i in range(0,self.numChr):
                self.totalBP += int(self.chromosomes[i].end)
                curChr = self.chromosomes[i]
                #print("Name: %s\nStart: %s\nEnd: %s\n" % (curChr.name,curChr.start,curChr.end))
            #print("Total base pairs: %d" % (self.totalBP))
            return 1

    def returnTotalBP(self):
        return self.totalBP

    def returnChrList(self):
        return self.chromosomes

    def returnCoverageNorm(self):
        return self.coverageNorm

    def returnCoverageNormLog(self):
        return self.coverageNormLog

    def readColorTab(self, toRead):
        self.colorTabName = toRead
        with open(toRead, 'r') as tab:

            #Read the first line in the file, should start with #chromosome.
            line = tab.readline()
            if (not line.startswith("#chromosome")):
                print('TAB file is not in correct format')
                return -1
            else:
                print('TAB file seems ok, continuing read')
            #The fields are as follwing: #chromosome, startPos, endPos, color
            for line in tab:
                fields = line.split('\t')
                fields[3] = fields[3].strip('\n')
                colorTab = [fields[0], fields[1], fields[2], fields[3]]
                self.colorTabInfo.append(colorTab)

    def returnColorTab(self):
        return self.colorTabInfo

    def readCytoTab(self, toRead):
        self.cytoTabName = toRead
        with open(toRead, 'r') as tab:

			#Read the first line in the file, should start with #chromosome.
            line = tab.readline()
            if (not line.startswith("chr1")):
                print('TAB file is not in correct format')
                return -1
            else:
                print('CytoBandTAB file seems ok, continuing read')
            #The fields are as following: #chromosome, startPos, endPos, cytoband, stain value
            fields = line.split('\t')
            fields[0] = fields[0].strip('chr')
            fields[4] = fields[4].strip('\n')
            cytoTab = [fields[0], fields[1], fields[2], fields[3], fields[4]]
            self.cytoTabInfo.append(cytoTab)
            for line in tab:
                fields = line.split('\t')
                fields[0] = fields[0].strip('chr')
                fields[4] = fields[4].strip('\n')
                cytoTab = [fields[0], fields[1], fields[2], fields[3], fields[4]]
                self.cytoTabInfo.append(cytoTab)

    def returnCytoTab(self):
        return self.cytoTabInfo

    def readVCFFile(self, toRead):
        self.vcfFileName = toRead
        with open(toRead, 'r') as vcf:

            #The first lines should be a number of meta-information lines, prepended by ##.
            #Should begin with fileformat. Store these. Check first line for correct format.
            line = vcf.readline()
            if (not line.startswith("##fileformat=")):
                print("VCF file is not in correct format")
                return -1
            else:
                print("VCF file seems ok, continuing read")
            while (line.startswith("##")):
                self.vcfInfoLines.append(line)
                line = vcf.readline()

            #A header line prepended by # should follow containing 8 fields, tab-delimited.
            #These are in order CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO. Store in info line list.
            fields = line.split('\t')
            if (not (line.startswith('#') or len(fields) == 8) ):
                print("Header columns missing in VCF file")
                return -1
            else:
                self.vcfInfoLines.append(line)

            #All following lines are tab-delmited data lines.
            #Store variant data in chromosome item corresponding to CHROM field
            numvars = 0
            for line in vcf:
                numvars += 1
                #Feed every data line into readVCF, returning: (chrA,posA,chrB,posB,event_type,description,format)
                (chrA,posA,chrB,posB,event_type,description,format) = readVCF.readVCFLine(line)
                #Iterate through chromosome list to find match to insert data into
                for chromo in self.chromosomes:
                    if chromo.name == chrA:
                        chromo.addVariant(chrA,posA,chrB,posB,event_type,description,format)
                        break
            return 1

    def returnVCFHeader(self):
        #The last element of information lines should be the header, if we have read a VCF file.
        #Returns an empty list if vcfInfoLines is not populated, -1 if a vcf file has not been read.
        if self.vcfInfoLines:
             return self.vcfInfoLines[-1]
        else:
             return -1

    def returnVCFInfo(self):
        return self.vcfInfoLines

    def returnTabName(self):
        return self.tabFileName

    def returnVcfName(self):
        return self.vcfFileName

class Chromosome():

    def __init__(self, name, start):
        self.name = name
        self.start = start
        self.coverage = []
        self.coverageLog = []
        self.display = True
        self.variants = []
        self.connections = []
        self.connection_list = []
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
        #For every variant we would like the genes in CSQ
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
        #We would also like the CYTOBAND field, if this exists
        if "CYTOBAND" in description:
            cband = description["CYTOBAND"]
        else:
            cband = None
        #Add the variant data to this chromosome
        variant = [chrA,posA,chrB,posB,event_type,description,format,allGenes,cband]
        self.variants.append(variant)

    def createConnections(self):
        #These corresponding values for the variant are added to the list: CHRA,CHRB,WINA,WINB,CYTOBAND
        for variant in self.variants:
            if variant[0] is not variant[2]:
                description = variant[5]
                if "CYTOBAND" in description:
                    cband = description["CYTOBAND"]
                else:
                    cband = None
                connection = [description["CHRA"],description["CHRB"],description["WINA"],description["WINB"],cband]
                self.connections.append(connection)
