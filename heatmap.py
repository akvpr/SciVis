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

class HeatmapScrollArea(QScrollArea):

    def __init__(self,dataDict,parent):
        super().__init__(parent)
        self.type = "heatmap"
        self.subview = HeatmapView(dataDict)
        self.setWidget(self.subview)
        self.setWidgetResizable(True)

    def returnSettingsWidget(self):
        return self.subview.returnSettingsWidget()

    def returnChromoInfoWidget(self):
        return self.subview.returnChromoInfoWidget()

    def closeOpenWindows(self):
        try:
            self.subview.chDia.close()
        except:
            pass

    def returnActiveDataset(self):
        return self.subview.returnActiveDataset()

    def viewVariants(self):
        self.subview.viewVariants()

    def createVariantWidget(self,row):
        return self.subview.createVariantWidget(row)

    def addVariant(self):
        self.subview.addVariant()


class HeatmapView(QWidget):

    def __init__(self,dataDict):
        super().__init__()
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
        self.createSettings()
        self.createChInfo()

    def returnActiveDataset(self):
        return self.dataDict

    #A dialog window used to gather data from the user (chromA, chromB, binSize)
    def addHeatmap(self):
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
                heatMap = HeatmapWindow(chromoA, chromoB, binSize, "TLOC", self)
                self.subWindows.append(heatMap)
                self.arrangePlots()

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
            heatMap = HeatmapWindow(self.chromoA, self.chromoB, self.binSize, mapping, self)
            self.subWindows.append(heatMap)
            self.arrangePlots()
        return;

    def arrangePlots(self):
        currentColumn = 0
        currentRow = 0
        for plot in self.subWindows:
            self.grid.addWidget(plot,currentRow,currentColumn)
            if currentColumn == self.maxColumns-1:
                currentRow += 1
                currentColumn = 0
            else:
                currentColumn += 1
        self.update()

    #Removes a plot and rearranges existing plots
    def removeHeatmap(self,plot):
        self.subWindows.remove(plot)
        self.grid.removeWidget(plot)
        plot.destroy()
        self.arrangePlots()

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

    def updateSettings(self):
        #Go through every row in the settings model and update accordingly
        for row in range(self.settingsModel.rowCount()):
            item = self.settingsModel.item(row,1)
            if row == 0:
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


