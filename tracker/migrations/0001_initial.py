from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CycleEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('is_period_day', models.BooleanField(default=True)),
                ('flow', models.CharField(
                    blank=True, null=True, max_length=20,
                    choices=[('spotting','Spotting'),('light','Light'),('medium','Medium'),('heavy','Heavy')]
                )),
                ('mood', models.CharField(
                    blank=True, null=True, max_length=20,
                    choices=[('calm','Calm'),('anxious','Anxious'),('irritable','Irritable'),
                             ('happy','Happy'),('sad','Sad'),('fatigued','Fatigued'),('energized','Energized')]
                )),
                ('cramps', models.BooleanField(default=False)),
                ('headache', models.BooleanField(default=False)),
                ('bloating', models.BooleanField(default=False)),
                ('fatigue', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-date']},
        ),
    ]
