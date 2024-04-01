from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
import uuid
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
  id          = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False, verbose_name='ID')
  username    = models.CharField(
                  _("username"),
                  max_length=150,
                  unique=True,
                  help_text=_(
                      "Required. Minimum 5 characters, up to 150. a-z, 0-9 and _ only."
                  ),
                  validators=[
                      RegexValidator(r"^[a-zA-Z0-9_]+\Z", message=_('Invalid characters!')),
                      MinLengthValidator(5),
                  ],
                  error_messages={
                      "unique": _("A user with that username already exists."),
                  },
                )
  first_name  = models.CharField(_("first name"), max_length=150, null=True, blank=True)
  last_name   = models.CharField(_("last name"), max_length=150, null=True, blank=True)
  email       = models.EmailField(_('email address'), unique=True)


