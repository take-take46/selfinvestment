from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class CalendarEvent(models.Model):
    """カレンダーイベントモデル"""
    
    EVENT_CATEGORY_CHOICES = [
        ('study', _('勉強')),
        ('exercise', _('運動')),
        ('meeting', _('ミーティング')),
        ('reading', _('読書')),
        ('personal', _('個人')),
        ('other', _('その他')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='calendar_events',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    start_time = models.DateTimeField(_('開始時間'))
    end_time = models.DateTimeField(_('終了時間'))
    all_day = models.BooleanField(_('終日'), default=False)
    category = models.CharField(_('カテゴリ'), max_length=20, choices=EVENT_CATEGORY_CHOICES, default='other')
    location = models.CharField(_('場所'), max_length=255, blank=True)
    
    # 繰り返し設定
    is_recurring = models.BooleanField(_('繰り返し'), default=False)
    recurring_pattern = models.CharField(_('繰り返しパターン'), max_length=50, blank=True,
                                       help_text=_('daily, weekly, monthly, yearly'))
    recurring_end_date = models.DateField(_('繰り返し終了日'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('カレンダーイベント')
        verbose_name_plural = _('カレンダーイベント')
        ordering = ['start_time']
    
    def __str__(self):
        return self.title


class DailyJournal(models.Model):
    """日々の活動記録・日記モデル"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='daily_journals',
        verbose_name=_('ユーザー')
    )
    date = models.DateField(_('日付'))
    content = models.TextField(_('内容'))
    mood = models.CharField(_('気分'), max_length=50, blank=True)
    productivity_rating = models.PositiveSmallIntegerField(
        _('生産性評価'), 
        null=True, 
        blank=True, 
        choices=[(i, i) for i in range(1, 11)]
    )
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('日記')
        verbose_name_plural = _('日記')
        unique_together = ('user', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username}の日記 - {self.date}"