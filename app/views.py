from django.shortcuts import render

import base64
from io import BytesIO
import threading
from django.http import JsonResponse
from PIL import Image
from . import face_task
from .models import User, Check
import pickle, numpy as np
from django.utils import timezone
from .forms import BootstrapAuthenticationForm
import datetime

work_time = 45  ## 每节课上课+休息时间

init_time = [float((datetime.datetime.strptime("8.30", "%H.%M") +
                    datetime.timedelta(minutes=work_time * x)).strftime("%H.%M"))
             for x in range(5)] + [
                float((datetime.datetime.strptime("14.00", "%H.%M") +
                       datetime.timedelta(minutes=work_time * x)).strftime("%H.%M"))
                for x in range(5)]  ### 每节课开始的时间
print("每节课开始时间", init_time)  ## 错过时间点签到 就算是迟到


def checkLogin(func):
    def check(request, *args, **kwargs):
        if request.user.is_anonymous:
            return render(request, "login.html", {"form": BootstrapAuthenticationForm()})
        else:
            return func(request, *args, **kwargs)

    return check


# Create your views here.
def index(request):
    if request.method == "GET":

        return render(request, "index.html")
    else:
        img_content = request.POST.get("img").replace("data:image/jpeg;base64,", "").replace("data:image/png;base64,",
                                                                                             "")
        faceencodings = face_task.get_face_encoding(BytesIO(base64.b64decode(img_content)))
        users = []
        for encoding in faceencodings:
            face_names = face_task.base_match_faces(encoding, face_task.known_face_encodings,
                                                    face_task.known_face_names)
            users.append(face_names)

        if len(users) == 0:
            return JsonResponse({"code": 200, "data": []})

        method = request.POST.get("method", "work")
        now_time = float(datetime.datetime.now().strftime("%H.%M"))
        work_status = ""
        if method == "work":
            for i, x in enumerate(init_time):
                if now_time > x:
                    if i < len(init_time) - 1 and now_time < init_time[i + 1]:
                        work_status = f"第{i + 1}节课迟到"
                        break
                    else:
                        continue
                if now_time <= x:
                    work_status = f"第{i + 1}节课出勤"
                    break
            else:
                if work_status == "":
                    work_status = f"第{len(init_time)}节课迟到"

        else:
            for i, x in enumerate(init_time):
                if now_time > x:
                    if i < len(init_time) - 1 and now_time < init_time[i + 1]:
                        work_status = f"第{i + 1}节课签退正常"
                        break
                    else:
                        continue
                if now_time <= x:
                    work_status = f"第{i + 1}节课早退"
                    break
            else:
                if work_status == "":
                    work_status = f"第{len(init_time)}节课签退正常"
        status = []
        for username in users:
            try:
                user = User.objects.get(username=username)
            except:
                continue

            try:
                check = Check.objects.get(user=user, status__icontains=work_status.split("课")[0],
                                          time__gte=timezone.now().date(), method=method)
            except Check.DoesNotExist:
                Check.objects.create(user=user, status=work_status, method=method)
                status.append(f"{username} {work_status}")

        return JsonResponse({"code": 200, "data": status})


def register(request):
    if request.method == "GET":

        return render(request, "register.html")
    else:
        img1 = request.POST.get("face1").replace("data:image/jpeg;base64,",
                                                 "").replace("data:image/png;base64,", "")

        img2 = request.POST.get("face2").replace("data:image/jpeg;base64,",
                                                 "").replace("data:image/png;base64,", "")

        img3 = request.POST.get("face3").replace("data:image/jpeg;base64,",
                                                 "").replace("data:image/png;base64,", "")
        encodings = face_task.get_face_encoding([BytesIO(base64.b64decode(img1)),
                                                 BytesIO(base64.b64decode(img2)),
                                                 BytesIO(base64.b64decode(img3)), ])
        print(encodings)
        if len(encodings) != 3:
            return JsonResponse({"code": 500, "msg": "您其中有一张图片没有检测到人脸哦!", })

        password = request.POST.get("password", "")
        clss = request.POST.get("clss", "")
        pro = request.POST.get("pro", "")
        snum = request.POST.get("snum", "")
        college = request.POST.get("college", "")
        username = request.POST.get("username")

        if "" in [password, clss, pro, snum, college, username]:
            return JsonResponse({"code": 500, "msg": "请填入正确的信息!", })

        user = User.objects.create_user(username=username,
                                        password=password,
                                        clss=clss,
                                        pro=pro,
                                        snum=snum,
                                        college=college,
                                        feature1=str(list(encodings[0])),
                                        feature2=str(list(encodings[1])),
                                        feature3=str(list(encodings[2]))
                                        )
        face_task.known_face_names, face_task.known_face_encodings = face_task.load_all_users()
        return JsonResponse({"code": 200, "msg": "用户注册成功!", "data": {"user": user.username}})


#
def face_online(request):
    img3 = BytesIO(
        base64.b64decode(request.POST.get("img").replace("data:image/jpeg;base64,",
                                                         "").replace("data:image/png;base64,", "")))
    face = face_task.face_detector(np.array(Image.open(img3).convert("RGB")), 1)

    return JsonResponse({"code": 200, "data": len(face)})


from django.db.models import Q

from django.db.models import Sum, Count, Value, Avg



def search(request):
    if request.method == "GET":
        return render(request, "search.html")
    else:
        lst = []
        username = request.POST.get("username", "")

        college = request.POST.get("college", "")
        snum = request.POST.get("snum", "")
        pro = request.POST.get("pro", "")
        clss = request.POST.get("clss", "")
        date  =  request.POST.get("date", " - ")

        date1, date2 = date.split(" - ") if " - " in date else "",""
        if username != "":
            lst.append(Q(user__username=username))


        if college != "":
            lst.append(Q(user__college=college))
        if snum != "":
            lst.append(Q(user__snum=snum))
        if pro != "":
            lst.append(Q(user__pro=pro))

        if clss != "":
            lst.append(Q(user__clss=clss))
        if len(lst) > 0:
            checks = Check.objects.filter(lst[0])
            for x in lst[1:]:
                checks = checks.filter(x)
        else:
            checks = Check.objects.all()

        if date1 != "":
            date1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
            date2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
            checks = checks.filter(time__gte=date1, time__lte=date2)


        data = [{"username": x.user.username,
                 "time": x.time,
                 "status": x.status,
                 "pro":x.user.pro,
                 "snum":x.user.snum,
                 "college":x.user.college,
                 "clss":x.user.clss,

                 } for x in checks]

        over_time = checks.filter(status__icontains="迟到").count()
        early_time = checks.filter(status__icontains="早退").count()
        on_time = checks.filter(status__icontains="出勤").count()
        on_time_out = checks.filter(status__icontains="正常").count()
        user_data = {
            "name": '出勤统计',
            "type": 'pie',
            "radius": [30, 100],

            "data": [

            ]
        }
        if over_time:
            user_data["data"].append({"value": over_time, "name": '迟到'})
        if early_time:
            user_data["data"].append({"value": early_time, "name": '早退'})
        if on_time:
            user_data["data"].append({"value": on_time, "name": '出勤'}, )
        if on_time_out:
            user_data["data"].append({"value": on_time_out, "name": '签退正常'}, )




        return JsonResponse({"code": 200, "data": {"user_data": user_data, "detail": data}})
