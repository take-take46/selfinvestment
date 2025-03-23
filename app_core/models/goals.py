from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Goal(models.Model):
    """目標モデル"""
    
    STATUS_CHOICES = [
        ('not_started', _('未開始')),
        ('in_progress', _('進行中')),
        ('completed', _('達成済み')),
        ('abandoned', _('放棄')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('低')),
        ('medium', _('中')),
        ('high', _('高')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='goals',
        verbose_name=_('ユーザー')
    )
    parent_goal = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='sub_goals',
        null=True,
        blank=True,
        verbose_name=_('親目標')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    start_date = models.DateField(_('開始日'))
    due_date = models.DateField(_('期限日'), null=True, blank=True)
    status = models.CharField(_('状態'), max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.CharField(_('優先度'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    progress_percentage = models.PositiveSmallIntegerField(_('進捗率'), default=0)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('目標')
        verbose_name_plural = _('目標')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def update_progress(self):
        """サブステップの完了状態に基づいて進捗率を更新"""
        steps = self.goal_steps.all()
        if not steps:
            return
        
        completed_steps = steps.filter(is_completed=True).count()
        total_steps = steps.count()
        self.progress_percentage = int((completed_steps / total_steps) * 100)
        self.save(update_fields=['progress_percentage'])


class GoalStep(models.Model):
    """目標の達成ステップモデル"""
    
    goal = models.ForeignKey(
        Goal, 
        on_delete=models.CASCADE, 
        related_name='goal_steps',
        verbose_name=_('目標')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    description = models.TextField(_('説明'), blank=True)
    order = models.PositiveSmallIntegerField(_('順序'), default=0)
    is_completed = models.BooleanField(_('完了'), default=False)
    due_date = models.DateField(_('期限日'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('目標ステップ')
        verbose_name_plural = _('目標ステップ')
        ordering = ['order']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """保存時に親目標の進捗状況を更新"""
        super().save(*args, **kwargs)
        self.goal.update_progress()


class GoalProgress(models.Model):
    """目標の進捗記録モデル"""
    
    goal = models.ForeignKey(
        Goal, 
        on_delete=models.CASCADE, 
        related_name='progress_logs',
        verbose_name=_('目標')
    )
    date = models.DateField(_('日付'))
    progress = models.PositiveSmallIntegerField(_('進捗率'), default=0)
    notes = models.TextField(_('メモ'), blank=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('目標進捗')
        verbose_name_plural = _('目標進捗')
        unique_together = ('goal', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.goal.title} - {self.date} ({self.progress}%)"