"""
API endpoints for audit log management.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import models

from dockspace.core.models import AuditLog
from dockspace.api.decorators import json_admin_required


@json_admin_required
@require_http_methods(['GET'])
def list_audit_logs(request):
    """
    List audit logs with filtering and pagination.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    - action: Filter by action type
    - actor: Filter by actor ID
    - severity: Filter by severity level
    - search: Search in description and target_name
    - start_date: Filter logs from this date (ISO format)
    - end_date: Filter logs until this date (ISO format)
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        action_filter = request.GET.get('action', '')
        actor_filter = request.GET.get('actor', '')
        severity_filter = request.GET.get('severity', '')
        search = request.GET.get('search', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        # Build query
        queryset = AuditLog.objects.select_related('actor').all()

        # Apply filters
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        if actor_filter:
            queryset = queryset.filter(actor_id=actor_filter)

        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)

        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(target_name__icontains=search)
            )

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serialize
        logs = []
        for log in page_obj:
            logs.append({
                'id': log.id,
                'action': log.action,
                'action_display': log.get_action_display(),
                'actor': {
                    'id': log.actor.id,
                    'email': log.actor.email,
                    'name': f"{log.actor.first_name} {log.actor.last_name}".strip() or log.actor.email,
                } if log.actor else None,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'target_name': log.target_name,
                'description': log.description,
                'metadata': log.metadata,
                'ip_address': log.ip_address,
                'severity': log.severity,
                'success': log.success,
                'created_at': log.created_at.isoformat(),
            })

        return JsonResponse({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters': {
                'action_types': [{'value': action[0], 'label': action[1]} for action in AuditLog.ACTION_TYPES],
                'severity_levels': [{'value': sev[0], 'label': sev[1]} for sev in AuditLog.SEVERITY_LEVELS],
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@json_admin_required
@require_http_methods(['GET'])
def get_audit_stats(request):
    """
    Get statistics about audit logs for dashboard.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        stats = {
            'total_logs': AuditLog.objects.count(),
            'last_24h': AuditLog.objects.filter(created_at__gte=last_24h).count(),
            'last_7d': AuditLog.objects.filter(created_at__gte=last_7d).count(),
            'last_30d': AuditLog.objects.filter(created_at__gte=last_30d).count(),
            'critical_count': AuditLog.objects.filter(severity='critical').count(),
            'failed_actions': AuditLog.objects.filter(success=False).count(),
            'recent_critical': AuditLog.objects.filter(
                severity='critical'
            ).order_by('-created_at')[:5].values(
                'id', 'action', 'description', 'created_at'
            ),
            'action_distribution': list(
                AuditLog.objects.filter(
                    created_at__gte=last_7d
                ).values('action').annotate(
                    count=models.Count('id')
                ).order_by('-count')[:10]
            ),
        }

        return JsonResponse({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
