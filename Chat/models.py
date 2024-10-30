from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
# Create your models here.
class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    tokens = models.IntegerField(default=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        #hashing password
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        #checking password
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.id} - {self.email}"


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message} - {self.response}"