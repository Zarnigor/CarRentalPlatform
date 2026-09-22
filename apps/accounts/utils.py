from .models import Customer


def _customer_for(user) -> Customer | None:
    return Customer.objects.filter(user_id=user.pk).first()


def _me_data(user) -> dict:
    c = _customer_for(user)
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "license_no": c.license_no if c else None,
        "tier": c.tier if c else None,
        "risk_score": c.risk_score if c else None,
    }
