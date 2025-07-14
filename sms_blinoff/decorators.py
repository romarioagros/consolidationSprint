from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps

def group_required(group_name, redirect_to='sms_blinoff:mother_list', message="У вас нет прав для выполнения этого действия."):
    """
    Декоратор для проверки наличия пользователя в группе.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                messages.error(request, message)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
