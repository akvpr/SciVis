from PySide.QtCore import *
from PySide.QtGui import *
import data

#Reads a bed file and adds a list of bed elements for each chromosome
def createBedDict():
    #Construct a dict to contain all relevant lines for each chromosome
    #Each line should have final format [bed,start,end,text1...]
    newBedDict = {}
    bedFile = QFileDialog.getOpenFileName(None,"Specify bed file",QDir.currentPath(),
    "bed files (*.bed *.txt *.tab)")[0]
    if bedFile:
        reader = data.Reader()
        bedLines = reader.readGeneralTab(bedFile)
        bedFileName = bedFile.split('/')[-1].replace('.bed','').replace('.txt','').replace('.tab','')
        for line in bedLines:
            chrName = line[0]
            #If this is a new chrName, construct empty list
            if not chrName in newBedDict:
                newBedDict[chrName] = []
            #Add the bed name as first element to identify this list, remove chr field
            lineElements = [bedFileName]
            line.pop(0)
            lineElements.extend(line)
            newBedDict[chrName].append(lineElements)
    return newBedDict

#Creates and returns data model for variants in given chromosome
def createVariantInfo(chromo):
    varModel = QStandardItemModel()
    topstring = ['Active','TYPE', 'START', 'END', 'GENE(S)', 'CYTOBAND', 'Rank Score']
    varModel.setHorizontalHeaderLabels(topstring)
    #Adding variant info to a list
    for variant in chromo.variants:
        infoitem = []
        #this is a check for displaying a variant or not
        dispCheckItem = QStandardItem()
        dispCheckItem.setCheckable(False)
        if variant[9]:
            dispCheckItem.setCheckState(Qt.Checked)
        else:
            dispCheckItem.setCheckState(Qt.Unchecked)
        infoitem.append(dispCheckItem)
        #this is event_type in the variant
        infoitem.append(QStandardItem(variant[4]))
        #this is posA in the variant
        startItem = QStandardItem()
        #set data with start as role 0
        startItem.setData(variant[1],0)
        infoitem.append(startItem)
        #this is posB or chrB: posB in the variant (if interchromosomal)
        if variant[0] is not variant[2]:
            endText = str(variant[2]) + ": " + str(variant[3])
            endItem = QStandardItem()
            #if chrB, set this as data with role 32, end as role 33
            endItem.setData(variant[2],32)
            endItem.setData(variant[3],33)
        else:
            endText = str(variant[3])
            endItem = QStandardItem()
            #if no chrB, set 0 as role 32, end as role 33
            endItem.setData(str(0),32)
            endItem.setData(variant[3],33)
        endItem.setData(endText,Qt.DisplayRole)
        infoitem.append(endItem)
        #this is allGenes in the variant
        infoitem.append(QStandardItem(variant[7]))
        #this is cband in the variant
        infoitem.append(QStandardItem(variant[8]))
        #this is rankscore in the variant
        infoitem.append(QStandardItem(variant[10]))
        varModel.appendRow(infoitem)
    return varModel

#Creates and returns a popup containing variant info in a table.
def createVariantDia(chromo,parent):
    sourceModel = createVariantInfo(chromo)
    viewVarDia = QDialog(parent)
    viewVarDia.setWindowTitle("Variants in contig " + chromo.name)
    varList = QTableView()
    #Create button for activation of variants
    varButton = QPushButton('Toggle selected variant(s)', viewVarDia)
    varButton.clicked.connect(lambda: toggleVariants(chromo, varList))
    varList.setSortingEnabled(True)
    varList.setMinimumSize(700,400)
    varList.verticalHeader().hide()
    varList.setEditTriggers(QAbstractItemView.NoEditTriggers)
    proxyModel = VariantSortModel()
    proxyModel.setSourceModel(sourceModel)
    varList.setModel(proxyModel)
    varList.resizeColumnToContents(1)
    varList.resizeColumnToContents(2)
    viewVarDia.layout = QGridLayout(viewVarDia)
    viewVarDia.layout.addWidget(varList,0,0)
    viewVarDia.layout.addWidget(varButton,1,0)
    return viewVarDia

#Creates and returns a widget containing variant info in a table.
def createVariantWidget(chromo):
    sourceModel = createVariantInfo(chromo)
    varList = QTableView()
    #Create button for activation of variants
    varButton = QPushButton('Toggle selected variant(s)')
    varButton.clicked.connect(lambda: toggleVariants(chromo, varList))
    varList.setSortingEnabled(True)
    varList.verticalHeader().hide()
    varList.setEditTriggers(QAbstractItemView.NoEditTriggers)
    proxyModel = VariantSortModel()
    proxyModel.setSourceModel(sourceModel)
    varList.setModel(proxyModel)
    varList.resizeColumnToContents(1)
    varList.resizeColumnToContents(2)
    labelText = "Variants in " + chromo.name
    chromoLabel = QLabel(labelText)
    varLayout = QGridLayout()
    varLayout.addWidget(chromoLabel,0,0)
    varLayout.setAlignment(chromoLabel,Qt.AlignHCenter)
    varLayout.addWidget(varList,1,0)
    varLayout.addWidget(varButton,2,0)
    varWidget = QWidget()
    varWidget.setLayout(varLayout)
    return varWidget

