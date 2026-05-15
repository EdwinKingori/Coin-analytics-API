from django.shortcuts import render
from rest_framework import status, filters
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Max, Q
from datetime import timedelta

from api.serializers import (
    ProfileSerializer,
    ScrapeLogSerializer,
    UserPreferenceSerializer,
    ScheduleScrapeSerializer,
    ErrorLogSerializer,
    ExchangeRateSnapshotSerializer,
    CoinComparisonSerializer,
    UserActivitySerializer
)
from scraper_app.models import (
    Profile,
    ScrapeLog,
    UserPreference,
    ScheduledScrape,
    ErrorLog,
    ExchangeRateSnapshot,
    CoinComparison,
    UserActivity
)


# ✅ Viewset for managing user profiles
class ProfileViewSet(ModelViewSet):
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    permission_classes = [IsAuthenticated]
    filtered_fields = ['username', 'bio']
    search_fields = ['username']
    ordering_fields = ['username']
    ordering = ['username']

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def get_permissions(self):
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Fetching user's profile
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ✅ Viewset for managing scrape logs
class ScrapeLogViewSet(ModelViewSet):
    serializer_class = ScrapeLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filtered_fields = ['coin', 'price', 'currency']
    search_fields = ['coin']
    ordering_fields = ['timestamp', 'price']
    ordering = ['-timestamp']

    def get_queryset(self):
        return ScrapeLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # fetching scrape logs filtered by specific coin
    @action(detail=False, methods=['get'])
    def by_coin(self, request):
        coin = request.query_params.get('coin')
        if not coin:
            return Response(
                {'error': 'Coin parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        logs = self.get_queryset().filter(coin__iexact=coin)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    # Fetching price history for a specific coin over time
    @action(detail=False, methods=['get'])
    def price_history(self, request):
        coin = request.query_params.get('coin')
        days = int(request.query_params.get('days', 30))

        if not coin:
            return Response(
                {'error': 'Coin Parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        start_date = timezone.now() - timedelta(days=days)
        logs = self.get_queryset().filter(
            coin__iexact=coin,
            timestamp__gte=start_date
        ).order_by('timestamp')

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


# ✅ Viewset for managing user's preference
class UserPreferenceViewSet(ModelViewSet):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_fields = ['favorite_coins', 'preferred_currency']
    search_fields = ['preferred_currency', 'favorite_coins']
    ordering_fields = ['preferred_currency']
    ordering = ['preferred_currency']

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    # Fetching the user preference
    @action(detail=False, methods=['get'])
    def my_preference(self, request):
        try:
            preference = UserPreference.objects.get(user=request.user)
            serializer = self.get_serializer(preference)
            # BUG FIX 1: Response(serializer) was passing the Serializer object
            # itself, not its validated output. DRF's Response does not know how
            # to serialise a Serializer instance, so it returned an unrenderable
            # object at runtime. The fix is Response(serializer.data) which
            # returns the already-serialised OrderedDict that DRF can render as
            # JSON.
            #
            # BUG FIX 2: The except clause used a set literal {'error', 'Preference
            # not found'} instead of a dict {'error': 'Preference not found'}.
            # A set is unordered and loses the key-value relationship, so the
            # response body would be meaningless to API consumers. Replaced with
            # a proper dict using the colon (:) operator.
            return Response(serializer.data)
        except UserPreference.DoesNotExist:
            return Response(
                {'error': 'Preference not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # Adding a coin to a user's favorites
    @action(detail=True, methods=['post'])
    def get_coin(self, request, pk=None):
        preference = self.get_object()
        coin = request.data.get('coin')

        if not coin:
            return Response(
                {'error': 'Coin parameter is required'},
                status=status.HTTP_404_NOT_FOUND
            )

        if coin not in preference.favorite_coins:
            preference.favorite_coins.append(coin.upper())
            preference.save()

        serializer = self.get_serializer(preference)
        return Response(serializer.data)

    # Removing a coin from a users favorites
    @action(detail=True, methods=['post'])
    def remove_favorite_coin(self, request, pk=None):
        preference = self.get_object()
        coin = request.data.get('coin')

        if not coin:
            return Response(
                {'error': 'Coin parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if coin.upper() in preference.favorite_coins:
            preference.favorite_coins.remove(coin.upper())
            preference.save()

        serializer = self.get_serializer(preference)
        return Response(serializer.data)


# ✅ Viewset to manage scheduled scraping jobs
class ScheduledScrapeViewSet(ModelViewSet):
    serializer_class = ScheduleScrapeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_fields = ['coin', 'currency', 'is_active']
    ordering_fields = ['last_run', 'interval_minutes']
    ordering = ['-last_run']

    def get_queryset(self):
        # BUG FIX: .get() raises MultipleObjectsReturned when a user has more
        # than one ScheduledScrape row, and raises DoesNotExist when they have
        # none — both crash the view. ModelViewSet's list/retrieve/update
        # actions all call get_queryset() and expect a QuerySet, not a single
        # instance. Replaced with .filter() which returns a QuerySet in all
        # cases and is safe for users with 0, 1, or N rows.
        return ScheduledScrape.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    # Toggle the active status of a scheduled scrape
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        Scheduled_scrape = self.get_object()
        Scheduled_scrape.is_active = not Scheduled_scrape.is_active
        Scheduled_scrape.save()

        serializer = self.get_serializer(Scheduled_scrape)
        return Response(serializer.data)

    # Fetching all active scheduled scrapes
    @action(detail=False, methods=['get'])
    def active_scrapes(self, request):
        active_scrapes = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_scrapes, many=True)
        return Response(serializer.data)

    # Updating the last run timestamp for a scheduled scrape
    @action(detail=True, methods=['post'])
    def update_last_run(self, request, pk=None):
        scheduled_scrape = self.get_object()
        scheduled_scrape.last_run = timezone.now()
        scheduled_scrape.save()

        serializer = self.get_serializer(scheduled_scrape)
        return Response(serializer.data)


# ✅ A read-only viewset for error logs with filtering capabilities
class ErrorLogViewSet(ModelViewSet):
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['error_message', 'source']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    # Admin users can see all errors, regular users see only their own
    def get_queryset(self):
        if self.request.user.is_staff:
            return ErrorLog.objects.all()
        return ErrorLog.objects.filter(user=self.request.user)

    # Fetching recent errors (last 24 hours)
    @action(detail=False, methods=['get'])
    def recent_errors(self, request):
        yesterday = timezone.now() - timedelta(days=1)
        recent_errors = self.get_queryset().filter(timestamp__gte=yesterday)
        serializer = self.get_serializer(recent_errors, many=True)
        return Response(serializer.data)

    # Fetching error summary by source
    @action(detail=False, methods=['get'])
    def error_summary(self, request):
        from django.db.models import Count

        summary = self.get_queryset().values('source').annotate(
            error_count=Count('id')
        ).order_by('-error_count')


# ✅ Read-only viewset for exchange rate snapshots
class ExchangeRateSnapShotViewSet(ModelViewSet):
    serializer_class = ExchangeRateSnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_fields = ['base_currency', 'target_currency']
    ordering = ['rate', 'timestamp']

    def get_queryset(self):
        return ExchangeRateSnapshot.objects.all()

    # Fetching the latest timestamp for each currency pair
    @action(detail=False, methods=['get'])
    def latest_rates(self, request):

        latest_snapshots = ExchangeRateSnapshot.objects.values(
            'base_currency', 'target_currency'
        ).annotate(
            latest_timestamp=Max('timestamp')
        )

        # Filtering to get only the latest snapshots
        latest_rates = []
        for snapshot_info in latest_snapshots:
            latest_rate = ExchangeRateSnapshot.objects.filter(
                base_currency=snapshot_info['base_currency'],
                target_currency=snapshot_info['target_currency'],
                timestamp=snapshot_info['latest_timestamp']
            ).first()
            if latest_rate:
                latest_rates.append(latest_rate)

        serializer = self.get_serializer(latest_rates, many=True)
        return Response(serializer.data)

    # Fetching exchange rate history for specific currency pair
    @action(detail=False, methods=['get'])
    def currency_pair(self, request):
        base = request.query_params.get('base')
        target = request.query_params.get('target')
        days = int(request.query_params.get('days', 30))

        if not base or not target:
            return Response(
                {'error': 'Both base and target currency parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = timezone.now() - timedelta(days=days)
        rates = self.get_queryset().filter(
            base_currency=base.upper(),
            target_currency=target.upper(),
            timestamp__gte=start_date
        ).order_by('timestamp')

        serializer = self.get_serializer(rates, many=True)
        return Response(serializer.data)


# ✅  Managing coin comparisons ViewSet
class CoinComparisonViewSet(ModelViewSet):
    serializer_class = CoinComparisonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['coin1', 'coin2']
    search_fields = ['coin1', 'coin2']
    ordering_fields = ['comparison_date']
    ordering = ['-comparison_date']

    def get_queryset(self):
        return CoinComparison.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])  # Comparing two specific coins
    def compare_coins(self, request):
        coin1 = request.query_params.get('coin1')
        coin2 = request.query_params.get('coin2')

        if not coin1 or not coin2:
            return Response(
                {'error': 'Both coin1 and coin2 parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comparisons = self.get_queryset().filter(
            Q(coin1__iexact=coin1, coin2__iexact=coin2) |
            Q(coin1__iexact=coin2, coin2__iexact=coin1)
        ).order_by('-comparison_date')

        serializer = self.get_serializer(comparisons, many=True)
        return Response(serializer.data)

    # Fetching recent comparisons (last 7 days)
    @action(detail=False, methods=['get'])
    def recent_comparisons(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        recent_comparisons = self.get_queryset().filter(
            comparison_date__gte=week_ago
        )
        serializer = self.get_serializer(recent_comparisons, many=True)
        return Response(serializer.data)


# ✅  Read-only ViewSet for user activity tracking
class UserActivityViewSet(ReadOnlyModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)

    # Fetching recent user activity (last 24 hours)
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):

        yesterday = timezone.now() - timedelta(days=1)
        recent_activity = self.get_queryset().filter(timestamp__gte=yesterday)
        serializer = self.get_serializer(recent_activity, many=True)
        return Response(serializer.data)

    # Fetch activity summary with counts
    @action(detail=False, methods=['get'])
    def activity_summary(self, request):
        from django.db.models import Count

        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        summary = self.get_queryset().filter(
            timestamp__gte=start_date
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'period_days': days,
            'activities': summary,
            'total_activities': sum(item['count'] for item in summary)
        })

    @action(detail=False, methods=['post'])  # Logging a new user activity
    def log_activity(self, request):
        action = request.data.get('action')

        if not action:
            return Response(
                {'error': 'Action parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        activity = UserActivity.objects.create(
            user=request.user,
            action=action
        )

        serializer = self.get_serializer(activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
