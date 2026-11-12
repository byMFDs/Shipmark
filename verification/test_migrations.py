"""Data migrations keep existing proof visible as a state, never delete it silently."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone

BEFORE = [("verification", "0006_repolink_facts_and_review"), ("moderation", "0002_report"),
          ("projects", "0004_project_repo_token")]  # later project fields are unknown to this old state
AFTER = [("verification", "0007_contributor_links_need_recheck")]


class ContributorLinksMigrationTests(TransactionTestCase):
    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        self.migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_contributor_links_become_needs_recheck_and_are_logged(self):
        apps = self.migrate(BEFORE)
        User = apps.get_model("accounts", "User")
        Project = apps.get_model("projects", "Project")
        RepoLink = apps.get_model("verification", "RepoLink")
        owner = User.objects.create(username="ann")
        owned = Project.objects.create(owner=owner, name="Owned", slug="owned", tagline="t")
        contributed = Project.objects.create(owner=owner, name="Contributed", slug="contributed", tagline="t")
        RepoLink.objects.create(project=owned, repo_full_name="ann/a", github_repo_id=1, is_owner=True,
                                checked_at=timezone.now())
        RepoLink.objects.create(project=contributed, repo_full_name="org/b", github_repo_id=2, is_owner=False,
                                user_commit_count=12, checked_at=timezone.now())

        apps = self.migrate(AFTER)
        RepoLink = apps.get_model("verification", "RepoLink")
        AuditLog = apps.get_model("moderation", "AuditLog")
        self.assertEqual(RepoLink.objects.count(), 2)  # nothing deleted
        self.assertEqual(RepoLink.objects.get(github_repo_id=1).review_state, "")
        self.assertEqual(RepoLink.objects.get(github_repo_id=2).review_state, "needs_recheck")
        entry = AuditLog.objects.get(action="hallmark.authored.needs_recheck")
        self.assertEqual(entry.target_id, str(contributed.pk))
        self.assertEqual(entry.metadata["reason"], "contributor_rule_removed")

        apps = self.migrate(BEFORE)  # reversible
        self.assertEqual(apps.get_model("verification", "RepoLink").objects.get(github_repo_id=2).review_state, "")
