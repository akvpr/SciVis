import sys
import math

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

    #Reads a vcf file with name string given by toRead.
    #Stores meta information lines and inserts variants located in a chromosome
    #into corresponding chromosome items created by reading a tab file.
    #note that tab file has to have been read first.
    def readVCF(self, toRead):
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
                fields = line.split('\t')
                chromRefName = fields[0]
                #Iterate through chromosome list to find match to insert data into
                for chromo in self.chromosomes:
                    if chromo.name == chromRefName:
                        #The ALT field is stripped of its '< >'
                        if fields[4].startswith('<'):
                            fields[4] = fields[4].strip('<')
                            fields[4] = fields[4].strip('>')
                        #the INFO field is here processed, looking for the END and GENE data points
                        list = fields[7].split(';')
                        END = '.'
                        for index in range(len(list)):
                            if list[index].startswith('END'):
                                END = list[index].split('=')[1]
                            if list[index].startswith('CSQ'):
                                #The CSQ field has several sub-fields, each separated with ','
                                sub_list = list[index].split(',')
                                geneList = []
                                for sub_index in range(len(sub_list)):
                                    #The gene name field is always the fourth element in the CSQ field separated with '|'
                                    sub_sub_list = sub_list[sub_index].split('|')
                                    geneList.append(sub_sub_list[3])
                                #Convert the list to a set to remove any duplicates
                                geneSet = set(geneList)
                                s = ', '
                                GENES = s.join(geneSet)
                            if list[index].startswith('CYTOBAND'):
                                sub_list = list[index].split('=')
                                #CBAND = sub_list[1].split(',')[0]
                                CBAND = sub_list[1]

                        chromo.addVariant(fields[1],fields[4], fields[7],END,GENES,CBAND)
                        break

            #DEBUG: print where variants are found, how many
            #print("Found %d variants:" % (numvars))
            #for chromo in self.chromosomes:
            #    print("%d in chromosome " % (len(chromo.variants)) + chromo.name)
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

    def addVariant(self,pos,alt,info,end,gene,cband):
        variant = [pos,alt,info,end,gene,cband]
        self.variants.append(variant)

    def createConnections(self):
        #Checks if the fourth field in the variant array i.e. the "ALT" field starts with "N", this implies the variant has an interaction
        #These corresponding values for the variant are then added to the list: CHRA,CHRB,WINA,WINB,CBANDS
        for variant in self.variants:
            if variant[1].startswith('N'):
                list = variant[2].split(';')
                connection = [list[1].split('=')[1], list[3].split('=')[1], list[2].split('=')[1], list[4].split('=')[1], list[16].split('=')[1]]
                self.connections.append(connection)
