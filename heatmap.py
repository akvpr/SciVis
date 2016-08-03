import common
from PySide.QtCore import *
from PySide.QtGui import *
import numpy as np
import math

class HeatmapView(QGraphicsView):

    def __init__(self,dataDict, parent):

        self.scene = QGraphicsScene()
        self.type = "heatmap"
        super().__init__(self.scene, parent)
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.variantNames = {"BND":"Break end", "DEL":"Deletion", "DUP":"Duplication", "IDUP":"Interspersed duplication", "INS":"Insertion", "INV":"Inversion", "TDUP":"Tandem duplication", "TLOC":"Translocation"}
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.bpWindow = 50
        self.minCoverage = 0
        self.maxCoverage = 5
        self.stainColors = parent.stainColors
        self.activeIndex = 0
        self.color = QColor(self.stainColors['heatmapColor'])
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.hide()
        self.origin = QPoint(0,0)
        self.binSize = 10000
        self.chromoA = self.chromosomes[0]
        self.chromoB = self.chromosomes[0]
        self.mapping = "DEL"
        self.createSettings()
        self.createChInfo()
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.clearScene()
        self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        self.scale(0.7, 0.7)

    def returnActiveDataset(self):
        return self.dataDict

    def changeMappingType(self, mapping):
        self.variantNames = {"Break end":"BND", "Deletion":"DEL", "Duplication":"DUP", "Interspersed duplication":"IDUP", "Insertion":"INS", "Inversion":"INV", "Tandem duplication":"TDUP", "Translocation":"TLOC"}
        self.mapping = self.variantNames[mapping]
        if self.chromoA is self.chromoB and (self.mapping == "DEL" or self.mapping == "BND" or self.mapping == "DUP" or self.mapping == "IDUP" or self.mapping == "INS" or self.mapping == "INV" or self.mapping == "TDUP"):
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        elif self.chromoA is not self.chromoB and self.mapping == "TLOC":
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        
    def changeBinsize(self, binSize):
        self.binSize = int(binSize)
        self.clearScene()
        self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
    
    def changeChromoA(self, chromoA):
        self.chromoA = self.chromosomes[chromoA]
        if self.chromosomes[chromoA] is self.chromoB and (self.mapping == "DEL" or self.mapping == "BND" or self.mapping == "DUP" or self.mapping == "IDUP" or self.mapping == "INS" or self.mapping == "INV" or self.mapping == "TDUP"):
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        elif self.chromosomes[chromoA] is not self.chromoB and self.mapping == "TLOC":
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        
    def changeChromoB(self, chromoB):
        self.chromoB = self.chromosomes[chromoB]
        if self.chromosomes[chromoB] is self.chromoA and (self.mapping == "DEL" or self.mapping == "BND" or self.mapping == "DUP" or self.mapping == "IDUP" or self.mapping == "INS" or self.mapping == "INV" or self.mapping == "TDUP"):
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
        elif self.chromosomes[chromoB] is not self.chromoA and self.mapping == "TLOC":
            self.clearScene()
            self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping)
            
    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = ["minCoverage", "maxCoverage"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        self.settingsModel.itemChanged.connect(self.updateSettings)

    def closeOpenWindows(self):
        try:
            self.chDia.close()
        except:
            pass
        
    def updateSettings(self):
        #Go through every row in the settings model and update accordingly
        self.color = QColor(self.stainColors['heatmapColor'])
        self.clearScene()
        self.updateHeatmap(self.activeIndex)

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
        varWidget.layout().itemAtPosition(2,0).widget().clicked.connect(lambda: self.createHeatmap(self.chromoA, self.chromoB, self.binSize, self.mapping))
        return varWidget

    def addVariant(self):
        selectedIndexes = self.chList.selectedIndexes()
        selectedRows = [index.row() for index in selectedIndexes]
        selectedRows = set(selectedRows)
        for row in selectedRows:
            chromo = self.chromosomes[row]
            common.addVariant(chromo,self.chromosomes)

    def createHeatmap(self, chromoA, chromoB, binSize, mapping):
        self.clearScene()
        self.variantNames = {"BND":"Break end", "DEL":"Deletion", "DUP":"Duplication", "IDUP":"Interspersed duplication", "INS":"Insertion", "INV":"Inversion", "TDUP":"Tandem duplication", "TLOC":"Translocation"}
        binSize = binSize*1000
        self.matrices = []
        self.activeIndex = 0
        zoomLevel = 0
        zoomFactor = 10
        xAxis = int(int(chromoA.end)/binSize)+1
        yAxis = int(int(chromoB.end)/binSize)+1
        A = self.constructMatrix(chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, 0, 0, zoomLevel)
        matrixInfo = [chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, 0, 0, zoomLevel]
        self.matrices.append([A, matrixInfo])
        self.updateHeatmap(self.activeIndex)

    def updateHeatmap(self, activeIndex):
        self.clearScene()
        (chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart, zoomLevel) = self.matrices[activeIndex][1]
        zoomFactor = math.pow(zoomFactor, -zoomLevel)
        A = self.matrices[activeIndex][0]
        if mapping == "TLOC":
            startString = "Position"
            endString = "Position"
        else:
            startString = "Start position"
            endString = "End position"
        size = self.size()

        containerRect = QRect(QPoint(50,50), QPoint(size.width()-50,size.height()-50))
        #create and add axes to scene
        xAxisPath = QPainterPath()
        xAxisPath.moveTo(50,containerRect.height()-50)
        xAxisPath.lineTo(containerRect.width()-250, containerRect.height()-50)
        xAxisItem = QGraphicsPathItem(xAxisPath)
        yAxisPath = QPainterPath()
        yAxisPath.moveTo(50,containerRect.height()-50)
        yAxisPath.lineTo(50, 50)
        yAxisItem = QGraphicsPathItem(yAxisPath)
        xAxisPath.moveTo(50, 50)
        xAxisPath.lineTo(containerRect.width()-250, 50)
        xAxisItemTop = QGraphicsPathItem(xAxisPath)
        yAxisPath.moveTo(containerRect.width()-250, containerRect.height()-50)
        yAxisPath.lineTo(containerRect.width()-250, 50)
        yAxisItemRight = QGraphicsPathItem(yAxisPath)
        self.graphArea = QGraphicsRectItem(QRectF(yAxisItem.boundingRect().topLeft(), xAxisItem.boundingRect().bottomRight()))
        self.scene.addItem(self.graphArea)
        self.scene.addItem(xAxisItem)
        self.scene.addItem(yAxisItem)
        self.scene.addItem(xAxisItemTop)
        self.scene.addItem(yAxisItemRight)
        #calculate the size of each element
        self.elementWidth = xAxisItem.boundingRect().width()/xAxis
        self.elementHeight = yAxisItem.boundingRect().height()/yAxis

        #draw the actual heatmap
        #since the y-axis is flipped, y values has an offset of yAxis - yInd - 1
        for xInd in range(xAxis):
            for yInd in range(yAxis):
                elementPath = QPainterPath()
                elementPath.addRect(xInd*self.elementWidth + xAxisItem.boundingRect().left(), yInd*self.elementHeight + yAxisItem.boundingRect().top(), self.elementWidth, self.elementHeight)
                elementItem = ElementGraphicItem(elementPath, xAxisStart + xInd*zoomFactor, yAxisStart + (yAxis - yInd - 1)*zoomFactor)
                elementItem.setToolTip("x: " + str((xAxisStart + xInd*zoomFactor)*binSize*1000) + "bp\n" + "y: " + str((yAxisStart + (yAxis - yInd - 1)*zoomFactor)*binSize*1000) + "bp\n" + "#interactions: " +  str(A[yInd][xInd]))
                #Color each element depending on how many "hits" or interactions they have, more hits -> lighter color
                color = self.color.lighter(105*(1+(A[yInd][xInd])/(np.amax(A)+1)))
                colorPen = QPen(QBrush(self.color),1)
                #color the edges
                elementItem.setPen(colorPen)
                #fill the rectangles
                elementItem.setBrush(QBrush(color))
                self.scene.addItem(elementItem)

        #Creates a colorbar
        #uses a gradient which goes from self.color at 0 interactions to the darkest color on the heatmap for max interactions
        colorBarPath = QPainterPath()
        colorBarPath.addRect(xAxisItem.boundingRect().right() + 75, yAxisItem.boundingRect().top(), 50, yAxisItemRight.boundingRect().height())
        colorBarItem = QGraphicsPathItem(colorBarPath)
        linearGradient = QLinearGradient(colorBarItem.boundingRect().bottomLeft() + QPointF(25,0), colorBarItem.boundingRect().topLeft() + QPointF(25,0))
        linearGradient.setColorAt(0, self.color)
        linearGradient.setColorAt(1, self.color.lighter(105*(1+(np.amax(A)/(np.amax(A)+1)))))
        colorBarItem.setBrush(QBrush(linearGradient))
        self.scene.addItem(colorBarItem)

        #Add colorbar ticks and labels
        colorBarTick = QPainterPath()
        lineBetween = QLineF(colorBarItem.boundingRect().bottomRight(), colorBarItem.boundingRect().bottomRight() + QPointF(5,0))
        colorBarTick.moveTo(lineBetween.pointAt(1))
        colorBarTick.lineTo(lineBetween.pointAt(0))
        lineBetween = QLineF(colorBarItem.boundingRect().topRight(), colorBarItem.boundingRect().topRight() + QPointF(5,0))
        colorBarTick.moveTo(lineBetween.pointAt(1))
        colorBarTick.lineTo(lineBetween.pointAt(0))
        colorBarTickItem = QGraphicsPathItem(colorBarTick)
        colorBarTickLabelTopItem = QGraphicsTextItem(str(np.amax(A)))
        colorBarTickLabelBottomItem = QGraphicsTextItem(str(np.amin(A)))
        colorBarTickLabelTopItem.setPos(colorBarItem.boundingRect().topRight() + QPointF(10,-20))
        colorBarTickLabelBottomItem.setPos(colorBarItem.boundingRect().bottomRight() + QPointF(10,-20))
        colorBarTickLabelTopItem.setScale(2)
        colorBarTickLabelBottomItem.setScale(2)

        colorBarLabel = QGraphicsTextItem("# of interactions")
        colorBarLabel.setPos(colorBarItem.boundingRect().bottomRight() + QPointF(20, 100-colorBarItem.boundingRect().height()/2))
        colorBarLabel.setRotation(270)
        colorBarLabel.setScale(3)

        self.scene.addItem(colorBarTickItem)
        self.scene.addItem(colorBarTickLabelTopItem)
        self.scene.addItem(colorBarTickLabelBottomItem)
        self.scene.addItem(colorBarLabel)

        #Create axes ticks and labels (xAxis)
        for i in range(xAxis+1):
            xTickPath = QPainterPath()
            xTickLabel = ""
            if i%2 == 0:
                lineBetween = QLineF(xAxisItem.boundingRect().left() + i*self.elementWidth, xAxisItem.boundingRect().bottom(), xAxisItem.boundingRect().left() + i*self.elementWidth, xAxisItem.boundingRect().bottom() + 5)
                xTickPath.moveTo(lineBetween.pointAt(0))
                xTickPath.lineTo(lineBetween.pointAt(1))
                if zoomLevel == 0:
                    xTickLabel = str(int(xAxisStart + i*zoomFactor))
                else:
                    xTickLabel = str(round((xAxisStart + i*zoomFactor),zoomLevel))
            xTickItem = QGraphicsPathItem(xTickPath)
            xTickLabelItem = QGraphicsTextItem(xTickLabel)
            xTickLabelItem.setPos(xTickPath.currentPosition() + QPointF(-15,0))
            xTickLabelItem.setScale(2)
            self.scene.addItem(xTickItem)
            self.scene.addItem(xTickLabelItem)

        #yAxis
        for i in range(yAxis+1):
            yTickPath = QPainterPath()
            yTickLabel = ""
            if i%2 == 0:
                lineBetween = QLineF(yAxisItem.boundingRect().left(), yAxisItem.boundingRect().bottom() - i*self.elementHeight, yAxisItem.boundingRect().left() - 5, yAxisItem.boundingRect().bottom() - i*self.elementHeight)
                yTickPath.moveTo(lineBetween.pointAt(0))
                yTickPath.lineTo(lineBetween.pointAt(1))
                if zoomLevel == 0:
                    yTickLabel = str(int(yAxisStart + i*zoomFactor))
                else:
                    yTickLabel = str(round((yAxisStart + i*zoomFactor),zoomLevel))
            yTickItem = QGraphicsPathItem(yTickPath)
            yTickLabelItem = QGraphicsTextItem(yTickLabel)
            yTickLabelItem.setPos(yTickPath.currentPosition() + QPointF(-50,20))
            yTickLabelItem.setScale(2)
            yTickLabelItem.setRotation(270)
            self.scene.addItem(yTickItem)
            self.scene.addItem(yTickLabelItem)

        titleLabel = QGraphicsTextItem("Heatmapping chromosome " + chromoA.name + " to " + chromoB.name + " (" + self.variantNames[mapping] + ")")
        yAxisLabel = QGraphicsTextItem(endString + " on chromosome " + chromoB.name + " (x" + str(int(binSize/1000)) + "kb)")
        xAxisLabel = QGraphicsTextItem(startString + " on chromosome " + chromoA.name + " (x" + str(int(binSize/1000)) + "kb)")

        titleLabel.setPos(xAxisItemTop.boundingRect().center() + QPointF(-400,-100-yAxisItem.boundingRect().height()/2))
        yAxisLabel.setPos(yAxisItem.boundingRect().center() + QPointF(-150, 300))
        xAxisLabel.setPos(xAxisItem.boundingRect().center() + QPointF(-300, 60))

        titleLabel.setScale(4)
        yAxisLabel.setScale(3)
        xAxisLabel.setScale(3)

        yAxisLabel.setRotation(270)

        self.scene.addItem(titleLabel)
        self.scene.addItem(yAxisLabel)
        self.scene.addItem(xAxisLabel)

    def constructMatrix(self, chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart, zoomLevel):
        zoomFactor = math.pow(zoomFactor, -zoomLevel)
        B=[[0 for j in range(yAxis)] for i in range(xAxis)]
        for i in range(xAxis):
            for j in range(yAxis):
                counter = 0
                for variant in chromoA.variants:    
                    #special case if the mapping is a translocation
                    if mapping == "TLOC" and variant[9] and variant[0] is not variant[2] and variant[2] == chromoB.name:
                        #If chrA higher in order than chrB, WINA and WINB are switched, so check this first
                        if self.chromosomes.index(chromoA) > self.chromosomes.index(chromoB):
                            startWinA = int(variant[5]["WINB"].split(',')[0])
                            endWinA = int(variant[5]["WINB"].split(',')[1])
                            startWinB = int(variant[5]["WINA"].split(',')[0])
                            endWinB = int(variant[5]["WINA"].split(',')[1])
                        else: 
                            startWinA = int(variant[5]["WINA"].split(',')[0])
                            endWinA = int(variant[5]["WINA"].split(',')[1])
                            startWinB = int(variant[5]["WINB"].split(',')[0])
                            endWinB = int(variant[5]["WINB"].split(',')[1])
                        start = (startWinA + endWinA)/2
                        end = (startWinB + endWinB)/2
                        if (start >= (xAxisStart*binSize + i*(binSize*zoomFactor)) and start < (xAxisStart*binSize + i*binSize*zoomFactor + binSize*zoomFactor) and end >= (yAxisStart*binSize + j*binSize*zoomFactor) and end < (yAxisStart*binSize + j*binSize*zoomFactor + binSize*zoomFactor)):
                            counter = counter + 1
                            B[i][j] = counter
                            
                    elif (variant[4]==mapping and variant[9]):
                        start = int(variant[1])
                        end = int(variant[3])
                        #going through the elements to check if an interaction is made there, if it is -> add a "hit" i.e. counter increases by one
                        if (start >= (xAxisStart*binSize + i*(binSize*zoomFactor)) and start < (xAxisStart*binSize + i*binSize*zoomFactor + binSize*zoomFactor) and end >= (yAxisStart*binSize + j*binSize*zoomFactor) and end < (yAxisStart*binSize + j*binSize*zoomFactor + binSize*zoomFactor)):
                            counter = counter + 1
                            B[i][j] = counter
        B = np.asarray(B)
        B = B.T
        #the QT coordinate system has the origin in the top left corner, the y-axis is therefore flipped upside down to get an origin in the bottom left corner.
        B = np.flipud(B)


        return B


    def clearScene(self):
        self.scene.clear()
        self.update()

    def wheelEvent(self,event):
    
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)


    #Zoom function
    #takes the argument zoom, which determines if the zoom should be magnified or not
    #otherwise creates a new matrix B with the magnified values and adds it to the matrices list
    def zoomIn(self,zoom, xAxisStart, yAxisStart, xAxis, yAxis):
        (chromoA, chromoB, mapping, binSize, zoomFactor, b, c, d, e, zoomLevel) = self.matrices[self.activeIndex][1]
        if zoom:
            zoomLevel += 1
        B = self.constructMatrix(chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart, zoomLevel)
        matrixInfo = [chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart, zoomLevel]
        #removing matrices with higher index than self.activeIndex
        if self.activeIndex < len(self.matrices)-1:
            for index in range(self.activeIndex,len(self.matrices)-1):
                self.matrices.pop()

        self.matrices.append([B, matrixInfo])
        self.activeIndex += 1
        self.clearScene()
        self.updateHeatmap(self.activeIndex)

    def back(self):
        if self.activeIndex > 0:
            self.activeIndex -= 1
            self.updateHeatmap(self.activeIndex)
        #print("ActiveIndex: " + str(self.activeIndex))

    def forward(self):
        if self.activeIndex < len(self.matrices)-1:
            self.activeIndex += 1
            self.updateHeatmap(self.activeIndex)
        #print("ActiveIndex: " + str(self.activeIndex))

    #Creates a selecting rectangle on left click on the graph area
    def mousePressEvent(self, event):
        self.origin = event.pos()
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill):
            if not self.rubberBand.isVisible():
                self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    #Handles the size of the selecting rectangle on mouse movements
    def mouseMoveEvent(self, event):
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill) and self.mapFromScene(self.graphArea.boundingRect()).containsPoint(event.pos(), Qt.OddEvenFill):
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.origin,event.pos()).normalized())
                selectedItems = self.items(self.rubberBand.geometry())

    #When the mouse button is released two things can happen
    #Either the rectangle has selected more than one elements, then the zoom is started without any magnification, origin will be bottomLeft of the rectangle
    #and will cover the width and height of the rectangle
    #OR if the rectangle has only selected one element, then the zoom is started with magnification on the selected indices and cover an area 10x10
    def mouseReleaseEvent(self, event):
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill):
            self.rubberBand.hide()
            selectedItems = self.items(self.rubberBand.geometry())
            itemCounter = 0
            for item in selectedItems:
                if item.data(0) == "ElementItem":
                    itemCounter += 1
            if itemCounter > 1:
                yIndices = []
                xIndices = []
                for item in selectedItems:
                    if item.data(0) == "ElementItem":
                        yIndices.append(item.yInd)
                        xIndices.append(item.xInd)
                self.zoomIn(False, min(xIndices), min(yIndices), len(list(set(xIndices))), len(list(set(yIndices))))
            else:
                selectedItem = self.items(event.pos())
                for item in selectedItem:
                    if item.data(0) == "ElementItem":
                        xInd = item.xInd
                        yInd = item.yInd
                self.zoomIn(True, xInd, yInd, 10, 10)

#Subclass of graphics path item for custom handling of mouse events
class ElementGraphicItem(QGraphicsPathItem):

    def __init__(self,path,xInd, yInd):
        super().__init__(path)
        self.selected = False
        self.xInd = xInd
        self.yInd = yInd
        self.setData(0,"ElementItem")
        #self.setPen(QPen(Qt.darkRed,1))

    #Marks the chromosome item with a blue outline if selected
    def mark(self):
        currentPen = self.pen()
        currentPen.setStyle(Qt.DashLine)
        currentPen.setBrush(Qt.blue)
        currentPen.setWidth(3)
        self.setPen(currentPen)
        self.selected = True

    def unmark(self):
        self.setPen(QPen(Qt.darkRed,1))
        self.selected = False

    #Paints the name of the chromosone in the middle of the item -- possible to implemend changing of font etc if needed
    #Put this in separate function for more flexible handling of when name is painted?
    def paint(self,painter,option,widget):
        super().paint(painter,option,widget)
