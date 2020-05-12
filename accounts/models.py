import datetime

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import JSONField
from django.db import models


class DiscordUserManager(BaseUserManager):
    """
    Mainly utility for Django manage.py commands to handle creating users and
    superusers from the script.
    """
    def create_user(self, id, email, username, discriminator, password=None, **extra_fields):
        if id is None:
            return ValueError("id required.")
        if email is None:
            return ValueError("email required.")
        if username is None:
            return ValueError("username required.")
        if discriminator is None:
            return ValueError("discriminator required.")

        user = self.model(
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
            id=id,
            email=self.normalize_email(email),
            username=username,
            discriminator=discriminator,
            **extra_fields
        )
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, id, email, username, discriminator, password, **extra_fields):
        if password is None:
            return ValueError("Super User requires password")
        user = self.create_user(id, email, username, discriminator, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user

class DiscordUser(AbstractUser):
    """
    Custom AbstractUser for ZCL that assumes that all our users have a Discord
    account. This is required for our website and our main authentication will
    go through this.
    """

    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Prevent Precision errors from large numbers. Keep id as string.
    id = models.CharField(max_length=25, unique=True, primary_key=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(verbose_name='Email Address', max_length=255, unique=True)
    discriminator = models.IntegerField()
    avatar = models.CharField(max_length=255, blank=True, null=True)
    client_heartbeat = models.DateTimeField(null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['id', 'username', 'discriminator']
    objects = DiscordUserManager()


class SocialAccount(models.Model):
    """
    Represents any of the social accounts that we have OAUTH flows for.
    This model stores the extra_data which has the tokens and expirations.

    This is used to show connections as well as make API requests.

    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE, related_name='connections')
    provider = models.CharField(max_length=100)
    username = models.CharField(max_length=200, default="No Username")
    extra_data = JSONField(default=dict)


    def __str__(self):
        return "{0} - {1}".format(self.user, self.provider)



class AppToken(models.Model):
    """
    Represents App Tokens at the application level, and not the user.
    """
    created = models.DateTimeField(auto_created=True, auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    provider = models.CharField(max_length=50, unique=True)
    extra_data = JSONField(default=dict)

    @property
    def data(self):
        """
        Annotates the extra data with expires_at
        Returns
        -------

        """
        expires_in = self.extra_data.get('expires_in', 0)
        expires_at = self.updated + datetime.timedelta(seconds=expires_in)
        result = self.extra_data
        result['expires_at'] = expires_at
        return result


