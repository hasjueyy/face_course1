from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.


class User(AbstractUser):
    pro = models.CharField("专业", max_length=32)
    clss = models.CharField("班级", max_length=32)
    snum = models.CharField("学号", max_length=32)
    college = models.CharField("学院", max_length=32)
    feature1 = models.TextField("人脸特征")
    feature2 = models.TextField("人脸特征")
    feature3 = models.TextField("人脸特征")

    class Meta(AbstractUser.Meta):
        pass

    def __str__(self):
        return self.username


# Create your models here.


class Check(models.Model):
    user = models.ForeignKey(User, verbose_name="用户", related_name="Check", on_delete=models.CASCADE)
    status = models.CharField("状态", max_length=32, default="出勤")
    method = models.CharField("签到/签退",max_length=12,default="work")
    time = models.DateTimeField("签到时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "签到记录"
