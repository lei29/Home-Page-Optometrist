#!/usr/local/bin/python3.4
import urllib.request
import hashlib
from mimetypes import guess_extension
import os, sys, tempfile, shutil, contextlib
import collections
import validators
import cv2
from lxml.html import HTMLParser, document_fromstring
from PIL import Image

EYE_DATA = "/home/ecegridfs/a/ee364/site-packages/cv2/data/haarcascade_eye.xml"
FACE_DATA_PATH = "/home/ecegridfs/a/ee364/site-packages/cv2/data/haarcascade_frontalface_default.xml"
usr_url = ""
def get_html_at_url(url, charset="UTF-8"):
    global usr_url
    usr_url = url
    resp = urllib.request.urlopen(url)
    bystr = resp.read()
    try:
        rtstr = bystr.decode(charset)
    except UnicodeDecodeError:
        return "cannot decode(unicodeError), please go back"
    else:
        return rtstr

def make_etree(html,url):
    parser = HTMLParser(encoding="UTF-8")
    root = document_fromstring(html, parser=parser, base_url=url)
    return root

# Credit: Adapted from example in Python 3.4 Documentation, urllib.request
#         License: PSFL https://www.python.org/download/releases/3.4.1/license/
#                  https://docs.python.org/3.4/library/urllib.request.html
def make_outline(etree):
    str = ""
    for node in etree.iter():
        if(node.tag == "title"):
            str = str+node.text_content()
            str = str+"\n"
        elif(node.tag == "h1"):
            str = str+"    "
            str = str+node.text_content()+"\n"
        elif(node.tag == "h2"):
            str = str+"    "
            str = str+"    "
            str = str+node.text_content()+"\n"
            #print(node.text_content())
        elif(node.tag == "h3"):
            str = str+"    "
            str = str+"    "
            str = str+"    "
            str = str+node.text_content()+"\n"

    return "<pre>"+str+"</pre>"

def scrape_speaker_photos(url, dir_path):
    photo_list = []
    email_list = []
    html = get_html_at_url(url)
    etree = make_etree(html,url)
    photo_root = etree.findall(".//div[@class='content']//div[@class='row']")
    for node in photo_root:
        for elem in node.iter():
            #print(elem.text_content())
            if(elem.tag == "img" and elem not in photo_list):
                #print(elem.text_content())
                photo_list.append(elem)

            if(elem.get('href') and '@' in elem.text_content()):
                #print(elem.text_content())
                email_list.append(elem.text_content())

    for photo_node in photo_list:
        img_url = photo_node.get("src")
        obj = urllib.request.urlopen(img_url)
        type = obj.info().get("Content-type")
        ext = guess_extension(type)
        filename = make_filename(img_url, ext)
        #print(filename)
        filename = os.path.join(dir_path,filename)
        #temp_img = urllib.request.urlretrieve(photo_node.get("src"))
        with open(filename,"wb") as outfile:
            outfile.write(urllib.request.urlopen(img_url).read())


    #print(photo_list)
    #print(len(photo_list))


def make_filename(url, extension):
    #print(url)
    name = hashlib.sha1(url.encode('utf8'))
    #print(name)
    #print(name.hexdigest())
    return name.hexdigest()+extension
@contextlib.contextmanager
def pushd_temp_dir(base_dir=None, prefix="tmp.hpo."):
    '''
    Create a temporary directory starting with {prefix} within {base_dir}
    and cd to it.

    This is a context manager.  That means it can---and must---be called using
    the with statement like this:

        with pushd_temp_dir():
            ....   # We are now in the temp directory
        # Back to original directory.  Temp directory has been deleted.

    After the with statement, the temp directory and its contents are deleted.


    Putting the @contextlib.contextmanager decorator just above a function
    makes it a context manager.  It must be a generator function with one yield.

    - base_dir --- the new temp directory will be created inside {base_dir}.
                   This defaults to {main_dir}/data ... where {main_dir} is
                   the directory containing whatever .py file started the
                   application (e.g., main.py).

    - prefix ----- prefix for the temp directory name.  In case something
                   happens that prevents
    '''
    if base_dir is None:
        proj_dir = sys.path[0]
        # e.g., "/home/ecegridfs/a/ee364z15/hpo"

        base_dir = os.path.join(proj_dir, "data")
        # e.g., "/home/ecegridfs/a/ee364z15/hpo/data"

    # Create temp directory
    temp_dir_path = tempfile.mkdtemp(prefix=prefix, dir=base_dir)
    #print(temp_dir_path)

    try:
        start_dir = os.getcwd()  # get current working directory
        os.chdir(temp_dir_path)  # change to the new temp directory

        try:
            yield
        finally:
            # No matter what, change back to where you started.
            os.chdir(start_dir)
    finally:
        # No matter what, remove temp dir and contents.
        #print(temp_dir_path)
        shutil.rmtree(temp_dir_path, ignore_errors=True)

