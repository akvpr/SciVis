import sys
import data
import circ
import coverage
import karyogram
import heatmap
import pickle
from PySide.QtCore import *
from PySide.QtGui import *

#The main window of the program. Handles a central view widget, and menus and toolbars.
class SciVisView(QMainWindow):

    def __init__(self):
        super().__init__()
        self.activeScene = False
        self.datasetModel = QStandardItemModel()
        self.defaultFolder = ""
        self.initmainwin()

    def initmainwin(self):
        self.setWindowTitle('SciVis')
        self.setWindowState(Qt.WindowMaximized)
        #Adds a status bar to the main window
        self.statusBar()
        #Load various icons as QIcons
        self.deleteIcon = QIcon("icons/delete.png")
        self.editIcon = QIcon("icons/edit.png")
        self.exportImageIcon = QIcon("icons/exportimage.png")
        self.folderIcon = QIcon("icons/folder.png")
        self.loadIcon = QIcon("icons/load.png")
        self.newIcon = QIcon("icons/new.png")
        self.saveIcon = QIcon("icons/save.png")
        self.settingsIcon = QIcon("icons/settings.png")
        #Load config file
        (self.circularConfig,self.coverageConfig,self.karyoConfig,self.heatmapConfig) = data.readConfig("userSettings.conf")
        #Create actions for menus and toolbars, connect to functions
        newCircAct = QAction('New circular diagram',self)
        newCircAct.triggered.connect(self.newCirc)
        newCovDiagramAct = QAction('New coverage diagram',self)
        newCovDiagramAct.triggered.connect(self.newCovDiagram)
        newKaryogramAct = QAction('New karyogram',self)
        newKaryogramAct.triggered.connect(self.newKaryogram)
        newHeatmapAct = QAction('New heatmap',self)
        newHeatmapAct.triggered.connect(self.newHeatmap)
        exitAct = QAction('Exit',self)
        exitAct.triggered.connect(self.close)
        exportImageAct = QAction('Export image',self)
        exportImageAct.triggered.connect(self.exportImage)
        viewSettingsAct = QAction('Settings',self)
        viewSettingsAct.triggered.connect(self.viewSettings)
        #Create menus, and add actions
        self.createColorModel()
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('File')
        self.fileMenu.addAction(newCircAct)
        self.fileMenu.addAction(newCovDiagramAct)
        self.fileMenu.addAction(newKaryogramAct)
        self.fileMenu.addAction(newHeatmapAct)
        self.fileMenu.addAction(viewSettingsAct)
        self.fileMenu.addAction(exportImageAct)
        self.fileMenu.addAction(exitAct)
        #Create a tab widget handling active scenes
        self.sceneTabs = QTabWidget(self)
        self.sceneTabs.currentChanged.connect(self.viewChanged)
        self.sceneTabs.setTabsClosable(True)
        self.sceneTabs.tabCloseRequested.connect(self.closeView)
        self.setCentralWidget(self.sceneTabs)
        #Keep a list of views and selected chromosomes for these
        self.views = []
        self.viewChromosomes = []
        self.initDock()
        self.bedWidget = None
        self.show()

    def initDock(self):
        #Create a main dock widget to hold a tabbed widget (and possibly var view) in a vbox layout
        mainDockContents = QWidget()
        mainDockLayout = QVBoxLayout()
        #Create a tab widget for chromosomes, data
        self.dockTabs = QTabWidget()
        self.dockTabs.currentChanged.connect(self.dockTabChanged)
        #For each tab, create a page widget and collect views and buttons in a grid layout
        chromosomePage = QWidget()
        chromosomeLayout = QGridLayout()
        dataPage = QWidget()
        dataLayout = QGridLayout()

        #Placeholder for chromosome info in active view
        #Apply layout to page, add page to tab widget
        chromosomePage.setLayout(chromosomeLayout)
        self.dockTabs.addTab(chromosomePage,"Chromosomes")

        #Create data view and buttons
        dataList = QTreeView()
        dataList.setModel(self.datasetModel)
        dataList.setHeaderHidden(True)
        dataList.setSelectionMode(QAbstractItemView.SingleSelection)
        newButton = QPushButton(self.newIcon,"")
        newButton.setToolTip("Create new dataset")
        newButton.clicked.connect(self.createNewDataset)
        editButton = QPushButton(self.editIcon,"")
        editButton.setToolTip("Edit dataset")
        editButton.clicked.connect(lambda: self.editDataset(dataList.currentIndex()))
        loadButton = QPushButton(self.loadIcon,"")
        loadButton.setToolTip("Load dataset")
        loadButton.clicked.connect(self.loadDataset)
        saveButton = QPushButton(self.saveIcon,"")
        saveButton.setToolTip("Save dataset")
        saveButton.clicked.connect(lambda: self.saveSelectedDataset(dataList.currentIndex()))
        defaultFolderButton = QPushButton(self.folderIcon,"")
        defaultFolderButton.setToolTip("Set default folder")
        defaultFolderButton.clicked.connect(self.selectDefaultFolder)
        dataLayout.addWidget(dataList,0,0,1,5)
        dataLayout.addWidget(newButton,1,0,1,1)
        dataLayout.addWidget(editButton,1,1,1,1)
        dataLayout.addWidget(loadButton,1,2,1,1)
        dataLayout.addWidget(saveButton,1,3,1,1)
        dataLayout.addWidget(defaultFolderButton,1,4,1,1)
        #Apply layout to page, add page to tab widget
        dataPage.setLayout(dataLayout)
        tabIndex = self.dockTabs.addTab(dataPage,"Data")
        #Start on data tab for now
        self.dockTabs.setCurrentIndex(tabIndex)

        #Add the tab widget to the main dock layout
        mainDockLayout.addWidget(self.dockTabs)

        #Create placeholder variant widget
        variantWidget = QWidget()
        variantLayout = QGridLayout()
        variantList = QTableView()
        variantLayout.addWidget(variantList,0,0)
        variantWidget.setLayout(variantLayout)
        #Add variant widget to main dock layout
        mainDockLayout.addWidget(variantWidget)

        #Apply the main dock layout
        mainDockContents.setLayout(mainDockLayout)
        #Create the dock widget itself, set content to just created content widget, and add to main window
        self.dockWidget = QDockWidget("Dock", self)
        self.dockWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dockWidget.setWidget(mainDockContents)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget)
        self.setCorner(Qt.TopLeftCorner,Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner,Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner,Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner,Qt.RightDockWidgetArea)
        #Sets the title widget to an empty widget, effectively removing float ability and title bar
        self.dockWidget.setTitleBarWidget(QWidget())

    def dockTabChanged(self):
        pass

    #Exports anything in the current view as a png image
    def exportImage(self):
        if self.activeScene:
            #Set default name to same as the vcf file in current view
            view = self.sceneTabs.currentWidget()
            viewDataset = view.returnActiveDataset()
            tabName = viewDataset['tabName']
            vcfName = viewDataset['vcfName']
            try:
                defaultPath = QDir.currentPath() + "/" + vcfName
                defaultPath = defaultPath.replace("vcf","png")
            except:
                defaultPath = QDir.currentPath() + "/" + tabName
                defaultPath = defaultPath.replace("tab","png")
            savePath = QFileDialog.getSaveFileName(self, "Export image", defaultPath, "Images (*.png)")[0]
            viewType = view.type
            if viewType == 'circ' or viewType == 'karyogram' or viewType == 'heatmap':
                image = QImage(self.size(),QImage.Format_ARGB32)
                image.fill(Qt.white)
                imgPainter = QPainter(image)
                imgPainter.setRenderHint(QPainter.Antialiasing)
                view.scene.render(imgPainter)
                imgPainter.end()
                image.save(savePath)
            elif viewType == 'coverage':
                image = QImage(self.size(),QImage.Format_ARGB32)
                image.fill(Qt.white)
                imgPainter = QPainter(image)
                imgPainter.setRenderHint(QPainter.Antialiasing)
                view.mainScene.render(imgPainter)
                imgPainter.end()
                image.save(savePath)
            else:
                viewPixMap = QPixmap.grabWidget(self)
                viewPixMap.save(savePath)

    #Checks if an active scene is running and if it's ok to continue (closing scene?)
    def confirmClose(self):
        if self.activeScene:
            newSceneDialog = QDialog()
            newSceneDialog.setWindowTitle("Are you sure?")
            okButton = QPushButton('Ok', newSceneDialog)
            okButton.clicked.connect(newSceneDialog.accept)
            cancelButton = QPushButton('Cancel', newSceneDialog)
            cancelButton.clicked.connect(newSceneDialog.reject)
            textLabel = QLabel("The scene will be lost. Are you sure?")
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

    def selectDefaultFolder(self):
        selectedDir = QFileDialog.getExistingDirectory()
        if selectedDir:
            self.defaultFolder = selectedDir

    def saveSelectedDataset(self,index):
        if index.isValid() and not self.datasetModel.itemFromIndex(index).hasChildren():
            index = index.parent()
        if index.isValid():
            selectedData = self.datasetModel.itemFromIndex(index).data()
            filename = selectedData['setName'] + ".pkl"
            if not self.defaultFolder:
                startPath = QDir.currentPath() + "/" + filename
            else:
                startPath = self.defaultFolder + "/" + filename
            savePath = QFileDialog.getSaveFileName(self, "Save dataset", startPath, "Pickle files (*.pkl)")[0]
            if savePath:
                with open(savePath, 'wb') as output:
                    pickle.dump(selectedData, output, pickle.HIGHEST_PROTOCOL)

    def saveDataset(self):
        selectedData = self.selectDataset()
        filename = selectedData['setName'] + ".pkl"
        if not self.defaultFolder:
            startPath = QDir.currentPath() + "/" + filename
        else:
            startPath = self.defaultFolder + "/" + filename
        savePath = QFileDialog.getSaveFileName(self, "Save dataset", startPath, "Pickle files (*.pkl)")[0]
        if savePath:
            with open(savePath, 'wb') as output:
                pickle.dump(selectedData, output, pickle.HIGHEST_PROTOCOL)

    def loadDataset(self):
        filename = QFileDialog.getOpenFileName(None,"Specify pkl file",self.defaultFolder,
        "Pickle files (*.pkl)")[0]
        if filename:
            itemData = pickle.load( open( filename, "rb" ) )
            #Create a model item and add to the model containing datasets
            dataItem = QStandardItem(itemData['setName'])
            dataItem.setData(itemData)
            vcfItem = QStandardItem(itemData['vcfName'])
            vcfItem.setEnabled(False)
            tabItem = QStandardItem(itemData['tabName'])
            tabItem.setEnabled(False)
            cytoName = "cytoBand.txt"
            cytoItem = QStandardItem(cytoName)
            cytoItem.setEnabled(False)
            dataItem.appendRow(vcfItem)
            dataItem.appendRow(tabItem)
            dataItem.appendRow(cytoItem)
            self.datasetModel.appendRow(dataItem)

    #Creates data model item, and adds to main dataset model
    def createDatasetItem(self, tabName, vcfName, setName):
        self.statusBar().showMessage("Reading TAB..")
        (chromosomeList,coverageNorm,coverageNormLog,totalBP) = data.readTab(tabName)
        self.statusBar().showMessage("Reading VCF..")
        (chromosomeList,vcfInfoLines) = data.readVCFFile(vcfName,chromosomeList)
        self.statusBar().showMessage("Reading cytoband file..")
        cytoName = "cytoBand.txt"
        cytoTab = data.readCytoTab(cytoName)
        self.statusBar().clearMessage()
        #Should display setname as parent
        dataItem = QStandardItem(setName)
        #Create a dict storing the actual data, and attach to item
        itemData = {'chromosomeList':chromosomeList,'coverageNormLog':coverageNormLog,'coverageNorm':coverageNorm,
        'vcfName':vcfName,'tabName':tabName, 'cytoTab':cytoTab,'setName':setName}
        dataItem.setData(itemData)
        #Vcf and tab names should be child items
        vcfItem = QStandardItem(vcfName)
        vcfItem.setEditable(False)
        vcfItem.setSelectable(True)
        tabItem = QStandardItem(tabName)
        tabItem.setEditable(False)
        tabItem.setSelectable(True)
        cytoItem = QStandardItem(cytoName)
        cytoItem.setEditable(False)
        cytoItem.setSelectable(True)
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
            #Don't continue if user has cancelled
            if tabFile:
                vcfFile = QFileDialog.getOpenFileName(None,"Specify VCF file",self.defaultFolder,
                "VCF files (*.vcf)")[0]
                #Cancel results in empty string, only go ahead if not empty
                if tabFile and vcfFile:
                    #Create a model item to be used for viewing datasets
                    self.createDatasetItem(tabFile,vcfFile,setName)

    def editDataset(self,index):
        #User might have clicked on a child item with no data -- try to get parent item if so
        if index.isValid() and not self.datasetModel.itemFromIndex(index).hasChildren():
            index = index.parent()
        if index.isValid():
            tabFile = QFileDialog.getOpenFileName(None,"Specify TAB file",self.defaultFolder,
            "TAB files (*.tab)")[0]
            if tabFile:
                vcfFile = QFileDialog.getOpenFileName(None,"Specify VCF file",self.defaultFolder,
                "VCF files (*.vcf)")[0]
                cytoFile = "cytoBand.txt"
                #Cancel results in empty string, only go ahead if not empty
                if tabFile and vcfFile:
                    #Remove current item from model, create a new item, insert item
                    oldItem = self.datasetModel.itemFromIndex(index)
                    setName = oldItem.data()["setName"]
                    oldRow = index.row()
                    self.datasetModel.removeRow(oldRow)
                    self.createDatasetItem(tabFile,vcfFile,setName)

    #Opens a window showing existing datasets
    def viewDatasets(self):
        dataList = QTreeView()
        dataList.setModel(self.datasetModel)
        dataList.setHeaderHidden(True)
        dataList.setSelectionMode(QAbstractItemView.SingleSelection)
        datasetDia = QDialog(self)
        datasetDia.setWindowTitle("Data sets")
        #Connects to edit function with selected index
        editButton = QPushButton('Edit set', datasetDia)
        editButton.clicked.connect(lambda: self.editDataset(dataList.currentIndex()))
        newButton = QPushButton('New set', datasetDia)
        newButton.clicked.connect(self.createNewDataset)
        loadButton = QPushButton('Load set', datasetDia)
        loadButton.clicked.connect(self.loadDataset)
        defaultFolderButton = QPushButton('Set default folder', datasetDia)
        defaultFolderButton.clicked.connect(self.selectDefaultFolder)
        datasetDia.layout = QGridLayout(datasetDia)
        datasetDia.layout.addWidget(dataList,0,0,1,4)
        datasetDia.layout.addWidget(editButton,1,0,1,1)
        datasetDia.layout.addWidget(newButton,1,1,1,1)
        datasetDia.layout.addWidget(loadButton,1,2,1,1)
        datasetDia.layout.addWidget(defaultFolderButton,1,3,1,1)
        datasetDia.show()

    #Prompts user to select dataset and returns its data
    def selectDataset(self):
        dataList = QTreeView()
        dataList.setModel(self.datasetModel)
        dataList.setHeaderHidden(True)
        dataList.setSelectionMode(QAbstractItemView.SingleSelection)
        dataList.setSelectionBehavior(QAbstractItemView.SelectRows)
        datasetDia = QDialog(self)
        datasetDia.setWindowTitle("Choose data set")
        #Connect double click signal to dialog accept
        dataList.doubleClicked.connect(datasetDia.accept)
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
        #User might have clicked on a child item with no data -- try to get parent item if so
        if selectedIndex.isValid() and not self.datasetModel.itemFromIndex(selectedIndex).hasChildren():
            selectedIndex = selectedIndex.parent()
        #Only return a dataset if user has accepted and selection is valid
        if choice == QDialog.Accepted and selectedIndex.isValid():
            selectedItem = self.datasetModel.itemFromIndex(selectedIndex)
            return selectedItem.data()
        else:
            return None

    #Activates when a tab close button has been pressed
    def closeView(self,viewIndex):
        if self.confirmClose():
            view = self.sceneTabs.widget(viewIndex)
            self.views.remove(view)
            if not self.views:
                self.activeScene = False
                self.removeDockWidget(self.dockWidget)
                self.initDock()
            self.sceneTabs.removeTab(viewIndex)

    #Handles toolbar switching etc if the view is changed.
    def viewChanged(self,viewIndex):
        #Remove current toolbar and close open windows for last open view
        try:
            self.removeToolBar(self.tools)
            self.lastActiveView.closeOpenWindows()
            self.tools.hide()
            self.tools.deleteLater()
        except:
            pass
        #Return false if no new scene has been initialized, true otherwise
        if not self.activeScene:
            return False
        view = self.sceneTabs.currentWidget()
        self.lastActiveView = view
        #Add this view's chromosome info widget
        infoWidget = view.returnChromoInfoWidget()
        #Connect selection of chromosome to update variant view
        chTable = infoWidget.layout().itemAtPosition(0,0).widget()
        selModel = chTable.selectionModel()
        selModel.selectionChanged.connect(self.selectChromosome)
        self.dockTabs.removeTab(0)
        self.dockTabs.insertTab(0,infoWidget,"Chromosomes")
        self.dockTabs.setCurrentIndex(0)
        #Add appropriate toolbar for scene type
        viewType = view.type
        viewInd = self.views.index(view)
        if viewType == "circ":
            view.updateToggles()
            self.dockTabs.widget(0).layout().itemAtPosition(0,0).widget().selectRow(self.viewChromosomes[viewInd])
            self.tools = self.addToolBar('Circ tools')
            showChInfoAct = QAction('Chromosomes',self)
            showChInfoAct.triggered.connect(view.showChInfo)
            updateSceneAct = QAction('Update diagram',self)
            updateSceneAct.triggered.connect(view.initscene)
            toggleCoverageAct = QAction('Toggle coverage',self)
            toggleCoverageAct.triggered.connect(view.toggleCoverage)
            addImageAct = QAction('Add Image to plot', self)
            addImageAct.triggered.connect(view.addImage)
            importColorTabAct = QAction('Color regions with file', self)
            importColorTabAct.triggered.connect(view.importColorTab)
            addBedAct = QAction('Add layer',self)
            addBedAct.triggered.connect(view.addNewLayer)
            self.tools.addAction(showChInfoAct)
            self.tools.addAction(updateSceneAct)
            self.tools.addAction(toggleCoverageAct)
            self.tools.addAction(addImageAct)
            self.tools.addAction(importColorTabAct)
            self.tools.addAction(addBedAct)
            self.tools.show()
        if viewType == "coverage":
            view.startScene()
            self.dockTabs.widget(0).layout().itemAtPosition(0,0).widget().selectRow(self.viewChromosomes[viewInd])
            self.tools = self.addToolBar('Coverage tools')
            showChInfoAct = QAction('Chromosomes',self)
            showChInfoAct.triggered.connect(view.showChInfo)
            plotTypeBox = QComboBox()
            plotTypeBox.addItem("Plot type: scatter")
            plotTypeBox.addItem("Plot type: line")
            plotTypeBox.setCurrentIndex(view.plotType)
            plotTypeBox.currentIndexChanged.connect(view.changePlotType)
            addBedAct = QAction('Add bed track',self)
            addBedAct.triggered.connect(view.addBed)
            addExcludeFileAct = QAction('Add exclude file',self)
            addExcludeFileAct.triggered.connect(view.addExcludeFile)
            addExcludeGCFileAct = QAction('Add GC file',self)
            addExcludeGCFileAct.triggered.connect(view.addExcludeGCFile)
            self.tools.addAction(showChInfoAct)
            self.tools.addAction(addBedAct)
            self.tools.addAction(addExcludeFileAct)
            self.tools.addAction(addExcludeGCFileAct)
            self.tools.addWidget(plotTypeBox)
            self.tools.show()
        if viewType == "karyogram":
            view.updateToggles()
            self.dockTabs.widget(0).layout().itemAtPosition(0,0).widget().selectRow(self.viewChromosomes[viewInd])
            self.tools = self.addToolBar('Karyogram tools')
            updateKaryogramAct = QAction('Update karyogram', self)
            updateKaryogramAct.triggered.connect(view.updateItems)
            resetLayoutAct = QAction('Reset layout', self)
            resetLayoutAct.triggered.connect(view.resetLayout)
            showChInfoAct = QAction('Chromosomes',self)
            showChInfoAct.triggered.connect(view.showChInfo)
            self.tools.addAction(showChInfoAct)
            self.tools.addAction(resetLayoutAct)
            self.tools.addAction(updateKaryogramAct)
            self.tools.show()
        if viewType == "heatmap":
            self.dockTabs.widget(0).layout().itemAtPosition(0,0).widget().selectRow(self.viewChromosomes[viewInd])
            self.tools = self.addToolBar('Coverage tools')
            dataDict = view.returnActiveDataset()
            chromosomes = dataDict['chromosomeList']
            chromoABox = QComboBox()
            chromoStrings = [chromo.name for chromo in chromosomes if not "GL" in chromo.name]
            chromoABox.addItems(chromoStrings)
            chromoABox.currentIndexChanged.connect(view.changeChromoA)
            chromoBBox = QComboBox()
            chromoBBox.addItems(chromoStrings)
            chromoBBox.currentIndexChanged.connect(view.changeChromoB)
            binSizeBox = QLineEdit()
            binSizeBox.setValidator(QIntValidator(2000,20000, self))
            binSizeBox.insert("10000")
            binSizeBox.editingFinished.connect(lambda: view.changeBinsize(binSizeBox.text()))
            variantTypeBox = QComboBox()
            mappingStrings = ["Deletion", "Translocation", "Duplication", "Interspersed duplication", "Tandem duplication", "Inversion", "Insertion", "Break end"]
            variantTypeBox.addItems(mappingStrings)
            variantTypeBox.currentIndexChanged.connect(lambda: view.changeMappingType(variantTypeBox.currentText()))
            colorAct = QAction("Color", self)
            colorAct.triggered.connect(self.heatColor)
            backAct = QAction('Back', self)
            backAct.setShortcut(QKeySequence(Qt.Key_Left))
            backAct.triggered.connect(view.back)
            forwardAct = QAction('Forward', self)
            forwardAct.setShortcut(QKeySequence(Qt.Key_Right))
            forwardAct.triggered.connect(view.forward)
            binSizeBox.setMaximumWidth(100)
            self.tools.addWidget(QLabel("Map chromosome:"))
            self.tools.addWidget(chromoABox)
            self.tools.addWidget(QLabel("to chromosome: "))
            self.tools.addWidget(chromoBBox)
            self.tools.addWidget(QLabel("with respect to: "))
            self.tools.addWidget(variantTypeBox)
            self.tools.addWidget(QLabel("Bin size: "))
            self.tools.addWidget(binSizeBox)
            self.tools.addWidget(QLabel("kb"))
            self.tools.addAction(colorAct)
            self.tools.addAction(backAct)
            self.tools.addAction(forwardAct)
            self.tools.show()
        return True

    #Creates and initializes a new circular diagram
    def newCirc(self):

        self.statusBar().showMessage("Initializing new circular diagram..")
        selectedData = self.selectDataset()
        self.statusBar().clearMessage()
        #Initialize scene if a valid dataset has been returned
        if selectedData is not None:
            self.activeScene = True
            view = circ.CircView(selectedData,self.circularConfig,self)
            self.views.append(view)
            self.viewChromosomes.append(0)
            tabIndex = self.sceneTabs.addTab(view,"Circular")
            self.sceneTabs.setCurrentIndex(tabIndex)
            self.show()

    #Creates and initializes a new coverage diagram
    def newCovDiagram(self):

        self.statusBar().showMessage("Initializing new coverage diagram..")
        selectedData = self.selectDataset()
        self.statusBar().clearMessage()
        #Initialize scene if a valid dataset has been returned
        if selectedData is not None:
            self.activeScene = True
            self.update()
            view = coverage.CoverageView(selectedData,self.coverageConfig,self)
            self.views.append(view)
            self.viewChromosomes.append(0)
            tabIndex = self.sceneTabs.addTab(view,"Coverage")
            self.sceneTabs.setCurrentIndex(tabIndex)
            self.show()


    #Creates and initializes a new karyotype diagram
    def newKaryogram(self):

        self.statusBar().showMessage("Initializing karyogram..")
        selectedData = self.selectDataset()
        self.statusBar().clearMessage()
        #Initialize scene if a valid dataset has been returned
        if selectedData is not None:
            self.activeScene = True
            view = karyogram.KaryogramView(selectedData,self.karyoConfig,self)
            self.views.append(view)
            self.viewChromosomes.append(0)
            tabIndex = self.sceneTabs.addTab(view,"Karyogram")
            self.sceneTabs.setCurrentIndex(tabIndex)
            self.show()

    #Creates and initializes a new heatmap diagram
    def newHeatmap(self):

        self.statusBar().showMessage("Initializing new heatmap..")
        selectedData = self.selectDataset()
        self.statusBar().clearMessage()
        #Initialize scene if a valid dataset has been returned
        if selectedData is not None:
            self.activeScene = True
            view = heatmap.HeatmapView(selectedData,self.heatmapConfig,self)
            self.views.append(view)
            self.viewChromosomes.append(0)
            tabIndex = self.sceneTabs.addTab(view,"Heatmap")
            self.sceneTabs.setCurrentIndex(tabIndex)
            self.show()

    def createColorModel(self):
        #Model allowing stain colors to be changed globally
        self.stainNames = ['heatmapColor', 'acen','gneg','gpos100','gpos25','gpos50','gpos75','gvar','stalk']
        self.stainColors = {'heatmapColor':Qt.darkRed, 'acen':Qt.darkRed, 'gneg':Qt.white,'gpos100':Qt.black,'gpos25':Qt.lightGray,'gpos50':Qt.gray,
        'gpos75':Qt.darkGray,'gvar':Qt.white,'stalk':Qt.red}
        self.colorModel = QStandardItemModel()
        stainItems = []
        colorItems = []
        for stainName in self.stainNames:
            stainItem = QStandardItem(stainName)
            stainItem.setEditable(False)
            stainItem.setSelectable(False)
            stainItems.append(stainItem)
            colorItem = QStandardItem()
            colorItem.setSizeHint(QSize(40,40))
            colorItem.setBackground(self.stainColors[stainName])
            colorItem.setEditable(False)
            colorItem.setSelectable(False)
            colorItems.append(colorItem)
        self.colorModel.appendColumn(stainItems)
        self.colorModel.appendColumn(colorItems)

    def pickColor(self,modelIndex):
        selectedRow = modelIndex.row()
        stainItem = self.colorModel.item(selectedRow,0)
        colorItem = self.colorModel.item(selectedRow,1)
        chosenColor = QColorDialog.getColor(colorItem.background().color())
        self.stainColors[stainItem.text()] = chosenColor
        colorItem.setBackground(chosenColor)

    def heatColor(self):
        color = QColorDialog.getColor(self.stainColors["heatmapColor"])
        self.stainColors["heatmapColor"] = color
        self.colorModel.item(0,1).setBackground(color)
        self.updateSettings()

    def viewSettings(self):
        settingsLayout = QGridLayout()
        #Get the active view settings, if any are active. Else empty.
        if self.activeScene:
            view = self.sceneTabs.currentWidget()
            activeViewPage = view.returnSettingsWidget()
        else:
            activeViewPage = QWidget()
        #General settings
        generalPage = QWidget()
        generalLayout = QGridLayout()
        generalList = QTableView()
        generalList.setShowGrid(False)
        generalList.horizontalHeader().hide()
        generalList.verticalHeader().hide()
        generalLayout.addWidget(generalList,0,0)
        generalPage.setLayout(generalLayout)
        #Color settings
        colorPage = QWidget()
        colorLayout = QGridLayout()
        colorList = QTableView()
        colorList.setShowGrid(False)
        colorList.horizontalHeader().hide()
        colorList.verticalHeader().hide()
        colorList.setModel(self.colorModel)
        colorList.resizeColumnsToContents()
        colorList.doubleClicked.connect(self.pickColor)
        colorLayout.addWidget(colorList,0,0)
        colorPage.setLayout(colorLayout)
        #Create the settings stack and a list for selection
        settingsStack = QStackedWidget()
        settingsStack.addWidget(activeViewPage)
        settingsStack.addWidget(generalPage)
        settingsStack.addWidget(colorPage)
        stackList = QListWidget()
        QListWidgetItem("Active view", stackList)
        QListWidgetItem("General", stackList)
        QListWidgetItem("Colors", stackList)
        stackList.currentRowChanged.connect(settingsStack.setCurrentIndex)
        settingsDia = QDialog(self)
        okButton = QPushButton('Ok', settingsDia)
        okButton.clicked.connect(self.updateSettings)
        okButton.clicked.connect(settingsDia.accept)
        applyButton = QPushButton('Apply', settingsDia)
        applyButton.clicked.connect(self.updateSettings)
        saveSettingsButton = QPushButton('Save settings', settingsDia)
        saveSettingsButton.clicked.connect(self.saveSettings)
        resetSettingsButton = QPushButton('Reset settings to default', settingsDia)
        resetSettingsButton.clicked.connect(self.resetSettings)
        settingsLayout.addWidget(stackList,0,0)
        settingsLayout.addWidget(settingsStack,0,1,1,4)
        settingsLayout.addWidget(okButton,1,0,1,1)
        settingsLayout.addWidget(applyButton,1,1,1,1)
        settingsLayout.addWidget(saveSettingsButton,1,2,1,1)
        settingsLayout.addWidget(resetSettingsButton,1,3,1,1)
        settingsDia.setWindowTitle("Settings")
        settingsDia.setLayout(settingsLayout)
        settingsDia.show()

    #Updates settings for active view
    def updateSettings(self):
        if self.activeScene:
            view = self.sceneTabs.currentWidget()
            view.updateSettings()
            if view.type == 'circ':
                self.circularConfig = view.returnSettingsDict()
            if view.type == 'coverage':
                self.coverageConfig = view.returnSettingsDict()
            if view.type == 'karyogram':
                self.karyoConfig = view.returnSettingsDict()
            if view.type == 'heatmap':
                self.heatmapConfig = view.returnSettingsDict()

    def saveSettings(self):
        if self.activeScene:
            data.saveConfig("userSettings.conf",self.circularConfig,self.coverageConfig,self.karyoConfig,self.heatmapConfig)

    def resetSettings(self):
        (self.circularConfig,self.coverageConfig,self.karyoConfig,self.heatmapConfig) = data.readConfig("defaultSettings.conf")

    def selectChromosome(self,selected,deselected):
        view = self.sceneTabs.currentWidget()
        viewInd = self.views.index(view)
        selectedInds = selected.indexes()
        if selectedInds:
            selectedRow = selectedInds[0].row()
            self.viewChromosomes[viewInd] = selectedRow
            varWidget = view.createVariantWidget(selectedRow)
            self.dockWidget.widget().layout().addWidget(varWidget)
            oldWidget = self.dockWidget.widget().layout().takeAt(1).widget()
            oldWidget.deleteLater()
            self.dockWidget.updateGeometry()
            if view.type == 'coverage':
                #Connect selection of variant to mark the variant in the view
                varTable = varWidget.layout().itemAtPosition(1,0).widget()
                selModel = varTable.selectionModel()
                selModel.selectionChanged.connect(view.updatePlot)
                view.setActiveChromosome(selectedRow,varTable)
            if view.type == 'karyogram':
                varTable = varWidget.layout().itemAtPosition(1,0).widget()
                selModel = varTable.selectionModel()
                selModel.selectionChanged.connect(view.updateItems)
                view.setActiveChromosome(selectedRow,varTable)
            if view.type == 'circ':
                varTable = varWidget.layout().itemAtPosition(1,0).widget()
                selModel = varTable.selectionModel()
                selModel.selectionChanged.connect(view.initscene)
                view.setActiveChromosome(selectedRow,varTable)
