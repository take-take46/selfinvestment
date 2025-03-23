from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    """本のモデル"""
    
    STATUS_CHOICES = [
        ('not_started', _('未読')),
        ('in_progress', _('読書中')),
        ('completed', _('読了')),
        ('on_hold', _('中断')),
        ('abandoned', _('放棄')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='books',
        verbose_name=_('ユーザー')
    )
    title = models.CharField(_('タイトル'), max_length=255)
    author = models.CharField(_('著者'), max_length=255)
    isbn = models.CharField(_('ISBN'), max_length=13, blank=True)
    publisher = models.CharField(_('出版社'), max_length=100, blank=True)
    published_date = models.DateField(_('出版日'), null=True, blank=True)
    page_count = models.PositiveIntegerField(_('ページ数'), null=True, blank=True)
    cover_image = models.ImageField(_('表紙画像'), upload_to='book_covers/', null=True, blank=True)
    description = models.TextField(_('概要'), blank=True)
    
    status = models.CharField(_('状態'), max_length=20, choices=STATUS_CHOICES, default='not_started')
    start_date = models.DateField(_('読み始め日'), null=True, blank=True)
    finish_date = models.DateField(_('読了日'), null=True, blank=True)
    current_page = models.PositiveIntegerField(_('現在のページ'), null=True, blank=True)
    
    rating = models.PositiveSmallIntegerField(_('評価'), null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(_('レビュー'), blank=True)
    
    created_at = models.DateTimeField(_('登録日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    
    class Meta:
        verbose_name = _('本')
        verbose_name_plural = _('本')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        """読書の進捗率を計算"""
        if not self.page_count or not self.current_page:
            return 0
        return min(100, int((self.current_page / self.page_count) * 100))


class BookNote(models.Model):
    """本の中から取ったメモやハイライト"""
    
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name='notes',
        verbose_name=_('本')
    )
    content = models.TextField(_('内容'))
    page_number = models.PositiveIntegerField(_('ページ番号'), null=True, blank=True)
    highlight = models.BooleanField(_('ハイライト'), default=False)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('読書メモ')
        verbose_name_plural = _('読書メモ')
        ordering = ['page_number', 'created_at']
    
    def __str__(self):
        return f"{self.book.title} - P.{self.page_number if self.page_number else 'N/A'}"