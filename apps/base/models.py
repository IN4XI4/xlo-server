from django.db import models
from django.utils.text import slugify


class TopicTag(models.Model):
    name = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Topic(models.Model):
    title = models.CharField(max_length=300)
    image = models.ImageField(upload_to="topics/", blank=True, null=True)
    tag = models.ForeignKey(TopicTag, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=320, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            title_words = self.title.split()[:7]
            short_title = " ".join(title_words)
            self.slug = slugify(short_title)

            original_slug = self.slug
            count = 0
            while Topic.objects.filter(slug=self.slug).exists():
                count += 1
                self.slug = f"{original_slug}-{count}"

        super(Topic, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["id"]


class SoftSkill(models.Model):
    name = models.CharField(max_length=250)
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=50, blank=True, null=True)
    monster_name = models.CharField(max_length=100, blank=True, null=True)
    monster_profile = models.TextField(blank=True, null=True)
    monster_picture = models.ImageField(upload_to="monsters_pics/", null=True, blank=True)
    logo = models.FileField(upload_to="logos/", null=True, blank=True)

    def __str__(self):
        return self.name


class Mentor(models.Model):
    name = models.CharField(max_length=100)
    job = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    profile = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to="mentors_pics/", null=True, blank=True)

    def __str__(self):
        return self.name
