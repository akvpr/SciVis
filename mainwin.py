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
        self.resize(QDesktopWidget().availableGeometry(self).size())
        #Center the main window on the user's screen
        frameGeo = self.frameGeometry()
        desktopCenter = QDesktopWidget().availableGeometry().center()
        frameGeo.moveCenter(desktopCenter)
        self.move(frameGeo.topLeft())
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
        #Create actions for menus and toolbars, connect to functions
        self.newCircAct = QAction('New circular diagram',self)
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
        self.saveDatasetAct = QAction('Save dataset',self)
        self.saveDatasetAct.triggered.connect(self.saveDataset)
        self.viewSettingsAct = QAction('Settings',self)
        self.viewSettingsAct.triggered.connect(self.viewSettings)
        #Create menus, and add actions
        self.createColorModel()
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('File')
        self.fileMenu.addAction(self.newCircAct)
        self.fileMenu.addAction(self.newCovDiagramAct)
        self.fileMenu.addAction(self.newKaryogramAct)
        self.fileMenu.addAction(self.newHeatmapAct)
        self.fileMenu.addAction(self.viewDatasetsAct)
        self.fileMenu.addAction(self.saveDatasetAct)
        self.fileMenu.addAction(self.viewSettingsAct)
        self.fileMenu.addAction(self.exportImageAct)
        self.fileMenu.addAction(self.exitAct)
        #Create a tab widget handling active scenes
        self.sceneTabs = QTabWidget(self)
        self.sceneTabs.currentChanged.connect(self.viewChanged)
        self.setCentralWidget(self.sceneTabs)
        self.views = []
        self.initDock()
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
            viewPixMap = QPixmap.grabWidget(view)
            viewPixMap.save(savePath)

    #Checks if an active scene is running and if it's ok to continue (closing scene?)
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
        'vcfName':vcfName,'tabName':tabName, 'cytoTab':cytoTab,'setName':setname}
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
                    reader = data.Reader()
                    self.statusBar().showMessage("Reading TAB..")
                    reader.readTab(tabFile)
                    self.statusBar().showMessage("Reading VCF..")
                    reader.readVCFFile(vcfFile)
                    self.statusBar().showMessage("Reading cytoband file..")
                    reader.readCytoTab(cytoFile)
                    self.statusBar().clearMessage()
                    #Remove current item from model, create a new item, insert item
                    oldItem = self.datasetModel.itemFromIndex(index)
                    setName = oldItem.data()["setName"]
                    oldRow = index.row()
                    self.datasetModel.removeRow(oldRow)
                    self.createDatasetItem(reader, setName)

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

    #Handles toolbar switching etc if the view is changed
    def viewChanged(self,viewIndex):
        view = self.sceneTabs.currentWidget()
        #Remove current toolbar and close open windows for last open view
        try:
            self.lastActiveView.closeOpenWindows()
            self.removeToolBar(self.tools)
            self.tools.hide()
            self.tools.deleteLater()
        except:
            pass
        self.lastActiveView = view
        #Add this view's chromosome info widget
        infoWidget = view.returnChromoInfoWidget()
        #Connect selection of chromosome to update variant view
        chTable = infoWidget.layout().itemAtPosition(0,0).widget()
        selModel = chTable.selectionModel()
        selModel.selectionChanged.connect(self.updateVariantView)
        self.dockTabs.removeTab(0)
        self.dockTabs.insertTab(0,infoWidget,"Chromosomes")
        self.dockTabs.setCurrentIndex(0)
        #Add appropriate toolbar for scene type
        viewType = view.type
        if viewType == "circ":
            view.updateToggles()
            self.tools = self.addToolBar('Circ tools')
            self.showChInfoAct = QAction('Chromosomes',self)
            self.showChInfoAct.triggered.connect(view.showChInfo)
            self.updateSceneAct = QAction('Update diagram',self)
            self.updateSceneAct.triggered.connect(view.initscene)
            self.toggleCoverageAct = QAction('Toggle coverage',self)
            self.toggleCoverageAct.triggered.connect(view.toggleCoverage)
            self.addImageAct = QAction('Add Image to plot', self)
            self.addImageAct.triggered.connect(view.addImage)
            self.importColorTabAct = QAction('Color regions with file', self)
            self.importColorTabAct.triggered.connect(view.importColorTab)
            self.tools.addAction(self.showChInfoAct)
            self.tools.addAction(self.updateSceneAct)
            self.tools.addAction(self.toggleCoverageAct)
            self.tools.addAction(self.addImageAct)
            self.tools.addAction(self.importColorTabAct)
            self.tools.show()
        if viewType == "coverage":
            self.tools = self.addToolBar('Coverage tools')
            self.showChInfoAct = QAction('Chromosomes',self)
            self.showChInfoAct.triggered.connect(view.showChInfo)
            self.addPlotAct = QAction('Add subplot', self)
            #self.addPlotAct.triggered.connect(view.addChromoPlot)
            self.updateLayoutAct = QAction('Update layout', self)
            #self.updateLayoutAct.triggered.connect(view.arrangePlots)
            self.tools.addAction(self.showChInfoAct)
            self.tools.addAction(self.addPlotAct)
            self.tools.addAction(self.updateLayoutAct)
            self.tools.show()
        if viewType == "karyogram":
            view.updateToggles()
            self.tools = self.addToolBar('Karyogram tools')
            self.updateKaryogramAct = QAction('Update karyogram', self)
            self.updateKaryogramAct.triggered.connect(view.updateItems)
            self.resetLayoutAct = QAction('Reset layout', self)
            self.resetLayoutAct.triggered.connect(view.resetLayout)
            self.showChInfoAct = QAction('Chromosomes',self)
            self.showChInfoAct.triggered.connect(view.showChInfo)
            self.tools.addAction(self.showChInfoAct)
            self.tools.addAction(self.resetLayoutAct)
            self.tools.addAction(self.updateKaryogramAct)
            self.tools.show()
        if viewType == "heatmap":
            self.tools = self.addToolBar('Coverage tools')
            self.showChInfoAct = QAction('Chromosomes',self)
            self.showChInfoAct.triggered.connect(view.showChInfo)
            self.addHeatmapAct = QAction('Add heatmap', self)
            self.addHeatmapAct.triggered.connect(view.addHeatmap)
            self.tools.addAction(self.showChInfoAct)
            self.tools.addAction(self.addHeatmapAct)
            self.tools.show()

    #Creates and initializes a new circular diagram
    def newCirc(self):

        self.statusBar().showMessage("Initializing new circular diagram..")
        selectedData = self.selectDataset()
        self.statusBar().clearMessage()
        #Initialize scene if a valid dataset has been returned
        if selectedData is not None:
            self.activeScene = True
            view = circ.CircView(selectedData,self)
            self.views.append(view)
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
            view = coverage.CoverageView(selectedData,self)
            self.views.append(view)
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
            view = karyogram.KaryogramView(selectedData,self)
            self.views.append(view)
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
            view = heatmap.HeatmapView(selectedData,self)
            self.views.append(view)
            tabIndex = self.sceneTabs.addTab(view,"Heatmap")
            self.sceneTabs.setCurrentIndex(tabIndex)
            self.show()

    def createColorModel(self):
        #Model allowing stain colors to be changed globally
        self.stainNames = ['acen','gneg','gpos100','gpos25','gpos50','gpos75','gvar','stalk']
        self.stainColors = {'acen':Qt.darkRed, 'gneg':Qt.white,'gpos100':Qt.black,'gpos25':Qt.lightGray,'gpos50':Qt.gray,
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
        applyButton = QPushButton('Apply', settingsDia)
        applyButton.clicked.connect(settingsDia.accept)
        applyButton.clicked.connect(self.updateSettings)
        settingsLayout.addWidget(stackList,0,0)
        settingsLayout.addWidget(settingsStack,0,1)
        settingsLayout.addWidget(applyButton,1,0,1,1)
        settingsDia.setWindowTitle("Settings")
        settingsDia.setLayout(settingsLayout)
        settingsDia.show()

    #Should update settings only on apply (currently updates on item change and color pick).
    def updateSettings(self):
        pass

    def updateVariantView(self,selected,deselected):
        view = self.sceneTabs.currentWidget()
        selectedRow = selected.indexes()[0].row()
        varWidget = view.createVariantWidget(selectedRow)
        self.dockWidget.widget().layout().addWidget(varWidget)
        oldWidget = self.dockWidget.widget().layout().takeAt(1).widget()
        oldWidget.deleteLater()
        self.dockWidget.updateGeometry()
