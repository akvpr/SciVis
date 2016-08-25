from PySide.QtGui import QApplication
import sys
import mainwin
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--export',type=str,nargs=4,help='Generate and export an image',
        metavar=('type', 'vcf', 'tab', 'chr'))
    args = parser.parse_args()

    if args.export:

        (diaType,vcfPath,tabPath,chromoName) = args.export
        app = QApplication(sys.argv)
        scivisInstance = mainwin.SciVisNoGUI(app)


        if diaType == 'circ':
            scivisInstance.newCirc(vcfPath,tabPath,chromoName)
            sys.exit(app.exec_())
        elif diaType == 'cov':
            scivisInstance.newCovDiagram(vcfPath,tabPath,chromoName)
            sys.exit(app.exec_())
        elif diaType == 'karyo':
            scivisInstance.newKaryogram(vcfPath,tabPath,chromoName)
            sys.exit(app.exec_())
        elif diaType == 'hmap':
            #Needs additional work for definig chromosomes and variant types, etc.
            pass
            #scivisInstance.newHeatmap(vcfPath,tabPath,chromoName)
            #sys.exit(app.exec_())
        else:
            print("type has to be one of: circ, cov, karyo, hmap")
    else:
        app = QApplication(sys.argv)
        sciVisWindow = mainwin.SciVisView()
        sys.exit(app.exec_())