class HeatmapWindow(QWidget):

    def __init__(self, chromoA, chromoB, binSize, mapping, parent):
        super().__init__(parent)
        #A dict for translating variant names
        self.variantNames = {"BND":"Break end", "DEL":"Deletion", "DUP":"Duplication", "IDUP":"Interspersed duplication", "INS":"Insertion", "INV":"Inversion", "TDUP":"Tandem duplication", "TLOC":"Translocation"}
        self.chromoA = chromoA
        self.chromoB = chromoB
        #the bin size is in kb and needs therefore be multiplied by 1000
        self.binSize = binSize * 1000
        self.mapping = mapping
        self.matrices = []
        self.activeIndex = 0
        self.setMinimumSize(500,500)
        self.figure = Figure(figsize=(5,2),dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()

        self.mpl_toolbar = MplToolbar(self.canvas, self)
        self.canvas.mpl_connect('button_release_event', self.onClick)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        self.setLayout(vbox)
        self.ax = self.figure.add_subplot(111)

        xAxis = int(round(int(chromoA.end)/self.binSize,0))
        yAxis = int(round(int(chromoB.end)/self.binSize,0))

        if not chromoA.connections:
            chromoA.createConnections()

        A = self.constructMatrix(self.chromoA, self.chromoB, self.mapping, self.binSize, 1, xAxis, yAxis, 0, 0)
        matrixInfo = [self.chromoA, self.chromoB, self.mapping, self.binSize, 1, xAxis, yAxis, 0, 0]
        self.matrices.append([A, matrixInfo])
        self.updateHeatmap(self.activeIndex)

    def updateHeatmap(self, activeIndex):

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        (chromoA, chromoB, mapping, binSize, zoomFactor, xAxis, yAxis, xAxisStart, yAxisStart) = self.matrices[activeIndex][1]
        if mapping == "TLOC":
            startString = "Position"
            endString = "Position"
        else:
            startString = "Start position"
            endString = "End position"

        self.heatmap = self.ax.pcolormesh(self.matrices[activeIndex][0].T, cmap = plt.cm.coolwarm)
        colorbar = self.figure.colorbar(self.heatmap)
        colorbar.set_label("# of interactions")

        self.ax.set_xlim(0, xAxis)
        self.ax.set_ylim(0, yAxis)
        xlabels = []
        ylabels = []
        for i in range(xAxis):
            if i%2:
                xlabels.append(str(i*zoomFactor + xAxisStart))
                ylabels.append(str(i*zoomFactor + yAxisStart))
        self.ax.set_xticks(range(0,xAxis,2))
        self.ax.set_yticks(range(0,yAxis,2))
        self.ax.set_xticklabels(xlabels)
        self.ax.set_yticklabels(ylabels)
        self.ax.set_title("Heatmapping chromosome " + chromoA.name + " to " + chromoB.name + " (" + self.variantNames[mapping] + ")")
        self.ax.set_ylabel(endString + " on chromosome " + chromoB.name + " (x" + str(binSize/1000) + "kb)")
        self.ax.set_xlabel(startString + " on chromosome " + chromoA.name + " (x" + str(binSize/1000) + "kb)")

        self.canvas.draw()

    def deletePlot(self):
        self.hide()
        self.parentWidget().removeHeatmap(self)

    #Opens a context menu on ctrl+right click on a plot
    def onClick(self, event):
        if event.button == 3:
           menu = QMenu()
           self.clickX = event.xdata
           self.clickY = event.ydata
           addPlotTextAct = QAction('Insert text',self)
           addPlotTextAct.triggered.connect(self.addPlotText)
           deletePlotAct = QAction('Delete plot',self)
           deletePlotAct.triggered.connect(self.deletePlot)
           zoomInAct = QAction('Zoom in on rectangle', self)
           zoomInAct.triggered.connect(self.zoomIn)
           menu.addAction(addPlotTextAct)
           menu.addAction(deletePlotAct)
           menu.addAction(zoomInAct)
           canvasHeight = int(self.figure.get_figheight()*self.figure.dpi)
           menu.exec_(self.mapToGlobal(QPoint(event.x,canvasHeight-event.y)))

    #Adds a given text to the clicked location (in data coordinates) to the plot
    def addPlotText(self):
        (text, ok) = QInputDialog.getText(None, 'Insert text', 'Text:')
        if ok and text:
            self.ax.text(self.clickX, self.clickY, text)
            self.canvas.draw()
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
                                #print((xStart*self.binSize + i*(self.binSize/10)), (xStart*self.binSize + i*self.binSize/10 + self.binSize/10), (yStart*self.binSize + j*self.binSize/10), (yStart*self.binSize + j*self.binSize + self.binSize/10))
                                #print(posConnA, posConnB)
                                #print(i, j)
                                B[i][j] = counter
        else:
            for i in range(xAxis):
                for j in range(yAxis):
                    counter = 0
                    for variant in self.chromoA.variants:
                       #Only look at the specified mapping variant (DEL, TDUP, IDUP, INV, DUP)
                       if (variant[4]==self.mapping):
                            start = int(variant[1])
                            end = int(variant[3])
                            #going through the elements to check if an interaction is made there, if it is -> add a "hit" i.e. counter increases by one
                            if (start >= (xAxisStart*binSize + i*(binSize*zoomFactor)) and start < (xAxisStart*binSize + i*binSize*zoomFactor + binSize*zoomFactor) and end >= (yAxisStart*binSize + j*binSize*zoomFactor) and end < (yAxisStart*binSize + j*binSize*zoomFactor + binSize*zoomFactor)):
                                counter = counter + 1
                                B[i][j] = counter
        B = np.asarray(B)
        return B

    def zoomIn(self):

        B = self.constructMatrix(self.chromoA, self.chromoB, self.mapping, self.binSize, 0.1, 10, 10, int(self.clickX), int(self.clickY))
        matrixInfo = [self.chromoA, self.chromoB, self.mapping, self.binSize, 0.1, 10, 10, int(self.clickX), int(self.clickY)]
        if self.activeIndex < len(self.matrices)-1:
            print("len: " + str(len(self.matrices)))
            for index in range(0,len(self.matrices)-1):
                print(index)
                self.matrices.pop()
        self.matrices.append([B, matrixInfo])
        self.activeIndex += 1
        self.updateHeatmap(self.activeIndex)

    def setColorBar(self):
        return 0

class MplToolbar(NavigationToolbar):

    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ("Back", "Forward" )]

    def __init__(self ,*args, **kwargs):
        super(MplToolbar, self).__init__(*args, **kwargs)
        self.layout().takeAt(2)

    def back(self):
        if self.parentWidget().activeIndex > 0:
            self.parentWidget().activeIndex -= 1
            self.parentWidget().updateHeatmap(self.parentWidget().activeIndex)
        self.mode = "go back"
        self.set_message(self.mode)
        print(self.parentWidget().activeIndex)

    def forward(self):
        if self.parentWidget().activeIndex < len(self.parentWidget().matrices)-1:
            self.parentWidget().activeIndex += 1
            self.parentWidget().updateHeatmap(self.parentWidget().activeIndex)
        self.mode = "go forward"
        self.set_message(self.mode)
        print(self.parentWidget().activeIndex)
