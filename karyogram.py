from PySide.QtCore import *
from PySide.QtGui import *
import math
import common
import data

class KaryogramView(QGraphicsView):

    def __init__(self,dataDict,karyoSettings,parent):
        self.type = "karyogram"
        self.scene = QGraphicsScene()
        self.dataDict = dataDict
        self.karyoSettings = karyoSettings
        super().__init__(self.scene,parent)
        self.chromosomes = self.dataDict['chromosomeList']
        self.chromosomeDict = {chromo.name: chromo for chromo in self.chromosomes}
        self.cytoInfo = self.dataDict['cytoTab']
        self.stainNames = parent.stainNames
        self.stainColors = parent.stainColors
        self.numDispChromos = 24
        self.itemsPerRow = int(self.karyoSettings["itemsPerRow"])
        self.cytoGraphicItems = {}
        self.cytoGraphicItemPositions = {}
        self.connectionGraphicItems = []
        self.variantMarkItems = []
        self.activeChromo = None
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.createSettings()
        self.createChInfo()
        #self.updateItems()

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
        verticalHeaders = ["itemsPerRow"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        itemsPerRowText = QStandardItem("Items per row")
        itemsPerRowText.setEditable(False)
        itemsPerRowText.setToolTip("Maximum of chromosomes to display per row in the scene")
        itemsPerRowData = QStandardItem()
        itemsPerRowData.setData(self.itemsPerRow,0)
        itemsPerRowData.setEditable(True)
        self.settingsModel.setItem(0,0,itemsPerRowText)
        self.settingsModel.setItem(0,1,itemsPerRowData)
        self.settingsModel.itemChanged.connect(self.updateSettings)

    def updateSettings(self):
        #Go through every row in the settings model and update accordingly
        #self.stainColors = self.stainColors
        self.updateItems()
        for row in range(self.settingsModel.rowCount()):
            item = self.settingsModel.item(row,1)
            if row == 0:
                self.itemsPerRow = item.data(0)

    #Creates and returns a widget with this view's settings
    def returnSettingsWidget(self):
        settingsWidget = QWidget()
        settingsLayout = QGridLayout()
        settingsList = QTableView()
        #settingsList.setColumnWidth(0,700)
        #settingsList.setColumnWidth(1,100)
        settingsList.setEditTriggers(QAbstractItemView.AllEditTriggers)
        settingsList.setShowGrid(False)
        settingsList.horizontalHeader().hide()
        settingsList.verticalHeader().hide()
        settingsList.setModel(self.settingsModel)
        settingsList.setTextElideMode(Qt.ElideNone)
        settingsList.resizeColumnsToContents()
        settingsLayout.addWidget(settingsList,0,0,1,5)
        settingsWidget.setLayout(settingsLayout)
        return settingsWidget

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
        
        self.updateItems()

    #Creates data model for info window
    def createChInfo(self):
        self.chModel = QStandardItemModel()
        topstring = ["Name","Length","No. of variants","Display","Draw connections", "Cyto band names"]
        self.chModel.setHorizontalHeaderLabels(topstring)
        for chromo in self.chromosomes:
            infostring = [chromo.name,chromo.end,str(len(chromo.variants))]
            infoItems = [QStandardItem(string) for string in infostring]
            dispCheckItem = QStandardItem()
            dispCheckItem.setCheckable(False)
            connCheckItem = QStandardItem()
            connCheckItem.setCheckable(False)
            connCheckItem.setCheckState(Qt.Unchecked)
            cytoCheckItem = QStandardItem()
            cytoCheckItem.setCheckable(False)
            cytoCheckItem.setCheckState(Qt.Unchecked)
            checkList = [dispCheckItem, connCheckItem, cytoCheckItem]
            infoItems.extend(checkList)
            chromo.display_connections = False
            chromo.display_cytoBandNames = False
            if (self.chromosomes.index(chromo) < 24):
                dispCheckItem.setCheckState(Qt.Checked)
                self.chModel.appendRow(infoItems)
                chromo.display = True
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
        #Button for viewing selected chromosome selectedVariants
        viewVarButton = QPushButton('View selectedVariants', self.chDia)
        viewVarButton.clicked.connect(self.viewselectedVariants)
        #Button for toggling connections
        connButton = QPushButton('Toggle connections', self.chDia)
        connButton.clicked.connect(self.toggleConnections)
        #Button for toggling cyto band names
        cytoButton = QPushButton('Toggle cyto band names', self.chDia)
        cytoButton.clicked.connect(self.toggleBandNames)
        self.chDia.layout = QGridLayout(self.chDia)
        self.chDia.layout.addWidget(self.chList,0,0,1,4)
        self.chDia.layout.addWidget(togButton,1,0,1,1)
        self.chDia.layout.addWidget(viewVarButton,1,1,1,1)
        self.chDia.layout.addWidget(connButton,1,2,1,1)
        self.chDia.layout.addWidget(cytoButton,1,3,1,1)
        self.chDia.setMinimumSize(700,400)
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
        #Button for viewing selected chromosome selectedVariants
        viewVarButton = QPushButton(QIcon("icons/viewList.png"),"")
        viewVarButton.clicked.connect(self.viewselectedVariants)
        viewVarButton.setToolTip("View selectedVariants in chromosome")
        #Button for adding selectedVariants
        #addVariantButton = QPushButton(QIcon("icons/new.png"),"")
        #addVariantButton.clicked.connect(self.addVariant)
        #addVariantButton.setToolTip("Add custom variant")
        #Button for toggling connections
        connButton = QPushButton(QIcon("icons/connections.png"),"")
        connButton.clicked.connect(self.toggleConnections)
        connButton.setToolTip("Toggle display of connections between selectedVariants")
        #Button for toggling cyto band names
        cytoButton = QPushButton(QIcon("icons/display.png"),"")
        cytoButton.clicked.connect(self.toggleBandNames)
        cytoButton.setToolTip("Toggle display of band names")
        chromoInfoLayout = QGridLayout()
        chromoInfoLayout.addWidget(self.chList,0,0,1,4)
        chromoInfoLayout.addWidget(togButton,1,0,1,1)
        chromoInfoLayout.addWidget(connButton,1,1,1,1)
        chromoInfoLayout.addWidget(viewVarButton,1,2,1,1)
        #chromoInfoLayout.addWidget(addVariantButton,1,3,1,1)
        chromoInfoLayout.addWidget(cytoButton,1,3,1,1)
        chromoWidget = QWidget()
        chromoWidget.setLayout(chromoInfoLayout)
        return chromoWidget
        
    def setActiveChromosome(self,chromoNumber,varTable):
        self.varTable = varTable
        self.activeChromo = self.chromosomes[chromoNumber]
        self.updateItems()

    #Creates a popup containing variant info in a table.
    def viewselectedVariants(self):
        #Find which chromosome's selectedVariants is to be viewed by looking at chList rows
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        #Display a variant window for every selected chromosome
        for row in selectedRows:
            chromo = self.chromosomes[row]
            viewVarDia = common.createVariantDia(chromo,self)
            #Also connect toggle button in the widget to update scene
            viewVarDia.layout.itemAtPosition(2,0).widget().clicked.connect(self.updateItems)
            viewVarDia.show()

    def createVariantWidget(self,row):
        chromo = self.chromosomes[row]
        varWidget = common.createVariantWidget(chromo)
        #Also connect toggle button in the widget to update scene
        varWidget.layout().itemAtPosition(2,0).widget().clicked.connect(self.updateItems)
        return varWidget

    def addVariant(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            common.addVariant(chromo,self.chromosomes)

    def toggleDisp(self):
        #The row associated with the item corresponds to a chromosome
        #row 1 is chr 1, row 2 is chr2 ... 23 is x, 24 is y and so on
        #which corresponds to index 0, 2 ... 22, 23 in list of chromosomes
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
                self.numDispChromos -= 1
            else:
                dispItem.setCheckState(Qt.Checked)
                self.chromosomes[row].display = True
                self.numDispChromos += 1
        self.updateItems()

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
        self.updateItems()

    def toggleBandNames(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            dispCytoName = self.chModel.item(row,5)
            if self.chromosomes[row].display_cytoBandNames:
                dispCytoName.setCheckState(Qt.Unchecked)
                self.chromosomes[row].display_cytoBandNames = False
            else:
                dispCytoName.setCheckState(Qt.Checked)
                self.chromosomes[row].display_cytoBandNames = True
        self.updateItems()

    def drawConnections(self):
        self.connectionGraphicItems = []
        selectedselectedVariants = []
        
        placeLeft = True
        print(0)
        #Loops through the full list of chromosomes and checks if the connections should be displayed or not
        for chrA in self.chromosomes:
            if not (chrA.display_connections and chrA.display):
                continue
            print(1)
            #only create the connection list if it has not been initialized earlier
            if not chrA.connections:
                chrA.createConnections()
            for connection in chrA.connections:
                print(2)
                #The information is stored as string elements and needs to be converted to integers
                if connection[1] == 'X':
                    chrBIndex=22
                    chrB = self.chromosomes[chrBIndex]
                elif connection[1] == 'Y':
                    chrBIndex=23
                    chrB = self.chromosomes[chrBIndex]
                elif (connection[1].startswith('G') or connection[1].startswith('M')):
                    continue
                else:
                    chrB = self.chromosomes[int(connection[1])-1]
                print(3)
                if not chrB.display or connection[4] is None:
                    continue 
                #If chrA higher in order than chrB, WINA and WINB are switched, so check this first  
                print(4)
                if self.chromosomes.index(chrA) > self.chromosomes.index(chrB):
                    connEndPos = int(connection[2].split(',')[1])
                    connStartPos = int(connection[3].split(',')[1])
                else:
                    connEndPos = int(connection[3].split(',')[1])
                    connStartPos = int(connection[2].split(',')[1])
                print(5)
                #The cytobands which the connections will go between
                #look for the cytoband on chrA, data(2) is the start pos for the cytoband and data(3) is the end pos
                for cytoItem in self.cytoGraphicItems[chrA.name].bandItemsDict.values():
                    if connStartPos > cytoItem.data(2) and connStartPos < cytoItem.data(3):
                            cbandA = cytoItem.data(0)
                #look for the cytoband on chrB
                for cytoItem in self.cytoGraphicItems[chrB.name].bandItemsDict.values():
                    if connEndPos > cytoItem.data(2) and connEndPos < cytoItem.data(3):
                        cbandB = cytoItem.data(0)  
                #do not show small selectedVariants within one cytoband
                if cbandA == cbandB:
                    continue
                #do not show connections to bands that does not exist in the dictionary
                if not (cbandA in self.cytoGraphicItems[chrA.name].bandItemsDict and cbandB in self.cytoGraphicItems[chrB.name].bandItemsDict):
                    continue
                print(6)
                if chrA.name == chrB.name:    
                    if placeLeft:
                        xPosA = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA].boundingRect().left()
                        xPosB = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB].boundingRect().left()
                    else:
                        xPosA = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA].boundingRect().right()
                        xPosB = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB].boundingRect().right()
                else:
                    xPosA = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA].boundingRect().right()
                    xPosB = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB].boundingRect().left() 
                print(7)
                #Find the y position of the actual cytoband in each chromosome, by accessing the chromosome band dicts
                cBandAItem = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA]                
                cBandBItem = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB]
                yPosA = cBandAItem.boundingRect().top() + cBandAItem.boundingRect().height() / 2
                yPosB = cBandBItem.boundingRect().top() + cBandBItem.boundingRect().height() / 2
                #If the item has been moved, x and y are how much the item has been moved by; update position with these
                xPosA += self.cytoGraphicItems[chrA.name].x()
                xPosB += self.cytoGraphicItems[chrB.name].x()
                yPosA += self.cytoGraphicItems[chrA.name].y()
                yPosB += self.cytoGraphicItems[chrB.name].y()
                pointA = QPoint(xPosA, yPosA)
                pointB = QPoint(xPosB, yPosB)
                connectionPath = QPainterPath()
                connectionPath.moveTo(pointA)
                if chrA.name == chrB.name:
                    if placeLeft:
                        pointC = QPoint(xPosA-80, (yPosA+yPosB)/2)
                    else:
                        pointC = QPoint(xPosA+80, (yPosA+yPosB)/2)
                    placeLeft = not placeLeft
                    connectionPath.quadTo(pointC, pointB)
                else:
                    connectionPath.lineTo(pointB)
                print(9)
                connectionItem = QGraphicsPathItem(connectionPath)
                pen = QPen()
                pen.setBrush(Qt.darkCyan)
                pen.setWidth(2)
                connectionItem.setZValue(2)
                if self.activeChromo and self.varTable:        
                    selectedChromo = self.activeChromo
                    selectedselectedVariants = common.returnselectedVariants(selectedChromo,self.varTable)
                    for variant in selectedselectedVariants:
                        if variant[0] is not variant[2]:
                            variantConnection = [variant[0],variant[2],variant[5]["WINA"],variant[5]["WINB"],variant[8]]
                        else:
                            variantConnection = [variant[0], variant[2], str(variant[1]) + "," + str(variant[1]), str(variant[3]) + "," + str(variant[3]), variant[8]]
                        if variantConnection == connection:
                            pen.setBrush(Qt.red)
                            connectionItem.setZValue(3)
                connectionItem.setPen(pen)
                print(8)
                self.scene.addItem(connectionItem)
                self.connectionGraphicItems.append(connectionItem)

    #Create chromosome items consisting of cytobands, names of bands, and chromosome names
    def createChromosomeItems(self):
        if self.numDispChromos > 0:

            size = self.size()
            containerRect = QRect(QPoint(50,50), QPoint(size.width()-50,size.height()-50))
            #find the maximum displayed chromosome length, and let this be 100% of item length
            maxBp = 0
            for chromo in self.chromosomes:
                if not (chromo.display or "GL" in chromo.name or "MT" in chromo.name):
                    continue
                if int(chromo.end) > maxBp:
                    maxBp = int(chromo.end)

            #Lays out items vetically with equal spacing between each other, with a width depending on screen size
            currentXPosition = 0
            xIncrement = (containerRect.width() / self.numDispChromos) + 60
            self.chromoWidth = containerRect.width() / 48
            counter = 0
            numRows = math.ceil(24 / self.itemsPerRow)
            displaceY = 0
            longestItemInRow = 0
            
            #Create the graphic items for each chromosome if they are set to be displayed
            for chromo in self.chromosomes:
                if not chromo.display or "GL" in chromo.name or "MT" in chromo.name:
                    continue
                chromoHeight = (int(chromo.end)/maxBp)*(containerRect.height())
                if chromoHeight > longestItemInRow:
                    longestItemInRow = chromoHeight
                bandItems = []
                textItems = []
                placeLeft = True
                firstAcen = True
                rounded = ""
                #Find each cytoband for this chromosome, and create band items using this data
                for cyto in self.cytoInfo:
                    if cyto[0] == chromo.name:
                        cytoStart = int(cyto[1])
                        cytoEnd = int(cyto[2])
                        totalCytoBP = cytoEnd-cytoStart
                        bandHeight = (totalCytoBP / int(chromo.end)) * (chromoHeight)
                        bandYPos = (cytoStart / int(chromo.end)) * (chromoHeight)
                        bandXPos = currentXPosition
                        bandWidth = self.chromoWidth
                        #If first item, round on top
                        if cytoStart is 0:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setBottom(rect.bottom() + rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            rounded = "top"
                        #If first acen, round on bottom
                        elif cyto[4] == 'acen' and firstAcen:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            firstAcen = False
                            rounded = "bottom"
                        #If second acen, round on top
                        elif cyto[4] == 'acen':
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setBottom(rect.bottom() + rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            rounded = "top"
                        #If last item, round on bottom (i.e. last index in last chr or new chr next on next index)
                        elif self.cytoInfo.index(cyto) == len(self.cytoInfo)-1:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            rounded = "bottom"
                        elif self.cytoInfo[self.cytoInfo.index(cyto)+1][0] != chromo.name:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            rounded = "bottom"
                        else:
                            #Create a rect item with corresponding stain color, tooltip, set data to band name for later use
                            bandRectItem = QGraphicsRectItem(bandXPos,bandYPos,bandWidth,bandHeight)
                            rounded = "none"
                        bandRectItem.setBrush(self.stainColors[cyto[4]])
                        bandRectItem.setToolTip(cyto[3] + ": " + str(totalCytoBP) + " bp")
                        bandRectItem.setData(0,cyto[3])
                        bandRectItem.setData(2, cytoStart)
                        bandRectItem.setData(3, cytoEnd)
                        bandRectItem.setData(4, bandYPos)
                        bandRectItem.setData(5, rounded)
                        self.scene.addItem(bandRectItem)
                        bandItems.append(bandRectItem)
                        if chromo.display_cytoBandNames:
                            bandNameItem = QGraphicsTextItem(cyto[3])
                            nameXPosition = bandRectItem.boundingRect().left()-bandRectItem.boundingRect().width() if placeLeft else bandRectItem.boundingRect().right()
                            bandNameItem.setPos(nameXPosition,bandRectItem.boundingRect().center().y()-12)
                            bandNameItem.setScale(self.chromoWidth/35)
                            self.scene.addItem(bandNameItem)
                            nameRectItem = QGraphicsRectItem
                            textItems.append(bandNameItem)
                            placeLeft = not placeLeft
                chromoNameItem = QGraphicsTextItem(chromo.name)
                chromoNameItem.setPos(currentXPosition,chromoHeight)
                chromoNameItem.setScale(self.chromoWidth/20)
                self.scene.addItem(chromoNameItem)
                textItems.append(chromoNameItem)
                #Create a custom graphic item group from created items, enter in dict
                cytoItem = KaryoGraphicItem(bandItems,textItems,chromo.name)
                cytoItem.setPos(cytoItem.pos().x(),cytoItem.pos().y() + displaceY)
                self.cytoGraphicItems[chromo.name] = cytoItem
                currentXPosition += xIncrement
                self.scene.addItem(cytoItem)
                counter += 1
                if counter%self.itemsPerRow == 0:
                    currentXPosition = 0
                    displaceY += longestItemInRow + 30
                    longestItemInRow = 0

    def markselectedVariants(self):
        self.variantMarkItems = []
        selectedVariants = []
        for chrA in self.chromosomes:
            if not chrA.display or "GL" in chrA.name or "MT" in chrA.name:
                continue
            if self.activeChromo and self.varTable and self.activeChromo.display:
                selectedVariants = common.returnselectedVariants(self.activeChromo,self.varTable)
            chrAHeight = 0
            xPosA = self.cytoGraphicItems[chrA.name].mapRectToScene(self.cytoGraphicItems[chrA.name].boundingRect()).left()
            yPosA = self.cytoGraphicItems[chrA.name].mapRectToScene(self.cytoGraphicItems[chrA.name].boundingRect()).bottom()
            for band in self.cytoGraphicItems[chrA.name].bandItemsDict.values():
                chrAHeight += band.mapRectToScene(band.boundingRect()).height()
                xPosA = band.mapRectToScene(band.boundingRect()).left()
                if band.mapRectToScene(band.boundingRect()).top() < yPosA:
                            yPosA = band.mapRectToScene(band.boundingRect()).top()
            chrAWidth = self.chromoWidth+1
            chrALength = int(chrA.end)
            for variant in selectedVariants:
                print(variant)
            for variant in chrA.variants:
                if variant[9] and not variant[2].startswith("G") and (variant in selectedVariants or variant[11]):
                    if "WINA" in variant[5]:
                        if not self.chromosomeDict[variant[2]].display:
                            continue
                        chrB = self.chromosomeDict[variant[2]]
                        chrBHeight = 0
                        xPosB = self.cytoGraphicItems[chrB.name].mapRectToScene(self.cytoGraphicItems[chrB.name].boundingRect()).left()
                        yPosB = self.cytoGraphicItems[chrB.name].mapRectToScene(self.cytoGraphicItems[chrB.name].boundingRect()).bottom()
                        for band in self.cytoGraphicItems[chrB.name].bandItemsDict.values():
                            chrBHeight += band.mapRectToScene(band.boundingRect()).height()
                            xPosB = band.mapRectToScene(band.boundingRect()).left()
                            if band.mapRectToScene(band.boundingRect()).top() < yPosB:
                                yPosB = band.mapRectToScene(band.boundingRect()).top()
                        chrBWidth = self.chromoWidth+1
                        chrBLength = int(chrB.end)
                        if self.chromosomes.index(chrA) > self.chromosomes.index(chrB):
                                startWinA = int(variant[5]["WINB"].split(',')[0])
                                endWinA = int(variant[5]["WINB"].split(',')[1])
                                startWinB = int(variant[5]["WINA"].split(',')[0])
                                endWinB = int(variant[5]["WINA"].split(',')[1])
                        else: 
                                startWinA = int(variant[5]["WINA"].split(',')[0])
                                endWinA = int(variant[5]["WINA"].split(',')[1])
                                startWinB = int(variant[5]["WINB"].split(',')[0])
                                endWinB = int(variant[5]["WINB"].split(',')[1])
                        lengthWinA = endWinA - startWinA
                        lengthWinB = endWinB - startWinB
                        markHeightA = (lengthWinA/chrALength)*chrAHeight
                        markHeightB = (lengthWinB/chrBLength)*chrBHeight
                        markRectA = QRect(xPosA, yPosA + (startWinA/chrALength)*chrAHeight, chrAWidth, markHeightA)
                        markRectB = QRect(xPosB, yPosB + (startWinB/chrBLength)*chrBHeight, chrBWidth, markHeightB)
                        markRectItemA = QGraphicsRectItem(markRectA)
                        markRectItemB = QGraphicsRectItem(markRectB)
                        if variant[4] == "DEL":
                            markRectItemA.setBrush(QBrush(Qt.red))
                            markRectItemB.setBrush(QBrush(Qt.red))
                            markRectItemA.setPen(QPen(QBrush(Qt.red),1))
                            markRectItemB.setPen(QPen(QBrush(Qt.red),1))
                        elif variant[4] == "DUP":
                            markRectItemA.setBrush(QBrush(Qt.green))
                            markRectItemB.setBrush(QBrush(Qt.green))
                            markRectItemA.setPen(QPen(QBrush(Qt.green),1))
                            markRectItemB.setPen(QPen(QBrush(Qt.green),1))
                        else:   
                            markRectItemA.setBrush(QBrush(Qt.blue))
                            markRectItemB.setBrush(QBrush(Qt.blue))
                            markRectItemA.setPen(QPen(QBrush(Qt.blue),1))
                            markRectItemB.setPen(QPen(QBrush(Qt.blue),1))
                        markRectItemA.setOpacity(0.5)
                        markRectItemB.setOpacity(0.5)
                        self.cytoGraphicItems[chrA.name].addToGroup(markRectItemA)
                        self.cytoGraphicItems[chrB.name].addToGroup(markRectItemB)
                        self.scene.addItem(markRectItemA)
                        self.scene.addItem(markRectItemB)
                        self.variantMarkItems.append(markRectItemA)
                        self.variantMarkItems.append(markRectItemB)

                    else:
                        
                        startPos = variant[1]
                        endPos = variant[3]
                        variantLength = endPos-startPos
                        variantHeight = (variantLength/chrALength)*chrAHeight
                        markRect = QRect(xPosA, yPosA + (startPos/chrALength)*chrAHeight, chrAWidth, variantHeight)
                        markRectItem = QGraphicsRectItem(markRect)
                        if variant[4] == "DEL":
                            markRectItem.setBrush(QBrush(Qt.red))
                            markRectItem.setPen(QPen(QBrush(Qt.red),1))
                        elif variant[4] == "DUP":
                            markRectItem.setBrush(QBrush(Qt.green))
                            markRectItem.setPen(QPen(QBrush(Qt.green),1))
                        else:   
                            markRectItem.setBrush(QBrush(Qt.blue))
                            markRectItem.setPen(QPen(QBrush(Qt.blue),1))
                        markRectItem.setOpacity(0.5)
                        self.cytoGraphicItems[chrA.name].addToGroup(markRectItem)
                        self.scene.addItem(markRectItem)
                        self.variantMarkItems.append(markRectItem)
                    
          
    def updateItems(self):
        #Should use clear instead of individually removing..
        #Save any old positions of items in case they have been moved by the user
        for graphicItem in self.cytoGraphicItems.values():
            self.cytoGraphicItemPositions[graphicItem.nameString] = graphicItem.pos()
            try:
                self.scene.removeItem(graphicItem)
            except:
                pass
        self.scene.clear()
        self.createChromosomeItems()
        #Move back the items to their old positions
        for graphicItem in self.cytoGraphicItems.values():
            if graphicItem.nameString in self.cytoGraphicItemPositions and self.chromosomeDict[graphicItem.nameString].display:
                graphicItem.setPos(self.cytoGraphicItemPositions[graphicItem.nameString])
        try:
            print("tja")
            self.drawConnections()
            self.markselectedVariants()
        except:
            pass
        self.update()

    #Rearranges the graphic items to their default position
    def resetLayout(self):
        for graphicItem in self.cytoGraphicItems.values():
            try:
                self.scene.removeItem(graphicItem)
            except:
                pass
        for connItem in self.connectionGraphicItems:
            try:
                self.scene.removeItem(connItem)
            except:
                pass
        self.createChromosomeItems()
        self.drawConnections()
        self.update()

    def updateConnections(self):
        for item in self.connectionGraphicItems:
            try:
                self.scene.removeItem(item)
            except:
                pass
        self.drawConnections()
        self.update()

    #Opens a context menu on right click
    def contextMenuEvent(self,event):
        self.lastContextPos = event.pos()
        menu = QMenu()
        addSceneTextAct = QAction('Insert text',self)
        addSceneTextAct.triggered.connect(self.addSceneText)
        addLabelAct = QAction('Add label',self)
        addLabelAct.triggered.connect(self.addLabel)
        menu.addAction(addSceneTextAct)
        menu.addAction(addLabelAct)
        menu.exec_(QCursor.pos())

    def addSceneText(self):
        (text, ok) = QInputDialog.getText(None, 'Insert text', 'Text:')
        if ok and text:
            textItem = QGraphicsTextItem(text)
            textItem.setPos(self.lastContextPos)
            textItem.setFlag(QGraphicsItem.ItemIsMovable)
            textItem.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.scene.addItem(textItem)

    def addLabel(self):
        #Adds a label item
        labelDialog = QDialog()
        labelDialog.setWindowTitle("Add label")
        applyButton = QPushButton('Ok', labelDialog)
        applyButton.clicked.connect(labelDialog.accept)
        textBox = QLineEdit()
        colorBox = QComboBox()
        colorStrings = QColor.colorNames()
        colorBox.addItems(colorStrings)
        textLabel = QLabel("Label text: ")
        colorLabel = QLabel("Label color: ")
        labelDialog.layout = QGridLayout(labelDialog)
        labelDialog.layout.addWidget(textLabel,0,0)
        labelDialog.layout.addWidget(textBox,0,1)
        labelDialog.layout.addWidget(colorLabel,1,0)
        labelDialog.layout.addWidget(colorBox,1,1)
        labelDialog.layout.addWidget(applyButton,2,0)
        choice = labelDialog.exec_()
        if choice == QDialog.Accepted:
            textItem = QGraphicsTextItem(textBox.text())
            rectItem = QGraphicsRectItem(textItem.boundingRect())
            rectItem.setBrush(QColor(colorBox.currentText()))
            self.scene.addItem(rectItem)
            self.scene.addItem(textItem)
            labelItem = self.scene.createItemGroup([rectItem,textItem])
            labelItem.setFlag(QGraphicsItem.ItemIsMovable)
            labelItem.setPos(self.lastContextPos)

    def mouseMoveEvent(self,event):
        QGraphicsView.mouseMoveEvent(self,event)
        if event.buttons() == Qt.LeftButton and self.scene.mouseGrabberItem():
            movedItem = self.scene.mouseGrabberItem()
            if movedItem.data(1) == 'karyoItem':
                self.updateConnections()

    def wheelEvent(self,event):
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)


#Custom graphics group class for more convenient handling of cytoband items
class KaryoGraphicItem(QGraphicsItemGroup):

    def __init__(self,bandItems,textItems,nameString):
        super().__init__()
        self.setData(1,'karyoItem')
        #Go through the band items and add them to a dict, with key as band name
        self.bandItemsDict = {}
        for bandItem in bandItems:
            self.bandItemsDict[bandItem.data(0)] = bandItem
            bandItem.setData(1,'karyoItem')
            self.addToGroup(bandItem)
        for textItem in textItems:
            textItem.setData(1,'textItem')
            self.addToGroup(textItem)
        self.nameString = nameString
        self.setFlag(QGraphicsItem.ItemIsMovable)
