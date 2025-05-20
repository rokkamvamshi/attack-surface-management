from rest_framework import serializers
from .models import NucleiResult

class NucleiResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = NucleiResult
        fields = ['id', 'target', 'subdomain', 'bug_class', 'scan_results', 'created_at']
