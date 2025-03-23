from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""
    
    def create_user(self, email, username, password=None, **extra_fields):
        """通常ユーザーを作成"""
        if not email:
            raise ValueError(_('Emailは必須です'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        """スーパーユーザーを作成"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('スーパーユーザーはis_staff=Trueである必要があります'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('スーパーユーザーはis_superuser=Trueである必要があります'))
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """カスタムユーザーモデル"""
    
    email = models.EmailField(_('メールアドレス'), unique=True)
    username = models.CharField(_('ユーザー名'), max_length=50, unique=True)
    profile_image = models.ImageField(_('プロフィール画像'), upload_to='profile_images/', null=True, blank=True)
    bio = models.TextField(_('自己紹介'), blank=True)
    date_joined = models.DateTimeField(_('登録日'), default=timezone.now)
    time_zone = models.CharField(_('タイムゾーン'), max_length=50, default='Asia/Tokyo')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('ユーザー')
        verbose_name_plural = _('ユーザー')
    
    def __str__(self):
        return self.username

# Create your models here.
