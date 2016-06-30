import sys
import data
import circos
import coverage
import karyogram
import heatmap
from PySide.QtCore import *
from PySide.QtGui import *

#The main window of the program. Handles a central view widget, and menus and toolbars.
class WGSView(QMainWindow):

    def __init__(self):
        super().__init__()
        self.activeScene = False
        self.datasetModel = QStandardItemModel()
        self.defaultFolder = ""
        self.initmainwin()

    def initmainwin(self):
        self.setWindowTitle('WGS')
        self.resize(QDesktopWidget().availableGeometry(self).size())
        #Center the main window on the user's screen
        frameGeo = self.frameGeometry()
        desktopCenter = QDesktopWidget().availableGeometry().center()
        frameGeo.moveCenter(desktopCenter)
        self.move(frameGeo.topLeft())
        #Adds a status bar to the main window
        self.statusBar()
        #Create actions for menus and toolbars, connect to functions
        self.newCircAct = QAction('New CIRCOS',self)
        self.newCircAct.triggered.connect(self.newCirc)
        self.newCovDiagramAct = QAction('New coverage diagram',self)
        self.newCovDiagramAct.triggered.connect(self.newCovDiagram)
        self.newKaryogramAct = QAction('New karyogram',self)
        self.newKaryogramAct.triggered.connect(self.newKaryogram)
        self.newHeatmapAct = QAction('New heatmap',self)
        self.newHeatmapAct.triggered.connect(self.newHeatmap)
        self.exitAct = QAction('Exit',self)
        self.exitAct.triggered.connect(self.close)
        self.exportImageAct = QAction('Export image',self)
        self.exportImageAct.triggered.connect(self.exportImage)
        self.viewDatasetsAct = QAction('View datasets',self)
        self.viewDatasetsAct.triggered.connect(self.viewDatasets)
        #Create menus, toolbar, and add actions
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('File')
        self.addMenuItems()
        self.show()

    #Exports anything in the current view as a png image
    def exportImage(self):
        #Set default name to same as the vcf file in current view
        viewDataset = self.view.returnActiveDataset()
        tabName = viewDataset['tabName']
        vcfName = viewDataset['vcfName']
        try:
            defaultPath = QDir.currentPath() + "/" + vcfName
            defaultPath = defaultPath.replace("vcf","png")
        except:
            defaultPath = QDir.currentPath() + "/" + tabName
            defaultPath = defaultPath.replace("tab","png")
        savePath = QFileDialog.getSaveFileName(self, "Export image", defaultPath, "Images (*.png)")[0]
        viewPixMap = QPixmap.grabWidget(self.view)
        viewPixMap.save(savePath)

    #Checks if an active scene is running and if it's ok to continue scene change
    def confirmChange(self):
        if self.activeScene:
            newSceneDialog = QDialog()
            newSceneDialog.setWindowTitle("Are you sure?")
            okButton = QPushButton('Ok', newSceneDialog)
            okButton.clicked.connect(newSceneDialog.accept)
            cancelButton = QPushButton('Cancel', newSceneDialog)
            cancelButton.clicked.connect(newSceneDialog.reject)
            textLabel = QLabel("The current scene will be lost. Are you sure?")
            newSceneDialog.layout = QGridLayout(newSceneDialog)
            newSceneDialog.layout.addWidget(textLabel,0,0,1,2)
            newSceneDialog.layout.addWidget(okButton,1,0)
            newSceneDialog.layout.addWidget(cancelButton,1,1)
            choice = newSceneDialog.exec_()
            if choice == QDialog.Accepted:
                return True
            else:
                return False
        #If there's no active scene running, always go ahead
        else:
            return True

    #Remove any old toolbars, menu items, clear up resources
    def clearActiveView(self):
        try:
            self.removeToolBar(self.tools)
            self.tools.hide()
            self.tools.destroy()
            self.view.destroy()
        except:
            pass
        self.fileMenu.clear()

    def addMenuItems(self):
        self.fileMenu.addAction(self.newCircAct)
        self.fileMenu.addAction(self.newCovDiagramAct)
        self.fileMenu.addAction(self.newKaryogramAct)
        self.fileMenu.addAction(self.newHeatmapAct)
        if self.activeScene:
            self.viewSettingsAct = QAction('Settings',self)
            self.viewSettingsAct.triggered.connect(self.view.viewSettings)
            self.fileMenu.addAction(self.viewSettingsAct)
            self.fileMenu.addAction(self.exportImageAct)
        self.fileMenu.addAction(self.viewDatasetsAct)
        self.fileMenu.addAction(self.exitAct)

    def selectDefaultFolder(self):
        selectedDir = QFileDialog.getExistingDirectory()
        if selectedDir:
            self.defaultFolder = selectedDir

    #Creates data model item, and adds to main dataset model
    def createDatasetItem(self, reader, setname):
        #Should display setname as parent
        dataItem = QStandardItem(setname)
        #Create a dict storing the actual data, and attach to item
        chromosomeList = reader.returnChrList()
        coverageNormLog = reader.returnCoverageNormLog()
        coverageNorm = reader.returnCoverageNorm()
        vcfName = reader.returnVcfName()
        tabName = reader.returnTabName()
        cytoTab = reader.returnCytoTab()
        cytoName = "cytoBand.txt"
        itemData = {'chromosomeList':chromosomeList,'coverageNormLog':coverageNormLog,'coverageNorm':coverageNorm,
        'vcfName':vcfName,'tabName':tabName, 'cytoTab':cytoTab}
        dataItem.setData(itemData)
        #Vcf and tab names should be child items
        vcfItem = QStandardItem(vcfName)
        vcfItem.setEnabled(False)
        tabItem = QStandardItem(tabName)
        tabItem.setEnabled(False)
        cytoItem = QStandardItem(cytoName)
        cytoItem.setEnabled(False)
        dataItem.appendRow(vcfItem)
        dataItem.appendRow(tabItem)
        dataItem.appendRow(cytoItem)
        #Add finished item to model
        self.datasetModel.appendRow(dataItem)

    #Creates a new set of data consisting of a vcf and a tab file
    def createNewDataset(self):
        #Prompt the user for a name of the dataset
        setName, ok = QInputDialog.getText(self, "Enter set name", "Set name", QLineEdit.Normal, "New set")
        if ok and setName:
            #If no default folder for data is set, use current path
            if not self.defaultFolder:
                startFolder = QDir.currentPath()
            else:
                startFolder = self.defaultFolder
            #Some confusion with python bindings makes getOpenFileName return a tuple.
            #First element is the name of the file.
            tabFile = QFileDialog.getOpenFileName(None,"Specify TAB file",startFolder,
            "TAB files (*.tab)")[0]
            #If no default folder was set, set it to folder containing chosen tab
            if not self.defaultFolder and tabFile:
                self.defaultFolder = QFileInfo(tabFile).absolutePath()
            elif not self.defaultFolder:
                self.defaultFolder = QDir.currentPath()
            vcfFile = QFileDialog.getOpenFileName(None,"Specify VCF file",self.defaultFolder,
            "VCF files (*.vcf)")[0]
            cytoFile = "cytoBand.txt"
            #Cancel results in empty string, only go ahead if not empty
            if tabFile and vcfFile:
                reader = data.Reader()
                self.statusBar().showMessage("Reading TAB..")
                reader.readTab(tabFile)
                self.statusBar().showMessage("Reading VCF..")
                reader.readVCFFile(vcfFile)
                self.statusBar().showMessage("Reading cytoband file..")
                reader.readCytoTab(cytoFile)
                self.statusBar().clearMessage()
                #Create a model item to be used for viewing datasets
                self.createDatasetItem(reader, setName)

    #Opens a window showing existing datasets
    def viewDatasets(self):
        dataList = QTreeView()
        dataList.setModel(self.datasetModel)
        dataList.setHeaderHidden(True)
        datasetDia = QDialog(self)
        datasetDia.setWindowTitle("Data sets")
        editButton = QPushButton('Edit set', datasetDia)
        #Should connect to function to edit a chosen set
        #editButton.clicked.connect(datasetDia.accept)
        newButton = QPushButton('New set', datasetDia)
        newButton.clicked.connect(self.createNewDataset)
        defaultFolderButton = QPushButton('Set default folder', datasetDia)
        defaultFolderButton.clicked.connect(self.selectDefaultFolder)
        datasetDia.layout = QGridLayout(datasetDia)
        datasetDia.layout.addWidget(dataList,0,0,1,3)
        datasetDia.layout.addWidget(editButton,1,0,1,1)
        datasetDia.layout.addWidget(newButton,1,1,1,1)
        datasetDia.layout.addWidget(defaultFolderButton,1,2,1,1)
        datasetDia.show()

    #Prompts user to select dataset and returns its data
    def selectDataset(self):
        dataList = QTreeView()
        dataList.setModel(self.datasetModel)
        datasetDia = QDialog(self)
        datasetDia.setWindowTitle("Choose data set")
        selectButton = QPushButton('Select set', datasetDia)
        selectButton.clicked.connect(datasetDia.accept)
        newButton = QPushButton('New set', datasetDia)
        newButton.clicked.connect(self.createNewDataset)
        datasetDia.layout = QGridLayout(datasetDia)
        datasetDia.layout.addWidget(dataList,0,0,1,2)
        datasetDia.layout.addWidget(selectButton,1,0,1,1)
        datasetDia.layout.addWidget(newButton,1,1,1,1)
        choice = datasetDia.exec_()
        selectedIndex = dataList.currentIndex()
        #Only return a dataset if user has accepted and selection is valid
        if choice == QDialog.Accepted and selectedIndex.isValid():
            selectedItem = self.datasetModel.itemFromIndex(selectedIndex)
            return selectedItem.data()
        else:
            return None

    #Creates and initializes a new circos diagram
    def newCirc(self):
        if self.confirmChange():

            self.statusBar().showMessage("Initializing new CIRCOS..")
            selectedData = self.selectDataset()
            self.statusBar().clearMessage()
            #Initialize scene if a valid dataset has been returned
            if selectedData is not None:
                self.activeScene = True
                self.clearActiveView()
                self.view = circos.CircosView(selectedData)
                self.setCentralWidget(self.view)
                self.addMenuItems()
                #Toolbar actions
                self.showChInfoAct = QAction('Chromosomes',self)
                self.showChInfoAct.triggered.connect(self.view.showChInfo)
                self.updateSceneAct = QAction('Update CIRCOS',self)
                self.updateSceneAct.triggered.connect(self.view.initscene)
                self.toggleCoverageAct = QAction('Toggle coverage',self)
                self.toggleCoverageAct.triggered.connect(self.view.toggleCoverage)
                self.addImageAct = QAction('Add Image to plot', self)
                self.addImageAct.triggered.connect(self.view.addImage)
                self.importColorTabAct = QAction('Color regions with file', self)
                self.importColorTabAct.triggered.connect(self.view.importColorTab)
                self.tools = self.addToolBar('Chromosome tools')
                self.tools.addAction(self.showChInfoAct)
                self.tools.addAction(self.updateSceneAct)
                self.tools.addAction(self.toggleCoverageAct)
                self.tools.addAction(self.addImageAct)
                self.tools.addAction(self.importColorTabAct)
                self.tools.show()
                self.show()

    #Creates and initializes a new coverage diagram
    def newCovDiagram(self):
        if self.confirmChange():

            self.statusBar().showMessage("Initializing new coverage diagram..")
            selectedData = self.selectDataset()
            self.statusBar().clearMessage()
            #Initialize scene if a valid dataset has been returned
            if selectedData is not None:
                self.activeScene = True
                self.clearActiveView()
                self.view = coverage.CoverageView(selectedData)
                self.scrollArea = QScrollArea(self)
                self.scrollArea.setWidget(self.view)
                self.scrollArea.setWidgetResizable(True)
                self.setCentralWidget(self.scrollArea)
                self.addMenuItems()
                #Toolbar actions
                self.tools = self.addToolBar('Coverage tools')
                self.showChInfoAct = QAction('Chromosomes',self)
                self.showChInfoAct.triggered.connect(self.view.showChInfo)
                self.addPlotAct = QAction('Add subplot', self)
                self.addPlotAct.triggered.connect(self.view.addChromoPlot)
                self.updateLayoutAct = QAction('Update layout', self)
                self.updateLayoutAct.triggered.connect(self.view.arrangePlots)
                self.tools.addAction(self.showChInfoAct)
                self.tools.addAction(self.addPlotAct)
                self.tools.addAction(self.updateLayoutAct)
                self.tools.show()
                self.show()

    #Creates and initializes a new karyotype diagram
    def newKaryogram(self):
        if self.confirmChange():

            self.statusBar().showMessage("Initializing karyogram..")
            selectedData = self.selectDataset()
            self.statusBar().clearMessage()
            #Initialize scene if a valid dataset has been returned
            if selectedData is not None:
                self.activeScene = True
                self.clearActiveView()
                self.view = karyogram.KaryogramView(selectedData)
                self.setCentralWidget(self.view)
                self.addMenuItems()
                #Toolbar actions
                self.tools = self.addToolBar('Karyogram tools')
                self.updateKaryogramAct = QAction('Update karyogram', self)
                self.updateKaryogramAct.triggered.connect(self.view.updateItems)
                self.showChInfoAct = QAction('Chromosomes',self)
                self.showChInfoAct.triggered.connect(self.view.showChInfo)
                self.tools.addAction(self.showChInfoAct)
                self.tools.addAction(self.updateKaryogramAct)
                self.tools.show()
                self.show()

    #Creates and initializes a new heatmap diagram
    def newHeatmap(self):
        if self.confirmChange():

            self.statusBar().showMessage("Initializing new heatmap..")
            selectedData = self.selectDataset()
            self.statusBar().clearMessage()
            #Initialize scene if a valid dataset has been returned
            if selectedData is not None:
                self.activeScene = True
                self.clearActiveView()
                self.view = heatmap.HeatmapView(selectedData)
                self.scrollArea = QScrollArea(self)
                self.scrollArea.setWidget(self.view)
                self.scrollArea.setWidgetResizable(True)
                self.setCentralWidget(self.scrollArea)
                self.addMenuItems()
                #Toolbar actions
                self.tools = self.addToolBar('Coverage tools')
                self.showChInfoAct = QAction('Chromosomes',self)
                self.showChInfoAct.triggered.connect(self.view.showChInfo)
                self.addHeatmapAct = QAction('Add heatmap', self)
                self.addHeatmapAct.triggered.connect(self.view.addHeatmap)
                self.updateLayoutAct = QAction('Update layout', self)
                self.updateLayoutAct.triggered.connect(self.view.arrangePlots)
                self.tools.addAction(self.showChInfoAct)
                self.tools.addAction(self.addHeatmapAct)
                self.tools.addAction(self.updateLayoutAct)
                self.tools.show()
                self.show()
