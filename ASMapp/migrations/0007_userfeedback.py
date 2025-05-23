# Generated by Django 5.1.2 on 2025-04-27 05:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ASMapp', '0006_user_completed_onboarding'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('bug', 'Bug Report'), ('feature', 'Feature Request'), ('usability', 'Usability Issue'), ('praise', 'Praise'), ('other', 'Other')], max_length=20)),
                ('rating', models.IntegerField(blank=True, null=True)),
                ('feedback_text', models.TextField()),
                ('contact_consent', models.BooleanField(default=False)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('page_url', models.URLField()),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ASMapp.user')),
            ],
        ),
    ]
