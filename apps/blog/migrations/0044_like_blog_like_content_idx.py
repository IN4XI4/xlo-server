from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0043_alter_notification_notification_type"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="like",
            index=models.Index(fields=["content_type", "object_id"], name="blog_like_content_idx"),
        ),
    ]
