from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("quran", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QuranReadingProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("goal_days", models.PositiveIntegerField(default=30)),
                ("reminder_enabled", models.BooleanField(default=False)),
                ("started_at", models.DateField(auto_now_add=True)),
                ("completed_at", models.DateField(blank=True, null=True)),
                ("reset_count", models.PositiveIntegerField(default=0)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="RecitationAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("surah_number", models.PositiveSmallIntegerField()),
                ("ayah_number", models.PositiveIntegerField()),
                ("verse_key", models.CharField(max_length=20)),
                ("transcript", models.TextField(blank=True)),
                ("score", models.PositiveSmallIntegerField(default=0)),
                ("mistakes", models.JSONField(blank=True, default=list)),
                ("feedback", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recitation_attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="HifzPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("verses_per_day", models.PositiveIntegerField(default=3)),
                ("repetition_target", models.PositiveIntegerField(default=5)),
                ("streak_days", models.PositiveIntegerField(default=0)),
                ("reminder_enabled", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="hifz_plan", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="HifzAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("surah_number", models.PositiveSmallIntegerField()),
                ("surah_name", models.CharField(blank=True, max_length=150)),
                ("start_ayah", models.PositiveIntegerField(default=1)),
                ("end_ayah", models.PositiveIntegerField(default=1)),
                ("repetition_target", models.PositiveIntegerField(default=5)),
                ("repetition_done", models.PositiveIntegerField(default=0)),
                ("next_review_at", models.DateField(blank=True, null=True)),
                ("difficulty", models.PositiveSmallIntegerField(default=1)),
                ("is_mastered", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hifz_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["is_mastered", "surah_number", "start_ayah"]},
        ),
        migrations.CreateModel(
            name="ReadSurah",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("surah_number", models.PositiveSmallIntegerField()),
                ("surah_name", models.CharField(blank=True, max_length=150)),
                ("surah_name_ar", models.CharField(blank=True, max_length=150)),
                ("verses_count", models.PositiveIntegerField(default=0)),
                ("marked_at", models.DateTimeField(auto_now_add=True)),
                ("progress", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="read_surahs", to="quran.quranreadingprogress")),
            ],
            options={"ordering": ["surah_number"], "unique_together": {("progress", "surah_number")}},
        ),
    ]