#Toggles individual variants on and off
def toggleVariants(chromo, varView):
    selectedProxyIndexes = varView.selectedIndexes()
    #Selected indexes are indexes in proxy model, so translate to source indexes
    selectedIndexes = [varView.model().mapToSource(proxyIndex) for proxyIndex in selectedProxyIndexes]
    selectedRows = [index.row() for index in selectedIndexes]
    selectedRows = set(selectedRows)
    for row in selectedRows:
        dispVarItem = varView.model().sourceModel().item(row,0)
        if chromo.variants[row][9]:
            dispVarItem.setCheckState(Qt.Unchecked)
            chromo.variants[row][9] = False
        else:
            dispVarItem.setCheckState(Qt.Checked)
            chromo.variants[row][9] = True
    chromo.createConnections()

#Toggles individual variants on and off
def returnVariants(chromo, varView):
    selectedProxyIndexes = varView.selectedIndexes()
    #Selected indexes are indexes in proxy model, so translate to source indexes
    selectedIndexes = [varView.model().mapToSource(proxyIndex) for proxyIndex in selectedProxyIndexes]
    selectedRows = [index.row() for index in selectedIndexes]
    selectedRows = set(selectedRows)
    selectedVariants = []
    for row in selectedRows:
        selectedVariants.append(chromo.variants[row])
    return selectedVariants

#Adds a variant to selected chromosomes. Some models still have to be updated.
#Not sure how to best handle input yet.
def addVariant(chromo,chromosomes):
    addVariantDialog = QDialog()
    addVariantDialog.setWindowTitle("Add variant in contig " + chromo.name)
    applyButton = QPushButton('Ok', addVariantDialog)
    applyButton.clicked.connect(addVariantDialog.accept)
    cancelButton = QPushButton('Cancel', addVariantDialog)
    cancelButton.clicked.connect(addVariantDialog.reject)
    locBoxValidator = QIntValidator()
    locBoxValidator.setBottom(0)
    locABox = QLineEdit()
    locBBox = QLineEdit()
    locABox.setValidator(locBoxValidator)
    locBBox.setValidator(locBoxValidator)
    chromoBox = QComboBox()
    chromoStrings = [chromo.name for chromo in chromosomes if not "GL" in chromo.name]
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

#Custom class of proxy model to handle custom sorting of variants
class VariantSortModel(QSortFilterProxyModel):

    def sort(self, column, order):
        if column != 0:
            QSortFilterProxyModel.sort(self,column,order)

    #Return true if left less than right, otherwise false
    #left and right are QModelIndexes, taking displayrole data by default
    def lessThan(self, left, right):
        if left.column() == 1:
            #sort alphabetically by TYPE
            leftData = self.sourceModel().data(left)
            rightData = self.sourceModel().data(right)
            return leftData < rightData
        elif left.column() == 2:
            #sort by START as ints
            leftData = int(self.sourceModel().data(left,0))
            rightData = int(self.sourceModel().data(right,0))
            return leftData < rightData
        elif left.column() == 3:
            #if the column is 2, i.e. END, see if role 32 data for both items is > 0 (both have chrB)
            #if only one of the items has chrB, put item with chrB as less than
            leftData = self.sourceModel().data(left,32)
            rightData = self.sourceModel().data(right,32)
            if leftData != '0' and rightData != '0':
                #If both are digits (i.e. not X,Y,GL.. etc), compare as ints
                #If only one is digit put digit chr as the lesser data
                if leftData.isdigit() and rightData.isdigit():
                    return int(leftData) < int(rightData)
                elif leftData.isdigit():
                    return True
                elif rightData.isdigit():
                    return False
                else:
                    return leftData < rightData
            elif leftData != '0':
                return True
            elif rightData != '0':
                return False
            else:
                #If no item has chrB, sort by end as an int
                leftData = int(self.sourceModel().data(left,33))
                rightData = int(self.sourceModel().data(right,33))
                return leftData < rightData
        elif left.column() == 4 or left.column() == 5:
            #sort alphabetically by GENE(S) or CYTOBAND
            leftData = self.sourceModel().data(left)
            rightData = self.sourceModel().data(right)
            return leftData < rightData
        elif left.column() == 6:
            #sort by Rank Score. Format is x:y Second value is priority.
            leftData = self.sourceModel().data(left)
            rightData = self.sourceModel().data(right)
            leftSecondValue = int(leftData.split(':')[1])
            rightSecondValue = int(rightData.split(':')[1])
            return leftSecondValue < rightSecondValue
        else:
            leftData = self.sourceModel().data(left)
            rightData = self.sourceModel().data(right)
            return leftData < rightData
