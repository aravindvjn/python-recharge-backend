from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Provider, Plans
from .serializers import ProviderSerializer, PlansSerializer, PlansListSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plans_list(request):
    plans = Plans.objects.filter(is_active=True).select_related('provider')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        plans = plans.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(provider__title__icontains=search) |
            Q(identifier__icontains=search)
        )
    
    # Filter by provider
    provider_id = request.GET.get('provider_id', '')
    if provider_id:
        plans = plans.filter(provider_id=provider_id)
    
    # Filter by amount range
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    if min_amount:
        plans = plans.filter(amount__gte=min_amount)
    if max_amount:
        plans = plans.filter(amount__lte=max_amount)
    
    # Filter by validity range
    min_validity = request.GET.get('min_validity', '')
    max_validity = request.GET.get('max_validity', '')
    if min_validity:
        plans = plans.filter(validity__gte=min_validity)
    if max_validity:
        plans = plans.filter(validity__lte=max_validity)
    
    # Ordering
    ordering = request.GET.get('ordering', 'created_at')
    if ordering in ['title', '-title', 'amount', '-amount', 'validity', '-validity', 'created_at', '-created_at']:
        plans = plans.order_by(ordering)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = plans.count()
    plans_page = plans[start:end]
    
    serializer = PlansListSerializer(plans_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plans_detail(request, pk):
    try:
        plan = Plans.objects.select_related('provider').get(pk=pk, is_active=True)
        serializer = PlansSerializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Plans.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def providers_list(request):
    providers = Provider.objects.filter(is_active=True)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        providers = providers.filter(title__icontains=search)
    
    serializer = ProviderSerializer(providers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
