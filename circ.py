import sys
import random
import math
import data
import common
import copy
from PySide.QtCore import *
from PySide.QtGui import *

class CircView(QGraphicsView):

    def __init__(self,dataDict,circularSettings,parent):
        self.type = "circ"
        self.scene = CircScene()
        super().__init__(self.scene,parent)
        self.circularSettings = circularSettings
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.chromosomeDict = {chromo.name: chromo for chromo in self.chromosomes}
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.chromosomeItems = []
        self.graphicItems = []
        self.coverageItems = []
        self.connectionItems = {}

        self.startColor = QColor.fromRgb(243,241,172)
        self.bpWindow = int(self.circularSettings["bpWindow"])
        self.bpDistanceResolution = int(self.circularSettings["bpDistanceResolution"])
        self.useCoverageLog = self.circularSettings["useCoverageLog"] == "True"
        self.minCoverage = float(self.circularSettings["minCoverage"])/100
        self.maxCoverage = float(self.circularSettings["maxCoverage"])/100
        self.connWidth = int(self.circularSettings["connWidth"])
        self.showChrNames = self.circularSettings["showChrNames"] == "True"
        self.showCentromereRegion = self.circularSettings["showCentromereRegion"] == "True"
        self.minBedBp = int(self.circularSettings["minBedBp"])
        self.createSettings()

        self.coverageNormLog = self.dataDict['coverageNormLog']
        self.coverageNorm = self.dataDict['coverageNorm']
        self.tabName = self.dataDict['tabName']
        self.vcfName = self.dataDict['vcfName']
        self.createChInfo()

        self.activeChromo = None
        self.varTable = None
        self.chromosome_angle_list = {}
        #Initialize a dict with an empty list for each chromosome, to contain bed tracks
        self.bedDict = {chromo.name: [] for chromo in self.chromosomes}
        #Create a dict representing colors for the chromosomes
        self.chromoColors = {}
        color = self.startColor
        for chromo in self.chromosomes:
            self.chromoColors[chromo.name] = color
            color = color.darker(105)
        #A list containing rectangles for extra layers, starting empty
        self.addedLayers = []

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
        showChrNameText.setToolTip("Show or hide the chromosome names on the circular diagram")
        showChrNameCheck = QStandardItem()
        showChrNameCheck.setCheckable(True)
        showChrNameCheck.setCheckState(Qt.Checked)
        showChrNameCheck.setEditable(False)
        showCentromereRegionText = QStandardItem("Mark centromeres")
        showCentromereRegionText.setEditable(False)
        showCentromereRegionText.setToolTip("Add markings for centromere regions")
        showCentromereRegionCheck = QStandardItem()
        showCentromereRegionCheck.setCheckable(True)
        showCentromereRegionCheck.setCheckState(Qt.Unchecked)
        showCentromereRegionCheck.setEditable(False)
        minBedBpText = QStandardItem("Minimum bed bp (kb)")
        minBedBpText.setEditable(False)
        minBedBpText.setToolTip("Items with a smaller length will be hidden in the track viewer")
        minBedBpData = QStandardItem()
        minBedBpData.setData(self.minBedBp,0)
        minBedBpData.setEditable(True)
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
        self.settingsModel.setItem(7,0,showCentromereRegionText)
        self.settingsModel.setItem(7,1,showCentromereRegionCheck)
        self.settingsModel.setItem(8,0,minBedBpText)
        self.settingsModel.setItem(8,1,minBedBpData)

    def updateSettings(self):
        #Go through every row in the settings model and update accordingly
        for row in range(self.settingsModel.rowCount()):
            item = self.settingsModel.item(row,1)
            if row == 0:
                self.bpWindow = int(item.data(0))
            if row == 1:
                self.bpDistanceResolution = int(item.data(0))
            if row == 2:
                if item.checkState() == Qt.Checked:
                    self.useCoverageLog = True
                else:
                    self.useCoverageLog = False
            if row == 3:
                self.minCoverage = int(item.data(0))/100
            if row == 4:
                self.maxCoverage = int(item.data(0))/100
            if row == 5:
                self.connWidth = int(item.data(0))
            if row == 6:
                if item.checkState() == Qt.Checked:
                    self.showChrNames = True
                else:
                    self.showChrNames = False
            if row == 7:
                if item.checkState() == Qt.Checked:
                    self.showCentromereRegion = True
                else:
                    self.showCentromereRegion = False
            if row == 8:
                self.minBedBp = int(item.data(0))
        self.circularSettings["bpWindow"] = str(self.bpWindow)
        self.circularSettings["bpDistanceResolution"] = str(self.bpDistanceResolution)
        self.circularSettings["useCoverageLog"] = str(self.useCoverageLog)
        self.circularSettings["minCoverage"] = str(self.minCoverage*100)
        self.circularSettings["maxCoverage"] = str(self.maxCoverage*100)
        self.circularSettings["connWidth"] = str(self.connWidth)
        self.circularSettings["showChrNames"] = str(self.showChrNames)
        self.circularSettings["showCentromereRegion"] = str(self.showCentromereRegion)
        self.circularSettings["minBedBp"] = str(self.minBedBp)
        self.initscene()

    #Creates and returns a widget with this view's settings
    def returnSettingsWidget(self):
        settingsWidget = QWidget()
        settingsLayout = QGridLayout()
        settingsList = QTableView()
        settingsList.setEditTriggers(QAbstractItemView.AllEditTriggers)
        settingsList.setShowGrid(False)
        settingsList.horizontalHeader().hide()
        settingsList.verticalHeader().hide()
        settingsList.setModel(self.settingsModel)
        settingsList.resizeColumnsToContents()
        settingsList.setTextElideMode(Qt.ElideNone)
        settingsLayout.addWidget(settingsList,0,0,1,3)
        settingsWidget.setLayout(settingsLayout)
        return settingsWidget

    def returnSettingsDict(self):
        return self.circularSettings

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
        #self.chDia.layout.addWidget(addVariantButton,1,2,1,1)
        self.chDia.layout.addWidget(connButton,1,3,1,1)
        self.chDia.setMinimumSize(500,400)
        self.chDia.show()

    def returnChromoInfoWidget(self):
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
        #Button for toggling display of selected chromosomes in the scene
        togButton = QPushButton(QIcon("icons/display.png"),"")
        togButton.clicked.connect(self.toggleDisp)
        togButton.setToolTip("Toggle display of chromosome")
        #Button for viewing selected chromosome variants
        viewVarButton = QPushButton(QIcon("icons/viewList.png"),"")
        viewVarButton.clicked.connect(self.viewVariants)
        viewVarButton.setToolTip("View variants in chromosome")
        #Button for adding variants
        addVariantButton = QPushButton(QIcon("icons/new.png"),"")
        addVariantButton.clicked.connect(self.addVariant)
        addVariantButton.setToolTip("Add custom variant")
        #Button for toggling connections
        connButton = QPushButton(QIcon("icons/connections.png"),"")
        connButton.clicked.connect(self.toggleConnections)
        connButton.setToolTip("Toggle display of connections between variants")
        chromoInfoLayout = QGridLayout()
        chromoInfoLayout.addWidget(self.chList,0,0,1,4)
        chromoInfoLayout.addWidget(togButton,1,0,1,1)
        chromoInfoLayout.addWidget(connButton,1,1,1,1)
        chromoInfoLayout.addWidget(viewVarButton,1,2,1,1)
        #chromoInfoLayout.addWidget(addVariantButton,1,3,1,1)
        chromoWidget = QWidget()
        chromoWidget.setLayout(chromoInfoLayout)
        return chromoWidget

    #Creates a popup containing variant info in a table.
    def viewVariants(self):
        #Find which chromosome's variants is to be viewed by looking at chList rows
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        #Display a variant window for every selected chromosome
        for row in selectedRows:
            chromo = self.chromosomes[row]
            viewVarDia = common.createVariantDia(chromo,self)
            #Also connect toggle button in the widget to update scene
            viewVarDia.layout.itemAtPosition(1,0).widget().clicked.connect(self.initscene)
            viewVarDia.show()

    def createVariantWidget(self,row):
        chromo = self.chromosomes[row]
        varWidget = common.createVariantWidget(chromo)
        #Also connect toggle button in the widget to update scene
        varWidget.layout().itemAtPosition(1,0).widget().clicked.connect(self.initscene)
        return varWidget

    def addVariant(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            common.addVariant(chromo,self.chromosomes)

    #Reads an image and adds it to the scene
    def addImage(self):
        self.defineRectangles()
        outerChrRect = self.outerChrRect
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
        pixmapItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.scene.addItem(pixmapItem)

    #Toggles display of whole chromosomes on or off
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

    #Toggles if connections for variants are to be displayed for a chromosome
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

    #Toggles coverage items on or off
    def toggleCoverage(self):
        for covItem in self.coverageItems:
            if covItem.isVisible():
                covItem.hide()
            else:
                covItem.show()

    #Define rectangles used for drawing of chromosomes etc, if user has changed window size
    def defineRectangles(self):
        size = self.size()
        self.outerChrRect = QRect(QPoint(50,50), QPoint(size.height()-50,size.height()-50))
        self.innerChrRect = QRect(QPoint(100,100),QPoint(size.height()-100,size.height()-100))
        self.outerCoverageRect = QRect(QPoint(125,125),QPoint(size.height()-125,size.height()-125))
        self.innerCoverageRect = QRect(QPoint(180,180),QPoint(size.height()-180,size.height()-180))
        #If no added layers are added, the outermost rectangle is outerChrRect
        if not self.addedLayers:
            self.outermostRect = self.outerChrRect

    #Method for defining or reinitializing the chromosome items.
    def makeItems(self):
        #To determine the length (therefore angle below) of a chromosome, let 360 deg represent
        #total number of bp to be displayed. The angle to increment for each chromosome
        #is then (chromosome.end / totalDispBP)*360. Cut off 1 deg for separation.
        curAngle = 0
        totalDispBP = self.returnTotalDisplayedBP()
        for chromo in self.chromosomes:
            if not chromo.display:
                continue
            angleIncr = (int(chromo.end) / totalDispBP) * 360
            #Define two painter paths constructing circle sectors
            outer = QPainterPath()
            inner = QPainterPath()
            outer.moveTo(self.outerChrRect.center())
            outer.arcTo(self.outerChrRect,-curAngle, -angleIncr+1)
            inner.moveTo(self.innerChrRect.center())
            inner.arcTo(self.innerChrRect,-curAngle, -angleIncr+1)
            #Removes any leftover painting path that may cause ugly lines in the middle
            leftoverArea = QPainterPath()
            leftoverArea.moveTo(self.innerChrRect.center())
            leftoverArea.arcTo(self.innerChrRect,0,360)
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
            self.scene.addItem(chromoItem)
            #Background for coverage area
            leftoverArea = QPainterPath()
            leftoverArea.moveTo(self.innerCoverageRect.center())
            leftoverArea.arcTo(self.innerCoverageRect,0,360)
            outerBackgroundPath = QPainterPath()
            innerBackgroundPath = QPainterPath()
            outerBackgroundPath.moveTo(self.outerCoverageRect.center())
            outerBackgroundPath.arcTo(self.outerCoverageRect,-curAngle, -angleIncr+1)
            innerBackgroundPath.moveTo(self.innerCoverageRect.center())
            innerBackgroundPath.arcTo(self.innerCoverageRect,-curAngle, -angleIncr+1)
            backgroundPath = outerBackgroundPath.subtracted(innerBackgroundPath)
            backgroundPath = backgroundPath.subtracted(leftoverArea)
            backgroundPathItem = QGraphicsPathItem(backgroundPath)
            backgroundPathItem.setBrush(Qt.lightGray)
            backgroundPathItem.setOpacity(0.5)
            self.coverageItems.append(backgroundPathItem)
            self.scene.addItem(backgroundPathItem)
            #Saving the angles for later use, see drawConnections
            angles = [curAngle, angleIncr]
            self.chromosome_angle_list[chromo.name] = angles
            curAngle += angleIncr

    #Creates a coverage graph.
    def createCoverage(self):
        totalDispBP = self.returnTotalDisplayedBP()
        chrStartAngle = 0
        if self.useCoverageLog:
            normValue = self.coverageNormLog
        else:
            normValue = self.coverageNorm
        centerPoint = self.innerCoverageRect.center()
        coveragePaths = []
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
                innerPath.arcMoveTo(self.innerCoverageRect,-curAngle)
                outerPath.arcMoveTo(self.outerCoverageRect,-curAngle)
                lineBetween = QLineF(outerPath.currentPosition(),innerPath.currentPosition())
                outerPath.moveTo(lineBetween.pointAt(0.5))
                outerPath.lineTo(lineBetween.pointAt(tVal))
                curAngle += angleIncr
            chrStartAngle += chrEndAngle + 1
            coveragePaths.append(outerPath)
        #For more convenient coloring, create a new graphics item consisting of all coverages added together
        completeCoveragePath = QPainterPath()
        for path in coveragePaths:
            completeCoveragePath.addPath(path)
        self.completeCoveragePathItem = QGraphicsPathItem(completeCoveragePath)
        #We then create a gradient with short interpolation distances, based on
        #the rectangles used for defining coverage items
        gradRadius = self.outerCoverageRect.width()/2
        radialGrad = QRadialGradient(self.outerCoverageRect.center(), gradRadius)
        diff = self.outerCoverageRect.width()/2 - self.innerCoverageRect.width()/2
        #In setColorAt, 0 is the circle center, 1 is the edge.
        #The coverage graph reaches from a radius of 1, to 1-diff/gradRadius, in these coordinates.
        #We use stops for a color switch, placed in the middle of coverage graph reach.
        radialGrad.setColorAt(1,Qt.red)
        radialGrad.setColorAt(1-diff/gradRadius*(1/2),Qt.red)
        radialGrad.setColorAt(1-diff/gradRadius*(1/1.99),Qt.green)
        #Create a pen with a brush using the gradient, tell the graphic item to use the pen, add to scene.
        covBrush = QBrush(radialGrad)
        covPen = QPen()
        covPen.setBrush(covBrush)
        self.completeCoveragePathItem.setPen(covPen)
        self.coverageItems.append(self.completeCoveragePathItem)
        self.scene.addItem(self.completeCoveragePathItem)

    def drawConnections(self):
        #Loops through the full list of chromosomes and checks if the connections should be displayed or not
        counter = 0
        for chrA in self.chromosomeDict.values():
            self.connectionItems[chrA.name] = []
            if not (chrA.display_connections and chrA.display):
                continue
            #only create the connection list if it has not been initialized earlier
            if not chrA.connections:
                chrA.createConnections()
            for connection in chrA.connections:
                chrB = self.chromosomeDict[connection[1]]
                if chrB.name.startswith('G') or chrB.name == 'MT':
                    continue
                if not chrB.display:
                    continue
                #The curAngle determines where on the circle the chromosome is located (also used in makeItems)
                curAngle_A = self.chromosome_angle_list[chrA.name][0]
                curAngle_B = self.chromosome_angle_list[chrB.name][0]
                #The windows of each variant (WINA, WINB) are used to determine where on the chromosome the interaction is located
                #If chrA higher in order than chrB, WINA and WINB are switched, so check this first
                if self.chromosomes.index(chrA) > self.chromosomes.index(chrB):
                    bp_End_A = int(connection[3].split(',')[1])
                    chrA_length = int(chrA.end)
                    bp_End_B = int(connection[2].split(',')[1])
                    chrB_length = int(chrB.end)
                else:
                    bp_End_A = int(connection[2].split(',')[1])
                    chrA_length = int(chrA.end)
                    bp_End_B = int(connection[3].split(',')[1])
                    chrB_length = int(chrB.end)
                #A percentage of the total angle (used to draw the chromosome in makeItems) determines where on the
                #chromosome the connection is located
                angleIncr_A = (1-((chrA_length - bp_End_A) / chrA_length)) * (self.chromosome_angle_list[chrA.name][1]-2)
                angleIncr_B = (1-((chrB_length - bp_End_B) / chrB_length)) * (self.chromosome_angle_list[chrB.name][1]-2)
                #A Path is created to assign the position for the connections
                tempPath = QPainterPath()
                #The arMoveTo() function is used to get the different points on each chromosome the connection is located
                tempPath.arcMoveTo(self.innerChrRect, - (curAngle_A + angleIncr_A))
                posA = tempPath.currentPosition()
                tempPath.arcMoveTo(self.innerChrRect, - (curAngle_B + angleIncr_B))
                posB = tempPath.currentPosition()
                centerPos = self.outerChrRect.center()
                #A Bezier curve is then created between these three points
                connectionPath = QPainterPath()
                connectionPath.moveTo(posA)
                connectionPath.quadTo(centerPos,posB)
                #The path is converted to a graphics path item
                connectionItem = QGraphicsPathItem(connectionPath)
                #The PathItem is given the color of chromosome B and a width (default is 1 pixel wide)
                pen = QPen(self.chromoColors[chrB.name], self.connWidth)
                connectionItem.setPen(pen)
                connectionItem.setZValue(1)
                #Creating a rectangle (1x1 pixels) around each posB point for use when heat mapping the connections
                rect = QRect(posB.toPoint(),QSize(1,1))
                rect.moveCenter(posB.toPoint())
                connectionInfo = [connectionItem, rect, posA, posB, chrB, counter]
                #The item is added to a list
                self.connectionItems[chrA.name].append(connectionInfo)
                counter = counter + 1

        #Checking to see if any neighbouring connections are close to eachother, if they are -> create a color gradient for both the
        #neighbouring connection lines, that gets darker closer to the connection
        for chrA in self.chromosomes:
            for connItemA in self.connectionItems[chrA.name]:
                for chrB in self.chromosomes:
                    for connItemB in self.connectionItems[chrB.name]:
                        #check to see if one rectangle is comparing with itself
                        if connItemA[5] == connItemB[5]:
                            continue
                        if connItemA[1].intersects(connItemB[1]):
                            linearGrad = QLinearGradient(connItemA[2], connItemA[3])
                            linearGrad.setColorAt(0, self.chromoColors[connItemA[4].name])
                            linearGrad.setColorAt(1, self.chromoColors[connItemA[4].name].darker(300))
                            connItemA[0].setPen(QPen(QBrush(linearGrad), self.connWidth))
                            connItemB[0].setPen(QPen(QBrush(linearGrad), self.connWidth))

    def numDispChromosomes(self):
        dispChromos = 0
        for chromo in self.chromosomes:
            if chromo.display:
                dispChromos += 1
        return dispChromos

    def createDistanceMarkers(self):
        totalDispBP = self.returnTotalDisplayedBP()
        if totalDispBP > 0:
            adjustPoint = QPoint(3,3)
            inRect = QRect(self.outerChrRect.topLeft()-adjustPoint, self.outerChrRect.bottomRight()+adjustPoint)
            outRect = QRect(self.outerChrRect.topLeft()+adjustPoint, self.outerChrRect.bottomRight()-adjustPoint)
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

                while curAngle < (chrStartAngle + chrEndAngle):
                    if angleCounter%10 == 0:
                        adjustPoint = QPoint(10,10)
                        inRect = QRect(self.outerChrRect.topLeft()-adjustPoint, self.outerChrRect.bottomRight()+adjustPoint)
                        outRect = QRect(self.outerChrRect.topLeft()+adjustPoint, self.outerChrRect.bottomRight()-adjustPoint)
                        distanceName = str(int(angleCounter))
                    else:
                        adjustPoint = QPoint(3,3)
                        inRect = QRect(self.outerChrRect.topLeft()-adjustPoint, self.outerChrRect.bottomRight()+adjustPoint)
                        outRect = QRect(self.outerChrRect.topLeft()+adjustPoint, self.outerChrRect.bottomRight()-adjustPoint)
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
                    self.scene.addItem(distanceNameItem)
                    lineBetween = QLineF(outerPath.currentPosition(),innerPath.currentPosition())
                    outerPath.moveTo(lineBetween.pointAt(0))
                    outerPath.lineTo(lineBetween.pointAt(1))
                    angleCounter += 1
                    curAngle += angleIncr

                chrStartAngle += chrEndAngle + 1
                distItem = QGraphicsPathItem(outerPath)
                self.scene.addItem(distItem)

            diaAdjust = (math.sqrt(2) * self.outermostRect.width() - self.outermostRect.width()) / 8
            startPos = QPointF(self.outermostRect.bottomRight()) - QPointF(diaAdjust,diaAdjust)
            for incr in range(11):
                adjustPoint1 = QPointF(incr*10,10)
                adjustPoint2 = QPointF(incr*10,-10)
                adjustPoint3 = QPointF(incr*10,5)
                adjustPoint4 = QPointF(incr*10,-5)
                if incr%10 == 0:
                    lineBetween = QLineF(startPos + adjustPoint1, startPos + adjustPoint2)
                    legendNameItem = QGraphicsTextItem(str(incr))
                else:
                    lineBetween = QLineF(startPos + adjustPoint3, startPos + adjustPoint4)
                    legendNameItem = QGraphicsTextItem("")
                legendPath = QPainterPath()
                legendPath.moveTo(lineBetween.pointAt(0))
                legendPath.lineTo(lineBetween.pointAt(1))
                legendNameItem.setPos(legendPath.currentPosition().x()-10,legendPath.currentPosition().y()-20)
                legendItem = QGraphicsPathItem(legendPath)
                self.scene.addItem(legendItem)
                self.scene.addItem(legendNameItem)

            lineBetween = QLineF(startPos, startPos + QPointF(100,0))
            legendTitleItem = QGraphicsTextItem("x" + str(self.bpDistanceResolution) + " Mb")
            legendPath = QPainterPath()
            legendPath.moveTo(lineBetween.pointAt(0))
            legendPath.lineTo(lineBetween.pointAt(1))
            legendTitleItem.setPos(legendPath.currentPosition().x()-75, legendPath.currentPosition().y()+20)
            legendItem = QGraphicsPathItem(legendPath)
            self.scene.addItem(legendItem)
            self.scene.addItem(legendTitleItem)

    #Imports either a tab file with specified regions to color, or a cytoband file
    def importColorTab(self):
        fileName = QFileDialog.getOpenFileName(None, "Specify a color tab-file", QDir.currentPath(), "tab-files (*.tab *.txt)")[0]
        if fileName.endswith("tab"):
            colorTab = data.readGeneralTab(fileName)
            self.colorRegions(colorTab,False,1)
        else:
            colorTab = data.readCytoTab(fileName)
            self.colorRegions(colorTab,True,1)

    def colorCentromeres(self):
        #Look in the cyto file definitions for acen regions, prepare a list of chromosomes and positions for these
        cytoTab = self.dataDict['cytoTab']
        centromereRegions = []
        for cyto in cytoTab:
            if cyto[4] == 'acen':
                chromoName = cyto[0]
                cytoStart = int(cyto[1])
                cytoEnd = int(cyto[2])
                color = 'red'
                centromereRegions.append([chromoName,cytoStart,cytoEnd,color])
        self.colorRegions(centromereRegions,False,0.5)

    def colorRegions(self,colorTab,cytoband,opacity):
        self.defineRectangles()
        colors = {'red': Qt.red, 'magenta': Qt.magenta, 'blue': Qt.blue, 'cyan': Qt.cyan, 'yellow': Qt.yellow, 'darkBlue': Qt.darkBlue}
        stainColors = {'acen':Qt.darkRed, 'gneg':Qt.white,'gpos100':Qt.black,'gpos25':Qt.lightGray,'gpos50':Qt.gray,
        'gpos75':Qt.darkGray,'gvar':Qt.white,'stalk':Qt.red}
        #Every item in colorTab, if not a cytoband file, contains 4 items: chromosome name, startPos, endPos, color
        #If a cytoband file, use the stain name to determine color
        for region in colorTab:
            #Find a matching chromosome item for every region and make sure it's displayed
            for chromo in self.chromosomes:
                if not chromo.display:
                    continue
                if chromo.name == region[0]:
                    #where on the circle does this chromosome start, how much does it span?
                    startAngle = self.chromosome_angle_list[chromo.name][0]
                    angleSpan = self.chromosome_angle_list[chromo.name][1]
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
                    outer.moveTo(self.outerChrRect.center())
                    outer.arcTo(self.outerChrRect,-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    inner.moveTo(self.innerChrRect.center())
                    inner.arcTo(self.innerChrRect,-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    #Removes any leftover painting path that may cause ugly lines in the middle
                    leftoverArea = QPainterPath()
                    leftoverArea.moveTo(self.innerChrRect.center())
                    leftoverArea.arcTo(self.innerChrRect,0,360)
                    #Remove the inner circle sector from the outer sector to get the area to display
                    regionPath = outer.subtracted(inner)
                    regionPath = regionPath.subtracted(leftoverArea)
                    regionItem = QGraphicsPathItem(regionPath)
                    if cytoband:
                        regionColor = stainColors[region[4]]
                    else:
                        regionColor = colors[region[3]]
                    regionItem.setBrush(regionColor)
                    regionItem.setOpacity(opacity)
                    #Add the finished graphics item to a list
                    self.graphicItems.append(regionItem)
                    self.scene.addItem(regionItem)

    def initscene(self):
        self.defineRectangles()
        #Clear old items
        for chrItem in self.chromosomeItems:
            #Update the color dict in case user modified these
            self.chromoColors[chrItem.nameString] = chrItem.brush().color()
        self.scene.clear()
        self.scene.markedChromItems = []
        self.chromosomeItems = []
        self.coverageItems = []
        self.graphicItems = []
        #Create new graphics items, add these to the scene.
        self.makeItems()
        self.createCoverage()
        self.drawConnections()
        self.addLayers()
        self.createDistanceMarkers()
        self.addFileText()
        for connList in self.connectionItems.values():
            for connItem in connList:
                self.scene.addItem(connItem[0])
        if self.showCentromereRegion:
            self.colorCentromeres()
        #Exception when changing between views and variant table is old; needs to be fixed
        #Should save the view's active chromosome and select this again on view change (in mainwin)
        try:
            self.highlightVariants()
        except:
            pass
        self.update()

    #Adds the VCF and TAB file names as text items to the top of the scene
    def addFileText(self):
        tabText = self.scene.addText("TAB File: " + self.tabName.split('/')[-1])
        tabText.setFlag(QGraphicsItem.ItemIsMovable)
        tabText.setTextInteractionFlags(Qt.TextEditorInteraction)
        tabText.setPos(self.outermostRect.topLeft())
        tabText.setX(tabText.pos().x() - tabText.boundingRect().width() - 100)
        tabText.setX(tabText.pos().y() - tabText.boundingRect().height() - 100)
        vcfText = self.scene.addText("VCF File: " + self.vcfName.split('/')[-1])
        vcfText.setPos(tabText.pos())
        vcfText.setY(vcfText.pos().y()-tabText.boundingRect().height())
        vcfText.setFlag(QGraphicsItem.ItemIsMovable)
        vcfText.setTextInteractionFlags(Qt.TextEditorInteraction)

    def setActiveChromosome(self,chromoNumber,varTable):
        self.varTable = varTable
        self.activeChromo = self.chromosomes[chromoNumber]
        self.initscene()

    def highlightVariants(self):
        selectedVariants = []
        for chrA in self.chromosomes:
            if not chrA.display:
                continue
            if self.activeChromo and self.varTable and self.activeChromo.display:
                selectedVariants = common.returnVariants(self.activeChromo,self.varTable)
            for variant in chrA.variants:
                if variant[9] and not variant[2].startswith("G") and not variant[2].startswith("M") and (variant in selectedVariants or variant[11]):
                    if not self.chromosomeDict[variant[2]].display:
                            continue
                    chrB = self.chromosomeDict[variant[2]]
                    #The curAngle determines where on the circle the chromosome is located (also used in makeItems)
                    curAngle_A = self.chromosome_angle_list[chrA.name][0]
                    curAngle_B = self.chromosome_angle_list[chrB.name][0]
                    #The windows of each variant (WINA, WINB) are used to determine where on the chromosome the interaction is located
                    #If chrA higher in order than chrB, WINA and WINB are switched, so check this first
                    if "WINA" in variant[5]:
                        
                        if self.chromosomes.index(chrA) > self.chromosomes.index(chrB):
                            bp_End_A = int(variant[5]["WINB"].split(',')[1])
                            chrA_length = int(chrA.end)
                            bp_End_B = int(variant[5]["WINA"].split(',')[1])
                            chrB_length = int(chrB.end)
                        else:
                            bp_End_A = int(variant[5]["WINA"].split(',')[1])
                            chrA_length = int(chrA.end)
                            bp_End_B = int(variant[5]["WINB"].split(',')[1])
                            chrB_length = int(chrB.end)
                    else:
                        bp_End_A = variant[1]
                        chrA_length = int(chrA.end)
                        bp_End_B = variant[3]
                        chrB_length = int(chrB.end)
                    #A percentage of the total angle (used to draw the chromosome in makeItems) determines where on the
                    #chromosome the connection is located
                    angleIncr_A = (1-((chrA_length - bp_End_A) / chrA_length)) * (self.chromosome_angle_list[chrA.name][1]-2)
                    angleIncr_B = (1-((chrB_length - bp_End_B) / chrB_length)) * (self.chromosome_angle_list[chrB.name][1]-2)
                    #A Path is created to assign the position for the connections
                    tempPath = QPainterPath()
                    #The arMoveTo() function is used to get the different points on each chromosome the connection is located
                    tempPath.arcMoveTo(self.innerChrRect, - (curAngle_A + angleIncr_A))
                    posA = tempPath.currentPosition()
                    tempPath.arcMoveTo(self.innerChrRect, - (curAngle_B + angleIncr_B))
                    posB = tempPath.currentPosition()
                    centerPos = self.outerChrRect.center()
                    #A Bezier curve is then created between these three points
                    connectionPath = QPainterPath()
                    connectionPath.moveTo(posA)
                    connectionPath.quadTo(centerPos,posB)
                    #The path is converted to a graphics path item
                    connectionItem = QGraphicsPathItem(connectionPath)
                    #The PathItem is given the color of chromosome B and a width (default is 1 pixel wide)
                    pen = QPen(Qt.red, self.connWidth)
                    pen.setStyle(Qt.DashLine)
                    connectionItem.setPen(pen)
                    connectionItem.setZValue(2)
                    connectionItem.setOpacity(0.6)
                    self.scene.addItem(connectionItem)

    #Iterates through lists of regions for each chr formatted as identifier,start,end,text ..  and adds a circle layer with these regions
    def addLayers(self):
        for chromo in self.chromosomes:
            if not chromo.display:
                continue
            layerIndex = 0
            for regionList in self.bedDict[chromo.name]:
                layerRects = self.addedLayers[layerIndex]
                layerRects[0].moveCenter(self.innerCoverageRect.center())
                layerRects[1].moveCenter(self.innerCoverageRect.center())
                for region in regionList:
                    #where on the circle does this chromosome start, how much does it span?
                    startAngle = self.chromosome_angle_list[chromo.name][0]
                    angleSpan = self.chromosome_angle_list[chromo.name][1]
                    #the region starts and ends at certain points in this span
                    regionStart = int(region[1])
                    regionEnd = int(region[2])
                    #if the files are slightly misaligned, set maximum end to chromo end
                    if regionEnd > int(chromo.end):
                        regionEnd = int(chromo.end)
                    regionStartAngle = startAngle + (regionStart/int(chromo.end))*(angleSpan-2)
                    regionEndAngle = startAngle + (regionEnd/int(chromo.end))*(angleSpan-2)
                    #Only construct an item if the span is larger than one degree
                    if (regionEnd-regionStart) <= self.minBedBp*1000:
                        continue
                    #Define two painter paths constructing circle sectors
                    outer = QPainterPath()
                    inner = QPainterPath()
                    outer.moveTo(layerRects[1].center())
                    outer.arcTo(layerRects[1],-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    inner.moveTo(layerRects[0].center())
                    inner.arcTo(layerRects[0],-regionStartAngle, -(regionEndAngle-regionStartAngle))
                    #Removes any leftover painting path that may cause ugly lines in the middle
                    leftoverArea = QPainterPath()
                    leftoverArea.moveTo(layerRects[0].center())
                    leftoverArea.arcTo(layerRects[0],0,360)
                    #Remove the inner circle sector from the outer sector to get the area to display
                    regionPath = outer.subtracted(inner)
                    regionPath = regionPath.subtracted(leftoverArea)
                    regionItem = BedRegionItem(regionPath,region)
                    regionItem.setBrush(self.chromoColors[chromo.name])
                    self.scene.addItem(regionItem)
                layerIndex += 1

    def addLayerRect(self):
        newRectInner = copy.copy(self.outermostRect)
        newRectOuter = copy.copy(self.outermostRect)
        offset1 = QPoint(50,50)
        offset2 = QPoint(20,20)
        newRectInner.setTopLeft(self.outermostRect.topLeft()-offset1)
        newRectInner.setBottomRight(self.outermostRect.bottomRight()+offset1)
        newRectOuter.setTopLeft(newRectInner.topLeft()-offset2)
        newRectOuter.setBottomRight(newRectInner.bottomRight()+offset2)
        self.addedLayers.append([newRectInner,newRectOuter])
        self.outermostRect = newRectOuter

    #Reads a bed file and adds a list of bed (or any similarly structured file) elements for each chromosome
    def addNewLayer(self):
        newBedDict = common.createBedDict()
        #Insert the list with new layer regions for each chromosome
        for key in self.chromosomeDict.keys():
            if key in newBedDict.keys():
                self.bedDict[key].append(newBedDict[key])
            else:
                #If no match in newly created list, insert empty region list for this chromosome
                self.bedDict[key].append([])
        self.addLayerRect()
        self.initscene()

    def wheelEvent(self,event):
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)

#Bed graphic item with some convenience functions for marking etc
class BedRegionItem(QGraphicsPathItem):

    def __init__(self,path,bedFields):
        super().__init__(path)
        self.bedText = bedFields[3]
        self.setToolTip(self.bedText)
        self.marked = False
        self.setData(0,"bedItem")

    def toggleMarked(self):
        if not self.marked:
            pen = self.pen()
            pen.setStyle(Qt.DashLine)
            pen.setBrush(Qt.red)
        else:
            pen = QPen()
        self.setPen(pen)
        self.marked = not self.marked

    def setMarked(self):
        pen = self.pen()
        pen.setStyle(Qt.DashLine)
        pen.setBrush(Qt.red)
        self.setPen(pen)
        self.marked = True

    def setUnmarked(self):
        pen = QPen()
        self.setPen(pen)
        self.marked = False

#Subclass of graphics path item for custom handling of mouse events
class ChromoGraphicItem(QGraphicsPathItem):

    def __init__(self,path,nameString):
        super().__init__(path)
        self.selected = False
        self.nameString = nameString
        self.setData(0,"chromoItem")
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
    #Put this in separate function for more flexible handling of when name is painted?
    def paint(self,painter,option,widget):
        super().paint(painter,option,widget)
        painter.drawText(self.path().boundingRect().center(),self.nameString)

#Subclass of graphics scene for custom handling of mouse events
class CircScene(QGraphicsScene):

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
            if item.data(0) == "chromoItem":
                if item.selected:
                    item.unmark()
                    self.markedChromItems.remove(item)
                else:
                    item.mark()
                    self.markedChromItems.append(item)
            if item.data(0) == 'bedItem':
                item.toggleMarked()
                menu = QMenu()
                linkAct = QAction("OMIM search: " + item.bedText, self)
                linkAct.triggered.connect(lambda: self.openLink(item.bedText))
                menu.addAction(linkAct)
                menu.exec_(QCursor.pos())
                item.toggleMarked()
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
                #Update color dict
                self.views()[0].chromoColors[item.nameString] = chosenColor
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

    #Primitive function to search for bed item name in OMIM database
    #Currently opens a browser and simply searches for the term, but could use omim REST-api?
    def openLink(self,linkText):
        linkUrl = QUrl("https://www.ncbi.nlm.nih.gov/omim/?term=" + linkText)
        QDesktopServices.openUrl(linkUrl)
