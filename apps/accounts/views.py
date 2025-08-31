from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

User = get_user_model()

@login_required
def users_list(request):
    q = request.GET.get("q", "").strip()
    users = User.objects.order_by("-date_joined")
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    return render(request, "accounts/users_list.html", {"users": users, "q": q})

@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, "accounts/user_detail.html", {"u": user})

