from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DashboardSetting(models.Model):
    """ダッシュボード設定モデル"""
    
    THEME_CHOICES = [
        ('light', _('ライト')),
        ('dark', _('ダーク')),
        ('auto', _('システム設定に合わせる')),
    ]
    
    DEFAULT_VIEW_CHOICES = [
        ('dashboard', _('ダッシュボード')),
        ('learning', _('学習記録')),
        ('habits', _('習慣トラッキング')),
        ('books', _('読書管理')),
        ('calendar', _('カレンダー')),
        ('goals', _('目標設定')),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboard_settings',
        verbose_name=_('ユーザー')
    )
    theme = models.CharField(_('テーマ'), max_length=10, choices=THEME_CHOICES, default='light')
    default_view = models.CharField(_('デフォルト表示'), max_length=20, choices=DEFAULT_VIEW_CHOICES, default='dashboard')
    
    # ウィジェット表示設定（JSONフィールド）
    widget_layout = models.JSONField(
        _('ウィジェットレイアウト'),
        default=dict,
        help_text=_('ダッシュボードのウィジェット配置設定')
    )
    
    # データ表示設定
    show_streak_counts = models.BooleanField(_('連続達成数を表示'), default=True)
    show_goal_progress = models.BooleanField(_('目標進捗を表示'), default=True)
    show_habit_summary = models.BooleanField(_('習慣サマリーを表示'), default=True)
    show_reading_stats = models.BooleanField(_('読書統計を表示'), default=True)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('ダッシュボード設定')
        verbose_name_plural = _('ダッシュボード設定')
    
    def __str__(self):
        return f"{self.user.username}のダッシュボード設定"


class Widget(models.Model):
    """ダッシュボードウィジェットモデル"""
    
    WIDGET_TYPE_CHOICES = [
        ('habit_tracker', _('習慣トラッカー')),
        ('goal_progress', _('目標進捗')),
        ('reading_stats', _('読書統計')),
        ('calendar', _('カレンダー')),
        ('recent_learning', _('最近の学習')),
        ('streak_calendar', _('ストリークカレンダー')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='widgets',
        verbose_name=_('ユーザー')
    )
    widget_type = models.CharField(_('ウィジェットタイプ'), max_length=30, choices=WIDGET_TYPE_CHOICES)
    title = models.CharField(_('タイトル'), max_length=100)
    is_enabled = models.BooleanField(_('有効'), default=True)
    position = models.PositiveSmallIntegerField(_('表示位置'), default=0)
    settings = models.JSONField(_('設定'), default=dict)
    
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('ウィジェット')
        verbose_name_plural = _('ウィジェット')
        ordering = ['position']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"