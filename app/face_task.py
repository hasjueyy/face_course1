import cv2
import numpy as np
from .models import User
import sys

from numpy import expand_dims
import tensorflow as tf
import threading
from tensorflow.python.keras.backend import set_session
from keras.models import load_model
from keras.backend import clear_session

global mtcnn_model, face_model



# 程序开始时声明

sess = tf.compat.v1.Session()

graph = tf.compat.v1.get_default_graph()
from PIL import Image
import dlib

face_detector = dlib.get_frontal_face_detector()  # 获取人脸分类器

model_path = 'facenet_keras.h5'

"""主要 人脸识别代码"""
set_session(sess)
face_model = load_model(model_path)  ## 载入人脸特征提取神经网络


def get_face_encoding(imgs):
    """ 编码头像信息 可以是传 BytesIO对象 也可传多个图片BytesIO数组
    """


    def getencoding(img, ):
        required_size = (160, 160)
        pixels = np.array(img)  # 转换图片为数组矩阵

        results = face_detector(pixels, 1)  ## 使用dlib找出人脸
        if len(results) <= 0:
            return

        face_encodings = []
        for index, face in enumerate(results):
            x1 = face.left()
            y1 = face.top()
            x2 = face.right()
            y2 = face.bottom()

            face = pixels[y1:y2, x1:x2]  ## 切出人脸
            print(face.shape)
            if all(face.shape):

                face = cv2.resize(face, required_size).astype('float32')  # 转换人脸图片大小为160*160
                mean, std = face.mean(), face.std()

                face_pixels = (face - mean) / std  # 归一化
                samples = expand_dims(face_pixels, axis=0)  ## 增加一个图片数量维度
                global graph
                global sess
                with graph.as_default():
                    set_session(sess)
                    face_encoding = face_model.predict(samples)[0]  ##人脸特征提取的神经网络提取人脸特征
                face_encodings.append(face_encoding)

        return face_encodings



    encodings = []
    if isinstance(imgs, list):
        for x in imgs:
            img = Image.open(x).convert("RGB")  # 打开图片
            encoding = getencoding(img)
            if encoding:
                encodings = encodings + encoding
    else:
        img = Image.open(imgs).convert("RGB")
        encoding = getencoding(img)
        if encoding:
            encodings = encodings + encoding

    return encodings


def base_match_faces(face_encoding, known_face_encodings, known_face_names):
    """   传入人脸特征 将输出最匹配的人脸名称  如果没有最匹配的将返回None 使用欧式距离计算 """

    face_distances = np.linalg.norm(known_face_encodings - face_encoding, axis=1)
    best_match_index = np.argmin(face_distances)
    print(face_distances, face_distances[best_match_index])
    if face_distances[best_match_index] < 6:
        name = known_face_names[best_match_index]
        return name


def load_all_users():
    users = User.objects.all()
    known_face_names = []
    known_face_encodings = []
    for x in users:
        if len(x.feature1) > 5:
            face_encoding = np.array(eval(x.feature1))
            known_face_encodings.append(face_encoding)
            known_face_names.append(x.username)

            face_encoding = np.array(eval(x.feature2))
            known_face_encodings.append(face_encoding)
            known_face_names.append(x.username)

            face_encoding = np.array(eval(x.feature3))
            known_face_encodings.append(face_encoding)
            known_face_names.append(x.username)
    return known_face_names, known_face_encodings
    # np.save("known_face_names.npy", np.array(known_face_names))
    # np.save("known_face_encodings.npy", np.array(known_face_names))
    # return list(np.load("known_face_names.npy")), list(np.load("known_face_encodings.npy"))


if "runserver" in sys.argv:
    known_face_names, known_face_encodings = load_all_users()
    print("载入已知人脸", known_face_names)
