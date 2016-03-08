from django.http import JsonResponse

def case_stats_view(request):
    return JsonResponse("test", safe=False)
