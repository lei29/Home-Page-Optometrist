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

EYE_DATA = "/home/jingchen/Desktop/projects/364proj/hpo/static/haarcascade_eye.xml"
FACE_DATA_PATH = "/home/jingchen/Desktop/projects/364proj/hpo/static/haarcascade_frontalface_default.xml"
usr_url = ""
oldpath = ""
url_to_sha = dict()
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
    filename = name.hexdigest()+extension
    #print(filename)
    return filename
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
    global url_to_sha
    #print(main.usrarg)
    with pushd_temp_dir():
        #print("inside pushd")
        filename_to_node = collections.OrderedDict()
        photo_list = []
        photo_root = etree.findall(".//img")
        dir_path = os.getcwd()
        for node in photo_root:
            for elem in node.iter():
                if(elem.tag == "img" and elem not in photo_list):
                    photo_list.append(elem)
        for photo_node in photo_list:
            img_url = photo_node.get("src")
            src = img_url
            if(img_url.find("http") == -1):
                if(img_url.find(usr_url) == -1):
                    img_url = usr_url+img_url
            urlvalidity = validators.url(img_url)
            if(urlvalidity is True):
                obj = urllib.request.urlopen(img_url)
                type = obj.info().get("Content-type")
                ext = guess_extension(type)
                filename = make_filename(img_url, ext)
                filename = os.path.join(dir_path,filename)
                url_to_sha[filename] = src

                with open(filename,"wb") as outfile:
                    outfile.write(urllib.request.urlopen(img_url).read())
                if(ext == ".gif"):
                    im = Image.open(filename)
                    im = im.convert("RGB")
                    filename = filename[:-4]+".jpg"
                    im.save(filename,"JPEG")
                filename_to_node[filename] = photo_node
        #print(url_to_sha)
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

def add_glasses(filename, face_info,style,color):
    #print(face_info)
    img = cv2.imread(filename)
    eyes_cascade = cv2.CascadeClassifier(EYE_DATA)
    eyes = eyes_cascade.detectMultiScale(img)
    print(eyes)
    #print(len(eyes))
    color_dict = dict()
    red = (0,0,255)
    blue = (255,0,0)
    green = (0,255,0)
    color_dict["red"] = red
    color_dict["blue"] = blue
    color_dict["green"] = green
    eyes_pos = []
    if(color == ""):
        color = "green"
    if(len(eyes)!=0):
        print(eyes[0])
        lex,ley,lew,leh = eyes[1]
        rex,rey,rew,reh = eyes[0]
        #print(ex)
        #print(ey)
        #print(ew)
        #print(eh)
        #cv2.circle(roi_color, (ex,ey),20, color_dict[color], 2)
        #cv2.rectangle(img,(ex,ey),(10,ey+eh),color_dict[color],2)
        if(style == "square"):
            #print("square")
            cv2.rectangle(img,(lex,ley),(lex+lew,ley+leh),color_dict[color],2)
            cv2.rectangle(img,(rex,rey), (rex+lew,rey+leh),color_dict[color],2)
            cv2.line(img,(lex+lew,int(ley+leh/2)),(rex,int(rey+reh/2)),color_dict[color],2)
            cv2.line(img,(lex,int(ley+leh/2)),(lex-15,ley),color_dict[color],2)
            cv2.line(img,(rex+lew,int(rey+reh/2)), (rex+lew+15,rey),color_dict[color],2)
        elif(style =="circle"):
            pass
            #print("circle")
            #cv2.circle(img,(int(ex+ew/4),int(ey+eh/2)),int(ew/5),color_dict[color],2)
            #cv2.circle(img,(int(ex+3*ew/4),int(ey+eh/2)), int(ew/5),color_dict[color],2)
            #cv2.line(img,(ex,ey),(ex-10,ey-2),color_dict[color],2)
            #cv2.line(img,(ex+ew,ey),(ex+ew+10,ey-2),color_dict[color],2)
            #cv2.line(img,(int(ex+ew/2 - 4),int(ey+eh/2)), (int(ex+ew/2 + 4),int(ey+eh/2)),color_dict[color],2)

        #print("eyes:"+str(eyes))
        #img.save(filename,"jpg")


        #print("imwrite:"+filename)
        cv2.imwrite(filename,img)
    return img

def add_mustache(filename,mustache_img):
    faceCascade = cv2.CascadeClassifier(FACE_DATA_PATH)
    noseCascade = cv2.CascadeClassifier("/home/ecegridfs/a/ee364d10/hpo/Nariz.xml")

    imgM = cv2.imread(mustache_img,-1)

    orig_mask = imgM[:,:,3]

    orig_mask_inv = cv2.bitwise_not(orig_mask)

    imgM = imgM[:,:,0:3]
    origmh, origmw = imgM.shape[:2]



    frame = cv2.imread(filename)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale(gray,1.3,5)
    print(len(faces))
    for (x, y, w, h) in faces:
        #print(x)
        #print(y)
        ##print(w)
        #print(h)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        #print(noseCascade.load("/home/ecegridfs/a/ee364d10/hpo/Nariz.xml"))
        nose = noseCascade.detectMultiScale(roi_gray)
        for (nx,ny,nw,nh) in nose:

            mw =  3 * nw
            mh = mw * origmh / origmw

            x1 = nx - int(mw/4)
            x2 = nx + nw + int(mw/4)
            y1 = ny + nh - int(mh/2)
            y2 = ny + nh + int(mh/2)

            mw =int( x2 - x1)
            mh = int(y2 - y1)

            mustache = cv2.resize(imgM, (mw,mh), interpolation = cv2.INTER_AREA)
            mask = cv2.resize(orig_mask, (mw,mh), interpolation = cv2.INTER_AREA)
            mask_inv = cv2.resize(orig_mask_inv, (mw,mh), interpolation = cv2.INTER_AREA)

            roi = roi_color[y1:y2, x1:x2]

            roi_bg = cv2.bitwise_and(roi,roi,mask = mask_inv)

            roi_fg = cv2.bitwise_and(mustache,mustache,mask = mask)
            dst = cv2.add(roi_bg,roi_fg)
            roi_color[y1:y2, x1:x2] = dst

    cv2.imwrite(filename,frame)
    return frame

def find_profile_photo_filename(filename_to_etree,style,color,mustache):

    for i in filename_to_etree:
        dimension_dict = get_image_info(i)
        if(len(dimension_dict["faces"])==1):
            if(style!=""):
                add_glasses(i,dimension_dict["faces"][0],style,color)
            if(mustache!=""):
                add_mustache(i,"/home/ecegridfs/a/ee364d10/hpo/mustache.jpeg")
            #print("oldpath:"+i)

            return i

    return None

def copy_profile_photo_static(etree,style,color, mustache):
    global oldpath
    with fetch_images(etree) as filename_to_node:
        answer = find_profile_photo_filename(filename_to_node, style,color,mustache)
        #print(answer)
        oldpath = answer
        photo_dir = os.getcwd()
        filename = answer[len(photo_dir):]
        os.chdir("..")
        os.chdir("..")
        os.chdir("static")
        shutil.copyfile(answer,os.getcwd()+filename)
        return os.getcwd()+filename
'''
answer = add_mustache("/home/ecegridfs/a/ee364d10/hpo/quinn.jpg","/home/ecegridfs/a/ee364d10/hpo/mustache.jpeg")
print(answer)

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
