from django.db import models


class TopicTag(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name


class Topic(models.Model):
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    tag = models.ForeignKey(TopicTag, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class SoftSkill(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class Monster(models.Model):
    name = models.CharField(max_length=100)
    profile = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to="monsters_pics/", null=True, blank=True)

    def __str__(self):
        return self.name


class Mentor(models.Model):
    name = models.CharField(max_length=100)
    job = models.CharField(max_length=100, blank=True, null=True)
    profile = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to="mentors_pics/", null=True, blank=True)

    def __str__(self):
        return self.name
