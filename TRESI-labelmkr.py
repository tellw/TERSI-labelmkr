try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
import sys
import os.path
from functools import partial
from toolBar import ToolBar
from canvas import Canvas
import cv2
import numpy as np
import urllib
import requests
import configparser
import xml.etree.ElementTree as ET
from PIL import Image

#os.chdir('H:/TERSI-labelmkr/TERSI-labelmkr-v1.0')
#print(os.getcwd())
__appname__ = 'TERSI-labelmkr'

def newIcon(icon):
    if not os.path.exists('./icons/'+icon+'.png'):
        downloadIcons(icon)
    return QIcon('./icons/' + icon + '.png')

#将QAction属性全建立完
def newAction(parent, text, slot=None, shortcut=None, icon=None,
              tip=None, checkable=False, enabled=True):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QAction(text, parent)
    if icon is not None:
        a.setIcon(newIcon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    return a

class MainWindow(QMainWindow):
    def __init__(self, defaultFilename=None):
        super(MainWindow, self).__init__()
        '''with fopen('log.txt', 'r') with f:
            self.targetFile = f.readline().strip('\n')
            targetSaveDir = f.readline().strip('\n')'''
        self.resize(800, 600)
        self.setWindowTitle(__appname__)
        cf = configparser.ConfigParser()
        cf.read('./TERSI-labelmkr.ini')
        self.lastOpenDir = cf.get('env', 'lastOpenDir')
        #with open('config/lastOpenDir.txt', 'r') as f:
            #self.lastOpenDir = f.readline().strip('\n')
        self.dirname = None
        print('you have input some parameters: '+str(defaultFilename))
        self.filePath = defaultFilename
        self.mImgList = []
        '''if(targetSaveDir == 'None'):
            self.defaultSaveDir = None
        else:'''
        self.defaultSaveDir = cf.get('env', 'defaultSaveDir')
        self.cropSaveDir = cf.get('env', 'cropSaveDir')
        '''with open('config/defaultSaveDir.txt', 'r') as f:
            self.defaultSaveDir =  f.readline().strip('\n')'''
        self.filename = None
        #最近打开文件
        self.recentFiles = []
        self.maxRecent = 7
        self.picw = 0
        self.pich = 0
        #QAction关联到QToolBar并以QToolButton显示出来
        action = partial(newAction, self)
        open_ = action('&Open', self.openFile,
                      'Ctrl+O', 'open', u'Open image or label file')
        opendir = action('&Open Dir', self.openDirDialog,
                         'Ctrl+u', 'opendir', u'Open Dir')
        changeSavedir = action('&Change Save Dir', self.changeSavedirDialog,
                               'Ctrl+r', 'changesavedir', u'Change default saved Annotation dir')
        openNextImg = action('&Next Image', self.openNextImg,
                             'd', 'next', u'Open Next')
        openPrevImg = action('&Prev Image', self.openPrevImg,
                             'a', 'prev', u'Open Prev')
        verify = action('&Verify Image', self.verifyImg,
                        'space', 'verify', u'Verify Image')
        test = action('&Test Label', self.test, 't', 'test', u'Test Label')
        test_sample = action('&Test Sample', self.testSample,'s','testsample', u'Test Sample')
        delete_img = action('&Delete Img', self.delImg, 'del', 'delimg', u'Delete Img')
        crop_and_save = action('&Crop And Save', self.cropAndSave, 'c', 'cropandsave', u'Crop And Save')
        clear = action('&Clear', self.clear, 'e', 'clear', u'Clear')
        tools = {open_ : 'Open', opendir : 'Open Dir', changeSavedir : 'Change Save Dir',
                 openNextImg : 'Next Image', openPrevImg : 'Prev Image', verify : 'Verify Image',
                 test: 'Test', test_sample: 'Test Sample', delete_img: 'Delete Img', crop_and_save: 'Crop And Save',
                 clear: 'Clear'}
        tools = tools.items()
        toolbar = ToolBar('tools')
        toolbar.setObjectName(u'%s ToolBar' % 'tools')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        for act, title in tools:
            '''
            toolbar = ToolBar(title)
            toolbar.setObjectName(u'%s ToolBar' % title)
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            toolbar.addAction(act)
            self.addToolBar(Qt.LeftToolBarArea, toolbar)
            '''
            if act:
                toolbar.addAction(act)
            self.addToolBar(Qt.LeftToolBarArea, toolbar)
        #中间显示图片区域
        self.canvas = Canvas(parent=self)
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollArea = scroll
        self.setCentralWidget(scroll)
        #右侧文件列表
        self.fileListWidget = QListWidget()
        self.fileListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.filedock = QDockWidget(u'File List', self)
        self.filedock.setObjectName(u'Files')
        self.filedock.setWidget(fileListContainer)
        self.addDockWidget(Qt.RightDockWidgetArea, self.filedock)
        self.filedock.setFeatures(QDockWidget.DockWidgetFloatable)
        #状态栏
        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()
        self.labelCoordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.labelCoordinates)
        print(self.filePath)
        if self.filePath:
            if len(self.filePath) == 1:
                if os.path.isdir(self.filePath[0]):
                    self.importDirImages(self.filePath[0])
                elif os.path.isfile(self.filePath[0]):
                    self.mImgList = self.filePath
                    print('opening the file '+self.filePath[0])
                    for imgPath in self.mImgList:
                        item = QListWidgetItem(imgPath)
                        self.fileListWidget.addItem(item)
                    self.loadFile(self.filePath[0])
            elif len(self.filePath) > 1:
                self.mImgList = self.filePath
                for imgPath in self.mImgList:
                    item = QListWidgetItem(imgPath)
                    self.fileListWidget.addItem(item)
                self.loadFile(self.mImgList[0])
        else:
            if os.path.exists(self.lastOpenDir):
                messageBox = QMessageBox()
                messageBox.setWindowTitle('询问框标题')
                messageBox.setText('是否载入上次打开的图片目录？')
                buttonY = messageBox.addButton('确定', QMessageBox.YesRole)
                buttonN = messageBox.addButton('取消', QMessageBox.NoRole)
                messageBox.exec_()
                if messageBox.clickedButton() == buttonY:
                    self.importDirImages(self.lastOpenDir)
        if os.path.exists(self.defaultSaveDir):
            print('your labels\' default save dir is ', self.defaultSaveDir)

    def resetState(self):
        self.filePath = None
        self.imageData = None
        self.canvas.resetState()
        self.labelCoordinates.clear()

    def errorMessage(self, title, message):
        return QMessageBox.critical(self, title, '<p><b>%s</b></p>%s' % (title, message))

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.adjustSize()
        self.canvas.update()
        
    def addRecentFile(self, filePath):
        if filePath in self.recentFiles:
            self.recentFiles.remove(filePath)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filePath)
        
    def loadFile(self, filePath=None):
        self.resetState()
        self.canvas.setEnabled(False)
        if filePath is None or len(filePath) == 0:
            pass
        else:
            print('loading '+filePath)
            self.filename = os.path.split(filePath)[-1]
            if self.fileListWidget.count() > 0:
                index = self.mImgList.index(filePath)
                fileWidgetItem = self.fileListWidget.item(index)
                fileWidgetItem.setSelected(True)
            if os.path.exists(filePath):
                self.imageData = read(filePath, None)
                self.canvas.verified = False
                self.filePath = filePath
            image = QImage.fromData(self.imageData)
            if image.isNull():
                self.errorMessage(u'Error opening file', u"<p>Make sure <i>%s</i> is a valid image file." % filePath)
                self.status("Error reading %s" % filePath)
            else:
                self.status("Loaded %s" % os.path.basename(filePath))
                self.image = image
                self.im = open_img(filePath)
                self.pich, self.picw = self.im.shape[:2]
                self.canvas.loadPixmap(QPixmap.fromImage(image))
                self.canvas.setEnabled(True)
                self.paintCanvas()
                #self.addRecentFile(self.filePath)
                self.setWindowTitle(__appname__ + ' ' + filePath)
                self.canvas.setFocus(True)
        
    def openFile(self):
        path = os.path.dirname(self.filePath) if self.filePath else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats)
        filename, _ = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                self.mImgList = filename
                filename = filename[0]
            else:
                self.mImgList = [filename]
            print('opening the file '+filename)
            self.fileListWidget.clear()
            for imgPath in self.mImgList:
                item = QListWidgetItem(imgPath)
                self.fileListWidget.addItem(item)
            self.loadFile(filename)

    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = os.path.join(root, file)
                    path = os.path.abspath(relativePath)
                    images.append(path)
        images.sort(key=lambda x: x.lower())
        return images

    def openNextImg(self):
        if len(self.mImgList) <= 0:
            return
        filename = None
        if self.filePath is None:
            filename = self.mImgList[0]
        else:
            currIndex = self.mImgList.index(self.filePath)
            if currIndex + 1 < len(self.mImgList):
                filename = self.mImgList[currIndex + 1]
        if filename:
            self.loadFile(filename)
            
    def importDirImages(self, dirpath):
        self.lastOpenDir = dirpath
        cf = configparser.ConfigParser()
        cf.read('./TERSI-labelmkr.ini')
        cf.set('env', 'lastOpenDir', self.lastOpenDir)
        with open('./TERSI-labelmkr.ini', 'w+') as f:
            cf.write(f)
        self.dirname = dirpath
        self.filePath = None
        self.fileListWidget.clear()
        self.mImgList = self.scanAllImages(dirpath)
        self.openNextImg()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.fileListWidget.addItem(item)

    def openDirDialog(self):
        if self.lastOpenDir != 'None' and os.path.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = os.path.dirname(self.filePath) if self.filePath else '.'
        #print(defaultOpenDirPath)
        targetDirPath = QFileDialog.getExistingDirectory(self, '%s - Open Directory' % __appname__,
                                                         defaultOpenDirPath, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        self.importDirImages(targetDirPath)

    def changeSavedirDialog(self):
        if self.defaultSaveDir != 'None' and os.path.exists(self.defaultSaveDir):
            path = self.defaultSaveDir
        else:
            path = '.'
        dirpath = QFileDialog.getExistingDirectory(self, '%s - Save xml to the directory' % __appname__, path,
                                                   QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dirpath is not None and len(dirpath) > 1:
            self.defaultSaveDir = dirpath
        print('you have chosen save dir: '+self.defaultSaveDir)
        cf = configparser.ConfigParser()
        cf.read('./TERSI-labelmkr.ini')
        cf.set('env', 'defaultSaveDir', self.defaultSaveDir)
        with open('./TERSI-labelmkr.ini', 'w+') as f:
            cf.write(f)
        self.statusBar().showMessage('%s . Annotation will be saved to %s' % ('Change saved folder',
                                                                              self.defaultSaveDir))
        self.statusBar().show()

    def cropSavedirDialog(self):
        if self.cropSaveDir != 'None' and os.path.exists(self.cropSaveDir):
            path = self.cropSaveDir
        else:
            path = '.'
        dirpath = QFileDialog.getExistingDirectory(self, '%s - Save the section to the directory' % __appname__, path,
                                                   QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dirpath is not None and len(dirpath) > 1:
            self.cropSaveDir = dirpath
        print('you have chosen cropped pic save dir: '+self.cropSaveDir)
        cf = configparser.ConfigParser()
        cf.read('./TERSI-labelmkr.ini')
        cf.set('env', 'cropSaveDir', self.cropSaveDir)
        with open('./TERSI-labelmkr.ini', 'w+') as f:
            cf.write(f)
        self.statusBar().showMessage('%s .jpg file will be saved to %s' % ('Change cropped pic saved folder',
                                                                              self.cropSaveDir))
        self.statusBar().show()

    def openPrevImg(self):
        if len(self.mImgList) <= 0:
            return
        if self.filePath is None:
            return
        currIndex = self.mImgList.index(self.filePath)
        if currIndex - 1 >= 0:
            filename = self.mImgList[currIndex - 1]
            if filename:
                self.loadFile(filename)
    
    def verifyImg(self):
        if self.defaultSaveDir == 'None':
            self.changeSavedirDialog()
        fname = self.filename.split('.')[0] + '.xml'
        fname = os.path.join(self.defaultSaveDir, fname)
        print('verifying label info of '+fname)
        '''
        with open(fname, 'w') as f:
            f.write(self.filename)
            for point in self.canvas.points:
                f.write(' ' + str(point.x()) + ' ' + str(point.y()))
                '''
        root = ET.Element('TERSI-label')
        subElement(root, 'picpath', os.path.abspath(self.filePath))
        subElement(root, 'xmlpath', fname)
        size = subElement(root, 'size')
        subElement(size, 'picw', str(self.picw))
        subElement(size, 'pich', str(self.pich))
        for i in range(len(self.canvas.rectangles)//2):
            leftTop = self.canvas.rectangles[2*i]
            rightBottom = self.canvas.rectangles[2*i+1]
            xmin = min(leftTop.x(), rightBottom.x())
            xmax = max(leftTop.x(), rightBottom.x())
            ymin = min(leftTop.y(), rightBottom.y())
            ymax = max(leftTop.y(), rightBottom.y())
            rectangle = subElement(root, 'rectangle')
            subElement(rectangle, 'xmin', str(self.regularize_point_pos(x=xmin)))
            subElement(rectangle, 'xmax', str(self.regularize_point_pos(x=xmax)))
            subElement(rectangle, 'ymin', str(self.regularize_point_pos(y=ymin)))
            subElement(rectangle, 'ymax', str(self.regularize_point_pos(y=ymax)))
        for p in self.canvas.points:
            point = subElement(root, 'point')
            subElement(point, 'x', str(self.regularize_point_pos(x=p.x())))
            subElement(point, 'y', str(self.regularize_point_pos(y=p.y())))
        tree = ET.ElementTree(root)
        tree.write(fname, encoding='utf-8', xml_declaration=True)
        self.openNextImg()

    def test(self):
        if self.filename:
            if os.path.exists(self.defaultSaveDir):
                labelfile = os.path.join(self.defaultSaveDir, self.filename.split('.')[0]+'.xml')
                if os.path.exists(labelfile):
                    #self.canvas.test(labelfile)
                    tree = ET.parse(labelfile)
                    root = tree.getroot()
                    #print(root.find('picpath'))
                    #print(self.filePath)
                    if root.find('picpath').text == self.filePath:
                        print('testing '+self.filePath)
                        for rect in root.findall('rectangle'):
                            x1 = int(float(rect.find('xmin').text))
                            y1 = int(float(rect.find('ymin').text))
                            x2 = int(float(rect.find('xmax').text))
                            y2 = int(float(rect.find('ymax').text))
                            #print(x1, y1, x2, y2)
                            cv2.rectangle(self.im, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        count = 1
                        for p in root.findall('point'):
                            x = int(float(p.find('x').text))
                            y = int(float(p.find('y').text))
                            #print(x, y)
                            cv2.circle(self.im, (x, y), 2, (0, 0, 255), -1)
                            cv2.putText(self.im, str(count), (x+2, y+2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            count += 1
                    cv2.imshow('Test Image %s'%self.filePath, self.im)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                else:
                    '''
                    box = QMessageBox.information(self,
                                    "消息框标题",  
                                    "请核查该图片标注文件存储目录是否正确或者请保存一个标注文件",  
                                    QMessageBox.Yes)'''
                    messageBox = QMessageBox()
                    messageBox.setWindowTitle('消息框标题')
                    messageBox.setText('请核查该图片标注文件存储目录是否正确或者请保存一个标注文件')
                    messageBox.addButton(QPushButton('确定'), QMessageBox.YesRole)
                    messageBox.exec_()
            else:
                self.changeSavedirDialog()

    def testSample(self):
        if os.path.exists(self.defaultSaveDir):
            for file in os.listdir(self.defaultSaveDir):
                if file.endswith('.xml'):
                    tree = ET.parse(os.path.join(self.defaultSaveDir, file))
                    root = tree.getroot()
                    picpath = root.find('picpath').text
                    if os.path.exists(picpath):
                        img = open_img(picpath)
                        print('testing '+picpath)
                        for rect in root.findall('rectangle'):
                            x1 = int(float(rect.find('xmin').text))
                            y1 = int(float(rect.find('ymin').text))
                            x2 = int(float(rect.find('xmax').text))
                            y2 = int(float(rect.find('ymax').text))
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        count = 1
                        for p in root.findall('point'):
                            x = int(float(p.find('x').text))
                            y = int(float(p.find('y').text))
                            cv2.circle(img, (x, y), 2, (0, 0, 255), -1)
                            cv2.putText(img, str(count), (x+2, y+2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            count += 1
                        cv2.imshow('Test Sample - %s'%picpath, img)
                        keycode = cv2.waitKey(0)
                        cv2.destroyAllWindows()
                        if keycode == 27:
                            break
        else:
            self.changeSavedirDialog()
                
    def fileitemDoubleClicked(self, item=None):
        currIndex = self.mImgList.index(item.text())
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename)

    def delImg(self):
        print('deleting '+self.filePath)
        self.status('deleting '+self.filePath)
        os.remove(self.filePath)
        to_remove = self.filePath
        self.openNextImg()
        self.mImgList.remove(to_remove)
        self.fileListWidget.clear()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.fileListWidget.addItem(item)

    def regularize_point_pos(self, x=None, y=None):
        if x is not None:
            if x < 0:
                x = 0
            elif x >= self.picw:
                x = self.picw-1
            return x
        elif y is not None:
            if y < 0:
                y = 0
            elif y >= self.pich:
                y = self.pich-1
            return y

    def cropAndSave(self):
        if self.filename:
            self.cropSavedirDialog()
            if len(self.canvas.rectangles) == 2:
                rect1 = self.canvas.rectangles[0]
                rect2 = self.canvas.rectangles[1]
                x1 = int(self.regularize_point_pos(x=min(rect1.x(), rect2.x())))
                y1 =int(self.regularize_point_pos(y=min(rect1.y(), rect2.y())))
                x2 = int(self.regularize_point_pos(x=max(rect1.x(), rect2.x())))
                y2 = int(self.regularize_point_pos(y=max(rect1.y(), rect2.y())))
                croppedim = self.im[y1:y2, x1:x2, :]
                #cv2.imshow('img', croppedim)
                #cv2.waitKey()
                croppedimg = Image.fromarray(cv2.cvtColor(croppedim, cv2.COLOR_BGR2RGB))
                croppedimpath = os.path.join(self.cropSaveDir, self.filename.split('.')[-2]+'%d%d%d%d.jpg'%(x1, y1, x2, y2))
                #croppedimg.show()
                #input()
                #cv2.imwrite(croppedimpath, croppedim)
                croppedimg.save(croppedimpath)
                print('saved %s into %s' % (croppedimpath, self.cropSaveDir))
            else:
                messageBox = QMessageBox()
                messageBox.setWindowTitle('消息框标题')
                messageBox.setText('请标注一个矩形，如此才能截取')
                messageBox.addButton(QPushButton('确定'), QMessageBox.YesRole)
                messageBox.exec_()
    def clear(self):
        self.canvas.resetState()

def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return default

def subElement(root, tag, text=''):
    ele = ET.SubElement(root, tag)
    ele.text = text
    ele.tail = '\n'
    return ele
                                                   
def get_main_app(argv=[]):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_() -- so that we can test the application in one thread
    """
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(newIcon("app"))
    # Tzutalin 201705+: Accept extra agruments to change predefined class file
    # Usage : labelImg.py image predefClassFile saveDir
    win = MainWindow(argv[1:] if len(argv) >= 2 else None)
    win.show()
    return app, win

def init():
    print('initializing... current working directory is '+os.getcwd())
    os.chdir(os.path.dirname(sys.argv[0]))
    print('changing to working directory '+os.path.dirname(sys.argv[0]))
    cf = configparser.ConfigParser()
    if(os.path.exists('./TERSI-labelmkr.ini')):
        cf.read('./TERSI-labelmkr.ini')
        if 'env' not in cf.sections():
            cf.add_section('env')
        opts = cf.options('env')
        print('.ini file has options: ', opts)
        #print('defaultsavedir' in opts)
        if not 'defaultsavedir' in opts:
            cf.set('env', 'defaultSaveDir', 'None')
        if not 'lastopendir' in opts:
            cf.set('env', 'lastOpenDir', 'None')
        if not 'iconurl' in opts:
            cf.set('env', 'iconURL', 'https://github.com/tellw/TERSI-labelmkr/tree/master/icons')
        if not 'cropsavedir' in opts:
            cf.set('env', 'cropSaveDir', 'None')
        with open('./TERSI-labelmkr.ini', 'w+') as f:
            cf.write(f)
    else:
        cf.add_section('env')
        #cf.set('env', 'argv0dir', os.path.dirname(sys.argv[0]))
        cf.set('env', 'defaultSaveDir', 'None')
        cf.set('env', 'lastOpenDir', 'None')
        cf.set('env', 'iconURL', 'https://raw.githubusercontent.com/tellw/TERSI-labelmkr/master/icons')
        cf.set('env', 'cropSaveDir', 'None')
        #cf.add_section('init')
        #cf.set('init', 'switch', 1)
        with open('./TERSI-labelmkr.ini', 'w+') as f:
            cf.write(f)
    if not os.path.exists('icons'):
        os.mkdir('icons')
        downloadIcons()

def downloadIcons(icons=['app', 'open', 'opendir', 'changesavedir', 'next', 'prev', 'verify', 'test', 'testsample', 'delimg', 'cropandsave', 'clear']):
    cf = configparser.ConfigParser()
    cf.read('./TERSI-labelmkr.ini')
    iconURL = cf.get('env', 'iconURL')
    if isinstance(icons, (list, tuple)):
        for ii in icons:
            downloadIcon(iconURL, ii)
    else:
        downloadIcon(iconURL, icons)

def downloadIcon(iconURL, icon):
    if not os.path.exists('./icons/'+icon+'.png'):
        try:
            '''
            conn = urllib.request.urlopen(iconURL+'/'+icon+'.png')
            with open('./icons/'+icon+'.png', 'wb') as f:
                 f.write(conn.read())
                 '''
            urllib.request.urlretrieve(iconURL+'/'+icon+'.png', filename='./icons/'+icon+'.png')
            '''
            pic = requests.get(iconURL+'/'+icon+'.png')
            with open('./icons/'+icon+'.png', 'wb') as f:
                 f.write(pic.content)'''
            print('./icons/'+icon+'.png downloaded')
        except Exception as e:
            print('downloading ./icons/'+icon+'.png failed caused by '+str(e))

def open_img(imgpath):
    img = Image.open(imgpath).convert('RGB')
    #img.show()
    im = np.asarray(img)
    im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
    #cv2.imshow('img', im)
    return im
            
init()
app, _win = get_main_app(sys.argv)
sys.exit(app.exec_())
