from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

from .models import ActivitySummary, ProductivityInsight, LearningPattern
from .serializers import ActivitySummarySerializer, ProductivityInsightSerializer, LearningPatternSerializer

from app_core.models import (
    LearningEntry, Habit, HabitLog, Book, CalendarEvent, Goal, GoalStep, GoalProgress, DailyJournal
)


class ActivitySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """活動サマリーの取得用ビューセット"""
    serializer_class = ActivitySummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのサマリーのみを取得"""
        return ActivitySummary.objects.filter(user=self.request.user)


class ProductivityInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """生産性インサイトの取得用ビューセット"""
    serializer_class = ProductivityInsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーのインサイトのみを取得"""
        return ProductivityInsight.objects.filter(user=self.request.user)


class LearningPatternViewSet(viewsets.ReadOnlyModelViewSet):
    """学習パターンの取得用ビューセット"""
    serializer_class = LearningPatternSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """ログインユーザーの学習パターンのみを取得"""
        return LearningPattern.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_activity_summary(request):
    """活動サマリーを生成するAPI"""
    period_type = request.data.get('period_type', 'daily')
    date_str = request.data.get('date')
    
    if not date_str:
        date = datetime.now().date()
    else:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # 期間の開始日と終了日を計算
    if period_type == 'daily':
        start_date = date
        end_date = date
    elif period_type == 'weekly':
        start_date = date - timedelta(days=date.weekday())
        end_date = start_date + timedelta(days=6)
    elif period_type == 'monthly':
        start_date = date.replace(day=1)
        if start_date.month == 12:
            end_date = date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    else:
        return Response({"error": "Invalid period_type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 既存のサマリーがあれば更新、なければ新規作成
    summary, created = ActivitySummary.objects.get_or_create(
        user=request.user,
        period_type=period_type,
        start_date=start_date,
        defaults={
            'end_date': end_date,
            'activity_data': {}
        }
    )
    
    if not created:
        summary.end_date = end_date
    
    # 学習時間統計の計算
    study_habits = Habit.objects.filter(
        user=request.user,
        category__in=['study', 'programming', 'language']
    )
    study_habit_ids = [habit.id for habit in study_habits]
    
    study_logs = HabitLog.objects.filter(
        habit__id__in=study_habit_ids,
        log_date__gte=start_date,
        log_date__lte=end_date
    )
    
    total_study_time = sum(log.value for log in study_logs)
    days_in_period = (end_date - start_date).days + 1
    avg_daily_study_time = total_study_time / days_in_period if days_in_period > 0 else 0
    
    # 習慣達成統計の計算
    all_habits = Habit.objects.filter(user=request.user, is_active=True)
    all_habit_logs = HabitLog.objects.filter(
        habit__in=all_habits,
        log_date__gte=start_date,
        log_date__lte=end_date
    )
    
    total_habits_completed = all_habit_logs.count()
    total_possible_completions = all_habits.count() * days_in_period
    habit_completion_rate = (total_habits_completed / total_possible_completions * 100
                            if total_possible_completions > 0 else 0)
    
    # 読書統計の計算
    books = Book.objects.filter(user=request.user)
    books_completed = books.filter(
        finish_date__gte=start_date,
        finish_date__lte=end_date
    ).count()
    
    pages_read = 0
    for book in books:
        if book.status == 'completed' and book.finish_date and start_date <= book.finish_date <= end_date:
            # 読了した本の場合
            pages_read += book.page_count if book.page_count else 0
        elif book.status == 'in_progress':
            # 読書中の本の場合、期間内の進捗を推定
            if book.start_date and book.current_page:
                if book.start_date <= end_date:
                    total_days = (datetime.now().date() - book.start_date).days
                    if total_days > 0:
                        pages_per_day = book.current_page / total_days
                        overlap_start = max(start_date, book.start_date)
                        overlap_end = min(end_date, datetime.now().date())
                        overlap_days = (overlap_end - overlap_start).days + 1
                        pages_read += int(pages_per_day * overlap_days)
    
    # 目標進捗統計の計算
    goals = Goal.objects.filter(user=request.user)
    goals_completed = goals.filter(
        status='completed',
        updated_at__gte=start_date,
        updated_at__lte=end_date
    ).count()
    
    goal_steps = GoalStep.objects.filter(
        goal__user=request.user,
        is_completed=True,
        updated_at__gte=start_date,
        updated_at__lte=end_date
    )
    goal_steps_completed = goal_steps.count()
    
    # 活動データの整形
    activity_data = {
        'study_time_by_day': defaultdict(float),
        'habit_completion_by_day': defaultdict(int),
        'pages_read_by_day': defaultdict(int),
        'goal_progress_by_day': defaultdict(float),
    }
    
    # 各日ごとのデータを集計
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # 学習時間
        day_study_logs = study_logs.filter(log_date=current_date)
        activity_data['study_time_by_day'][date_str] = sum(log.value for log in day_study_logs)
        
        # 習慣達成
        day_habit_logs = all_habit_logs.filter(log_date=current_date)
        activity_data['habit_completion_by_day'][date_str] = day_habit_logs.count()
        
        # 目標進捗
        day_goal_progresses = GoalProgress.objects.filter(
            goal__user=request.user,
            date=current_date
        )
        if day_goal_progresses.count() > 0:
            avg_progress = sum(p.progress for p in day_goal_progresses) / day_goal_progresses.count()
            activity_data['goal_progress_by_day'][date_str] = avg_progress
        
        current_date += timedelta(days=1)
    
    # サマリーの更新
    summary.total_study_time = int(total_study_time)
    summary.avg_daily_study_time = float(avg_daily_study_time)
    summary.total_habits_completed = total_habits_completed
    summary.habit_completion_rate = float(habit_completion_rate)
    summary.pages_read = pages_read
    summary.books_completed = books_completed
    summary.goals_completed = goals_completed
    summary.goal_steps_completed = goal_steps_completed
    summary.activity_data = dict(activity_data)
    summary.save()
    
    serializer = ActivitySummarySerializer(summary)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_insights(request):
    """ユーザーの生産性に関するインサイトを生成するAPI"""
    # 過去3ヶ月分のデータを分析対象とする
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    # 習慣ログデータの取得
    habit_logs = HabitLog.objects.filter(
        habit__user=request.user,
        log_date__gte=start_date,
        log_date__lte=end_date
    ).select_related('habit')
    
    # データが少ない場合はエラーを返す
    if habit_logs.count() < 7:  # 最低1週間分のデータが必要
        return Response({
            "error": "Not enough data for analysis. Please log more data."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 時間帯パターンのインサイト
    time_pattern_insight = generate_time_pattern_insight(request.user, habit_logs)
    
    # 相関分析のインサイト
    correlation_insight = generate_correlation_insight(request.user, habit_logs)
    
    # トレンド分析のインサイト
    trend_insight = generate_trend_insight(request.user, habit_logs)
    
    # 推奨事項のインサイト
    recommendation_insight = generate_recommendation_insight(request.user, habit_logs)
    
    # 生成したインサイトのIDを返す
    return Response({
        "insights": [
            time_pattern_insight.id,
            correlation_insight.id,
            trend_insight.id,
            recommendation_insight.id
        ]
    })


def generate_time_pattern_insight(user, habit_logs):
    """時間帯パターンに関するインサイトを生成"""
    # カレンダーイベントから時間帯情報を取得
    events = CalendarEvent.objects.filter(
        user=user,
        category__in=['study', 'exercise', 'reading'],
        start_time__date__gte=datetime.now().date() - timedelta(days=90)
    )
    
    # 時間帯ごとの活動データを集計
    hourly_data = defaultdict(int)
    event_count = defaultdict(int)
    
    for event in events:
        hour = event.start_time.hour
        hour_range = f"{hour:02d}:00-{hour+1:02d}:00"
        
        # イベントの長さ（時間）を計算
        duration_hours = (event.end_time - event.start_time).total_seconds() / 3600
        hourly_data[hour_range] += duration_hours
        event_count[hour_range] += 1
    
    # 平均活動時間を計算
    avg_hourly_data = {}
    for hour_range, total_hours in hourly_data.items():
        if event_count[hour_range] > 0:
            avg_hourly_data[hour_range] = total_hours / event_count[hour_range]
    
    # 最も活動的な時間帯を特定
    if avg_hourly_data:
        best_time_range = max(avg_hourly_data.items(), key=lambda x: x[1])[0]
    else:
        best_time_range = "データ不足"
    
    # 曜日ごとの活動データを集計
    weekday_data = defaultdict(int)
    weekday_count = defaultdict(int)
    weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    
    for event in events:
        weekday = event.start_time.weekday()
        weekday_name = weekday_names[weekday]
        
        # イベントの長さ（時間）を計算
        duration_hours = (event.end_time - event.start_time).total_seconds() / 3600
        weekday_data[weekday_name] += duration_hours
        weekday_count[weekday_name] += 1
    
    # 平均活動時間を計算
    avg_weekday_data = {}
    for weekday_name, total_hours in weekday_data.items():
        if weekday_count[weekday_name] > 0:
            avg_weekday_data[weekday_name] = total_hours / weekday_count[weekday_name]
    
    # 最も活動的な曜日を特定
    if avg_weekday_data:
        best_weekday = max(avg_weekday_data.items(), key=lambda x: x[1])[0]
    else:
        best_weekday = "データ不足"
    
    # インサイトタイトルと説明文を生成
    title = "あなたの最適な学習・活動時間帯"
    description = f"分析の結果、あなたが最も効率的に活動できるのは {best_time_range} の時間帯と {best_weekday} です。"
    
    if best_time_range != "データ不足":
        description += f" {best_time_range} の時間帯には平均 {avg_hourly_data[best_time_range]:.1f} 時間の活動を行っており、"
        description += "この時間帯を活用して重要なタスクをスケジュールすることで生産性を最大化できるでしょう。"
    
    # インサイトを保存
    insight_data = {
        "hourly_data": avg_hourly_data,
        "weekday_data": avg_weekday_data,
        "best_time_range": best_time_range,
        "best_weekday": best_weekday
    }
    
    insight, created = ProductivityInsight.objects.update_or_create(
        user=user,
        insight_type="time_pattern",
        defaults={
            "title": title,
            "description": description,
            "data": insight_data
        }
    )
    
    return insight


def generate_correlation_insight(user, habit_logs):
    """異なる活動間の相関関係に関するインサイトを生成"""
    # 習慣データをパンダスデータフレームに変換
    habit_data = []
    for log in habit_logs:
        habit_data.append({
            'date': log.log_date,
            'habit_id': log.habit.id,
            'habit_name': log.habit.name,
            'category': log.habit.category,
            'value': log.value
        })
    
    if not habit_data:
        # データがない場合はデフォルトのインサイトを返す
        insight, created = ProductivityInsight.objects.update_or_create(
            user=user,
            insight_type="correlation",
            defaults={
                "title": "活動間の相関関係",
                "description": "まだ十分なデータがないため、活動間の相関関係を分析できません。",
                "data": {}
            }
        )
        return insight
    
    df = pd.DataFrame(habit_data)
    
    # 日付ごと、習慣ごとに集計
    pivot_df = df.pivot_table(index='date', columns='habit_name', values='value', aggfunc='sum')
    
    # 欠損値を0で埋める
    pivot_df = pivot_df.fillna(0)
    
    # 相関係数行列を計算
    corr_matrix = pivot_df.corr()
    
    # 相関関係が強い組み合わせを抽出
    strong_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr = corr_matrix.iloc[i, j]
            
            if not np.isnan(corr) and abs(corr) >= 0.5:  # 相関係数の絶対値が0.5以上
                strong_correlations.append({
                    'habit1': col1,
                    'habit2': col2,
                    'correlation': float(corr),
                    'relationship': "正の相関" if corr > 0 else "負の相関"
                })
    
    # 相関が強い組み合わせの中から最も強いものを特定
    if strong_correlations:
        strongest = max(strong_correlations, key=lambda x: abs(x['correlation']))
        
        title = f"{strongest['habit1']}と{strongest['habit2']}の間に{strongest['relationship']}があります"
        
        if strongest['correlation'] > 0:
            description = f"{strongest['habit1']}と{strongest['habit2']}は互いに良い影響を与えています。"
            description += f"相関係数は{strongest['correlation']:.2f}で、一方を行うと他方も増加する傾向があります。"
        else:
            description = f"{strongest['habit1']}と{strongest['habit2']}は互いに競合している可能性があります。"
            description += f"相関係数は{strongest['correlation']:.2f}で、一方を行うと他方が減少する傾向があります。"
    else:
        title = "活動間の相関関係"
        description = "現在のデータでは、活動間に強い相関関係は見つかりませんでした。"
        strongest = None
    
    # インサイトを保存
    insight_data = {
        "correlation_matrix": corr_matrix.to_dict(),
        "strong_correlations": strong_correlations,
        "strongest_correlation": strongest
    }
    
    insight, created = ProductivityInsight.objects.update_or_create(
        user=user,
        insight_type="correlation",
        defaults={
            "title": title,
            "description": description,
            "data": insight_data
        }
    )
    
    return insight


def generate_trend_insight(user, habit_logs):
    """トレンド分析に関するインサイトを生成"""
    # 習慣データをパンダスデータフレームに変換
    habit_data = []
    for log in habit_logs:
        habit_data.append({
            'date': log.log_date,
            'habit_id': log.habit.id,
            'habit_name': log.habit.name,
            'category': log.habit.category,
            'value': log.value
        })
    
    if not habit_data:
        # データがない場合はデフォルトのインサイトを返す
        insight, created = ProductivityInsight.objects.update_or_create(
            user=user,
            insight_type="trend",
            defaults={
                "title": "活動トレンドの分析",
                "description": "まだ十分なデータがないため、活動のトレンドを分析できません。",
                "data": {}
            }
        )
        return insight
    
    df = pd.DataFrame(habit_data)
    
    # 日付で並べ替え
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 習慣ごとのトレンドを分析
    habit_trends = {}
    
    for habit_name in df['habit_name'].unique():
        habit_df = df[df['habit_name'] == habit_name]
        
        if len(habit_df) < 7:  # 少なくとも1週間分のデータが必要
            continue
        
        # 7日間の移動平均を計算
        habit_df = habit_df.set_index('date')
        rolling_avg = habit_df['value'].rolling('7D').mean()
        
        # トレンドの方向を判定
        if len(rolling_avg.dropna()) < 2:
            trend = "データ不足"
        else:
            first_week_avg = rolling_avg.dropna().iloc[:7].mean()
            last_week_avg = rolling_avg.dropna().iloc[-7:].mean()
            
            if last_week_avg > first_week_avg * 1.1:
                trend = "上昇"
            elif last_week_avg < first_week_avg * 0.9:
                trend = "下降"
            else:
                trend = "横ばい"
        
        habit_trends[habit_name] = {
            'trend': trend,
            'first_week_avg': float(first_week_avg) if 'first_week_avg' in locals() else None,
            'last_week_avg': float(last_week_avg) if 'last_week_avg' in locals() else None,
            'change_percentage': float((last_week_avg - first_week_avg) / first_week_avg * 100) 
                                 if 'first_week_avg' in locals() and first_week_avg != 0 else None
        }
    
    # 最も大きな変化を示した習慣を特定
    significant_trends = []
    
    for habit_name, trend_data in habit_trends.items():
        if trend_data['trend'] != "データ不足" and trend_data['change_percentage'] is not None:
            significant_trends.append({
                'habit_name': habit_name,
                'trend': trend_data['trend'],
                'change_percentage': trend_data['change_percentage']
            })
    
    if significant_trends:
        # 変化率の絶対値が最大の習慣を見つける
        most_significant = max(significant_trends, key=lambda x: abs(x['change_percentage']))
        
        title = f"{most_significant['habit_name']}が{most_significant['trend']}傾向にあります"
        
        if most_significant['trend'] == "上昇":
            description = f"{most_significant['habit_name']}の活動量が上昇しています。"
            description += f"過去3ヶ月間で約{abs(most_significant['change_percentage']):.1f}%増加しました。"
        elif most_significant['trend'] == "下降":
            description = f"{most_significant['habit_name']}の活動量が減少しています。"
            description += f"過去3ヶ月間で約{abs(most_significant['change_percentage']):.1f}%減少しました。"
        else:
            description = f"{most_significant['habit_name']}の活動量は安定しています。"
    else:
        title = "活動トレンドの分析"
        description = "現在のデータでは、明確なトレンドは見つかりませんでした。"
        most_significant = None
    
    # インサイトを保存
    insight_data = {
        "habit_trends": habit_trends,
        "significant_trends": significant_trends,
        "most_significant": most_significant
    }
    
    insight, created = ProductivityInsight.objects.update_or_create(
        user=user,
        insight_type="trend",
        defaults={
            "title": title,
            "description": description,
            "data": insight_data
        }
    )
    
    return insight


def generate_recommendation_insight(user, habit_logs):
    """推奨事項に関するインサイトを生成"""
    # 習慣データを取得
    habits = Habit.objects.filter(user=user, is_active=True)
    
    # 各習慣の達成率を計算
    habit_completion_rates = {}
    
    for habit in habits:
        # 過去30日間のログを取得
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        logs = HabitLog.objects.filter(
            habit=habit,
            log_date__gte=start_date,
            log_date__lte=end_date
        )
        
        # 達成日数と目標達成率を計算
        completed_days = logs.count()
        completion_rate = completed_days / 30 * 100
        
        habit_completion_rates[habit.name] = {
            'id': habit.id,
            'completed_days': completed_days,
            'completion_rate': completion_rate
        }
    
    # 目標達成率が低い習慣を特定
    low_completion_habits = []
    for habit_name, data in habit_completion_rates.items():
        if data['completion_rate'] < 50:  # 50%未満の達成率
            low_completion_habits.append({
                'name': habit_name,
                'id': data['id'],
                'completion_rate': data['completion_rate']
            })
    
    # 最も達成率が低い習慣を特定
    if low_completion_habits:
        lowest_habit = min(low_completion_habits, key=lambda x: x['completion_rate'])
        
        title = f"{lowest_habit['name']}の継続が課題です"
        description = f"{lowest_habit['name']}の過去30日間の達成率は{lowest_habit['completion_rate']:.1f}%です。"
        description += "この習慣を継続するために、以下の対策を検討してみてください：\n"
        description += "1. リマインダーを設定して忘れないようにする\n"
        description += "2. より小さなステップに分解して取り組みやすくする\n"
        description += "3. カレンダーに固定の時間枠を確保する"
    else:
        # 達成率が高い習慣がある場合
        high_completion_habits = []
        for habit_name, data in habit_completion_rates.items():
            if data['completion_rate'] >= 80:  # 80%以上の達成率
                high_completion_habits.append({
                    'name': habit_name,
                    'id': data['id'],
                    'completion_rate': data['completion_rate']
                })
        
        if high_completion_habits:
            highest_habit = max(high_completion_habits, key=lambda x: x['completion_rate'])
            
            title = f"{highest_habit['name']}の習慣化に成功しています"
            description = f"{highest_habit['name']}の過去30日間の達成率は{highest_habit['completion_rate']:.1f}%です。"
            description += "この調子で継続し、さらなる目標に挑戦してみましょう。"
        else:
            title = "習慣継続のための推奨事項"
            description = "現在のデータからは、特定の推奨事項を導き出せませんでした。"
            description += "より多くの習慣を記録することで、パーソナライズされた提案を受けることができます。"
    
    # インサイトを保存
    insight_data = {
        "habit_completion_rates": habit_completion_rates,
        "low_completion_habits": low_completion_habits,
        "high_completion_habits": high_completion_habits if 'high_completion_habits' in locals() else []
    }
    
    insight, created = ProductivityInsight.objects.update_or_create(
        user=user,
        insight_type="recommendation",
        defaults={
            "title": title,
            "description": description,
            "data": insight_data
        }
    )
    
    return insight


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_learning_patterns(request):
    """学習パターンを分析するAPI"""
    # 習慣ログデータの取得（過去90日間）
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    habit_logs = HabitLog.objects.filter(
        habit__user=request.user,
        habit__category__in=['study', 'programming', 'language', 'reading'],  # 学習関連カテゴリのみ
        log_date__gte=start_date,
        log_date__lte=end_date
    ).select_related('habit')
    
    # データが少ない場合はエラーを返す
    if habit_logs.count() < 14:  # 最低2週間分のデータが必要
        return Response({
            "error": "Not enough data for analysis. Please log more learning activities."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 時間帯別効率データの計算
    hourly_efficiency = calculate_hourly_efficiency(request.user)
    
    # 曜日別効率データの計算
    weekday_efficiency = calculate_weekday_efficiency(request.user, habit_logs)
    
    # コンテンツタイプ別効率データの計算
    content_type_efficiency = calculate_content_type_efficiency(request.user, habit_logs)
    
    # 学習パターンを保存または更新
    learning_pattern, created = LearningPattern.objects.update_or_create(
        user=request.user,
        defaults={
            'hourly_efficiency': hourly_efficiency,
            'weekday_efficiency': weekday_efficiency,
            'content_type_efficiency': content_type_efficiency
        }
    )
    
    serializer = LearningPatternSerializer(learning_pattern)
    return Response(serializer.data)

def calculate_hourly_efficiency(user):
    """時間帯別の学習効率を計算"""
    # カレンダーイベントから学習活動を取得
    events = CalendarEvent.objects.filter(
        user=user,
        category__in=['study', 'programming', 'language', 'reading'],
        start_time__date__gte=datetime.now().date() - timedelta(days=90)
    )
    
    # 日記から生産性評価データを取得
    journals = DailyJournal.objects.filter(
        user=user,
        date__gte=datetime.now().date() - timedelta(days=90),
        productivity_rating__isnull=False
    )
    
    # 時間帯別の生産性スコアを初期化
    hourly_productivity = defaultdict(list)
    
    # カレンダーイベントと日記データを組み合わせて時間帯別効率を計算
    for event in events:
        event_date = event.start_time.date()
        # その日の生産性評価を取得
        journal = journals.filter(date=event_date).first()
        
        if journal and journal.productivity_rating:
            # イベントの時間帯を1時間単位で分割
            event_start_hour = event.start_time.hour
            event_end_hour = event.end_time.hour
            
            # 深夜をまたぐ場合は翌日の0時までとする
            if event_end_hour < event_start_hour:
                event_end_hour = 24
            
            # 各時間帯の生産性スコアを記録
            for hour in range(event_start_hour, event_end_hour):
                hour_range = f"{hour % 24:02d}:00-{(hour + 1) % 24:02d}:00"
                hourly_productivity[hour_range].append(journal.productivity_rating)
    
    # 時間帯別の平均生産性スコアを計算
    hourly_efficiency_data = {}
    for hour_range, scores in hourly_productivity.items():
        if scores:
            hourly_efficiency_data[hour_range] = sum(scores) / len(scores)
    
    return hourly_efficiency_data


def calculate_weekday_efficiency(user, habit_logs):
    """曜日別の学習効率を計算"""
    # 日記から生産性評価データを取得
    journals = DailyJournal.objects.filter(
        user=user,
        date__gte=datetime.now().date() - timedelta(days=90),
        productivity_rating__isnull=False
    )
    
    # 曜日別の生産性スコアを初期化
    weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    weekday_productivity = defaultdict(list)
    
    # 日記データから曜日別の生産性評価を集計
    for journal in journals:
        weekday = journal.date.weekday()
        weekday_name = weekday_names[weekday]
        weekday_productivity[weekday_name].append(journal.productivity_rating)
    
    # 習慣ログデータからも曜日別の達成度を補完
    for log in habit_logs:
        weekday = log.log_date.weekday()
        weekday_name = weekday_names[weekday]
        
        # 習慣の目標値に対する達成率を10段階評価に換算
        if log.habit.target_value > 0:
            achievement_rate = min(log.value / log.habit.target_value, 1.0)
            productivity_score = int(achievement_rate * 10)
            weekday_productivity[weekday_name].append(productivity_score)
    
    # 曜日別の平均生産性スコアを計算
    weekday_efficiency_data = {}
    for weekday_name in weekday_names:
        scores = weekday_productivity[weekday_name]
        if scores:
            weekday_efficiency_data[weekday_name] = sum(scores) / len(scores)
        else:
            weekday_efficiency_data[weekday_name] = 0
    
    return weekday_efficiency_data


def calculate_content_type_efficiency(user, habit_logs):
    """コンテンツタイプ別の学習効率を計算"""
    # 習慣カテゴリ別の達成度を集計
    category_achievement = defaultdict(list)
    
    for log in habit_logs:
        category = log.habit.category
        
        # 習慣の目標値に対する達成率を計算
        if log.habit.target_value > 0:
            achievement_rate = min(log.value / log.habit.target_value, 1.0)
            category_achievement[category].append(achievement_rate)
    
    # カテゴリ別の平均達成率を計算
    content_type_efficiency = {}
    for category, rates in category_achievement.items():
        if rates:
            content_type_efficiency[category] = sum(rates) / len(rates)
    
    return content_type_efficiency
