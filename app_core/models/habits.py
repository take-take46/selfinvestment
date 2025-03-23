from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Habit(models.Model):
    """習慣モデル"""
    
    CATEGORY_CHOICES = [
        ('study', _('勉強')),
        ('exercise', _('運動')),
        ('reading', _('読書')),
        ('meditation', _('瞑想')),
        ('programming', _('プログラミング')),
        ('language', _('語学')),
        ('other', _('その他')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='habits',
        verbose_name=_('ユーザー')
    )
    name = models.CharField(_('習慣名'), max_length=100)
    description = models.TextField(_('説明'), blank=True)
    category = models.CharField(_('カテゴリ'), max_length=20, choices=CATEGORY_CHOICES, default='other')
    target_value = models.FloatField(_('目標値'), default=0)
    unit_of_measure = models.CharField(_('単位'), max_length=20, default='分')
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    is_active = models.BooleanField(_('有効'), default=True)
    
    class Meta:
        verbose_name = _('習慣')
        verbose_name_plural = _('習慣')
    
    def __str__(self):
        return self.name


class HabitLog(models.Model):
    """習慣の記録モデル"""
    
    habit = models.ForeignKey(
        Habit, 
        on_delete=models.CASCADE, 
        related_name='logs',
        verbose_name=_('習慣')
    )
    log_date = models.DateField(_('日付'))
    value = models.FloatField(_('値'))
    notes = models.TextField(_('メモ'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('習慣記録')
        verbose_name_plural = _('習慣記録')
        unique_together = ('habit', 'log_date')
        ordering = ['-log_date']
    
    def __str__(self):
        return f"{self.habit.name} - {self.log_date}"