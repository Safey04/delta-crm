import logging

from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models import User
from app.models.role import Permission, Role, RolePermission  # noqa: F401
from app.repository import role as role_repo
from app.repository import user as user_repo

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

logger = logging.getLogger(__name__)

# Define all permissions
PERMISSIONS = [
    ("customer", "view"), ("customer", "create"), ("customer", "edit"), ("customer", "delete"),
    ("service_request", "view"), ("service_request", "create"), ("service_request", "edit"),
    ("service_request", "delete"), ("service_request", "approve"),
    ("quotation", "view"), ("quotation", "create"), ("quotation", "edit"),
    ("quotation", "delete"), ("quotation", "approve"),
    ("inventory", "view"), ("inventory", "create"), ("inventory", "edit"),
    ("inventory", "delete"), ("inventory", "request"),
    ("invoice", "view"), ("invoice", "create"), ("invoice", "edit"), ("invoice", "delete"),
    ("report", "view"), ("report", "financial"), ("report", "operational"), ("report", "inventory"),
    ("user", "view"), ("user", "create"), ("user", "edit"), ("user", "delete"),
]

# Default role → permission mappings
DEFAULT_ROLES = {
    "manager": [
        "customer.*", "service_request.*", "quotation.*", "inventory.*",
        "invoice.*", "report.*", "user.*",
    ],
    "support": [
        "customer.view", "customer.create", "customer.edit",
        "service_request.view", "service_request.create", "service_request.edit",
        "quotation.view", "quotation.create", "quotation.edit",
        "inventory.view",
        "invoice.view",
        "report.view", "report.operational",
    ],
    "engineer": [
        "customer.view",
        "service_request.view", "service_request.edit",
        "inventory.view", "inventory.request",
    ],
    "warehouse": [
        "customer.view",
        "service_request.view",
        "inventory.view", "inventory.create", "inventory.edit", "inventory.delete",
        "report.view", "report.inventory",
    ],
}


def _match_permission(perm_pattern: str, resource: str, action: str) -> bool:
    """Check if a permission pattern (e.g. 'customer.*') matches a resource.action."""
    pat_resource, pat_action = perm_pattern.split(".")
    if pat_resource != resource:
        return False
    return pat_action == "*" or pat_action == action


def seed_roles_and_permissions(session: Session) -> None:
    """Create default permissions and roles if they don't exist."""
    # Create all permissions
    perm_map: dict[tuple[str, str], Permission] = {}
    for resource, action in PERMISSIONS:
        perm = role_repo.get_or_create_permission(
            session=session, resource=resource, action=action,
            description=f"{action} {resource}",
        )
        perm_map[(resource, action)] = perm

    # Create default roles with permissions
    for role_name, patterns in DEFAULT_ROLES.items():
        existing = role_repo.get_role_by_name(session=session, name=role_name)
        if existing:
            continue

        from app.domain.role import RoleCreate
        role = role_repo.create_role(
            session=session,
            role_in=RoleCreate(name=role_name, description=f"Default {role_name} role"),
            is_system=True,
        )

        # Resolve patterns to permission IDs
        perm_ids = []
        for pattern in patterns:
            for (resource, action), perm in perm_map.items():
                if _match_permission(pattern, resource, action):
                    perm_ids.append(perm.id)

        role_repo.set_role_permissions(
            session=session, role_id=role.id, permission_ids=perm_ids,
        )


def init_db(session: Session) -> None:
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    # Seed roles and permissions
    seed_roles_and_permissions(session)

    # Seed default SLA configs
    from app.domain.sla_config import SLAConfigCreate
    from app.repository import sla_config as sla_repo
    from app.services.sla import DEFAULT_SLA

    for segment, hours in DEFAULT_SLA.items():
        sla_repo.upsert_sla_config(
            session=session,
            config_in=SLAConfigCreate(
                segment=segment,
                response_hours=hours["response"],
                resolution_hours=hours["resolution"],
            ),
        )

    # Create first superuser (manager role) if doesn't exist
    user = user_repo.get_user_by_email(session=session, email=settings.FIRST_SUPERUSER)
    if not user:
        manager_role = role_repo.get_role_by_name(session=session, name="manager")
        if manager_role:
            logger.warning(
                "First superuser local record must be created after Supabase auth user exists. "
                "Create the Supabase auth user first, then the app will sync on first login."
            )
