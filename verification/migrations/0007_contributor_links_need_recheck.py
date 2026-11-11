"""Repo owner no longer counts commits in someone else's repository (only owned, non-fork repos).

Links that passed only by commit count do not vanish silently: they become "needs re-check" (the
mark is withheld, the owner sees a neutral message) and each one is logged. `reverify_repos` or the
owner's "Check repository" button decides with the current rules.
"""
from django.db import migrations

ACTION = "hallmark.authored.needs_recheck"


def mark(apps, schema_editor):
    RepoLink = apps.get_model("verification", "RepoLink")
    AuditLog = apps.get_model("moderation", "AuditLog")
    for link in RepoLink.objects.filter(is_owner=False).exclude(review_state="needs_recheck").select_related("project"):
        link.review_state = "needs_recheck"
        link.save(update_fields=["review_state"])
        AuditLog.objects.create(
            actor=None, action=ACTION, target_type="projects.project", target_id=str(link.project_id),
            target_repr=str(link.project.name)[:200],
            metadata={"repo": link.repo_full_name, "reason": "contributor_rule_removed",
                      "commits": link.user_commit_count},
        )


def unmark(apps, schema_editor):
    # Back to the old rules: those links earn by commit count again. AuditLog entries stay (history).
    apps.get_model("verification", "RepoLink").objects.filter(is_owner=False, review_state="needs_recheck").update(review_state="")


class Migration(migrations.Migration):
    dependencies = [
        ("verification", "0006_repolink_facts_and_review"),
        ("moderation", "0002_report"),
    ]
    operations = [migrations.RunPython(mark, unmark)]
