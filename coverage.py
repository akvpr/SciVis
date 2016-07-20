from PySide.QtCore import *
from PySide.QtGui import *
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import math
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

class CoverageView(QGraphicsView):

    def __init__(self,dataDict, parent):
        self.scene = QGraphicsScene()
        self.type = "coverage"
        super().__init__(self.scene, parent)
        self.dataDict = dataDict
        self.chromosomes = self.dataDict['chromosomeList']
        self.cytoInfo = self.dataDict['cytoTab']
        self.subWindows = []
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.maxColumns = 2
        self.bpWindow = 100
        self.minCoverage = 0
        self.maxCoverage = 5
        self.plotType = 0
        self.createSettings()
        self.coverageNormLog = self.dataDict['coverageNormLog']
        self.coverageNorm = self.dataDict['coverageNorm']
        self.createChInfo()
        self.setRenderHints(QPainter.Antialiasing)
        self.resize(QDesktopWidget().availableGeometry(self).size())
        self.show()
        self.initscene(self.chromosomes[0])

    def returnActiveDataset(self):
        return self.dataDict

    #Adds a subwindow containing a matplotlib widget to the grid layout
    def addChromoPlot(self):
        addDialog = QDialog()
        addDialog.setWindowTitle("Add plot")
        applyButton = QPushButton('Ok', addDialog)
        applyButton.clicked.connect(addDialog.accept)
        chromoBox = QComboBox()
        chromoStrings = [chromo.name for chromo in self.chromosomes if not "GL" in chromo.name]
        chromoBox.addItems(chromoStrings)
        chrLabel = QLabel("Add plot for chromosome: ")
        typeBox = QComboBox()
        typeStrings = ["Line plot", "Scatter plot"]
        typeBox.addItems(typeStrings)
        typeLabel = QLabel("Plot method: ")
        addDialog.layout = QGridLayout(addDialog)
        addDialog.layout.addWidget(chrLabel,0,0)
        addDialog.layout.addWidget(chromoBox,0,1)
        addDialog.layout.addWidget(typeLabel,1,0)
        addDialog.layout.addWidget(typeBox,1,1)
        addDialog.layout.addWidget(applyButton,2,0)
        choice = addDialog.exec_()
        if choice == QDialog.Accepted:
            chromo = self.chromosomes[chromoBox.currentIndex()]
            chromoPlot = ChromoPlotWindow(chromo,typeBox.currentIndex(), self.cytoInfo,self)
            self.subWindows.append(chromoPlot)
            self.arrangePlots()


    def createSettings(self):
        self.settingsModel = QStandardItemModel()
        #create header labels to distinguish different settings.
        verticalHeaders = ["bpWindow", "minCoverage", "maxCoverage"]
        self.settingsModel.setVerticalHeaderLabels(verticalHeaders)
        bpWinText = QStandardItem("BP Resolution (kb)")
        bpWinText.setEditable(False)
        bpWinText.setToolTip("Show each data point as the average of this value (x1000 bp)")
        bpWinData = QStandardItem()
        bpWinData.setData(self.bpWindow,0)
        bpWinData.setEditable(True)
        minCovLimitText = QStandardItem("Min.coverage value (%)")
        minCovLimitText.setEditable(False)
        minCovLimitText.setToolTip("Minimum coverage value,\nin percentage of average coverage value of genome.")
        minCovLimitData = QStandardItem()
        minCovLimitData.setData(self.minCoverage*100,0)
        minCovLimitData.setEditable(True)
        maxCovLimitText = QStandardItem("Max. coverage value (%)")
        maxCovLimitText.setEditable(False)
        maxCovLimitText.setToolTip("Maximum coverage value,\nin percentage of average coverage value of genome.")
        maxCovLimitData = QStandardItem()
        maxCovLimitData.setData(self.maxCoverage*100,0)
        maxCovLimitData.setEditable(True)
        maxColumnsText = QStandardItem("Number of columns")
        maxColumnsText.setEditable(False)
        maxColumnsText.setToolTip("Number of columns to arrange diagrams in")
        maxColumnsData = QStandardItem()
        maxColumnsData.setData(self.maxColumns,0)
        maxColumnsData.setEditable(True)
        self.settingsModel.setItem(0,0,bpWinText)
        self.settingsModel.setItem(0,1,bpWinData)
        self.settingsModel.setItem(1,0,minCovLimitText)
        self.settingsModel.setItem(1,1,minCovLimitData)
        self.settingsModel.setItem(2,0,maxCovLimitText)
        self.settingsModel.setItem(2,1,maxCovLimitData)
        self.settingsModel.setItem(3,0,maxColumnsText)
        self.settingsModel.setItem(3,1,maxColumnsData)
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
            self.minCoverage = item.data(0)/100
        if item.row() == 2:
            self.maxCoverage = item.data(0)/100
        if item.row() == 3:
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

    def createLinePlot(self, chromo):
        size = self.size()
        coverageData = []
        normValue = self.coverageNorm
        minCov = normValue*self.minCoverage
        maxCov = normValue*self.maxCoverage
        containerRect = QRect(QPoint(50,50), QPoint(size.width()-50,size.height()-50))
        coverageChunks = [chromo.coverage[i:i+(self.bpWindow)] for i in range(0,len(chromo.coverage),(self.bpWindow))]
        for chunk in coverageChunks:
            val = sum(chunk) / len(chunk)
            if val > maxCov:
                val = maxCov
            if val < minCov:
                val = minCov
            #Presuming we're dealing with a diploid genome, the norm should represent 2 copies, so multiply by 2
            coverageData.append(2*val/normValue)
            
        xAxisPath = QPainterPath()
        xAxisPath.moveTo(50,containerRect.height()-50)
        xAxisPath.lineTo(containerRect.width()-250, containerRect.height()-50)
        xAxisItem = QGraphicsPathItem(xAxisPath)
        yAxisPath = QPainterPath()
        yAxisPath.moveTo(50,containerRect.height()-50)
        yAxisPath.lineTo(50, 50)
        yAxisItem = QGraphicsPathItem(yAxisPath)
        self.scene.addItem(xAxisItem)
        self.scene.addItem(yAxisItem)
        
        dupLimit = 2.25
        delLimit = 1.75
        xAxisIncrement = (int(xAxisItem.boundingRect().width()))/len(coverageData)
        yAxisIncrement = (int(yAxisItem.boundingRect().height()))/(10)
        
        for incr in range(int(xAxisItem.boundingRect().width())):
            xTickPath = QPainterPath()
            xTickLabel = ""
            if incr%200 == 0 and incr != 0 or incr == int(xAxisItem.boundingRect().width())-1:
                lineBetween = QLineF(xAxisItem.boundingRect().left() + incr, xAxisItem.boundingRect().top()-10, xAxisItem.boundingRect().left() + incr, xAxisItem.boundingRect().top()+10)            
                xTickPath.moveTo(lineBetween.pointAt(0))
                xTickPath.lineTo(lineBetween.pointAt(1))
                xTickLabel = str(int((math.pow(xAxisIncrement, -1))*incr))
            xTickItem = QGraphicsPathItem(xTickPath)
            xTickLabelItem = QGraphicsTextItem(xTickLabel)
            xTickLabelItem.setPos(xTickPath.currentPosition() + QPointF(-10, 10))
            self.scene.addItem(xTickItem)
            self.scene.addItem(xTickLabelItem)
        for incr in range(int(yAxisItem.boundingRect().height())):
            yTickPath = QPainterPath()
            yTickLabel = ""
            if incr%300 == 0 and incr != 0 or incr == int(yAxisItem.boundingRect().height())-1:
                lineBetween = QLineF(yAxisItem.boundingRect().left()-10, yAxisItem.boundingRect().bottom() - incr, yAxisItem.boundingRect().left()+10, yAxisItem.boundingRect().bottom() - incr)            
                yTickPath.moveTo(lineBetween.pointAt(0))
                yTickPath.lineTo(lineBetween.pointAt(1))
                yTickLabel = str(int((math.pow(yAxisIncrement, -1))*incr))
            yTickItem = QGraphicsPathItem(yTickPath)
            yTickLabelItem = QGraphicsTextItem(yTickLabel)
            yTickLabelItem.setPos(yTickPath.currentPosition() + QPointF(-65, -10))
            self.scene.addItem(yTickItem)
            self.scene.addItem(yTickLabelItem)
        
        offsetPoint = QPointF(xAxisItem.boundingRect().width()/2, 0)
        linearGradient = QLinearGradient(QPointF(yAxisItem.boundingRect().bottomLeft()) + offsetPoint, QPointF(yAxisItem.boundingRect().topLeft()) + offsetPoint)
        linearGradient.setColorAt(1, Qt.green)
        linearGradient.setColorAt(2.25/10, Qt.green)
        linearGradient.setColorAt(2.245/10, Qt.black)
        linearGradient.setColorAt(1.755/10, Qt.black)
        linearGradient.setColorAt(1.75/10, Qt.red)
        linearGradient.setColorAt(0, Qt.red)
        colorBrush = QBrush(linearGradient)
        colorPen = QPen()
        colorPen.setBrush(colorBrush)
        
        for index in range(len(coverageData)):
            if index < len(coverageData)-1:    
                linePath = QPainterPath()
                startPoint = QPointF(index*xAxisIncrement + 50, int(yAxisItem.boundingRect().height()) - coverageData[index]*yAxisIncrement + 50)
                endPoint = QPointF((index+1)*xAxisIncrement + 50, int(yAxisItem.boundingRect().height()) - coverageData[index+1]*yAxisIncrement + 50)
                linePath.moveTo(startPoint)
                linePath.lineTo(endPoint)
                lineItem = QGraphicsPathItem(linePath)
                lineItem.setPen(colorPen)
                self.scene.addItem(lineItem)
    
    def createScatterPlot(self, chromo):
        size = self.size()
        coverageData = []
        normValue = self.coverageNorm
        minCov = normValue*self.minCoverage
        maxCov = normValue*self.maxCoverage
        containerRect = QRect(QPoint(50,50), QPoint(size.width()-50,size.height()-50))
        coverageChunks = [chromo.coverage[i:i+(self.bpWindow)] for i in range(0,len(chromo.coverage),(self.bpWindow))]
        for chunk in coverageChunks:
            val = sum(chunk) / len(chunk)
            if val > maxCov:
                val = maxCov
            if val < minCov:
                val = minCov
            #Presuming we're dealing with a diploid genome, the norm should represent 2 copies, so multiply by 2
            coverageData.append(2*val/normValue)
            
        xAxisPath = QPainterPath()
        xAxisPath.moveTo(50,containerRect.height()-50)
        xAxisPath.lineTo(containerRect.width()-250, containerRect.height()-50)
        xAxisItem = QGraphicsPathItem(xAxisPath)
        yAxisPath = QPainterPath()
        yAxisPath.moveTo(50,containerRect.height()-50)
        yAxisPath.lineTo(50, 50)
        yAxisItem = QGraphicsPathItem(yAxisPath)
        self.scene.addItem(xAxisItem)
        self.scene.addItem(yAxisItem)
        
        dupLimit = 2.25
        delLimit = 1.75
        xAxisIncrement = (int(xAxisItem.boundingRect().width()))/len(coverageData)
        yAxisIncrement = (int(yAxisItem.boundingRect().height()))/(10)
        
        for incr in range(int(xAxisItem.boundingRect().width())):
            xTickPath = QPainterPath()
            xTickLabel = ""
            if incr%200 == 0 and incr != 0 or incr == int(xAxisItem.boundingRect().width())-1:
                lineBetween = QLineF(xAxisItem.boundingRect().left() + incr, xAxisItem.boundingRect().top()-10, xAxisItem.boundingRect().left() + incr, xAxisItem.boundingRect().top()+10)            
                xTickPath.moveTo(lineBetween.pointAt(0))
                xTickPath.lineTo(lineBetween.pointAt(1))
                xTickLabel = str(int((math.pow(xAxisIncrement, -1))*incr))
            xTickItem = QGraphicsPathItem(xTickPath)
            xTickLabelItem = QGraphicsTextItem(xTickLabel)
            xTickLabelItem.setPos(xTickPath.currentPosition() + QPointF(-10, 10))
            self.scene.addItem(xTickItem)
            self.scene.addItem(xTickLabelItem)
        for incr in range(int(yAxisItem.boundingRect().height())):
            yTickPath = QPainterPath()
            yTickLabel = ""
            if incr%300 == 0 and incr != 0 or incr == int(yAxisItem.boundingRect().height())-1:
                lineBetween = QLineF(yAxisItem.boundingRect().left()-10, yAxisItem.boundingRect().bottom() - incr, yAxisItem.boundingRect().left()+10, yAxisItem.boundingRect().bottom() - incr)            
                yTickPath.moveTo(lineBetween.pointAt(0))
                yTickPath.lineTo(lineBetween.pointAt(1))
                yTickLabel = str(int((math.pow(yAxisIncrement, -1))*incr))
            yTickItem = QGraphicsPathItem(yTickPath)
            yTickLabelItem = QGraphicsTextItem(yTickLabel)
            yTickLabelItem.setPos(yTickPath.currentPosition() + QPointF(-65, -10))
            self.scene.addItem(yTickItem)
            self.scene.addItem(yTickLabelItem)
        

        for index in range(len(coverageData)):
            pointPath = QPainterPath()
            pointPath.addEllipse(index*xAxisIncrement + 50, int(yAxisItem.boundingRect().height()) - coverageData[index]*yAxisIncrement + 45, 5, 5)
            pointItem = QGraphicsPathItem(pointPath)
            if coverageData[index] < delLimit:
                pointItem.setBrush(QBrush(Qt.red))
            elif coverageData[index] > dupLimit:
                pointItem.setBrush(QBrush(Qt.green))
            else:
                pointItem.setBrush(QBrush(Qt.black))
            self.scene.addItem(pointItem)
            
        
        
        
    def initscene(self, chromo):
        self.scene.clear()
        if self.plotType == 0:
            self.createScatterPlot(chromo)
        else:
            self.createLinePlot(chromo)
        self.update()
        
    def wheelEvent(self,event):
        if event.modifiers() == Qt.ControlModifier and event.delta() > 0:
            self.scale(0.9,0.9)
        elif event.modifiers() == Qt.ControlModifier and event.delta() < 0:
            self.scale(1.1,1.1)
        else:
            QGraphicsView.wheelEvent(self, event)
