from django.db import migrations

CATEGORIES = [
    ("Residential", "Houses, apartments, and other living spaces."),
    ("Commercial", "Offices, retail, and business premises."),
    ("Renovation", "Remodeling and refurbishment of existing structures."),
    ("Infrastructure", "Roads, bridges, and public works."),
]


def seed_categories(apps, schema_editor):
    ProjectCategory = apps.get_model("projects", "ProjectCategory")
    for name, description in CATEGORIES:
        ProjectCategory.objects.get_or_create(
            name=name, defaults={"description": description}
        )


def unseed_categories(apps, schema_editor):
    ProjectCategory = apps.get_model("projects", "ProjectCategory")
    ProjectCategory.objects.filter(name__in=[c[0] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
