from PySide.QtCore import *
from PySide.QtGui import *

class KaryogramView(QGraphicsView):

    def __init__(self,dataDict):
        self.scene = QGraphicsScene()
        self.dataDict = dataDict
        super().__init__(self.scene)
        self.chromosomes = self.dataDict['chromosomeList']
        self.cytoInfo = self.dataDict['cytoTab']
        self.numDispChromos = 24
        self.cytoGraphicItems = {}
        self.connectionGraphicItems = []
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(800,600)
        self.show()
        #create a list of stain names, to be able to set their colors later..
        self.stainNames = ['acen','gneg','gpos100','gpos25','gpos50','gpos75','gvar','stalk']
        self.colors = {'acen':Qt.darkRed, 'gneg':Qt.white,'gpos100':Qt.black,'gpos25':Qt.lightGray,'gpos50':Qt.gray,
        'gpos75':Qt.darkGray,'gvar':Qt.white,'stalk':Qt.red}
        self.createSettings()
        self.updateItems()
        self.createChInfo()

    def returnActiveDataset(self):
        return self.dataDict

    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = []
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        self.settingsModel.itemChanged.connect(self.updateSettings)
        self.colorModel = QStandardItemModel()
        stainItems = []
        colorItems = []
        for stainName in self.stainNames:
            stainItem = QStandardItem(stainName)
            stainItem.setEditable(False)
            stainItem.setSelectable(False)
            stainItems.append(stainItem)
            colorItem = QStandardItem()
            colorItem.setBackground(self.colors[stainName])
            colorItem.setEditable(False)
            colorItem.setSelectable(False)
            colorItems.append(colorItem)
        self.colorModel.appendColumn(stainItems)
        self.colorModel.appendColumn(colorItems)

    def updateSettings(self,item):
        pass

    def viewSettings(self):
        self.settingsList = QTableView()
        self.settingsList.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.settingsList.setShowGrid(False)
        self.settingsList.horizontalHeader().hide()
        self.settingsList.verticalHeader().hide()
        self.settingsList.setModel(self.settingsModel)
        self.settingsList.setTextElideMode(Qt.ElideNone)

        self.colorList = QTableView()
        self.colorList.setShowGrid(False)
        self.colorList.horizontalHeader().hide()
        self.colorList.verticalHeader().hide()
        self.colorList.setModel(self.colorModel)
        self.colorList.doubleClicked.connect(self.pickColor)

        self.settingsDia = QDialog(self)
        self.settingsDia.setWindowTitle("Settings")
        applyButton = QPushButton('Apply', self.settingsDia)
        applyButton.clicked.connect(self.settingsDia.accept)
        self.settingsDia.layout = QGridLayout(self.settingsDia)
        self.settingsDia.layout.addWidget(self.settingsList,0,0,1,2)
        self.settingsDia.layout.addWidget(self.colorList,0,2,1,2)
        self.settingsDia.layout.addWidget(applyButton,1,0,1,1)
        self.settingsDia.show()

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
            if (self.chromosomes.index(chromo) < 24):
                dispCheckItem.setCheckState(Qt.Checked)
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

    #Creates data model for variants in given chromosome
    def createVariantInfo(self, chromo):
        self.varModel = QStandardItemModel()
        topstring = ['START', 'ALT', 'END', 'GENE(S)', 'CYTOBAND']
        self.varModel.setHorizontalHeaderLabels(topstring)
        #Adding variant info to a list (except the info field, which has index=2 in the variant list)
        for variant in chromo.variants:
            infoitem = []
            infoitem.append(QStandardItem(variant[0]))
            infoitem.append(QStandardItem(variant[1]))
            infoitem.append(QStandardItem(variant[3]))
            infoitem.append(QStandardItem(variant[4]))
            infoitem.append(QStandardItem(variant[5]))
            self.varModel.appendRow(infoitem)

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
            varList.setMinimumSize(440,400)
            varList.verticalHeader().hide()
            varList.setEditTriggers(QAbstractItemView.NoEditTriggers)
            varList.setModel(self.varModel)
            varList.resizeColumnToContents(1)
            viewVarDia.layout = QGridLayout(viewVarDia)
            viewVarDia.layout.addWidget(varList,0,0)
            viewVarDia.show()

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
        #Loops through the full list of chromosomes and checks if the connections should be displayed or not
        for chrA in self.chromosomes:
            if not (chrA.display_connections and chrA.display):
                continue
            #only create the connection list if it has not been initialized earlier
            if not chrA.connections:
                chrA.createConnections()
            for connection in chrA.connections:
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
                if not chrB.display:
                    continue
                #The cytobands which the connections will go between are gathered
                cbandA = connection[4].split(',')[0]
                cbandB = connection[4].split(',')[1]
                #The x-positions are accessed, the chromosome A x-pos has the chromosome width added to it. This will make the connection start on its right side
                xPosA = self.cytoGraphicItems[chrA.name].boundingRect().x() + self.cytoGraphicItems[chrA.name].boundingRect().width()
                xPosB = self.cytoGraphicItems[chrB.name].boundingRect().x()
                #Find the y position of the actual cytoband in each chromosome, by accessing the chromosome band dicts
                cBandAItem = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA]
                cBandBItem = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB]
                yPosA = cBandAItem.rect().top() + cBandAItem.rect().height() / 2
                yPosB = cBandBItem.rect().top() + cBandBItem.rect().height() / 2
                #If the item has been moved, x and y are how much the item has been moved by; update position with these
                xPosA += self.cytoGraphicItems[chrA.name].x()
                xPosB += self.cytoGraphicItems[chrB.name].x()
                yPosA += self.cytoGraphicItems[chrA.name].y()
                yPosB += self.cytoGraphicItems[chrB.name].y()
                pointA = QPoint(xPosA, yPosA)
                pointB = QPoint(xPosB, yPosB)
                connectionPath = QPainterPath()
                connectionPath.moveTo(pointA)
                connectionPath.lineTo(pointB)
                connectionItem = QGraphicsPathItem(connectionPath)
                #Set the color of the line to chrB's stain color (makes it difficult to distinguish though..)
                pen = QPen()
                #pen.setBrush(cBandBItem.brush())
                pen.setBrush(Qt.darkYellow)
                connectionItem.setPen(pen)
                self.scene.addItem(connectionItem)
                self.connectionGraphicItems.append(connectionItem)

    def pickColor(self,modelIndex):
        if modelIndex.column() == 1:
            selectedRow = modelIndex.row()
            stainItem = self.colorModel.item(selectedRow,0)
            colorItem = self.colorModel.item(selectedRow,1)
            chosenColor = QColorDialog.getColor(colorItem.background().color())
            self.colors[stainItem.text()] = chosenColor
            colorItem.setBackground(chosenColor)

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
            currentXPosition = containerRect.left()
            xIncrement = containerRect.width() / self.numDispChromos
            self.chromoWidth = containerRect.width() / 48

            #Create the graphic items for each chromosome if they are set to be displayed
            for chromo in self.chromosomes:
                if not chromo.display or "GL" in chromo.name or "MT" in chromo.name:
                    continue
                chromoHeight = (int(chromo.end)/maxBp)*(containerRect.height())
                bandItems = []
                textItems = []
                placeLeft = True
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
                        #Create a rect item with corresponding stain color, tooltip, set data to band name for later use
                        bandRectItem = QGraphicsRectItem(bandXPos,bandYPos,bandWidth,bandHeight)
                        bandRectItem.setBrush(self.colors[cyto[4]])
                        bandRectItem.setToolTip(cyto[3] + ": " + str(totalCytoBP) + " bp")
                        bandRectItem.setData(0,cyto[3])
                        self.scene.addItem(bandRectItem)
                        bandItems.append(bandRectItem)
                        if chromo.display_cytoBandNames:
                            bandNameItem = QGraphicsTextItem(cyto[3])
                            nameXPosition = bandRectItem.rect().left()-bandRectItem.boundingRect().width() if placeLeft else bandRectItem.rect().right()
                            bandNameItem.setPos(nameXPosition,bandRectItem.rect().top())
                            self.scene.addItem(bandNameItem)
                            textItems.append(bandNameItem)
                            placeLeft = not placeLeft
                chromoNameItem = QGraphicsTextItem(chromo.name)
                chromoNameItem.setPos(currentXPosition,chromoHeight)
                chromoNameItem.setScale(0.8)
                self.scene.addItem(chromoNameItem)
                textItems.append(chromoNameItem)
                #Create a custom graphic item group from created items, enter in dict
                cytoItem = KaryoGraphicItem(bandItems,textItems,chromo.name)
                self.cytoGraphicItems[chromo.name] = cytoItem
                currentXPosition += xIncrement
                self.scene.addItem(cytoItem)

    def updateItems(self):
        self.scene.clear()
        self.createChromosomeItems()
        self.drawConnections()
        self.update()

    def updateConnections(self):
        for item in self.connectionGraphicItems:
            self.scene.removeItem(item)
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
            textItem.setData(1,'karyoItem')
            self.addToGroup(textItem)
        self.nameString = nameString
        self.setFlag(QGraphicsItem.ItemIsMovable)
