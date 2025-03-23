from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Reminder(models.Model):
    """リマインダーモデル"""
    
    REPEAT_CHOICES = [
        ('none', _('繰り返しなし')),
        ('daily', _('毎日')),
        ('weekdays', _('平日（月〜金）')),
        ('weekends', _('週末（土・日）')),
        ('weekly', _('毎週')),
        ('biweekly', _('隔週')),
        ('monthly', _('毎月')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reminders',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    trigger_time = models.DateTimeField(_('通知時間'))
    
    # 繰り返し設定
    repeat_pattern = models.CharField(_('繰り返しパターン'), max_length=20, choices=REPEAT_CHOICES, default='none')
    end_date = models.DateField(_('終了日'), null=True, blank=True, help_text=_('繰り返しの終了日'))
    
    # 関連モデルへの参照（オプション）
    related_goal = models.ForeignKey(
        'app_core.Goal', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reminders',
        verbose_name=_('関連目標')
    )
    related_habit = models.ForeignKey(
        'app_core.Habit', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reminders',
        verbose_name=_('関連習慣')
    )
    
    is_active = models.BooleanField(_('有効'), default=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('リマインダー')
        verbose_name_plural = _('リマインダー')
        ordering = ['trigger_time']
    
    def __str__(self):
        return self.title


class MotivationalQuote(models.Model):
    """モチベーションを高める名言モデル"""
    
    CATEGORY_CHOICES = [
        ('success', _('成功')),
        ('motivation', _('モチベーション')),
        ('learning', _('学習')),
        ('growth', _('成長')),
        ('consistency', _('継続')),
        ('wisdom', _('知恵')),
    ]
    
    content = models.TextField(_('内容'))
    author = models.CharField(_('著者'), max_length=100)
    source = models.CharField(_('出典'), max_length=255, blank=True)
    category = models.CharField(_('カテゴリ'), max_length=20, choices=CATEGORY_CHOICES, default='motivation')
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('モチベーション名言')
        verbose_name_plural = _('モチベーション名言')
    
    def __str__(self):
        return f"{self.content[:50]}... - {self.author}"


class Achievement(models.Model):
    """実績・達成バッジモデル"""
    
    BADGE_TYPE_CHOICES = [
        ('streak', _('継続ストリーク')),
        ('milestone', _('マイルストーン')),
        ('completion', _('完了')),
        ('progress', _('進捗')),
        ('special', _('特別')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='achievements',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'))
    badge_type = models.CharField(_('バッジタイプ'), max_length=20, choices=BADGE_TYPE_CHOICES)
    icon = models.CharField(_('アイコン名'), max_length=50, blank=True)
    achieved_at = models.DateTimeField(_('達成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('実績')
        verbose_name_plural = _('実績')
        ordering = ['-achieved_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
# Create your models here.
