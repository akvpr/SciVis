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

    def __init__(self,dataDict):
        super().__init__()
        self.type = "heatmap"
        self.subview = HeatmapView(dataDict)
        self.setWidget(self.subview)
        self.setWidgetResizable(True)

    def viewSettings(self):
        self.subview.viewSettings()

    def closeOpenWindows(self):
        try:
            self.subview.chDia.close()
        except:
            pass

    def returnActiveDataset(self):
        return self.subview.returnActiveDataset()


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
        self.showChInfo()

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
        self.setMinimumSize(500,500)
        self.figure = Figure(figsize=(5,2),dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()

        self.canvas.mpl_connect('button_release_event', self.onClick)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        self.setLayout(vbox)
        self.ax = self.figure.add_subplot(111)

        if (self.mapping == "TLOC"):
            startString = "Position"
            endString = "Position"
            #Creating connections, only create them if they haven't already
            if not chromoA.connections:
                chromoA.createConnections()
            #Dividing the lengths of each chromosome by the bin size to get the axes
            xAxis = int(round(int(chromoA.end)/self.binSize,0))
            yAxis = int(round(int(chromoB.end)/self.binSize,0))
            #Initializing an empty array, xAxis*yAxis
            A=[[0 for j in range(yAxis)] for i in range(xAxis)]
            #mapping the connections to elements in the array
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
                            if (posConnA >= i*self.binSize and posConnA < (i*self.binSize + self.binSize) and posConnB >= j*self.binSize and posConnB < (j*self.binSize + self.binSize)):
                                counter = counter + 1
                                A[i][j] = counter
        else:
            xAxis = int(round(int(chromoA.end)/self.binSize,0))
            yAxis = int(round(int(chromoB.end)/self.binSize,0))
            startString = "Start position"
            endString = "End position"
            A=[[0 for j in range(yAxis)] for i in range(xAxis)]
            for i in range(xAxis):
                for j in range(yAxis):
                    counter = 0
                    for variant in chromoA.variants:
                        #Only look at the specified mapping variant (DEL, TDUP, IDUP, INV, DUP)
                       if (variant[4]==self.mapping):
                            start = int(variant[1])
                            end = int(variant[3])
                            pos = (end + start)/2
                            #going through the elements to check if an interaction is made there, if it is -> add a "hit" i.e. counter increases by one
                            if (start >= i*self.binSize and start < (i*self.binSize + self.binSize) and end >= j*self.binSize and end < (j*self.binSize + self.binSize)):
                                counter = counter + 1
                                A[i][j] = counter


        #convert the list A to a numpy array for using the function .T (to make transpose of)
        A = np.asarray(A)
        #use imshow to smooth the edges with interpolation, (does not work 100%)
        #heatmap = self.ax.imshow(A, cmap=plt.cm.coolwarm, interpolation='bilinear', aspect='auto', extent=[0,xAxis,0,yAxis])
        heatmap = self.ax.pcolormesh(A.T, cmap = plt.cm.coolwarm)
        #create a colorbar
        colorbar = self.figure.colorbar(heatmap)
        colorbar.set_label("# of interactions")
        #set the limits of each axis as well as their labels
        self.ax.set_xlim(0,xAxis)
        self.ax.set_ylim(0,yAxis)
        self.ax.set_title("Heatmapping chromosome " + chromoA.name + " to " + chromoB.name + " (" + self.variantNames[self.mapping] + ")")
        self.ax.set_ylabel(endString + " on chromosome " + chromoB.name + " (x" + str(binSize) + "kb)")
        self.ax.set_xlabel(startString + " on chromosome " + chromoA.name + " (x" + str(binSize) + "kb)")

        self.canvas.updateGeometry()
        self.canvas.draw()

    def deletePlot(self):
        self.hide()
        self.parentWidget().removeHeatmap(self)

    #Opens a context menu on ctrl+right click on a plot
    def onClick(self, event):
        if event.button == 3 and event.key == 'control':
           menu = QMenu()
           self.clickX = event.xdata
           self.clickY = event.ydata
           addPlotTextAct = QAction('Insert text',self)
           addPlotTextAct.triggered.connect(self.addPlotText)
           deletePlotAct = QAction('Delete plot',self)
           deletePlotAct.triggered.connect(self.deletePlot)
           menu.addAction(addPlotTextAct)
           menu.addAction(deletePlotAct)
           canvasHeight = int(self.figure.get_figheight()*self.figure.dpi)
           menu.exec_(self.mapToGlobal(QPoint(event.x,canvasHeight-event.y)))

    #Adds a given text to the clicked location (in data coordinates) to the plot
    def addPlotText(self):
        (text, ok) = QInputDialog.getText(None, 'Insert text', 'Text:')
        if ok and text:
            self.ax.text(self.clickX, self.clickY, text)
            self.canvas.draw()
