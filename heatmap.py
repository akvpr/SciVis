import common
from PySide.QtCore import *
from PySide.QtGui import *
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


class HeatmapView(QGraphicsView):

    def __init__(self,dataDict, parent):
    
        self.scene = QGraphicsScene()
        self.type = "heatmap"
        super().__init__(self.scene, parent)
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.subWindows = []
        self.variantNames = {"Break end":"BND", "Deletion":"DEL", "Duplication":"DUP", "Interspersed duplication":"IDUP", "Insertion":"INS", "Inversion":"INV", "Tandem duplication":"TDUP", "Translocation":"TLOC"}
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.maxColumns = 2
        self.bpWindow = 50
        self.minCoverage = 0
        self.maxCoverage = 5
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.hide()
        self.origin = QPoint(0,0)
        self.binSize = 10000
        self.createSettings()
        self.createChInfo()
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.clearScene()

    def returnActiveDataset(self):
        return self.dataDict

    #A dialog window used to gather data from the user (chromA, chromB, binSize)
    def addHeatmap(self):
        self.variantNames = {"Break end":"BND", "Deletion":"DEL", "Duplication":"DUP", "Interspersed duplication":"IDUP", "Insertion":"INS", "Inversion":"INV", "Tandem duplication":"TDUP", "Translocation":"TLOC"}
        addDialog = QDialog()
        addDialog.setWindowTitle("Add plot")
        applyButton = QPushButton('Ok', addDialog)
        applyButton.clicked.connect(addDialog.accept)
        chromoBoxA = QComboBox()
        chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
        chromoBoxA.addItems(chromoStrings)
        chrLabelA = QLabel("Map chromosome: ")
        chromoBoxB = QComboBox()
        chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
        chromoBoxB.addItems(chromoStrings)
        chrLabelB = QLabel("To chromosome: ")
        binSizeLabel = QLabel("Bin size (kb): ")
        binSizeData = QLineEdit()
        addDialog.layout = QGridLayout(addDialog)
        addDialog.layout.addWidget(chrLabelA,0,0)
        addDialog.layout.addWidget(chromoBoxA,0,1)
        addDialog.layout.addWidget(chrLabelB,1,0)
        addDialog.layout.addWidget(chromoBoxB,1,1)
        addDialog.layout.addWidget(binSizeLabel,2,0)
        addDialog.layout.addWidget(binSizeData,2,1)
        addDialog.layout.addWidget(applyButton,3,0)
        choice = addDialog.exec_()
        if choice == QDialog.Accepted:
            chromoA = self.chromosomes[chromoBoxA.currentIndex()]
            chromoB = self.chromosomes[chromoBoxB.currentIndex()]
            binSize = int(binSizeData.text())
            #if the chromosome is mapped to itself the variant needs to be chosen, see mappingDialog
            if chromoA == chromoB:
                self.mappingDialog(chromoA, chromoB, binSize)
            #if the chromosomes are different then the variant to be mapped is chosen to be translocations "TLOC"
            else:
                self.clearScene()
                self.createHeatmap(chromoA, chromoB, binSize, "TLOC")
                

    def mappingDialog(self, chromoA, chromoB, binSize):
        self.chromoA = chromoA
        self.chromoB = chromoB
        self.binSize = binSize
        addDialog = QDialog()
        addDialog.setWindowTitle("Select mapping")
        applyButton = QPushButton('Ok', addDialog)
        applyButton.clicked.connect(addDialog.accept)
        mappingBox = QComboBox()
        #the below variants are the ones the user can chose from
        mappingStrings = ["Deletion", "Duplication", "Interspersed duplication", "Tandem duplication", "Inversion", "Insertion", "Break end"]
        mappingBox.addItems(mappingStrings)
        mappingLabel = QLabel("Map the chromosome with respect to which variant: ")
        addDialog.layout = QGridLayout(addDialog)
        addDialog.layout.addWidget(mappingLabel,0,0)
        addDialog.layout.addWidget(mappingBox,0,1)
        addDialog.layout.addWidget(applyButton,1,0)
        choice = addDialog.exec_()
        if choice == QDialog.Accepted:
            #A dict is used to translate the variant names
            mapping = self.variantNames[mappingBox.currentText()]
            self.clearScene()
            self.createHeatmap(chromoA, chromoB, binSize, mapping)
        return;


    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = ["bpWindow", "minCoverage", "maxCoverage"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        maxColumnsText = QStandardItem("Number of columns")
        maxColumnsText.setEditable(False)
        maxColumnsText.setToolTip("Number of columns to arrange diagrams in")
        maxColumnsData = QStandardItem()
        maxColumnsData.setData(self.maxColumns,0)
        maxColumnsData.setEditable(True)
        self.settingsModel.setItem(0,0,maxColumnsText)
        self.settingsModel.setItem(0,1,maxColumnsData)
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
            self.maxColumns = item.data(0)

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
            
    def createHeatmap(self, chromoA, chromoB, binSize, mapping):
        self.variantNames = {"BND":"Break end", "DEL":"Deletion", "DUP":"Duplication", "IDUP":"Interspersed duplication", "INS":"Insertion", "INV":"Inversion", "TDUP":"Tandem duplication", "TLOC":"Translocation"}
        binSize = binSize*1000
        self.matrices = []
        self.activeIndex = 0
        xAxis = int(round(int(chromoA.end)/binSize,0))
        yAxis = int(round(int(chromoB.end)/binSize,0))
        
        if not chromoA.connections:
            chromoA.createConnections()
            
        A = self.constructMatrix(chromoA, chromoB, mapping, binSize, 1, xAxis, yAxis, 0, 0)
        matrixInfo = [chromoA, chromoB, mapping, binSize, 1, xAxis, yAxis, 0, 0]
        self.matrices.append([A, matrixInfo])
        self.updateHeatmap(self.activeIndex)
        
    def updateHeatmap(self, activeIndex):
        self.clearScene()
        (chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart) = self.matrices[activeIndex][1]
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
        #
        for xInd in range(xAxis):
            for yInd in range(yAxis):
                elementPath = QPainterPath()
                elementPath.addRect(xInd*self.elementWidth + xAxisItem.boundingRect().left(), yInd*self.elementHeight + yAxisItem.boundingRect().top(), self.elementWidth, self.elementHeight)
                elementItem = ElementGraphicItem(elementPath, xAxisStart + xInd, yAxisStart + yAxis - yInd - 1)
                elementItem.setToolTip("(" + str(xAxisStart + xInd*zoomFactor) + ", " + str(yAxisStart + yAxis - yInd*zoomFactor-1) + "): " +   str(A[yInd][xInd]))
                color = QColor(Qt.darkRed)
                color = color.lighter(105*(1+(A[yInd][xInd])/10))
                colorPen = QPen(QBrush(Qt.darkRed),1)
                elementItem.setPen(colorPen)
                elementItem.setBrush(QBrush(color))
                self.scene.addItem(elementItem)
                
        colorBarPath = QPainterPath()
        colorBarPath.addRect(xAxisItem.boundingRect().right() + 75, yAxisItem.boundingRect().top(), 50, yAxisItemRight.boundingRect().height())
        colorBarItem = QGraphicsPathItem(colorBarPath)
        linearGradient = QLinearGradient(colorBarItem.boundingRect().bottomLeft() + QPointF(25,0), colorBarItem.boundingRect().topLeft() + QPointF(25,0))
        color = QColor(Qt.darkRed)
        linearGradient.setColorAt(0, color)
        linearGradient.setColorAt(1, color.lighter(105*(1+(np.amax(A)/10))))
        colorBarItem.setBrush(QBrush(linearGradient))
        self.scene.addItem(colorBarItem)
        
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
        colorBarTickLabelTopItem.setPos(colorBarItem.boundingRect().topRight() + QPointF(10,-10))
        colorBarTickLabelBottomItem.setPos(colorBarItem.boundingRect().bottomRight() + QPointF(10,-10))
        
        colorBarLabel = QGraphicsTextItem("# of interactions")
        colorBarLabel.setPos(colorBarItem.boundingRect().bottomRight() + QPointF(20, 20-colorBarItem.boundingRect().height()/2))
        colorBarLabel.setRotation(270)
        colorBarLabel.setScale(2)
        
        self.scene.addItem(colorBarTickItem)
        self.scene.addItem(colorBarTickLabelTopItem)
        self.scene.addItem(colorBarTickLabelBottomItem)
        self.scene.addItem(colorBarLabel)
        
        for i in range(xAxis):
            xTickPath = QPainterPath()
            xTickLabel = ""
            if i%3 == 0:
                lineBetween = QLineF(xAxisItem.boundingRect().left() + i*self.elementWidth, xAxisItem.boundingRect().bottom(), xAxisItem.boundingRect().left() + i*self.elementWidth, xAxisItem.boundingRect().bottom() + 5)
                xTickPath.moveTo(lineBetween.pointAt(0))
                xTickPath.lineTo(lineBetween.pointAt(1))
                xTickLabel = str(xAxisStart + i*zoomFactor)
            xTickItem = QGraphicsPathItem(xTickPath)
            xTickLabelItem = QGraphicsTextItem(xTickLabel)
            xTickLabelItem.setPos(xTickPath.currentPosition() + QPointF(-8,5))
            self.scene.addItem(xTickItem)
            self.scene.addItem(xTickLabelItem)
            
        for i in range(yAxis):
            yTickPath = QPainterPath()
            yTickLabel = ""
            if i%3 == 0:
                lineBetween = QLineF(yAxisItem.boundingRect().left(), yAxisItem.boundingRect().bottom() - i*self.elementHeight, yAxisItem.boundingRect().left() - 5, yAxisItem.boundingRect().bottom() - i*self.elementHeight)
                yTickPath.moveTo(lineBetween.pointAt(0))
                yTickPath.lineTo(lineBetween.pointAt(1))
                yTickLabel = str(yAxisStart + i*zoomFactor)
            yTickItem = QGraphicsPathItem(yTickPath)
            yTickLabelItem = QGraphicsTextItem(yTickLabel)
            yTickLabelItem.setPos(yTickPath.currentPosition() + QPointF(-25,-10))
            self.scene.addItem(yTickItem)
            self.scene.addItem(yTickLabelItem)
        
        titleLabel = QGraphicsTextItem("Heatmapping chromosome " + chromoA.name + " to " + chromoB.name + " (" + self.variantNames[mapping] + ")")
        yAxisLabel = QGraphicsTextItem(endString + " on chromosome " + chromoB.name + " (x" + str(binSize/1000) + "kb)")
        xAxisLabel = QGraphicsTextItem(startString + " on chromosome " + chromoA.name + " (x" + str(binSize/1000) + "kb)")
        
        titleLabel.setPos(xAxisItemTop.boundingRect().center() + QPointF(-130,-60-yAxisItem.boundingRect().height()/2))
        yAxisLabel.setPos(yAxisItem.boundingRect().center() + QPointF(-100, 150))
        xAxisLabel.setPos(xAxisItem.boundingRect().center() + QPointF(-130, 60))
        
        titleLabel.setScale(2)
        yAxisLabel.setScale(2)
        xAxisLabel.setScale(2)       
        
        yAxisLabel.setRotation(270)
        
        self.scene.addItem(titleLabel)
        self.scene.addItem(yAxisLabel)
        self.scene.addItem(xAxisLabel)
        
        
        
    def constructMatrix(self, chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart):
        B=[[0 for j in range(yAxis)] for i in range(xAxis)]
        if (mapping == "TLOC"):
            for i in range(xAxis):
                for j in range(yAxis):
                    counter = 0
                    for connection in chromoA.connections:
                        #Only look at connections made to chromosome B
                        if (connection[1] == chromoB.name):
                            #takes the position in the middle of each window
                            startWinA = int(connection[2].split(',')[0])
                            endWinA = int(connection[2].split(',')[1])
                            startWinB = int(connection[3].split(',')[0])
                            endWinB = int(connection[3].split(',')[1])
                            posConnA = (endWinA + startWinA)/2
                            posConnB = (endWinB + startWinB)/2
                            #going through the elements to check if an interaction is made there, if it is -> add a "hit" i.e. counter increases by one
                            if (posConnA >= (xAxisStart*binSize + i*(binSize*zoomFactor)) and posConnA < (xAxisStart*binSize + i*binSize*zoomFactor + binSize*zoomFactor) and posConnB >= (yAxisStart*binSize + j*binSize*zoomFactor) and posConnB < (yAxisStart*binSize + j*binSize*zoomFactor + binSize*zoomFactor)):
                                counter = counter + 1
                                #print((xAxisStart*binSize + i*(binSize/10)), (xAxisStart*binSize + i*binSize/10 + binSize/10), (yAxisStart*binSize + j*binSize/10), (yAxisStart*binSize + j*self.binSize + binSize/10))
                                #print(posConnA, posConnB)
                                #print(i, j)
                                B[i][j] = counter
        else:
            for i in range(xAxis):
                for j in range(yAxis):
                    counter = 0
                    for variant in chromoA.variants:
                       #Only look at the specified mapping variant (DEL, TDUP, IDUP, INV, DUP)
                       if (variant[4]==mapping):
                            start = int(variant[1])
                            end = int(variant[3])
                            #going through the elements to check if an interaction is made there, if it is -> add a "hit" i.e. counter increases by one
                            if (start >= (xAxisStart*binSize + i*(binSize*zoomFactor)) and start < (xAxisStart*binSize + i*binSize*zoomFactor + binSize*zoomFactor) and end >= (yAxisStart*binSize + j*binSize*zoomFactor) and end < (yAxisStart*binSize + j*binSize*zoomFactor + binSize*zoomFactor)):
                                counter = counter + 1
                                B[i][j] = counter
        B = np.asarray(B)
        B = B.T
        B = np.flipud(B)
        print()

        
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

    def zoomIn(self,zoomFactor, xAxisStart, yAxisStart, xAxis, yAxis):
        (chromoA, chromoB, mapping, binSize, a, b, c, d, e) = self.matrices[self.activeIndex][1]
        B = self.constructMatrix(chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart)
        matrixInfo = [chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart]
        if self.activeIndex < len(self.matrices)-1:
            for index in range(0,len(self.matrices)-1):
                self.matrices.pop()
        self.matrices.append([B, matrixInfo])
        self.activeIndex += 1
        self.clearScene()
        self.updateHeatmap(self.activeIndex)
        
    def back(self):
        if self.activeIndex > 0:
            self.activeIndex -= 1
            self.updateHeatmap(self.activeIndex)
        #print(self.activeIndex)
        
    def forward(self):
        if self.activeIndex < len(self.matrices)-1:
            self.activeIndex += 1
            self.updateHeatmap(self.activeIndex)
        #print(self.activeIndex)
        
    def mousePressEvent(self, event):
        self.origin = event.pos()
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill):
            if not self.rubberBand.isVisible():
                self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        
    def mouseMoveEvent(self, event):
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill) and self.mapFromScene(self.graphArea.boundingRect()).containsPoint(event.pos(), Qt.OddEvenFill):
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.origin,event.pos()).normalized())
                selectedItems = self.items(self.rubberBand.geometry())
                
        
    def mouseReleaseEvent(self, event):
        if self.mapFromScene(self.graphArea.boundingRect()).containsPoint(self.origin, Qt.OddEvenFill):
            if self.rubberBand.geometry().width() > self.elementWidth:
                self.rubberBand.hide()
                yIndices = []
                xIndices = []
                selectedItems = self.items(self.rubberBand.geometry())
                for item in selectedItems:
                    if item.data(0) == "ElementItem":
                        yIndices.append(item.yInd)
                        xIndices.append(item.xInd)
                self.zoomIn(1, min(xIndices), min(yIndices), max(xIndices)-min(xIndices)+1, max(yIndices)-min(yIndices)+1)
            elif self.rubberBand.geometry().width() < self.elementWidth:
                self.rubberBand.hide()
                selectedItem = self.items(event.pos())
                for item in selectedItem:
                    if item.data(0) == "ElementItem":
                        xInd = item.xInd
                        yInd = item.yInd
                self.zoomIn(0.1, xInd, yInd, 10, 10)
        
#Subclass of graphics path item for custom handling of mouse events
class ElementGraphicItem(QGraphicsPathItem):

    def __init__(self,path,xInd, yInd):
        super().__init__(path)
        self.selected = False
        self.xInd = xInd
        self.yInd = yInd
        self.setData(0,"ElementItem")
        self.setPen(QPen(Qt.darkRed,1))

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
        
