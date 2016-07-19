from PySide.QtCore import *
from PySide.QtGui import *
import math

class KaryogramView(QGraphicsView):

    def __init__(self,dataDict,parent):
        self.type = "karyogram"
        self.scene = QGraphicsScene()
        self.dataDict = dataDict
        super().__init__(self.scene,parent)
        self.chromosomes = self.dataDict['chromosomeList']
        self.chromosomeDict = {chromo.name: chromo for chromo in self.chromosomes}
        self.cytoInfo = self.dataDict['cytoTab']
        self.stainNames = parent.stainNames
        self.stainColors = parent.stainColors
        self.numDispChromos = 24
        self.itemsPerRow = 6
        self.cytoGraphicItems = {}
        self.cytoGraphicItemPositions = {}
        self.connectionGraphicItems = []
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.createSettings()
        self.createChInfo()
        self.updateItems()

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

    def updateSettings(self,item):
        if item.row() == 0:
            self.itemsPerRow = item.data(0)

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
        settingsList.setTextElideMode(Qt.ElideNone)
        settingsLayout.addWidget(settingsList,0,0,1,3)
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
        #addVariantButton = QPushButton(QIcon("icons/new.png"),"")
        #addVariantButton.clicked.connect(self.addVariant)
        #addVariantButton.setToolTip("Add custom variant")
        #Button for toggling connections
        connButton = QPushButton(QIcon("icons/connections.png"),"")
        connButton.clicked.connect(self.toggleConnections)
        connButton.setToolTip("Toggle display of connections between variants")
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

    #Creates data model for variants in given chromosome
    def createVariantInfo(self, chromo):
        self.varModel = QStandardItemModel()
        topstring = ['TYPE', 'START', 'END', 'GENE(S)', 'CYTOBAND']
        self.varModel.setHorizontalHeaderLabels(topstring)
        #Adding variant info to a list
        for variant in chromo.variants:
            infoitem = []
            #this is event_type in the variant
            infoitem.append(QStandardItem(variant[4]))
            #this is posA in the variant
            startText = str(variant[1])
            infoitem.append(QStandardItem(startText))
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
            varList.setMinimumSize(500,400)
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
                if not chrB.display or chrA.name == chrB.name or connection[4] is None:
                    continue
                #The cytobands which the connections will go between are gathered
                cbandA = connection[4].split(',')[0]
                cbandB = connection[4].split(',')[1]
                #The x-positions are accessed, the chromosome A x-pos has the chromosome width added to it. This will make the connection start on its right side
                #First check if these cytobands exist, in case of discrepancy in vcf and cytoband files
                if not (cbandA in self.cytoGraphicItems[chrA.name].bandItemsDict and cbandB in self.cytoGraphicItems[chrB.name].bandItemsDict):
                    continue
                xPosA = self.cytoGraphicItems[chrA.name].bandItemsDict[cbandA].boundingRect().right()
                xPosB = self.cytoGraphicItems[chrB.name].bandItemsDict[cbandB].boundingRect().left()
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
                connectionPath.lineTo(pointB)
                connectionItem = QGraphicsPathItem(connectionPath)
                #Set the color of the line to chrB's stain color (makes it difficult to distinguish though..)
                pen = QPen()
                #pen.setBrush(cBandBItem.brush())
                pen.setBrush(Qt.darkYellow)
                connectionItem.setPen(pen)
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
                        #If first acen, round on bottom
                        elif cyto[4] == 'acen' and firstAcen:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                            firstAcen = False
                        #If second acen, round on top
                        elif cyto[4] == 'acen':
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setBottom(rect.bottom() + rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                        #If last item, round on bottom (i.e. last index in last chr or new chr next on next index)
                        elif self.cytoInfo.index(cyto) == len(self.cytoInfo)-1:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                        elif self.cytoInfo[self.cytoInfo.index(cyto)+1][0] != chromo.name:
                            rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                            rect.setTop(rect.top() - rect.height())
                            roundPath = QPainterPath(rect.center())
                            roundPath.arcTo(rect,0,-180)
                            roundPath.closeSubpath()
                            bandRectItem = QGraphicsPathItem(roundPath)
                        else:
                            #Create a rect item with corresponding stain color, tooltip, set data to band name for later use
                            bandRectItem = QGraphicsRectItem(bandXPos,bandYPos,bandWidth,bandHeight)
                        bandRectItem.setBrush(self.stainColors[cyto[4]])
                        bandRectItem.setToolTip(cyto[3] + ": " + str(totalCytoBP) + " bp")
                        bandRectItem.setData(0,cyto[3])
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
                cytoItem.moveBy(0,displaceY)
                self.cytoGraphicItems[chromo.name] = cytoItem
                currentXPosition += xIncrement
                self.scene.addItem(cytoItem)
                counter += 1
                if counter%self.itemsPerRow == 0:
                    currentXPosition = 0
                    displaceY += longestItemInRow + 30
                    longestItemInRow = 0

    def updateItems(self):
        #Should use clear instead of individually removing..
        #Save any old positions of items in case they have been moved by the user
        for graphicItem in self.cytoGraphicItems.values():
            self.cytoGraphicItemPositions[graphicItem.nameString] = graphicItem.pos()
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
        #Move back the items to their old positions
        for graphicItem in self.cytoGraphicItems.values():
            if graphicItem.nameString in self.cytoGraphicItemPositions and self.chromosomeDict[graphicItem.nameString].display:
                graphicItem.setPos(self.cytoGraphicItemPositions[graphicItem.nameString])
        self.drawConnections()
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
            textItem.setData(1,'karyoItem')
            self.addToGroup(textItem)
        self.nameString = nameString
        self.setFlag(QGraphicsItem.ItemIsMovable)
