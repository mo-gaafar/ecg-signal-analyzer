from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit, QFileDialog, QScrollBar, QComboBox
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import numpy as np
import sys  # We need sys so that we can pass argv to QApplication
import os
import csv
from random import randint
import wfdb
from scipy.signal import butter,filtfilt

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs): #Initializes the Program
        super(MainWindow, self).__init__(*args, **kwargs)


        #Load the UI Page
        uic.loadUi('mainwindow.ui', self)
        #self.graphWidget = pg.PlotWidget()
        #self.setCentralWidget(self.graphWidget)
        self.filename = None
        self.filterStatus = 0
       #initializing the 4 Plotting lines

        self.x = list(range(20))  # 20 time points
        self.y =[ 1 for _ in range(20)]  # 100 data points
        
        self.x1 = list(range(20))
        self.y1 = [ 1 for _ in range(20)]

        self.x2 = list(range(20))
        self.y2 = [ 1 for _ in range(20)]

        self.x3 = list(range(20))
        self.y3 = [ 1 for _ in range(20)]

        #Anti aliasing for prettier lines
        #pg.setConfigOptions(antialias = True)

        #Set Background
        self.graphWidget.setBackground('w')
        #Axis Labels
        styles = {"color": "#fff", "font-size": "20px"}
        self.graphWidget.setLabel("left", "Value", **styles)
        self.graphWidget.setLabel("bottom", "bottom text", **styles)

        pen = pg.mkPen(color=(255, 0, 0), width = 1)

        #Plot Lines
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen) #Orignial Data
        self.band_line = self.graphWidget.plot(self.x1, self.y1, pen = pg.mkPen(color = (0,0,255),width = 1)) #Band Pass  filter line
        self.low_line = self.graphWidget.plot(self.x2, self.y2, pen = pg.mkPen(color = (0,0,255),width = 1)) #Low Pass filter line
        self.high_line = self.graphWidget.plot(self.x3, self.y3, pen = pg.mkPen(color = (0,0,255),width = 1)) #High Pass filter line

        #Hiding Filter Lines
        self.band_line.hide()
        self.low_line.hide()
        self.high_line.hide()

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
        self.MaxY = 100
        self.MinY = 0
        self.CounterX = 0
        self.ZoominCount = 0
        self.graphWidget.setLimits(xMin = 0)
        self.sigLength = 100
        self.filterIndex = 0

        # Filter requirements.
        self.T = 5         # Sample Period
        self.fs = 300.0       # sample rate, Hz
        self.cutoff = 100     # desired cutoff frequency of the filter, Hz ,      slightly higher than actual 1.2 Hz
        self.nyq = 0.5 * self.fs  # Nyquist Frequency
        self.order = 2       # sin wave can be approx represented as quadratic
        self.n = int(self.T * self.fs) # total number of samples

        self.buttonplay = self.findChild(QPushButton, "playButton")
        self.buttonplay.clicked.connect(self.clickedpBtn)

        self.buttonFilter = self.findChild(QPushButton, "filterButton")
        self.buttonFilter.clicked.connect(self.clickedfilterBtn)

        self.comboFilter = self.findChild(QComboBox, "comboBox")

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
    
    def plot_hide(self): #Shows the relevant Data Lines
       if self.filterIndex == 0:
            self.data_line.show()
            self.band_line.hide()
            self.low_line.hide()
            self.high_line.hide()

       if self.filterIndex == 1:
            self.data_line.hide()
            self.band_line.show()
            self.low_line.hide()
            self.high_line.hide()

       if self.filterIndex == 2:
            self.data_line.hide()
            self.band_line.hide()
            self.low_line.show()
            self.high_line.hide()

       if self.filterIndex == 3:
            self.data_line.hide()
            self.band_line.hide()
            self.low_line.hide()
            self.high_line.show()
            
    def clickedfilterBtn(self): #Shows Desired Filter Plot
        self.filterIndex = self.comboFilter.currentIndex()
        print("filter number:",self.filterIndex," applied!")
        self.plot_hide()

    def clickedpBtn(self):
      
        # if button is checked 
        if self.buttonplay.isChecked():   
            print("started")
            #starts the graph
            self.timer.start()
            self.graphWidget.setAutoPan(x=100, y=(self.MinY,self.MaxY))

        # if it is unchecked 
        else: 
            print("stopped")
            #stops the graph
            self.timer.stop() 

        self.show()

    def butter_lowpass_filter(self,data): #Butterworth Filter
        self.normal_cutoff = self.cutoff / self.nyq
        # Get the filter coefficients 
        b,a = butter(self.order, self.normal_cutoff, btype='lowpass', analog=False)
        y = filtfilt(b, a, data)
        return y
        
    def clickedbBtn(self): #Browse Button triggered
        self.filename = QFileDialog.getOpenFileName()[0]
        print(self.filename)

        self.filename = self.filename[:-4] #removes .hea ending
        #Original Signal Processing, ADC
        self.record = wfdb.rdrecord(self.filename )
        self.d_signal = self.record.adc()
        self.record.adc(inplace = True)
        self.MaxY = max(self.d_signal[:][0]) #Maximum Y Value in the ECG File
        self.MinY = min(self.d_signal[:][0]) #Minimum Y Value in the ECG File

        #Low Pass filter
        self.low_signal = self.butter_lowpass_filter(self.d_signal)

        print(self.record.sig_len) #Prints the length of the Original signal
        self.sigLength = self.record.sig_len #init signal length variable

        self.CounterX = 0 #resets array counter whenever a new file is selected

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

    
    def update_plot_data(self): #Live Data Plotting
       if self.filename == None: #if no file is imported

        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
        self.x1.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
        self.x2.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.
        self.x3.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.


        self.y.append(1)  # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.


       else:
        self.CounterX +=1
        self.x.append(self.x[-1] + 1)
        self.x2.append(self.x2[-1] + 1)

        if self.sigLength > self.CounterX: #Updates 4 Lines, unfiltered, Smooth Filter, Low Pass Filter, High Pass Filter
                self.y.append(self.record.d_signal[self.CounterX][0])
                self.data_line.setData(self.x,self.y)

                #self.y1.append(self.smoothfiltered)
                #self.smooth_line.setData(self.x1,self.y1)
                self.y2.append(self.low_signal[self.CounterX][0])
                self.low_line.setData(self.x2,self.y2)
        
            
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()