@contextlib.contextmanager
def fetch_images(etree):
    #print("fetch image")

    #print(main.usrarg)
    with pushd_temp_dir():
        #print("inside pushd")
        filename_to_node = collections.OrderedDict()
        #
        # Extract the image files into the current directory
        #
        photo_list = []
        photo_root = etree.findall(".//img")
        #print(len(photo_root))
        #print(os.getcwd())
        dir_path = os.getcwd()
        for node in photo_root:
            for elem in node.iter():
                #print(elem.text_content())
                if(elem.tag == "img" and elem not in photo_list):
                    #print(elem.text_content())
                    photo_list.append(elem)

        #print(photo_list)
        #print(len(photo_list))
        for photo_node in photo_list:
            img_url = photo_node.get("src")
            #print("a "+img_url)
            if(img_url.find("http") == -1):
                if(img_url.find(usr_url) == -1):
                    img_url = usr_url+img_url
            urlvalidity = validators.url(img_url)
            #print("valid: "+str(urlvalidity))

            if(urlvalidity is True):
                #print("valid")
                obj = urllib.request.urlopen(img_url)
                type = obj.info().get("Content-type")
                ext = guess_extension(type)
                #print(ext)

                filename = make_filename(img_url, ext)

                #print(filename)
                filename = os.path.join(dir_path,filename)
                #temp_img = urllib.request.urlretrieve(photo_node.get("src"))
                with open(filename,"wb") as outfile:
                    #print("write sth")
                    outfile.write(urllib.request.urlopen(img_url).read())
                if(ext == ".gif"):
                    #print("ext is gif")
                    #print(filename)
                    im = Image.open(filename)

                    #print("opened")
                    im = im.convert("RGB")
                    filename = filename[:-4]+".jpg"
                    #print(filename)
                    #print(im)
                    #print(os.getcwd())
                    im.save(filename,"JPEG")
                    print(im)
                #print("filename: "+filename)

                filename_to_node[filename] = photo_node
                #print(filename_to_node)
        yield filename_to_node


def get_image_info(filename):
    dimension_dict = dict()
    face_list = []
    img = cv2.imread(filename)
    height, width, channels = img.shape
    dimension_dict["h"] = height
    dimension_dict["w"] = width
    face_cascade = cv2.CascadeClassifier(FACE_DATA_PATH)
    gray= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for list in faces:
        temp = dict()
        temp["w"] = list[2]
        temp["h"] = list[3]
        temp["x"] = list[0]
        temp["y"] = list[1]
        face_list.append(temp)
    dimension_dict["faces"] = face_list

    return dimension_dict

    #https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_image_display/py_image_display.html
'''
def add_glasses(filename, face_info):
    #print(face_info)
    img = cv2.imread(filename)
    #print(img)
    #subprocess.check_output(['display',filename])
    #print(os.getcwd())

    #eyes_cascade = cv2.CascadeClassifier("hpo/parojos.xml")
    eyes_cascade = cv2.CascadeClassifier("/home/ecegridfs/a/ee364d10/hpo/parojos.xml")
    #print(eyes_cascade)
    gray= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eyes = eyes_cascade.detectMultiScale(gray, 1.3, 5)
    x= face_info["x"]
    y= face_info["y"]
    w= face_info["w"]
    h= face_info["h"]

    eyes = eyes_cascade.detectMultiScale(img)
    print(eyes)
    print(len(eyes))

    ex,ey,ew,eh = eyes[0]
    print(ex)
    print(ey)
    print(ew)
    print(eh)
    #cv2.circle(roi_color, (ex,ey),20, (0,255,0), 2)
    #cv2.rectangle(img,(ex,ey),(10,ey+eh),(0,255,0),2)
    cv2.rectangle(img,(int(ex+ew/2)+1,ey+eh),(ex+ew,ey),(0,255,0),2)
    cv2.rectangle(img,(ex,ey), (int(ex+ew/2)-1,ey+eh),(0,255,0),2)
    cv2.line(img,(ex,ey),(ex-10,ey-2),(0,255,0),2)
    cv2.line(img,(ex+ew,ey),(ex+ew+10,ey-2),(0,255,0),2)
    #print("eyes:"+str(eyes))
    #img.save(filename,"jpg")
    return img
'''



def find_profile_photo_filename(filename_to_etree):
    #print("inside find profile photo")
    #print(len(filename_to_etree))
    for i in filename_to_etree:
        print(i)
        dimension_dict = get_image_info(i)
        #print(len(dimension_dict["faces"]))
        if(len(dimension_dict["faces"])==1):
            #add_glasses(i,dimension_dict["faces"][0])
            #print("RETURNED ANYTHING")
            return i

    return None

def copy_profile_photo_static(etree):
    #print("indisde copy")
    with fetch_images(etree) as filename_to_node:
        #print("finish fetch image")
        answer = find_profile_photo_filename(filename_to_node)
        #print(answer)
        #print(len(filename_to_node))
        photo_dir = os.getcwd()
        filename = answer[len(photo_dir):]
        #print("filename:"+filename)
        #print(answer)
        os.chdir("..")
        os.chdir("..")
        os.chdir("static")
        #print(os.getcwd())
        shutil.copyfile(answer,os.getcwd()+filename)
        return os.getcwd()+filename
'''
face_info = {'h': 99, 'y': 52, 'x': 23, 'w': 99}
answer = add_glasses("/home/ecegridfs/a/ee364d10/hpo/templates/quinn.jpg", face_info)
cv2.imshow('img',answer)
cv2.waitKey(0)

filename = "/home/ecegridfs/a/ee364d10/hpo/templates/quinn.jpg"
get_image_info(filename)

#print(answer)


subprocess.check_output(['display',filename])

answer = get_image_info("image.jpg")
print(answer)

url = "http://alexquinn.org"

html = get_html_at_url(url)
html = "<base href="+url+">"+html
etree1 = make_etree(html,url)
#print(html)
#print(etree1)
path = copy_profile_photo_static(etree1)
print("path:"+path)

'''
