from typing import Annotated

from pydantic import StringConstraints

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$")]
