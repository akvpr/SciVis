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

        #Check if file locations are valid, try to read.
        #Create dataset item
        #Create circ.CircView etc
        #Export as in mainwin?

        if diaType == 'circ':
            pass
        elif diaType == 'cov':
            pass
        elif diaType == 'karyo':
            pass
        elif diaType == 'hmap':
            pass
        else:
            print("type has to be one of: circ, cov, karyo, hmap")
    else:
        app = QApplication(sys.argv)
        sciVisWindow = mainwin.SciVisView()
        sys.exit(app.exec_())
