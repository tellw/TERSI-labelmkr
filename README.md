# TERSI-labelmkr(Two-Eyes Recorder Sitting Identifier（双目摄像头坐站辨识器的标签制作器）)
一个依据labelImg开源代码做的能够标注MTCNN所需数据集的数据集制作工具<br>
A dataset-making tool that can annotate MTCNN data sets based on open source code of labelImg<br>

参考了[`labelimg`](https://github.com/tzutalin/labelImg)的代码。<br>
Refer to the code for [`Labelimg`](HTTPS://GITHUB.COM/TZUTALIN/LABELIMG).<br>
此项目能够标注点，当然是为了配合MTCNN识别人脸和器官点而确定地标注那几个，暂时功能比较僵硬，而且只能左键画框，右键标点，最后生成的标注文件会记录文件名，一个框和五个点的位置信息。<br>
This project can label points in order to match the MTCNN to identify the face and organ points.The temporary function is rigid, for you may only label bounding-box with left-click and label points with right-click. The last generated text file will record the file name and location information of the bounding-box and five points.<br>

* latest wiki on the [`link`](https://github.com/tellw/TERSI-labelmkr/wiki)

# Releases:
拓展：该制作器只会先允许使用者标注一个方框，方框的位置信息最后会存储入文本文件当中。其后不限制标注点的个数，且每个点的信息都会存入相对应的文本文件中。<br>
supplement:The maker will only allow the user to mark a box, and the location information for the box will eventually be stored in a text file. Thereafter the number of labeled points is unlimited, and the information for each point is stored in the corresponding text file.<br>

TERSI-labelmkr v1.1
增加了查看单张图片标注情况的功能  Add a function that help you check your label work on one picture <br>

TERSI-labelmkr v1.2 exe文件下载[`链接`](https://pan.baidu.com/s/176Ije6dCNa2XlFPuHqwh9g) 提取码: 531i<br>
downloading TERSI-labelmkr v1.2 .exe file here.[`link`](https://pan.baidu.com/s/176Ije6dCNa2XlFPuHqwh9g) CAPTCHA：531i <br>
增加了查看在标注文件保存目录下所有标注文件对应图片目录下的图片标注情况的功能 <br>
Add a function that help you check all of your label work <br>

TERSI-labelmkr v1.4.2 please see [`the link`](https://github.com/tellw/TERSI-labelmkr/releases)<br>

# Tips:
if you want to run the TERSI-labelmkr.py on your computer, please make sure you have python environment and run the following commands:
```bash
git clone https://github.com/tellw/TERSI-labelmkr
pip install PyQt5 functools opencv-python requests configparser Pillow lxml
python TERSI-labelmkr.py
```
