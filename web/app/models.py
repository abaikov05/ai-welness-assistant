from django.db import models

# Create your models here.
class User(models.Model):
    name = models.TextField(max_length=50)
    
    def __str__(self) -> str:
        return self.name
    
class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=200)
    nigger = models.BooleanField()

    def __str__(self):
        return self.text