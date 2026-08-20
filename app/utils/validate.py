import re

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
PASSWORD_EXAMPLE = (
    r'z8VkP9_3mXq~\h$M((G mTN|fBCSvH*xi<q$V~Iy2D"U(eG#C":CG),Ri>G[A\bTIT5ZAYpRFE;cHdY1'  # noqa: S105
)


def validate_username_format(value: str, field_label: str = "Value") -> str:
    """Shared format check: alphanumeric, hyphens allowed only in the middle."""
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValueError(f"{field_label} must follow the valid format")
    return value

