from PySide.QtCore import *
from PySide.QtGui import *
import math
import common

class CoverageView(QGraphicsView):

    def __init__(self,dataDict, parent):
        self.scene = QGraphicsScene()
        self.type = "coverage"
        super().__init__(self.scene, parent)
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.cytoInfo = self.dataDict['cytoTab']
        self.stainNames = parent.stainNames
        self.stainColors = parent.stainColors
        self.bpWindow = 100
        self.minCoverage = 0
        self.maxCoverage = 5
        self.dupLimit = 2.25
        self.delLimit = 1.75
        self.plotType = 0
        self.createSettings()
        self.coverageNormLog = self.dataDict['coverageNormLog']
        self.coverageNorm = self.dataDict['coverageNorm']
        self.createChInfo()
        self.setRenderHints(QPainter.Antialiasing)
        #self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def startScene(self):
        self.defineRectangles()
        self.activeChromo = 0
        #Dict for position marker values for chromosomes
        self.chromoSelectorRects = {chromo.name: QRectF(self.overviewArea) for chromo in self.chromosomes}
        self.selectorItem = AreaSelectorItem(self.overviewArea,self.overviewArea,self)
        self.setActiveChromosome(0)

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
        verticalHeaders = ["bpWindow", 'dupLimit', 'delLimit', "minCoverage", "maxCoverage"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        bpWinText = QStandardItem("BP Resolution (kb)")
        bpWinText.setEditable(False)
        bpWinText.setToolTip("Show each data point as the average of this value (x1000 bp)")
        bpWinData = QStandardItem()
        bpWinData.setData(self.bpWindow,0)
        bpWinData.setEditable(True)
        dupLimitText = QStandardItem("Duplication limit")
        dupLimitText.setEditable(False)
        dupLimitText.setToolTip("Upper bound for marking a data point as a duplication")
        dupLimitData = QStandardItem()
        dupLimitData.setData(self.dupLimit,0)
        dupLimitData.setEditable(True)
        delLimitText = QStandardItem("Deletion limit")
        delLimitText.setEditable(False)
        delLimitText.setToolTip("Lower bound for marking a data point as a deletion")
        delLimitData = QStandardItem()
        delLimitData.setData(self.delLimit,0)
        delLimitData.setEditable(True)
        minCovLimitText = QStandardItem("Min.coverage value (%)")
        minCovLimitText.setEditable(False)
        minCovLimitText.setToolTip("Lower bound for coverage values,\nin percentage of average coverage value of genome.")
        minCovLimitData = QStandardItem()
        minCovLimitData.setData(self.minCoverage*100,0)
        minCovLimitData.setEditable(True)
        maxCovLimitText = QStandardItem("Max. coverage value (%)")
        maxCovLimitText.setEditable(False)
        maxCovLimitText.setToolTip("Upper bound for coverage values,\nin percentage of average coverage value of genome.")
        maxCovLimitData = QStandardItem()
        maxCovLimitData.setData(self.maxCoverage*100,0)
        maxCovLimitData.setEditable(True)
        self.settingsModel.setItem(0,0,bpWinText)
        self.settingsModel.setItem(0,1,bpWinData)
        self.settingsModel.setItem(1,0,dupLimitText)
        self.settingsModel.setItem(1,1,dupLimitData)
        self.settingsModel.setItem(2,0,delLimitText)
        self.settingsModel.setItem(2,1,delLimitData)
        self.settingsModel.setItem(3,0,minCovLimitText)
        self.settingsModel.setItem(3,1,minCovLimitData)
        self.settingsModel.setItem(4,0,maxCovLimitText)
        self.settingsModel.setItem(4,1,maxCovLimitData)

    def updateSettings(self):
        #Go through every row in the settings model and update accordingly
        for row in range(self.settingsModel.rowCount()):
            item = self.settingsModel.item(row,1)
            if row == 0:
                self.bpWindow = item.data(0)
            if row == 1:
                self.dupLimit = item.data(0)
            if row == 2:
                self.delLimit = item.data(0)
            if row == 3:
                self.minCoverage = item.data(0)/100
            if row == 4:
                self.maxCoverage = item.data(0)/100
        self.updatePlot()

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

    #Creates data model for info window
    def createChInfo(self):
        self.chModel = QStandardItemModel()
        topstring = ["Name","Length","No. of variants"]
        self.chModel.setHorizontalHeaderLabels(topstring)
        for chromo in self.chromosomes:
            infostring = [chromo.name,chromo.end,str(len(chromo.variants))]
            infoItems = [QStandardItem(string) for string in infostring]
            #only keep chromosomes up to MT (no. 24)
            if (self.chromosomes.index(chromo) <= 24):
                self.chModel.appendRow(infoItems)

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
        #Button for viewing selected chromosome variants
        viewVarButton = QPushButton('View variants', self.chDia)
        viewVarButton.clicked.connect(self.viewVariants)
        #Button for adding variants
        addVariantButton = QPushButton('Add variant', self.chDia)
        addVariantButton.clicked.connect(self.addVariant)
        self.chDia.layout = QGridLayout(self.chDia)
        self.chDia.layout.addWidget(self.chList,0,0,1,4)
        self.chDia.layout.addWidget(viewVarButton,1,0,1,1)
        self.chDia.layout.addWidget(addVariantButton,1,1,1,1)
        self.chDia.setMinimumSize(450,400)
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
        #Button for viewing selected chromosome variants
        viewVarButton = QPushButton(QIcon("icons/viewList.png"),"")
        viewVarButton.clicked.connect(self.viewVariants)
        viewVarButton.setToolTip("View variants in chromosome")
        #Button for adding variants
        addVariantButton = QPushButton(QIcon("icons/new.png"),"")
        addVariantButton.clicked.connect(self.addVariant)
        addVariantButton.setToolTip("Add custom variant")
        chromoInfoLayout = QGridLayout()
        chromoInfoLayout.addWidget(self.chList,0,0,1,2)
        chromoInfoLayout.addWidget(viewVarButton,1,0,1,1)
        chromoInfoLayout.addWidget(addVariantButton,1,1,1,1)
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
            viewVarDia.show()

    def createVariantWidget(self,row):
        chromo = self.chromosomes[row]
        varWidget = common.createVariantWidget(chromo)
        return varWidget

    def addVariant(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            common.addVariant(chromo,self.chromosomes)

    def createOverview(self,chromo):
        bandHeight = self.overviewArea.height() / 2
        chromoWidth = self.overviewArea.width()
        bandYPos = self.overviewArea.top() + bandHeight/2
        firstAcen = True
        #Find each cytoband for this chromosome, and create band items using this data
        for cyto in self.cytoInfo:
            if cyto[0] == chromo.name:
                totalCytoBP = int(cyto[2]) - int(cyto[1])
                bandXPos = self.overviewArea.left() + (int(cyto[1]) / int(chromo.end)) * chromoWidth
                bandWidth = (totalCytoBP / int(chromo.end)) * chromoWidth
                #If first item, round on left
                if int(cyto[1]) is 0:
                    rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                    rect.setRight(rect.right() + rect.width())
                    roundPath = QPainterPath(rect.center())
                    roundPath.arcTo(rect,-90,-180)
                    roundPath.closeSubpath()
                    bandRectItem = QGraphicsPathItem(roundPath)
                #If first acen, round on right
                elif cyto[4] == 'acen' and firstAcen:
                    rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                    rect.setLeft(rect.left() - rect.width())
                    roundPath = QPainterPath(rect.center())
                    roundPath.arcTo(rect,-90,180)
                    roundPath.closeSubpath()
                    bandRectItem = QGraphicsPathItem(roundPath)
                    firstAcen = False
                #If second acen, round on left
                elif cyto[4] == 'acen':
                    rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                    rect.setRight(rect.right() + rect.width())
                    roundPath = QPainterPath(rect.center())
                    roundPath.arcTo(rect,-90,-180)
                    roundPath.closeSubpath()
                    bandRectItem = QGraphicsPathItem(roundPath)
                #If last item, round on right (i.e. last index in last chr or new chr next on next index)
                elif self.cytoInfo.index(cyto) == len(self.cytoInfo)-1:
                    rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                    rect.setLeft(rect.left() - rect.width())
                    roundPath = QPainterPath(rect.center())
                    roundPath.arcTo(rect,-90,180)
                    roundPath.closeSubpath()
                    bandRectItem = QGraphicsPathItem(roundPath)
                elif self.cytoInfo[self.cytoInfo.index(cyto)+1][0] != chromo.name:
                    rect = QRectF(bandXPos,bandYPos,bandWidth,bandHeight)
                    rect.setLeft(rect.left() - rect.width())
                    roundPath = QPainterPath(rect.center())
                    roundPath.arcTo(rect,-90,180)
                    roundPath.closeSubpath()
                    bandRectItem = QGraphicsPathItem(roundPath)
                else:
                    #Create a rect item with corresponding stain color, tooltip, set data to band name for later use
                    bandRectItem = QGraphicsRectItem(bandXPos,bandYPos,bandWidth,bandHeight)
                bandRectItem.setBrush(self.stainColors[cyto[4]])
                bandRectItem.setToolTip(cyto[3] + ": " + str(totalCytoBP) + " bp")
                self.scene.addItem(bandRectItem)
                #Add the chromosome name to the left of the area
                nameItem = QGraphicsTextItem(chromo.name)
                nameItem.setPos( QPointF(self.overviewArea.left()-20, self.overviewArea.top()+5) )
                font = QFont()
                font.setBold(True)
                nameItem.setFont(font)
                self.scene.addItem(nameItem)

    def createPlot(self,chromo,ptype,limits):
        coverageData = []
        normValue = self.coverageNorm
        minCov = normValue*self.minCoverage
        maxCov = normValue*self.maxCoverage
        #Create an average values for coverage, depending into user defined window
        coverageChunks = [chromo.coverage[i:i+(self.bpWindow)] for i in range(0,len(chromo.coverage),(self.bpWindow))]
        for chunk in coverageChunks:
            val = sum(chunk) / len(chunk)
            if val > maxCov:
                val = maxCov
            if val < minCov:
                val = minCov
            #Presuming we're dealing with a diploid genome, the norm should represent 2 copies, so multiply by 2
            coverageData.append(2*val/normValue)
        startIndex = round(limits[0] / int(chromo.end) * len(coverageData))
        endIndex = round((limits[0] + limits[1]) / int(chromo.end) * len(coverageData))
        coverageData = coverageData[startIndex:endIndex]

        #Draw the y axis
        leftLine = QLineF(self.graphArea.bottomLeft(),self.graphArea.topLeft())
        rightLine = QLineF(self.graphArea.bottomRight(),self.graphArea.topRight())
        self.scene.addLine(leftLine)
        self.scene.addLine(rightLine)
        #Set increments for axes
        yAxisIncrement = self.graphArea.height() / (self.maxCoverage*2)
        xAxisIncrement = self.graphArea.width() / 10

        #Draw markings for the limits
        dupLine = QLineF( QPointF(self.graphArea.left(),self.graphArea.bottom()-self.dupLimit*yAxisIncrement),
                          QPointF(self.graphArea.right(),self.graphArea.bottom()-self.dupLimit*yAxisIncrement) )
        delLine = QLineF( QPointF(self.graphArea.left(),self.graphArea.bottom()-self.delLimit*yAxisIncrement),
                          QPointF(self.graphArea.right(),self.graphArea.bottom()-self.delLimit*yAxisIncrement) )
        dupLineItem = QGraphicsLineItem(dupLine)
        dupLineItem.setPen(QPen(Qt.darkRed))
        dupLineItem.setOpacity(0.6)
        delLineItem = QGraphicsLineItem(delLine)
        delLineItem.setPen(QPen(Qt.darkRed))
        delLineItem.setOpacity(0.6)
        self.scene.addItem(dupLineItem)
        self.scene.addItem(delLineItem)

        #Create y ticks (as times average genome coverage), also height markers
        markerPen = QPen()
        markerPen.setStyle(Qt.DashLine)
        for i in range(0,int(2*self.maxCoverage)+1):
            yTickPath = QPainterPath()
            point = QPointF(self.graphArea.left(), self.graphArea.bottom() - (i)*yAxisIncrement)
            yTickPath.moveTo(point)
            line = QLineF()
            line.setP1(yTickPath.currentPosition())
            line.setP2(yTickPath.currentPosition() + QPointF(self.graphArea.width(),0))
            lineItem = QGraphicsLineItem(line)
            if not(i == 0 or i == self.maxCoverage*2):
                lineItem.setPen(markerPen)
                lineItem.setOpacity(0.5)
            self.scene.addItem(lineItem)
            yTickLabelItem = QGraphicsTextItem(str(i))
            yTickLabelItem.setPos(yTickPath.currentPosition() +  QPointF(-20, -10))
            self.scene.addItem(yTickLabelItem)

        #Create x ticks to show chromosome position
        bpIncrement = float(chromo.end)/10
        for i in range(1,10):
            point = QPointF(self.graphArea.left() + (i)*xAxisIncrement, self.graphArea.bottom())
            line = QLineF()
            line.setP1(point)
            line.setP2(point + QPointF(0,15))
            lineItem = QGraphicsLineItem(line)
            self.scene.addItem(lineItem)
            bpPosition = i*bpIncrement
            xTickLabelItem = QGraphicsTextItem(str(round(bpPosition)))
            xTickLabelItem.setPos(point +  QPointF(0, 0))
            self.scene.addItem(xTickLabelItem)

        #Place the actual data values on the graph
        if ptype == 0:

            for index in range(len(coverageData)):
                pointRect = QRectF( self.graphArea.left() + (index/len(coverageData))*self.graphArea.width() -2.5,
                self.graphArea.bottom() - coverageData[index]*yAxisIncrement -2.5, 5, 5  )
                pointItem = QGraphicsEllipseItem(pointRect)
                if coverageData[index] < self.delLimit:
                    pointItem.setBrush(QBrush(Qt.red))
                elif coverageData[index] > self.dupLimit:
                    pointItem.setBrush(QBrush(Qt.green))
                else:
                    pointItem.setBrush(QBrush(Qt.black))
                self.scene.addItem(pointItem)

        elif ptype == 1:

            #Create a gradient for coloring individual line items
            offsetPoint = QPointF(self.graphArea.width()/2, 0)
            linearGradient = QLinearGradient( QPointF(self.graphArea.bottomLeft()) + offsetPoint,
                                              QPointF(self.graphArea.topLeft())  + offsetPoint )
            linearGradient.setColorAt(1, Qt.green)
            linearGradient.setColorAt(self.dupLimit/10, Qt.green)
            linearGradient.setColorAt((self.dupLimit-0.005)/10, Qt.black)
            linearGradient.setColorAt((self.delLimit+0.005)/10, Qt.black)
            linearGradient.setColorAt(self.delLimit/10, Qt.red)
            linearGradient.setColorAt(0, Qt.red)
            colorBrush = QBrush(linearGradient)
            colorPen = QPen()
            colorPen.setBrush(colorBrush)

            for index in range(len(coverageData)-1):
                startPoint = QPointF( self.graphArea.left() + (index/len(coverageData))*self.graphArea.width(),
                                      self.graphArea.bottom() - coverageData[index]*yAxisIncrement)
                endPoint = QPointF( self.graphArea.left() + ((index+1)/len(coverageData))*self.graphArea.width(),
                                      self.graphArea.bottom() - coverageData[index+1]*yAxisIncrement)
                line = QLineF(startPoint, endPoint)
                lineItem = QGraphicsLineItem(line)
                lineItem.setPen(colorPen)
                self.scene.addItem(lineItem)

    def updatePlot(self):
        self.defineRectangles()
        chromo = self.chromosomes[self.activeChromo]
        mRect = self.selectorItem.returnMarkerRect()
        self.scene.clear()
        self.createOverview(chromo)
        self.createPlot(chromo,self.plotType,self.limits)
        self.selectorItem = AreaSelectorItem(mRect,self.overviewArea,self)
        self.scene.addItem(self.selectorItem)
        self.setSceneRect(self.viewArea)
        self.update()

    def updateLimits(self):
        chromo = self.chromosomes[self.activeChromo]
        #Find the marked region by looking at marker edges
        markRect = self.selectorItem.returnMarkerRect()
        regionStart = round((markRect.left() - self.overviewArea.left()) / self.overviewArea.width() * int(chromo.end))
        if regionStart < 0:
            regionStart = 0
        regionLength = round(markRect.width() / self.overviewArea.width() * int(chromo.end))
        if regionLength > int(chromo.end):
            regionLength = int(chromo.end)
        limits = [regionStart, regionLength]
        self.limits = limits
        self.updatePlot()

    def defineRectangles(self):
        size = self.size()
        self.viewArea = QRect(QPoint(20,20), QPoint(size.width()-20,size.height()-20))
        self.overviewArea = QRect(QPoint(50,50), QPoint(size.width()-50,80))
        self.graphArea = QRect(QPoint(50,120), QPoint(size.width()-50,size.height()-50))

    def changePlotType(self,index):
        self.plotType = index
        self.updatePlot()

    def setActiveChromosome(self,chromoNumber):
        #Before switching, save current marker for this chr
        self.chromoSelectorRects[self.chromosomes[self.activeChromo].name] = self.selectorItem.returnMarkerRect()
        self.activeChromo = chromoNumber
        self.limits = [0,int(self.chromosomes[self.activeChromo].end)]
        mRect = self.chromoSelectorRects[self.chromosomes[self.activeChromo].name]
        self.selectorItem = AreaSelectorItem(mRect,self.overviewArea,self)
        self.updateLimits()
        self.updatePlot()

    def wheelEvent(self,event):
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)

class AreaSelectorItem(QGraphicsItemGroup):

    def __init__(self,markRect,fullRect,parent):
        super().__init__()
        self.parent = parent
        self.originalRect = QRectF(fullRect)
        self.setAcceptHoverEvents(True)
        pen = QPen()
        pen.setStyle(Qt.DashLine)
        pen.setBrush(Qt.red)
        self.markRect = QGraphicsRectItem(markRect)
        self.markRect.setPen(pen)
        self.addToGroup(self.markRect)
        #Add some invisible margin so we can get mouse event margin outside edges
        leftRect = QRectF(self.markRect.rect().topLeft(), self.markRect.rect().bottomLeft())
        leftRect.setRight(leftRect.right() + 5)
        leftRect.setLeft(leftRect.left() - 5)
        self.leftDragItem = QGraphicsRectItem(leftRect)
        self.leftDragItem.setOpacity(0)
        self.addToGroup(self.leftDragItem)
        rightRect = QRectF(self.markRect.rect().topRight(), self.markRect.rect().bottomRight())
        rightRect.setLeft(rightRect.right() - 5)
        rightRect.setRight(rightRect.right() + 5)
        self.rightDragItem = QGraphicsRectItem(rightRect)
        self.rightDragItem.setOpacity(0)
        self.addToGroup(self.rightDragItem)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.draggingLeft = False
        self.draggingRight = False
        self.movingRect = False

    def returnMarkerRect(self):
        return self.markRect.rect()

    def hoverMoveEvent(self,event):
        if ( self.leftDragItem.contains(event.pos()) or self.rightDragItem.contains(event.pos()) ):
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.OpenHandCursor)
        QGraphicsItem.hoverMoveEvent(self,event)

    def mousePressEvent(self,event):
        if self.cursor().shape() == Qt.OpenHandCursor:
            self.setCursor(Qt.ClosedHandCursor)
            self.movingRect = True
            self.lastXPos = event.pos().x()
        if self.leftDragItem.contains(event.pos()):
            self.draggingLeft = True
        elif self.rightDragItem.contains(event.pos()):
            self.draggingRight = True

    def mouseMoveEvent(self,event):
        xPos = event.pos().x()
        #Should not be able to be dragged outside of full size boundary,
        #or too close to selection opposite edge
        if ( self.draggingLeft and xPos < (self.markRect.rect().right()-10) ):
            if xPos < self.originalRect.left():
                xPos = self.originalRect.left()
            newRect = self.markRect.rect()
            newRect.setLeft(xPos)
            self.markRect.setRect(newRect)
        elif (self.draggingRight and xPos > (self.markRect.rect().left()+10) ):
            if xPos > self.originalRect.right():
                xPos = self.originalRect.right()
            newRect = self.markRect.rect()
            newRect.setRight(xPos)
            self.markRect.setRect(newRect)
        elif self.movingRect:
            newRect = self.markRect.rect()
            if self.markRect.rect().left() < self.originalRect.left():
                translateBy = 0
                newRect.moveLeft(self.originalRect.left())
            elif self.markRect.rect().right() > self.originalRect.right():
                translateBy = 0
                newRect.moveRight(self.originalRect.right())
            else:
                translateBy = xPos - self.lastXPos
            newRect.translate(translateBy,0)
            self.markRect.setRect(newRect)
            self.lastXPos = xPos

    def mouseReleaseEvent(self,event):
        self.pressRelease = event.pos()
        self.setCursor(Qt.OpenHandCursor)
        self.draggingLeft = False
        self.draggingRight = False
        self.movingRect = False
        #Make sure marker is not outside of limits
        newRect = self.markRect.rect()
        if self.markRect.rect().left() < self.originalRect.left():
            newRect.moveLeft(self.originalRect.left())
        elif self.markRect.rect().right() > self.originalRect.right():
            newRect.moveRight(self.originalRect.right())
        self.markRect.setRect(newRect)
        #Place drag margins on edges
        newRect = self.leftDragItem.rect()
        newRect.moveLeft(self.markRect.rect().left()-newRect.width()/2)
        self.leftDragItem.setRect(newRect)
        newRect = self.rightDragItem.rect()
        newRect.moveRight(self.markRect.rect().right()+newRect.width()/2)
        self.rightDragItem.setRect(newRect)
        #Update the plot on release
        self.parent.updateLimits()
