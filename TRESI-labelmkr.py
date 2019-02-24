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

#print(os.getcwd())
__appname__ = 'TERSI-labelmkr'

def newIcon(icon):
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
        self.filePath = defaultFilename
        with open('config/lastOpenDir.txt', 'r') as f:
            self.lastOpenDir = f.readline().strip('\n')
        self.dirname = None
        self.mImgList = []
        '''if(targetSaveDir == 'None'):
            self.defaultSaveDir = None
        else:'''
        with open('config/defaultSaveDir.txt', 'r') as f:
            self.defaultSaveDir =  f.readline().strip('\n')
        self.filename = None
        #最近打开文件
        self.recentFiles = []
        self.maxRecent = 7
        #QAction关联到QToolBar并以QToolButton显示出来
        action = partial(newAction, self)
        open_ = action('&Open', self.openFile,
                      'Ctrl+O', 'open', u'Open image or label file')
        opendir = action('&Open Dir', self.openDirDialog,
                         'Ctrl+u', 'open', u'Open Dir')
        changeSavedir = action('&Change Save Dir', self.changeSavedirDialog,
                               'Ctrl+r', 'open', u'Change default saved Annotation dir')
        openNextImg = action('&Next Image', self.openNextImg,
                             'd', 'next', u'Open Next')
        openPrevImg = action('&Prev Image', self.openPrevImg,
                             'a', 'prev', u'Open Prev')
        verify = action('&Verify Image', self.verifyImg,
                        'space', 'verify', u'Verify Image')
        test = action('&Test Label', self.test, 't', 'test', u'Test Label')
        tools = {open_ : 'Open', opendir : 'Open Dir', changeSavedir : 'Change Save Dir',
                 openNextImg : 'Next Image', openPrevImg : 'Prev Image', verify : 'Verify Image',
                 test: 'Test'}
        tools = tools.items()
        for act, title in tools:
            toolbar = ToolBar(title)
            toolbar.setObjectName(u'%s ToolBar' % title)
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
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
        if filePath is None:
            return
        print(filePath)
        self.filename = os.path.split(filePath)[-1]
        if self.fileListWidget.count() > 0:
            index = self.mImgList.index(filePath)
            fileWidgetItem = self.fileListWidget.item(index)
            fileWidgetItem.setSelected(True)
        if os.path.exists(filePath):
            self.imageData = read(filePath, None)
            self.canvas.verified = False
        image = QImage.fromData(self.imageData)
        if image.isNull():
            self.errorMessage(u'Error opening file', u"<p>Make sure <i>%s</i> is a valid image file." % filePath)
            self.status("Error reading %s" % filePath)
            return False
        self.status("Loaded %s" % os.path.basename(filePath))
        self.image = image
        self.filePath = filePath
        self.canvas.loadPixmap(QPixmap.fromImage(image))
        self.canvas.setEnabled(True)
        self.paintCanvas()
        self.addRecentFile(self.filePath)
        self.setWindowTitle(__appname__ + ' ' + filePath)
        self.canvas.setFocus(True)
        
    def openFile(self):
        path = os.path.dirname(self.filePath) if self.filePath else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats)
        filename = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
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
        with open('config/lastOpenDir.txt', 'w') as f:
            f.write(self.lastOpenDir)
        self.dirname = dirpath
        self.filePath = None
        self.fileListWidget.clear()
        self.mImgList = self.scanAllImages(dirpath)
        self.openNextImg()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.fileListWidget.addItem(item)
    #请选择下面没有包含图片的子目录的目录，否则在测试时可能会出现bug，而且请注意标注文本文件所记录的图片路径名。
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
        dirpath = QFileDialog.getExistingDirectory(self, '%s - Save text to the directory' % __appname__, path,
                                                   QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dirpath is not None and len(dirpath) > 1:
            self.defaultSaveDir = dirpath
        with open('config/defaultSaveDir.txt', 'w') as f:
            f.write(self.defaultSaveDir)
        self.statusBar().showMessage('%s . Annotation will be saved to %s' % ('Change saved folder',
                                                                              self.defaultSaveDir))
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
    #确定保存标记文本文件
    def verifyImg(self):
        if self.defaultSaveDir == 'None':
            self.changeSavedirDialog()
        fname = self.filename.split('.')[0] + '.txt'
        fname = os.path.join(self.defaultSaveDir, fname)
        print(fname)
        with open(fname, 'w') as f:
            f.write(self.filename)
            for point in self.canvas.points:
                f.write(' ' + str(point.x()) + ' ' + str(point.y()))
        self.openNextImg()
    #测试，看标注的情况。
    def test(self):
        if self.filename:
            labelfile = os.path.join(self.defaultSaveDir, self.filename.split('.')[0]+'.txt')
            if os.path.isfile(labelfile):
                #self.canvas.test(labelfile)
                with open(labelfile,'r') as f:
                    line = f.readline().strip('\n').split(' ')
                line_len = len(line)
                img = cv2.imread(os.path.join(self.dirname, self.filename))
                if line_len > 1:
                    x1, y1, x2, y2 = (int(float(line[i])) for i in range(1, 5))
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    if line_len > 5:
                        for i in range((line_len - 5) // 2):
                            x = int(float(line[5+2*i]))
                            y = int(float(line[5+2*i+1]))
                            cv2.circle(img, (x, y), 2, (255, 0, 0), -1)
                cv2.imshow('Test Image', img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                
    def fileitemDoubleClicked(self, item=None):
        currIndex = self.mImgList.index(item.text())
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename)

def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return default
                                                   
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
    win = MainWindow(argv[1] if len(argv) >= 2 else None)
    win.show()
    return app, win

app, _win = get_main_app(sys.argv)
sys.exit(app.exec_())
