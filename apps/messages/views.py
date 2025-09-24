from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import (
    Q, OuterRef, Subquery, Count, Exists, Value, IntegerField, TextField
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .models import Message

User = get_user_model()


# ---------- helpers ----------

def _primary_admin():
    """
    Return a single 'primary' admin account to be used as the only contact
    for non-staff users. Preference order:
      1) superusers (newest first)
      2) staff (newest first)
    """
    return (
        User.objects
        .filter(Q(is_superuser=True) | Q(is_staff=True))
        .order_by('-is_superuser', '-date_joined')
        .first()
    )


def _annotated_convo_list(base_users_qs, me):
    """
    Given a users queryset, annotate with:
      - last_message_at
      - last_message_body
      - unread (count)
    and order it sensibly.
    """
    convo = Message.objects.filter(
        Q(sender=me, recipient=OuterRef("pk")) |
        Q(sender=OuterRef("pk"), recipient=me)
    ).order_by("-created_at")

    last_time = Subquery(convo.values("created_at")[:1])
    last_body = Subquery(convo.values("body")[:1])

    unread_qs = (
        Message.objects
        .filter(sender=OuterRef("pk"), recipient=me, is_read=False)
        .order_by()
        .values("sender")
        .annotate(c=Count("id"))
        .values("c")
    )

    return (
        base_users_qs
        .annotate(
            last_message_at=last_time,
            last_message_body=Coalesce(last_body, Value("", output_field=TextField())),
            unread=Coalesce(Subquery(unread_qs), Value(0, output_field=IntegerField())),
        )
        .order_by("-last_message_at", "username")
    )


# ---------- views ----------

@login_required
def messages_list(request):
    """
    Conversation list.
    - Non-staff: only the primary admin is listed (single contact).
    - Staff/admin: same behavior as before (all counterparts, with search).
    """
    q = (request.GET.get("q") or "").strip()

    # Non-staff: lock to admin only
    if not (request.user.is_staff or request.user.is_superuser):
        admin = _primary_admin()
        if not admin:
            messages.info(request, "Support is not available yet.")
            users = User.objects.none()
        else:
            users_qs = User.objects.filter(pk=admin.pk)

            # If user typed a query, allow matching against admin or message body
            if q:
                msg_match = Message.objects.filter(
                    Q(sender=admin, recipient=request.user) |
                    Q(sender=request.user, recipient=admin)
                ).filter(body__icontains=q)

                users_qs = users_qs.filter(
                    Q(username__icontains=q) |
                    Q(email__icontains=q) |
                    Q(first_name__icontains=q) |
                    Q(last_name__icontains=q) |
                    Exists(msg_match)
                )

            users = _annotated_convo_list(users_qs, request.user)

        return render(request, "messages/messages_list.html", {"users": users, "q": q})

    # Staff/admin: original counterpart logic
    to_ids = Message.objects.filter(sender=request.user).values_list("recipient_id", flat=True)
    from_ids = Message.objects.filter(recipient=request.user).values_list("sender_id", flat=True)
    counterpart_ids = set(list(to_ids) + list(from_ids))
    counterpart_ids.discard(request.user.id)

    users_qs = (
        User.objects.filter(id__in=counterpart_ids)
        if counterpart_ids else User.objects.exclude(id=request.user.id)
    )

    if q:
        msg_match = Message.objects.filter(
            Q(sender=OuterRef("pk"), recipient=request.user) |
            Q(sender=request.user, recipient=OuterRef("pk"))
        ).filter(body__icontains=q)

        users_qs = users_qs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Exists(msg_match)
        )

    users = _annotated_convo_list(users_qs, request.user)
    return render(request, "messages/messages_list.html", {"users": users, "q": q})


@login_required
def thread_view(request, user_id):
    """
    Single conversation view.
    - Non-staff are restricted to chatting with the primary admin only.
    - Marks incoming messages from 'other' as read.
    """
    # Gate for non-staff
    if not (request.user.is_staff or request.user.is_superuser):
        admin = _primary_admin()
        if not admin:
            messages.info(request, "Support is not available yet.")
            return redirect("messages:list")
        if user_id != admin.id:
            return redirect("messages:thread", user_id=admin.id)
        other = admin
    else:
        other = get_object_or_404(User, pk=user_id)
        if other.id == request.user.id:
            return redirect("messages:list")

    # mark incoming as read
    Message.objects.filter(sender=other, recipient=request.user, is_read=False).update(is_read=True)

    # thread messages
    msgs = Message.objects.filter(
        Q(sender=request.user, recipient=other) |
        Q(sender=other, recipient=request.user)
    ).order_by("created_at")

    # sidebar (for staff/admin: all counterparts; for users: just admin)
    if not (request.user.is_staff or request.user.is_superuser):
        users_sidebar = _annotated_convo_list(User.objects.filter(pk=other.pk), request.user)
    else:
        to_ids = Message.objects.filter(sender=request.user).values_list("recipient_id", flat=True)
        from_ids = Message.objects.filter(recipient=request.user).values_list("sender_id", flat=True)
        counterpart_ids = set(list(to_ids) + list(from_ids))
        counterpart_ids.discard(request.user.id)
        users_qs = (
            User.objects.filter(id__in=counterpart_ids)
            if counterpart_ids else User.objects.exclude(id=request.user.id)
        )
        users_sidebar = _annotated_convo_list(users_qs, request.user)

    ctx = {
        "other": other,
        "messages": msgs,
        "users_sidebar": users_sidebar,
    }
    return render(request, "messages/thread.html", ctx)


@login_required
def send_message(request, user_id):
    """
    POST a message.
    - Non-staff users may only send to the primary admin.
    """
    if request.method != "POST":
        return redirect("messages:thread", user_id=user_id)

    if not (request.user.is_staff or request.user.is_superuser):
        admin = _primary_admin()
        if not admin:
            messages.info(request, "Support is not available yet.")
            return redirect("messages:list")
        other = admin  # force admin as recipient
    else:
        other = get_object_or_404(User, pk=user_id)
        if other.id == request.user.id:
            return redirect("messages:list")

    body = (request.POST.get("body") or "").strip()
    if body:
        Message.objects.create(sender=request.user, recipient=other, body=body)
    return redirect("messages:thread", user_id=other.id)
