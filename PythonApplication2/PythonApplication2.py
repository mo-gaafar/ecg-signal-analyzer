from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit, QFileDialog, QScrollBar
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import numpy as np
import sys  # We need sys so that we can pass argv to QApplication
import os
import csv
from random import randint
import wfdb
filename = None
browsedfile = False

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)


        #Load the UI Page
        uic.loadUi('mainwindow.ui', self)
        #self.graphWidget = pg.PlotWidget()
        #self.setCentralWidget(self.graphWidget)
        self.filename = None
        #If No file opened, plot random points
        self.x = list(range(20))  # 20 time points
        self.y =[ 1 for _ in range(20)]  # 100 data points

        #p1 = win.addPlot(title="Basic array plotting", y=np.random.normal(size=100))

   
        #Anti aliasing for prettier lines
        pg.setConfigOptions(antialias = True)

        #Set Background
        self.graphWidget.setBackground('w')
        #Axis Labels
        styles = {"color": "#fff", "font-size": "20px"}
        self.graphWidget.setLabel("left", "Value", **styles)
        self.graphWidget.setLabel("bottom", "bottom text", **styles)

        pen = pg.mkPen(color=(255, 0, 0), width = 1)
        
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
        #timer to update plot every 10ms

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot_data)

        #Shows the grid
        self.graphWidget.showGrid(x=1,y=1)
        
        #Auto Pans with x value = 100


        self.graphWidget.setAutoPan(x=100, y=None)

        self.timer.stop()

        #Defining Buttons and GUI Events
        self.CounterX = 0
        self.ZoominCount = 0
        self.graphWidget.setLimits(xMin = 0)
        #self.buttonpause = self.findChild(QPushButton, "pauseButton")
        #self.buttonpause.clicked.connect(self.clickedBtn)

        self.buttonplay = self.findChild(QPushButton, "playButton")
        self.buttonplay.clicked.connect(self.clickedpBtn)

        self.buttonbrowse = self.findChild(QPushButton, "browseButton")
        self.buttonbrowse.clicked.connect(self.clickedbBtn)

        self.buttonzoomin = self.findChild(QPushButton,"zoominButton")
        self.buttonzoomin.clicked.connect(self.clickedzoominBtn)

        self.buttonzoomout = self.findChild(QPushButton,"zoomoutButton")
        self.buttonzoomout.clicked.connect(self.clickedzoomoutBtn)

        self.buttonFFT = self.findChild(QPushButton,"FFTButton")
        self.buttonFFT.clicked.connect(self.clickedFFTBtn)

        self.verticalScrollBar= self.findChild(QScrollBar, "verticalScrollBar")
        self.verticalScrollBar.sliderMoved.connect(self.sliderval1)

        self.horizonalScrollBar= self.findChild(QScrollBar, "horizontalScrollBar")
        self.horizontalScrollBar.sliderMoved.connect(self.sliderval2)

        self.show()

    def sliderval1(self):
        print (self.verticalScrollBar.value())
        self.graphWidget.setRange(yRange= (2*self.verticalScrollBar.value()-50,2*self.verticalScrollBar.value()))
        # self.graphWidget.translateBy(y=10*self.verticalScrollBar.value()) 
        

    def sliderval2(self):
        print(self.horizontalScrollBar.value())
        self.graphWidget.setRange(xRange= ((self.CounterX/100)*self.horizontalScrollBar.value(),(self.CounterX/100)*self.horizontalScrollBar.value()+100))

    def clickedpBtn(self):
      
        # if button is checked 
        if self.buttonplay.isChecked():   
            print("started")
            #starts the graph
            self.timer.start()
            self.graphWidget.setAutoPan(x=100, y=None)

        # if it is unchecked 
        else: 
            print("stopped")
            #stops the graph
            self.timer.stop() 

        self.show()
        
    def clickedbBtn(self): #Browse Button triggered
        self.filename = QFileDialog.getOpenFileName()[0]
        print(self.filename)

        self.filename = self.filename[:-4] #removes .hea ending

        record = wfdb.rdrecord(self.filename)
        print(record.sig_len) #Prints the length of the selected signal
        self.sigLength = record.sig_len #init signal length variable

        self.show

    def clickedzoominBtn(self):
        print("zoomin")
        self.ZoominCount+=10
        print(self.ZoominCount)
        #buggy
        self.graphWidget.setRange(xRange= (0,self.sigLength-self.ZoominCount))
        self.show

    def clickedzoomoutBtn(self):
        print("zoomout")
        self.ZoominCount = 0
        #self.graphWidget.setRange(xRange= (0,1000))
        self.graphWidget.autoRange()

    def clickedFFTBtn(self):  
        # if button is checked 
        if self.buttonFFT.isChecked(): 
            #Turns Fourier Transform View On
            self.graphWidget.getPlotItem().ctrl.fftCheck.setChecked(True) 
            self.graphWidget.autoRange()
        # if it is unchecked 
        else: 
            #Turns Fourier Transform View Off
            self.graphWidget.getPlotItem().ctrl.fftCheck.setChecked(False)  
            self.graphWidget.autoRange()
            self.graphWidget.setAutoPan(x=100, y=None)
    
    def update_plot_data(self):
       if self.filename == None:
        # self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

       # self.y = self.y[1:]  # Remove the first  x element
        self.y.append(1)  # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

       else:
        self.CounterX +=1
        self.x.append(self.x[-1] + 1)
        record = wfdb.rdrecord(self.filename )
        d_signal = record.adc()
        record.adc(inplace = True)
        
        if self.sigLength > self.CounterX:
            self.y.append(record.d_signal[self.CounterX][0])
            self.data_line.setData(self.x,self.y)
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()
