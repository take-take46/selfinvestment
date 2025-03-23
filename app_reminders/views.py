from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import random

from .models import Reminder, MotivationalQuote, Achievement
from .serializers import ReminderSerializer, MotivationalQuoteSerializer, AchievementSerializer

from app_core.models import Habit, HabitLog, Goal


class ReminderViewSet(viewsets.ModelViewSet):
    """リマインダーの管理用ビューセット"""
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのリマインダーのみを取得"""
        return Reminder.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """作成時にユーザーを自動設定"""
        serializer.save(user=self.request.user)


class MotivationalQuoteViewSet(viewsets.ReadOnlyModelViewSet):
    """モチベーション名言の取得用ビューセット"""
    serializer_class = MotivationalQuoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """全ての名言を取得（共有リソース）"""
        return MotivationalQuote.objects.all()


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """実績の取得用ビューセット"""
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの実績のみを取得"""
        return Achievement.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def random_quote(request):
    """ランダムにモチベーション名言を取得するAPI"""
    # カテゴリでフィルタリング（オプション）
    category = request.query_params.get('category')
    
    quotes = MotivationalQuote.objects.all()
    if category:
        quotes = quotes.filter(category=category)
    
    if not quotes.exists():
        return Response({"error": "No quotes found"}, status=status.HTTP_404_NOT_FOUND)
    
    # ランダムに1つ選択
    random_index = random.randint(0, quotes.count() - 1)
    quote = quotes[random_index]
    
    serializer = MotivationalQuoteSerializer(quote)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_reminders(request):
    """現在時刻に近いリマインダーを確認するAPI"""
    now = timezone.now()
    
    # 現在時刻から30分以内のリマインダーを取得
    upcoming_reminders = Reminder.objects.filter(
        user=request.user,
        is_active=True,
        trigger_time__gte=now,
        trigger_time__lte=now + timedelta(minutes=30)
    )
    
    # 過去24時間以内で通知されていないリマインダーも含める
    overdue_reminders = Reminder.objects.filter(
        user=request.user,
        is_active=True,
        trigger_time__lt=now,
        trigger_time__gte=now - timedelta(hours=24)
    )
    
    all_reminders = list(upcoming_reminders) + list(overdue_reminders)
    serializer = ReminderSerializer(all_reminders, many=True)
    
    return Response({
        "reminders": serializer.data,
        "count": len(all_reminders)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def earn_achievement(request):
    """実績を獲得するAPI"""
    # 実績タイプを取得
    achievement_type = request.data.get('type')
    
    if not achievement_type:
        return Response({"error": "Achievement type is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 実績の内容を決定
    achievement_data = None
    
    if achievement_type == 'streak':
        days = int(request.data.get('days', 0))
        
        if days <= 0:
            return Response({"error": "Days must be positive"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 既存の同種の実績をチェック
        existing = Achievement.objects.filter(
            user=request.user,
            title__contains=f"{days}日間",
            badge_type='streak'
        ).first()
        
        if existing:
            return Response({"error": "Achievement already earned", "achievement": AchievementSerializer(existing).data}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 新しい実績を作成
        achievement_data = {
            'title': f"{days}日間継続達成",
            'description': f"おめでとうございます！{days}日間連続して習慣を継続しました。",
            'badge_type': 'streak',
            'icon': 'calendar-check'
        }
    
    elif achievement_type == 'milestone':
        milestone = request.data.get('milestone')
        target = request.data.get('target')
        
        if not milestone or not target:
            return Response({"error": "Milestone and target are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 既存の同種の実績をチェック
        existing = Achievement.objects.filter(
            user=request.user,
            title__contains=milestone,
            badge_type='milestone'
        ).first()
        
        if existing:
            return Response({"error": "Achievement already earned", "achievement": AchievementSerializer(existing).data}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 新しい実績を作成
        achievement_data = {
            'title': f"{milestone}達成",
            'description': f"おめでとうございます！{target}を達成しました。",
            'badge_type': 'milestone',
            'icon': 'award'
        }
    
    elif achievement_type == 'completion':
        goal_id = request.data.get('goal_id')
        
        if not goal_id:
            return Response({"error": "Goal ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 目標を取得
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        
        # 既存の同種の実績をチェック
        existing = Achievement.objects.filter(
            user=request.user,
            title__contains=goal.title[:20],
            badge_type='completion'
        ).first()
        
        if existing:
            return Response({"error": "Achievement already earned", "achievement": AchievementSerializer(existing).data}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # 新しい実績を作成
        achievement_data = {
            'title': f"目標達成: {goal.title[:20]}",
            'description': f"おめでとうございます！目標「{goal.title}」を達成しました。",
            'badge_type': 'completion',
            'icon': 'target'
        }
    
    else:
        return Response({"error": "Invalid achievement type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 実績を保存
    achievement = Achievement.objects.create(
        user=request.user,
        **achievement_data
    )
    
    serializer = AchievementSerializer(achievement)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_streak_achievements(request):
    """習慣の継続日数に基づいて自動的に実績を付与するAPI"""
    # 習慣IDを取得（オプション、指定がなければ全ての習慣をチェック）
    habit_id = request.data.get('habit_id')
    
    if habit_id:
        habits = [get_object_or_404(Habit, id=habit_id, user=request.user)]
    else:
        habits = Habit.objects.filter(user=request.user, is_active=True)
    
    # 各習慣の継続日数を計算
    results = []
    
    for habit in habits:
        streak = calculate_current_streak(habit)
        
        # 継続日数に応じた実績を付与
        achievements = []
        
        for days in [7, 30, 60, 90, 180, 365]:
            if streak >= days:
                # 既存の実績をチェック
                existing = Achievement.objects.filter(
                    user=request.user,
                    title__contains=f"{days}日間",
                    badge_type='streak'
                ).first()
                
                if not existing:
                    # 新しい実績を作成
                    achievement = Achievement.objects.create(
                        user=request.user,
                        title=f"{days}日間継続達成",
                        description=f"おめでとうございます！{habit.name}を{days}日間連続して継続しました。",
                        badge_type='streak',
                        icon='calendar-check'
                    )
                    
                    achievements.append(AchievementSerializer(achievement).data)
        
        results.append({
            'habit_id': habit.id,
            'habit_name': habit.name,
            'streak': streak,
            'new_achievements': achievements
        })
    
    return Response(results)


def calculate_current_streak(habit):
    """現在の継続日数を計算する関数"""
    logs = HabitLog.objects.filter(habit=habit).order_by('-log_date')
    
    if not logs:
        return 0
    
    streak = 0
    today = timezone.now().date()
    
    # 最新のログが今日または昨日でない場合はストリーク切れ
    latest_log_date = logs.first().log_date
    if (today - latest_log_date).days > 1:
        return 0
    
    # 連続した日数を計算
    current_date = latest_log_date
    
    while True:
        # その日のログがあるかチェック
        has_log = logs.filter(log_date=current_date).exists()
        
        if not has_log:
            break
        
        streak += 1
        current_date -= timedelta(days=1)
    
    return streak