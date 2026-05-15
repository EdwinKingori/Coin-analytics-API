from rest_framework import serializers
from users.serializers import UserSerializer

from scraper_app.models import (
    Profile, ScrapeLog,
    UserPreference, ScheduledScrape,
    ErrorLog, ExchangeRateSnapshot,
    CoinComparison, UserActivity
)


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'bio', 'phone_number']


class ScrapeLogSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ScrapeLog
        fields = ['id', 'user', 'coin', 'price', 'currency', 'timestamp']


class UserPreferenceSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserPreference
        fields = ['id', 'user', 'preferred_currency', 'favorite_coins',
                  'notify_on_price_change', 'notify_threshhold']


class ScheduleScrapeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ScheduledScrape
        fields = ['id', 'user', 'coin', 'currency',
                  'interval_minutes', 'is_active', 'last_run']


class ErrorLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ErrorLog
        fields = ['id', 'source', 'error_message', 'timestamp']


class ExchangeRateSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateSnapshot
        # BUG FIX: 'field' (singular) is not a recognised Meta attribute in
        # ModelSerializer. DRF silently ignores it and falls back to including
        # ALL model fields, which can unintentionally expose internal columns
        # added in future migrations. The correct attribute is 'fields'
        # (plural). With 'field', the explicit allow-list was dead code.
        fields = ['id', 'base_currency', 'target_currency', 'rate', 'timestamp']


class CoinComparisonSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CoinComparison
        fields = ['id', 'user', 'coin1', 'coin2', 'coin1_price',
                  'coin2_price', 'comparison_date']


class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'action', 'timestamp']
