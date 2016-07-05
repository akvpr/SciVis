import sys
import random
import math
import data
from PySide.QtCore import *
from PySide.QtGui import *

class CircosView(QGraphicsView):

    def __init__(self,dataDict):
        self.type = "circos"
        self.scene = CircosScene()
        super().__init__(self.scene)
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.numChr = len(self.chromosomes)
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.chromosomeItems = []
        self.coverageItems = []
        self.distanceMarkerItems = []
        self.chromosome_connection_list = []
        self.regionItems = []
        self.legendItems = []
        self.activeVariantModels = {}
        self.activeVariantTables = {}

        self.bpWindow = 500
        self.bpDistanceResolution = 10
        self.useCoverageLog = True
        self.minCoverage = 0.5
        self.maxCoverage = 1.5
        self.startColor = QColor.fromRgb(243,241,172)
        self.connWidth = 1
        self.showChrNames = True
        self.createSettings()

        self.coverageNormLog = self.dataDict['coverageNormLog']
        self.coverageNorm = self.dataDict['coverageNorm']
        self.tabName = self.dataDict['tabName']
        self.vcfName = self.dataDict['vcfName']
        self.addFileText()
        self.createChInfo()

        self.chromosomeItems = []
        #Create a dict representing colors for the 24 default chromosomes
        self.chromoColors = {}
        color = self.startColor
        for i in range(24):
            self.chromoColors[self.chromosomes[i].name] = color
            color = color.darker(105)
        self.initscene()
        self.showChInfo()

    def returnActiveDataset(self):
        return self.dataDict

    def closeOpenWindows(self):
        try:
            self.chDia.close()
        except:
            pass

    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = ["bpWindow", "distanceMarkerResolution", "useCoverageLog", "minCoverage", "maxCoverage", "connectionWidth"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        bpWinText = QStandardItem("BP Resolution (kb)")
        bpWinText.setEditable(False)
        bpWinText.setToolTip("No. of base pairs (x1000) used to average data in calculations.\nSmaller values may decrease performance.")
        bpWinData = QStandardItem()
        bpWinData.setData(self.bpWindow,0)
        bpWinData.setEditable(True)
        distResText = QStandardItem("Distance between each marker (Mb)")
        distResText.setEditable(False)
        distResText.setToolTip("Set the distance between each marker around the circle")
        distResData = QStandardItem()
        distResData.setData(self.bpDistanceResolution,0)
        distResData.setEditable(True)
        useCovLog = QStandardItem("Use log2 of coverage")
        useCovLog.setEditable(False)
        useCovLog.setToolTip("Use log2(value) for coverage values when displaying coverage graph?")
        useCovLogCheck = QStandardItem()
        useCovLogCheck.setCheckable(True)
        useCovLogCheck.setCheckState(Qt.Checked)
        useCovLogCheck.setEditable(False)
        minCovLimitText = QStandardItem("Min.coverage value (%)")
        minCovLimitText.setEditable(False)
        minCovLimitText.setToolTip("Minimum coverage value in coverage graph,\nin percentage of average coverage value of genome.")
        minCovLimitData = QStandardItem()
        minCovLimitData.setData(self.minCoverage*100,0)
        minCovLimitData.setEditable(True)
        maxCovLimitText = QStandardItem("Max. coverage value (%)")
        maxCovLimitText.setEditable(False)
        maxCovLimitText.setToolTip("Maximum coverage value in coverage graph,\nin percentage of average coverage value of genome.")
        maxCovLimitData = QStandardItem()
        maxCovLimitData.setData(self.maxCoverage*100,0)
        maxCovLimitData.setEditable(True)
        connPenWidthText = QStandardItem("Width of connections")
        connPenWidthText.setEditable(False)
        connPenWidthText.setToolTip("Set the size (in pixels) of the connection lines")
        connPenWidthData = QStandardItem()
        connPenWidthData.setData(self.connWidth,0)
        connPenWidthData.setEditable(True)
        showChrNameText = QStandardItem("Show chromosome names")
        showChrNameText.setEditable(False)
        showChrNameText.setToolTip("Show or hide the chromosome names on the circos diagram")
        showChrNameCheck = QStandardItem()
        showChrNameCheck.setCheckable(True)
        showChrNameCheck.setCheckState(Qt.Checked)
        showChrNameCheck.setEditable(False)
        self.settingsModel.setItem(0,0,bpWinText)
        self.settingsModel.setItem(0,1,bpWinData)
        self.settingsModel.setItem(1,0,distResText)
        self.settingsModel.setItem(1,1,distResData)
        self.settingsModel.setItem(2,0,useCovLog)
        self.settingsModel.setItem(2,1,useCovLogCheck)
        self.settingsModel.setItem(3,0,minCovLimitText)
        self.settingsModel.setItem(3,1,minCovLimitData)
        self.settingsModel.setItem(4,0,maxCovLimitText)
        self.settingsModel.setItem(4,1,maxCovLimitData)
        self.settingsModel.setItem(5,0,connPenWidthText)
        self.settingsModel.setItem(5,1,connPenWidthData)
        self.settingsModel.setItem(6,0,showChrNameText)
        self.settingsModel.setItem(6,1,showChrNameCheck)
        self.settingsModel.itemChanged.connect(self.updateSettings)

    def viewSettings(self):
        self.settingsList = QTableView()
        self.settingsList.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.settingsList.setShowGrid(False)
        self.settingsList.horizontalHeader().hide()
        self.settingsList.verticalHeader().hide()
        self.settingsList.setModel(self.settingsModel)
        self.settingsList.setTextElideMode(Qt.ElideNone)
        self.settingsDia = QDialog(self)
        self.settingsDia.setWindowTitle("Settings")
        applyButton = QPushButton('Apply', self.settingsDia)
        applyButton.clicked.connect(self.settingsDia.accept)
        self.settingsDia.layout = QGridLayout(self.settingsDia)
        self.settingsDia.layout.addWidget(self.settingsList,0,0,1,3)
        self.settingsDia.layout.addWidget(applyButton,1,0,1,1)
        self.settingsDia.show()

    def updateSettings(self,item):
        if item.row() == 0:
            self.bpWindow = item.data(0)
        if item.row() == 1:
            self.bpDistanceResolution = item.data(0)
        if item.row() == 2:
            self.useCoverageLog = not self.useCoverageLog
        if item.row() == 3:
            self.minCoverage = item.data(0)/100
        if item.row() == 4:
            self.maxCoverage = item.data(0)/100
        if item.row() == 5:
            self.connWidth = item.data(0)
        if item.row() == 6:
           self.showChrNames = not self.showChrNames

    #Sums the end bp for every chromosome with display toggled on
    def returnTotalDisplayedBP(self):
        totalDispBP = 0
        for chromo in self.chromosomes:
            if chromo.display:
                totalDispBP += int(chromo.end)
        return totalDispBP

    #Updates display toggles according to this scene's active chModel
    def updateToggles(self):
        for row in range(self.chModel.rowCount()):
            dispConnItem = self.chModel.item(row,4)
            dispItem = self.chModel.item(row,3)
            if (dispItem.checkState() == Qt.Checked):
                self.chromosomes[row].display = True
            else:
                self.chromosomes[row].display = False
            if (dispConnItem.checkState() == Qt.Checked):
                self.chromosomes[row].display_connections = True
            else:
                self.chromosomes[row].display_connections = False
        self.initscene()

    #Creates data model for info window
    def createChInfo(self):
        self.chModel = QStandardItemModel()
        topstring = ["Name","Length","No. of variants","Display","Draw connections"]
        self.chModel.setHorizontalHeaderLabels(topstring)
        for chromo in self.chromosomes:
            infostring = [chromo.name,chromo.end,str(len(chromo.variants))]
            infoItems = [QStandardItem(string) for string in infostring]
            dispCheckItem = QStandardItem()
            dispCheckItem.setCheckable(False)
            connCheckItem = QStandardItem()
            connCheckItem.setCheckable(False)
            connCheckItem.setCheckState(Qt.Unchecked)
            checkList = [dispCheckItem, connCheckItem]
            infoItems.extend(checkList)
            chromo.display_connections = False
            #only keep chromosomes up to MT (no. 24), but toggle MT display off as default
            #do not add GLxxxx chr (no.25 and up)
            if (self.chromosomes.index(chromo) < 24):
                dispCheckItem.setCheckState(Qt.Checked)
                self.chModel.appendRow(infoItems)
                chromo.display = True
            elif (self.chromosomes.index(chromo) == 24):
                dispCheckItem.setCheckState(Qt.Unchecked)
                chromo.display = False
                self.chModel.appendRow(infoItems)
            else:
                chromo.display = False

    #Creates a window with chromosomes and toggles, info
    def showChInfo(self):
        #if any earlier window is open, close it
        try:
            self.chDia.close()
        except:
            pass
        self.chList = QTableView()
        self.chList.verticalHeader().hide()
        self.chList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.chList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.chList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.chList.setShowGrid(False)
        self.chList.setModel(self.chModel)
        self.chList.resizeColumnsToContents()
        #Give the length column some extra space..
        curWidth = self.chList.columnWidth(1)
        self.chList.setColumnWidth(1,curWidth+20)
        self.chDia = QDialog(self)
        self.chDia.setWindowTitle("Chromosome info")
        #Button for toggling display of selected chromosomes in the scene
        togButton = QPushButton('Toggle display', self.chDia)
        togButton.clicked.connect(self.toggleDisp)
        #Button for viewing selected chromosome variants
        viewVarButton = QPushButton('View variants', self.chDia)
        viewVarButton.clicked.connect(self.viewVariants)
        #Button for adding variants
        addVariantButton = QPushButton('Add variant', self.chDia)
        addVariantButton.clicked.connect(self.addVariant)
        #Button for toggling connections
        connButton = QPushButton('Toggle connections', self.chDia)
        connButton.clicked.connect(self.toggleConnections)
        self.chDia.layout = QGridLayout(self.chDia)
        self.chDia.layout.addWidget(self.chList,0,0,1,4)
        self.chDia.layout.addWidget(togButton,1,0,1,1)
        self.chDia.layout.addWidget(viewVarButton,1,1,1,1)
        self.chDia.layout.addWidget(addVariantButton,1,2,1,1)
        self.chDia.layout.addWidget(connButton,1,3,1,1)
        self.chDia.setMinimumSize(500,400)
        self.chDia.show()

    #Creates data model for variants in given chromosome
    def createVariantInfo(self, chromo):
        varModel = QStandardItemModel()
        topstring = ['TYPE', 'START', 'END', 'GENE(S)', 'CYTOBAND', 'Active']
        varModel.setHorizontalHeaderLabels(topstring)
        #Adding variant info to a list
        for variant in chromo.variants:
            infoitem = []
            #this is event_type in the variant
            infoitem.append(QStandardItem(variant[4]))
            #this is posA in the variant
            startText = str(variant[1])
            startData = QStandardItem()
            startData.setData(variant[1],0)
            infoitem.append(startData)
            #this is posB or chrB: posB in the variant (if interchromosomal)
            if variant[0] is not variant[2]:
                endText = str(variant[2]) + ": " + str(variant[3])
            else:
                endText = str(variant[3])
            infoitem.append(QStandardItem(endText))
            #this is allGenes in the variant
            infoitem.append(QStandardItem(variant[7]))
            #this is cband in the variant
            infoitem.append(QStandardItem(variant[8]))
            #this is a check for displaying a variant or not
            dispCheckItem = QStandardItem()
            dispCheckItem.setCheckable(False)
            dispCheckItem.setCheckState(Qt.Checked)
            infoitem.append(dispCheckItem)

            varModel.appendRow(infoitem)

        self.activeVariantModels[chromo.name] = varModel

    #Creates a popup containing variant info in a table.
    #Could be implemented in a better way than multiple dialogues..
    def viewVariants(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            self.createVariantInfo(chromo)
            viewVarDia = QDialog(self)
            viewVarDia.setWindowTitle("Variants in contig " + chromo.name)
            varList = QTableView()
            #Create button for activation of variants
            varButton = QPushButton('Toggle selected variant(s)', viewVarDia)
            varButton.clicked.connect(lambda: self.toggleVariants(chromo.name, row))

            varList.setSortingEnabled(True)
            varList.setMinimumSize(500,400)
            varList.verticalHeader().hide()
            varList.setEditTriggers(QAbstractItemView.NoEditTriggers)
            varList.setModel(self.activeVariantModels[chromo.name])
            varList.resizeColumnToContents(1)
            varList.horizontalHeader
            varList.horizontalHeader().sectionClicked.connect(lambda: self.sortVarList(varList,chromo))
            varList.horizontalHeader().sectionClicked.connect(chromo.sortVariants)
            #self.sortVarList()
            
            
            self.activeVariantTables[chromo.name] = varList

            viewVarDia.layout = QGridLayout(viewVarDia)
            viewVarDia.layout.addWidget(varList,0,0)
            viewVarDia.layout.addWidget(varButton, 1, 0)
            viewVarDia.show()
            
    def sortVarList(self, varList, chromo):
        activeSortType = chromo.activeSortType
        if activeSortType == 5:
            if chromo.sorted['START']:
                order = Qt.DescendingOrder
            else:
                order = Qt.AscendingOrder
            varList.sortByColumn(1, order)
        
        
        
        
        

    def toggleVariants(self, chromoName, chromoIndex):
        selectedIndexes = self.activeVariantTables[chromoName].selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            #sätta varModel i en lista å ta chromoIndex modellen för itemet
            dispVarItem = self.activeVariantModels[chromoName].item(row,5)
            if self.chromosomes[chromoIndex].variants[row][9]:
                dispVarItem.setCheckState(Qt.Unchecked)
                self.chromosomes[chromoIndex].variants[row][9] = False
            else:
                dispVarItem.setCheckState(Qt.Checked)
                self.chromosomes[chromoIndex].variants[row][9] = True
        self.chromosomes[chromoIndex].createConnections()
        self.initscene()

    def addVariant(self):
        #Adds a variant to selected chromosomes. Some models still have to be updated.
        #Not sure how to best handle input yet.
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            addVariantDialog = QDialog()
            addVariantDialog.setWindowTitle("Add variant in contig " + chromo.name)
            applyButton = QPushButton('Ok', addVariantDialog)
            applyButton.clicked.connect(addVariantDialog.accept)
            cancelButton = QPushButton('Cancel', addVariantDialog)
            cancelButton.clicked.connect(addVariantDialog.reject)
            locBoxValidator = QIntValidator(self)
            locBoxValidator.setBottom(0)
            locABox = QLineEdit()
            locBBox = QLineEdit()
            locABox.setValidator(locBoxValidator)
            locBBox.setValidator(locBoxValidator)
            chromoBox = QComboBox()
            chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
            chromoBox.addItems(chromoStrings)
            altBox = QLineEdit()
            geneBox = QLineEdit()
            locALabel = QLabel("Position A: ")
            chromoLabel = QLabel("Chromosome B: ")
            locBLabel = QLabel("Position B: ")
            altLabel = QLabel("ALT: ")
            geneLabel = QLabel("GENE(S): ")
            addVariantDialog.layout = QGridLayout(addVariantDialog)
            addVariantDialog.layout.addWidget(locALabel,0,0)
            addVariantDialog.layout.addWidget(locABox,0,1)
            addVariantDialog.layout.addWidget(chromoLabel,1,0)
            addVariantDialog.layout.addWidget(chromoBox,1,1)
            addVariantDialog.layout.addWidget(locBLabel,2,0)
            addVariantDialog.layout.addWidget(locBBox,2,1)
            addVariantDialog.layout.addWidget(altLabel,3,0)
            addVariantDialog.layout.addWidget(altBox,3,1)
            addVariantDialog.layout.addWidget(geneLabel,4,0)
            addVariantDialog.layout.addWidget(geneBox,4,1)
            addVariantDialog.layout.addWidget(applyButton,5,0)
            addVariantDialog.layout.addWidget(cancelButton,5,1)
            choice = addVariantDialog.exec_()
            if choice == QDialog.Accepted:
                #END field should only be filled if chrB is the same
                if chromoBox.currentText() == chromo.name:
                    end = locBBox.text()
                else:
                    end = "."
                chromo.addVariant(locABox.text(),altBox.text(),"",end,geneBox.text(),"")

    def addImage(self):
        size = self.size()
        outerChrRect = QRect(QPoint(50,50), QPoint(size.height()-50,size.height()-50))
        fileName = QFileDialog.getOpenFileName(None,"Specify Image file",QDir.currentPath(),
        "PNG files (*.png *.jpg *.bmp)")
        pixmap = QPixmap(fileName[0])
        if pixmap.isNull():
            print("is null")
        #Scaling the pixmap to 70% of the cirkos-diagram size
        #pixmap = pixmap.scaled(outerChrRect.size()*0.7)
        pixmapItem = QGraphicsPixmapItem(pixmap)
        #Moving the image to the right of the cirkos-diagram
        pixmapItem.setPos(outerChrRect.center().x() + (outerChrRect.width()/2) + (outerChrRect.width()/10), outerChrRect.center().y() - (pixmapItem.boundingRect().height()/2))
        self.scene.addItem(pixmapItem)
        pixmapItem.setFlag(QGraphicsItem.ItemIsMovable)

    def toggleDisp(self):
        #The row associated with the item corresponds to a chromosome
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        #Convert to a set to get unique rows, since every column in the table is selected
        selectedRows = set(selectedRows)
        for row in selectedRows:
            dispConnItem = self.chModel.item(row,4)
            dispItem = self.chModel.item(row,3)
            if (dispItem.checkState() == Qt.Checked):
                dispItem.setCheckState(Qt.Unchecked)
                self.chromosomes[row].display = False
                dispConnItem.setCheckState(Qt.Unchecked)
                self.chromosomes[row].display_connections = False
            else:
                dispItem.setCheckState(Qt.Checked)
                self.chromosomes[row].display = True
        self.initscene()

    def toggleConnections(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            dispConnItem = self.chModel.item(row,4)
            if self.chromosomes[row].display_connections:
                dispConnItem.setCheckState(Qt.Unchecked)
                self.chromosomes[row].display_connections = False
            else:
                dispConnItem.setCheckState(Qt.Checked)
                self.chromosomes[row].display_connections = True
        self.initscene()

    def toggleCoverage(self):
        if self.completeCoveragePathItem.isVisible():
            self.completeCoveragePathItem.hide()
        else:
            self.completeCoveragePathItem.show()

    #Method for defining or reinitializing the chromosome items.
    def makeItems(self):
        #To determine the length (therefore angle below) of a chromosome, let 360 deg represent
        #total number of bp to be displayed. The angle to increment for each chromosome
        #is then (chromosome.end / totalDispBP)*360. Cut off 1 deg for separation.
        size = self.size()
        outerChrRect = QRect(QPoint(50,50), QPoint(size.height()-50,size.height()-50))
        innerChrRect = QRect(QPoint(100,100),QPoint(size.height()-100,size.height()-100))
        curAngle = 0
        totalDispBP = self.returnTotalDisplayedBP()
        for chromo in self.chromosomes:
            if not chromo.display:
                continue
            angleIncr = (int(chromo.end) / totalDispBP) * 360
            #Define two painter paths constructing circle sectors
            outer = QPainterPath()
            inner = QPainterPath()
            outer.moveTo(outerChrRect.center())
            outer.arcTo(outerChrRect,-curAngle, -angleIncr+1)
            inner.moveTo(innerChrRect.center())
            inner.arcTo(innerChrRect,-curAngle, -angleIncr+1)
            #Saving the angles for later use, see drawConnections
            angles = [curAngle, angleIncr]
            del self.chromosome_angle_list[self.chromosomes.index(chromo)]
            self.chromosome_angle_list.insert(self.chromosomes.index(chromo), angles)
            curAngle += angleIncr
            #Removes any leftover painting path that may cause ugly lines in the middle
            leftoverArea = QPainterPath()
            leftoverArea.moveTo(innerChrRect.center())
            leftoverArea.arcTo(innerChrRect,0,360)
            #Remove the inner circle sector from the outer sector to get the area to display
            chromoPath = outer.subtracted(inner)
            chromoPath = chromoPath.subtracted(leftoverArea)
            #Finally, construct a graphics item from the path, to be added to the scene
            if self.showChrNames:
                nameString = chromo.name
            else:
                nameString = ""
            chromoItem = ChromoGraphicItem(chromoPath, nameString)
            chromoItem.setToolTip(chromo.name + ": " + chromo.end + " bp, " + str(len(chromo.variants)) + " variants")
            #Look up the chromo name in the color dict for its defined color
            currentColor = self.chromoColors[chromo.name]
            chromoItem.setBrush(currentColor)
            #Add the finished graphics item to a list
            self.chromosomeItems.append(chromoItem)

    #Creates a coverage graph. FIX: maybe add bp delineation?
    def createCoverage(self):
        size = self.size()
        totalDispBP = self.returnTotalDisplayedBP()
        inRect = QRect(QPoint(150,150),QPoint(size.height()-150,size.height()-150))
        outRect = QRect(QPoint(125,125),QPoint(size.height()-125,size.height()-125))
        chrStartAngle = 0
        if self.useCoverageLog:
            normValue = self.coverageNormLog
        else:
            normValue = self.coverageNorm
        centerPoint = inRect.center()
        for chromo in self.chromosomes:
            if not chromo.display:
                continue
            chrEndAngle = (int(chromo.end) / totalDispBP) * 360 - 1
            innerPath = QPainterPath()
            innerPath.moveTo(centerPoint)
            outerPath = QPainterPath()
            outerPath.moveTo(centerPoint)
            #No. of coverage data items ranging from 249250 to 59373 -- far too much to draw..
            #sum a number of entries as specified in bpWindow and create an average
            if self.useCoverageLog:
                coverageChunks = [chromo.coverageLog[i:i+self.bpWindow] for i in range(0,len(chromo.coverageLog),self.bpWindow)]
            else:
                coverageChunks = [chromo.coverage[i:i+self.bpWindow] for i in range(0,len(chromo.coverage),self.bpWindow)]
            angleIncr = ((chrEndAngle) / len(coverageChunks))
            curAngle = chrStartAngle
            for chunk in coverageChunks:
                avgCoverage = sum(chunk) / len(chunk)
                #for chromosomes up to 22, 150% of norm is max and 50% is min (default).
                #find the tVal using linear interpolation between these two points
                if (avgCoverage > normValue*self.maxCoverage):
                    avgCoverage = normValue*self.maxCoverage
                if (avgCoverage < normValue*self.minCoverage):
                    avgCoverage = normValue*self.minCoverage
                tVal = (avgCoverage - normValue*self.minCoverage)/(normValue*self.maxCoverage - normValue*self.minCoverage)
                innerPath.arcMoveTo(inRect,-curAngle)
                outerPath.arcMoveTo(outRect,-curAngle)
                lineBetween = QLineF(outerPath.currentPosition(),innerPath.currentPosition())
                outerPath.moveTo(lineBetween.pointAt(0.5))
                outerPath.lineTo(lineBetween.pointAt(tVal))
                curAngle += angleIncr
            chrStartAngle += chrEndAngle + 1
            covItem = QGraphicsPathItem(outerPath)
            self.coverageItems.append(covItem)

    def drawConnections(self):
        #Loops through the full list of chromosomes and checks if the connections should be displayed or not
        size = self.size()
        outerChrRect = QRect(QPoint(50,50), QPoint(size.height()-50,size.height()-50))
        innerChrRect = QRect(QPoint(100,100),QPoint(size.height()-100,size.height()-100))
        counter = 0
        for index in range(len(self.chromosomes)):
            if not self.chromosomes[index].display_connections & self.chromosomes[index].display:
                continue
            #only create the connection list if it has not been initialized earlier
            if not self.chromosomes[index].connections:
                self.chromosomes[index].createConnections()
            for connection in self.chromosomes[index].connections:
                #The information is stored as string elements and needs to be converted to integers
                if connection[1] == 'X':
                    ChrB=23
                elif connection[1] == 'Y':
                    ChrB=24
                elif connection[1].startswith('G'):
                    continue
                else:
                    ChrB = int(connection[1])
                if not self.chromosomes[ChrB-1].display:
                    continue
                #The curAngle determines where on the circle the chromosome is located (also used in makeItems)
                curAngle_A = self.chromosome_angle_list[index][0]
                curAngle_B = self.chromosome_angle_list[ChrB-1][0]
                #The windows of each variant (WINA, WINB) are used to determine where on the chromosome the interaction is located
                bp_End_A = int(connection[2].split(',')[1])
                ChrA_length = int(self.chromosomes[index].end)
                bp_End_B = int(connection[3].split(',')[1])
                ChrB_length = int(self.chromosomes[ChrB-1].end)
                #A percentage of the total angle (used to draw the chromosome in makeItems) determines where on the
                #chromosome the connection is located
                angleIncr_A = (1-((ChrA_length - bp_End_A) / ChrA_length)) * (self.chromosome_angle_list[index][1]-2)
                angleIncr_B = (1-((ChrB_length - bp_End_B) / ChrB_length)) * (self.chromosome_angle_list[ChrB-1][1]-2)
                #A Path is created to assign the position for the connections
                tempPath = QPainterPath()
                #The arMoveTo() function is used to get the different points on each chromosome the connection is located
                tempPath.arcMoveTo(innerChrRect, - (curAngle_A + angleIncr_A))
                posA = tempPath.currentPosition()
                tempPath.arcMoveTo(innerChrRect, - (curAngle_B + angleIncr_B))
                posB = tempPath.currentPosition()
                centerPos = outerChrRect.center()
                #A Bezier curve is then created between these three points
                connectionPath = QPainterPath()
                connectionPath.moveTo(posA)
                connectionPath.quadTo(centerPos,posB)
                #The path is converted to a graphics path item
                connectionItem = QGraphicsPathItem(connectionPath)
                #The PathItem is given the color of chromosome B and a width (default is 1 pixel wide)
                pen = QPen(self.chromoColors[self.chromosomes[ChrB-1].name], self.connWidth)
                connectionItem.setPen(pen)
                #Creating a rectangle (1x1 pixels) around each posB point for use when heat mapping the connections
                rect = QRect(posB.toPoint(),QSize(1,1))
                rect.moveCenter(posB.toPoint())
                #self.scene.addItem(QGraphicsRectItem(rect))
                connectionInfo = [connectionItem, rect, posA, posB, (ChrB-1), counter]
                #The item is added to a list
                self.chromosomes[index].connection_list.append(connectionInfo)
                counter = counter + 1

        #Checking to see if any neighbouring connections are close to eachother, if they are -> create a color gradient for both the
        #neighbouring connection lines, that gets darker closer to the connection
        for index1 in range(len(self.chromosomes)):
            for connItem1 in self.chromosomes[index1].connection_list:
                for index2 in range(len(self.chromosomes)):
                    for connItem2 in self.chromosomes[index2].connection_list:
                        #check to see if one rectangle is comparing with itself
                        if connItem1[5] == connItem2[5]:
                            continue
                        if connItem1[1].intersects(connItem2[1]):
                            linearGrad = QLinearGradient(connItem1[2], connItem1[3])
                            linearGrad.setColorAt(0, self.chromoColors[self.chromosomes[connItem1[4]].name])
                            linearGrad.setColorAt(1, self.chromoColors[self.chromosomes[connItem1[4]].name].darker(300))
                            connItem1[0].setPen(QPen(QBrush(linearGrad), self.connWidth))
                            connItem2[0].setPen(QPen(QBrush(linearGrad), self.connWidth))

    def numDispChromosomes(self):
        dispChromos = 0

        for chromo in self.chromosomes:
            if chromo.display:
                dispChromos += 1

        return dispChromos


    def createDistanceMarkers(self):
        size = self.size()
        totalDispBP = self.returnTotalDisplayedBP()
        outRect = QRect(QPoint(53,53),QPoint(size.height()-53,size.height()-53))
        inRect = QRect(QPoint(47,47),QPoint(size.height()-47,size.height()-47))
        bpPerDegree = (totalDispBP/(360 - self.numDispChromosomes()))/1000000
        bpPerDegree = round(bpPerDegree,2)
        degreePerBp = (360-self.numDispChromosomes())/(totalDispBP/(self.bpDistanceResolution*1000000))
        chrStartAngle = 0
        centerPoint = inRect.center()
        for chromo in self.chromosomes:
            if not chromo.display:
                continue
            chrEndAngle = ((int(chromo.end) / totalDispBP) * 360 - 1)
            innerPath = QPainterPath()
            innerPath.moveTo(centerPoint)
            outerPath = QPainterPath()
            outerPath.moveTo(centerPoint)
            chromoLength = int(chromo.end)
            curAngle = chrStartAngle
            angleIncr = degreePerBp
            angleCounter = 0
            distanceNameItemList = []
            while curAngle < (chrStartAngle + chrEndAngle):
                if angleCounter%10 == 0:
                    inRect = QRect(QPoint(40,40),QPoint(size.height()-40,size.height()-40))
                    outRect = QRect(QPoint(60,60),QPoint(size.height()-60,size.height()-60))
                    distanceName = str(int(angleCounter))
                else:
                    outRect = QRect(QPoint(53,53),QPoint(size.height()-53,size.height()-53))
                    inRect = QRect(QPoint(47,47),QPoint(size.height()-47,size.height()-47))
                    distanceName = ""
                textHeight = 20
                textWidth = 13 if curAngle<10 else 18
                innerPath.arcMoveTo(inRect, -curAngle)
                outerPath.arcMoveTo(outRect, -curAngle)
                distanceNameItem = QGraphicsTextItem(distanceName)

                if curAngle >= 0 and curAngle < 67:
                    offsetX = 0
                elif curAngle >= 67 and curAngle < 115:
                    offsetX = -0.5
                elif curAngle >= 115 and curAngle < 247:
                    offsetX = -1
                elif curAngle >= 247 and curAngle < 292:
                    offsetX = -0.5
                elif curAngle >= 292 and curAngle <= 360:
                    offsetX = 0

                offsetX = offsetX*textWidth
                offsetY = ((math.cos(math.radians(curAngle) - (math.pi/2)) - 1)/2)*textHeight
                offsetPoint = QPointF(offsetX,offsetY)

                distanceNameItem.setPos(innerPath.currentPosition()+offsetPoint)
                distanceNameItemList.append(distanceNameItem)

                lineBetween = QLineF(outerPath.currentPosition(),innerPath.currentPosition())
                outerPath.moveTo(lineBetween.pointAt(0))
                outerPath.lineTo(lineBetween.pointAt(1))
                self.scene.addPath(innerPath)
                angleCounter += 1
                curAngle += angleIncr

            chrStartAngle += chrEndAngle + 1

            distItem = QGraphicsPathItem(outerPath)
            self.distanceMarkerItems.append([distItem, distanceNameItemList])


        for incr in range(11):
            if incr%10 == 0:
                lineBetween = QLineF(outRect.width()+incr*10,outRect.height(), outRect.width()+incr*10, outRect.height()-20)
                legendNameItem = QGraphicsTextItem(str(incr))
            else:
                lineBetween = QLineF(outRect.width()+incr*10,outRect.height()-5, outRect.width()+incr*10, outRect.height()-15)
                legendNameItem = QGraphicsTextItem("")
            legendPath = QPainterPath()
            legendPath.moveTo(lineBetween.pointAt(0))
            legendPath.lineTo(lineBetween.pointAt(1))
            legendNameItem.setPos(legendPath.currentPosition().x()-10,legendPath.currentPosition().y()-20)
            legendItem = QGraphicsPathItem(legendPath)
            self.legendItems.append([legendItem, legendNameItem])
        #lineBetweenStart = QLineF(outRect.width(),outRect.height(), outRect.width(), outRect.height()-20)
        #lineBetweenEnd = QLineF(outRect.width()+100,outRect.height(), outRect.width()+100, outRect.height()-20)
        lineBetween = QLineF(outRect.width(),outRect.height()-10, outRect.width()+100, outRect.height()-10)

        #legendNameItem = QGraphicsTextItem("")
        legendTitleItem = QGraphicsTextItem("x" + str(self.bpDistanceResolution) + " Mb")
        legendPath = QPainterPath()
        #legendPath.moveTo(lineBetweenStart.pointAt(0))
        #legendPath.lineTo(lineBetweenStart.pointAt(1))
        #legendPath.moveTo(lineBetweenEnd.pointAt(0))
        #legendPath.lineTo(lineBetweenEnd.pointAt(1))
        legendPath.moveTo(lineBetween.pointAt(0))
        legendPath.lineTo(lineBetween.pointAt(1))
        legendTitleItem.setPos(legendPath.currentPosition().x()-75, legendPath.currentPosition().y()+20)
        legendItem = QGraphicsPathItem(legendPath)
        self.legendItems.append([legendItem, legendTitleItem])

    #Imports either a tab file with specified regions to color, or a cytoband file
    def importColorTab(self):
        fileName = QFileDialog.getOpenFileName(None, "Specify a color tab-file", QDir.currentPath(), "tab-files (*.tab *.txt)")[0]
        reader = data.Reader()
        if fileName.endswith("tab"):
            reader.readColorTab(fileName)
            colorTab = reader.returnColorTab()
            self.colorRegions(colorTab,False)
        else:
            reader.readCytoTab(fileName)
            colorTab = reader.returnCytoTab()
            self.colorRegions(colorTab,True)

    def colorRegions(self,colorTab,cytoband):
        size = self.size()
        outerChrRect = QRect(QPoint(50,50), QPoint(size.height()-50,size.height()-50))
        innerChrRect = QRect(QPoint(100,100),QPoint(size.height()-100,size.height()-100))
        colors = {'red': Qt.red, 'magenta': Qt.magenta, 'blue': Qt.blue, 'cyan': Qt.cyan, 'yellow': Qt.yellow, 'darkBlue': Qt.darkBlue}
        stainColors = {'acen':Qt.darkRed, 'gneg':Qt.white,'gpos100':Qt.black,'gpos25':Qt.lightGray,'gpos50':Qt.gray,
        'gpos75':Qt.darkGray,'gvar':Qt.white,'stalk':Qt.red}
        #Every item in colorTab, if not a cytoband file, contains 4 items: chromosome name, startPos, endPos, color
        #If a cytoband file, use the stain name to determine color
        self.regionItems = []
        for region in colorTab:
            #Find a matching chromosome item for every region and make sure it's displayed
            for chromo in self.chromosomes:
                if not chromo.display:
                    continue
                if chromo.name == region[0]:
                    #where on the circle does this chromosome start, how much does it span?
                    index = self.chromosomes.index(chromo)
                    startAngle = self.chromosome_angle_list[index][0]
                    angleSpan = self.chromosome_angle_list[index][1]
                    #the region starts and ends at certain points in this span
                    regionStart = int(region[1])
                    regionEnd = int(region[2])
                    #if the files are slightly misaligned, set maximum end to chromo end
                    if regionEnd > int(chromo.end):
                        regionEnd = int(chromo.end)
                    regionStartAngle = startAngle + (regionStart/int(chromo.end))*angleSpan
                    regionEndAngle = startAngle + (regionEnd/int(chromo.end))*angleSpan
                    #Define two painter paths constructing circle sectors
                    outer = QPainterPath()
                    inner = QPainterPath()
                    outer.moveTo(outerChrRect.center())
                    outer.arcTo(outerChrRect,-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    inner.moveTo(innerChrRect.center())
                    inner.arcTo(innerChrRect,-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    #Removes any leftover painting path that may cause ugly lines in the middle
                    leftoverArea = QPainterPath()
                    leftoverArea.moveTo(innerChrRect.center())
                    leftoverArea.arcTo(innerChrRect,0,360)
                    #Remove the inner circle sector from the outer sector to get the area to display
                    regionPath = outer.subtracted(inner)
                    regionPath = regionPath.subtracted(leftoverArea)
                    regionItem = QGraphicsPathItem(regionPath)
                    if cytoband:
                        regionColor = stainColors[region[4]]
                    else:
                        regionColor = colors[region[3]]
                    regionItem.setBrush(regionColor)
                    regionItem.setOpacity(1)
                    #Add the finished graphics item to a list
                    self.regionItems.append(regionItem)
        for regionItem in self.regionItems:
            self.scene.addItem(regionItem)

    def initscene(self):
        #Clear old chromosome items, coverage, connections
        try:
            self.scene.removeItem(self.completeCoveragePathItem)
        except:
            pass
        for chrItem in self.chromosomeItems:
            #Update the color dict in case user modified these
            self.chromoColors[chrItem.nameString] = chrItem.brush().color()
            self.scene.removeItem(chrItem)
        for distItem in self.distanceMarkerItems:
            self.scene.removeItem(distItem[0])
            for distNameItem in distItem[1]:
                self.scene.removeItem(distNameItem)
        for legendItem in self.legendItems:
            self.scene.removeItem(legendItem[0])
            self.scene.removeItem(legendItem[1])

        for index in range(len(self.chromosomes)):
             for connItem in self.chromosomes[index].connection_list:
                 try:
                     self.scene.removeItem(connItem[0])
                 except:
                     pass
        for regionItem in self.regionItems:
            try:
                self.scene.removeItem(regionItem)
            except:
                pass
        self.scene.markedChromItems = []
        self.chromosomeItems = []
        self.coverageItems = []
        self.distanceMarkerItems = []
        self.legendItems = []
        for index in range(len(self.chromosomes)):
             self.chromosomes[index].connection_list = []
        self.chromosome_angle_list = [None]*24
        #Create new graphics items, add these to the scene.
        self.makeItems()
        self.createCoverage()
        self.drawConnections()
        self.createDistanceMarkers()
        for chrItem in self.chromosomeItems:
            self.scene.addItem(chrItem)
        for index in range(len(self.chromosomes)):
             for connItem in self.chromosomes[index].connection_list:
                 self.scene.addItem(connItem[0])
        for distItem in self.distanceMarkerItems:
            self.scene.addItem(distItem[0])
            for distNameItem in distItem[1]:
                self.scene.addItem(distNameItem)
        for legendItem in self.legendItems:
            self.scene.addItem(legendItem[0])
            self.scene.addItem(legendItem[1])
        #For more convenient coloring, create a new graphics item consisting of all coverages added together
        completeCoveragePath = QPainterPath()
        for covItem in self.coverageItems:
            completeCoveragePath.addPath(covItem.path())
        self.completeCoveragePathItem = QGraphicsPathItem(completeCoveragePath)
        #We then create a gradient with short interpolation distances, based on
        #the rectangles used for defining coverage items
        size = self.size()
        outRect = QRect(QPoint(125,125),QPoint(size.height()-125,size.height()-125))
        inRect = QRect(QPoint(150,150),QPoint(size.height()-150,size.height()-150))
        gradRadius = outRect.width()/2
        radialGrad = QRadialGradient(outRect.center(), gradRadius)
        diff = outRect.width()/2 - inRect.width()/2
        #In setColorAt, 0 is the circle center, 1 is the edge.
        #The coverage graph reaches from a radius of 1, to 1-diff/gradRadius, in these coordinates.
        #We use two stops for a color switch, placed around thirds of coverage graph reach.
        radialGrad.setColorAt(1,Qt.red)
        radialGrad.setColorAt(1-diff/gradRadius*(1/3.1),Qt.red)
        radialGrad.setColorAt(1-diff/gradRadius*(1/3),Qt.black)
        radialGrad.setColorAt(1-diff/gradRadius*(2/3),Qt.black)
        radialGrad.setColorAt(1-diff/gradRadius*(2.1/3),Qt.blue)
        #Create a pen with a brush using the gradient, tell the graphic item to use the pen, add to scene.
        covBrush = QBrush(radialGrad)
        covPen = QPen()
        covPen.setBrush(covBrush)
        self.completeCoveragePathItem.setPen(covPen)
        self.scene.addItem(self.completeCoveragePathItem)
        self.update()

    #Adds the VCF and TAB file names as text items to the top of the scene
    def addFileText(self):
        tabText = self.scene.addText("TAB File: " + self.tabName)
        tabText.setFlag(QGraphicsItem.ItemIsMovable)
        tabText.setTextInteractionFlags(Qt.TextEditorInteraction)
        vcfText = self.scene.addText("VCF File: " + self.vcfName)
        vcfText.setPos(0,0+tabText.boundingRect().height())
        vcfText.setFlag(QGraphicsItem.ItemIsMovable)
        vcfText.setTextInteractionFlags(Qt.TextEditorInteraction)

    def wheelEvent(self,event):
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)

#Subclass of graphics path item for custom handling of mouse events
class ChromoGraphicItem(QGraphicsPathItem):

    def __init__(self,path,nameString):
        super().__init__(path)
        self.selected = False
        self.nameString = nameString
        self.setData(0,"CustomSelection")
        self.setPen(QPen(Qt.black,1))

    #Marks the chromosome item with a blue outline if selected
    def mark(self):
        currentPen = self.pen()
        currentPen.setStyle(Qt.DashLine)
        currentPen.setBrush(Qt.blue)
        currentPen.setWidth(3)
        self.setPen(currentPen)
        self.selected = True

    def unmark(self):
        self.setPen(QPen(Qt.black,1))
        self.selected = False

    #Paints the name of the chromosone in the middle of the item -- possible to implemend changing of font etc if needed
    def paint(self,painter,option,widget):
        super().paint(painter,option,widget)
        painter.drawText(self.path().boundingRect().center(),self.nameString)

#Subclass of graphics scene for custom handling of mouse events
class CircosScene(QGraphicsScene):

    def __init__(self):
        super().__init__()
        self.markedChromItems = []

    #Modified slightly for different selection behaviour (no default borders etc)
    def mousePressEvent(self,event):
        leftClickPos = event.buttonDownScenePos(Qt.LeftButton)
        clickedItems = self.items(leftClickPos)
        for item in clickedItems:
            if not item.isEnabled():
                continue
            #Items with custom selection behavior have custom data
            #These should have their own handling; other items go through the default implementation
            if (item.data(0) == "CustomSelection"):
                if item.selected:
                    item.unmark()
                    self.markedChromItems.remove(item)
                else:
                    item.mark()
                    self.markedChromItems.append(item)
            else:
                QGraphicsScene.mousePressEvent(self,event)


    #Opens a context menu on right click
    def contextMenuEvent(self,event):
        self.lastContextPos = event.scenePos()
        if self.markedChromItems:
            menu = QMenu()
            setColorAct = QAction('Set color of selected chromosomes',self)
            setColorAct.triggered.connect(self.setColor)
            menu.addAction(setColorAct)
            menu.exec_(QCursor.pos())
        else:
            menu = QMenu()
            addSceneTextAct = QAction('Insert text',self)
            addSceneTextAct.triggered.connect(self.addSceneText)
            addGeneLabelAct = QAction('Add gene label',self)
            addGeneLabelAct.triggered.connect(self.addGeneLabel)
            menu.addAction(addSceneTextAct)
            menu.addAction(addGeneLabelAct)
            menu.exec_(QCursor.pos())

    #Opens a color pick dialog, and sets chromosome item(s) to this color.
    #Several items can be marked, use color of first item as default in that case
    def setColor(self):
        if self.markedChromItems:
            initialColor = self.markedChromItems[0].brush().color()
            chosenColor = QColorDialog.getColor(initialColor)
            for item in self.markedChromItems:
                item.setBrush(chosenColor)
                item.unmark()
            self.markedChromItems = []

    def addSceneText(self):
        (text, ok) = QInputDialog.getText(None, 'Insert text', 'Text:')
        if ok and text:
            textItem = QGraphicsTextItem(text)
            textItem.setPos(self.lastContextPos)
            textItem.setFlag(QGraphicsItem.ItemIsMovable)
            textItem.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.addItem(textItem)

    def addGeneLabel(self):
        #Adds a label item, with user set chromosome, location, text, and color.
        #Currently only adds a graphic for the label, but should automatically draw a line from the item,
        #to specified chromosome and position. Needs input check..
        labelDialog = QDialog()
        labelDialog.setWindowTitle("Add label")
        applyButton = QPushButton('Ok', labelDialog)
        applyButton.clicked.connect(labelDialog.accept)
        chromoBox = QComboBox()
        chromoStrings = [chromo.name for chromo in self.views()[0].chromosomes if chromo.display]
        chromoBox.addItems(chromoStrings)
        locBox = QLineEdit()
        locBoxValidator = QIntValidator(self)
        locBoxValidator.setBottom(0)
        locBox.setValidator(locBoxValidator)
        textBox = QLineEdit()
        colorBox = QComboBox()
        colorStrings = QColor.colorNames()
        colorBox.addItems(colorStrings)
        chrLabel = QLabel("Add label for chromosome: ")
        locLabel = QLabel("Label location: ")
        geneLabel = QLabel("Label text: ")
        colorLabel = QLabel("Label color: ")
        labelDialog.layout = QGridLayout(labelDialog)
        labelDialog.layout.addWidget(chrLabel,0,0)
        labelDialog.layout.addWidget(chromoBox,0,1)
        labelDialog.layout.addWidget(locLabel,1,0)
        labelDialog.layout.addWidget(locBox,1,1)
        labelDialog.layout.addWidget(geneLabel,2,0)
        labelDialog.layout.addWidget(textBox,2,1)
        labelDialog.layout.addWidget(colorLabel,3,0)
        labelDialog.layout.addWidget(colorBox,3,1)
        labelDialog.layout.addWidget(applyButton,4,0)
        choice = labelDialog.exec_()
        if choice == QDialog.Accepted:
            textItem = QGraphicsTextItem(textBox.text())
            rectItem = QGraphicsRectItem(textItem.boundingRect())
            rectItem.setBrush(QColor(colorBox.currentText()))
            self.addItem(rectItem)
            self.addItem(textItem)
            labelItem = self.createItemGroup([rectItem,textItem])
            labelItem.setFlag(QGraphicsItem.ItemIsMovable)
            labelItem.setPos(self.lastContextPos)
