import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('storage_max', models.BigIntegerField(default=21474836480)),
                ('storage_used', models.BigIntegerField(default=0)),
                ('is_admin', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('weight', models.BigIntegerField(default=0)),
                ('parent_folder', models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subfolders', to='cloudstorage.folder')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='folders', to='cloudstorage.user')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('path', models.CharField(max_length=1024)),
                ('weight', models.BigIntegerField()),
                ('share_token', models.UUIDField(blank=True, null=True, unique=True)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='files', to='cloudstorage.folder')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='files', to='cloudstorage.user')),
            ],
        ),
    ]
