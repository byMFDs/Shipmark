"""Write AuditLog entries: audit.log("hallmark.live.removed", project, reason="token_missing")."""
from .models import AuditLog


def log(action, target, actor=None, **metadata):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target._meta.label_lower,
        target_id=str(target.pk),
        target_repr=str(target)[:200],
        metadata=metadata,
    )
