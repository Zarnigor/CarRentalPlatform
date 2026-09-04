from root.exceptions import NotFoundError, ConflictError
from django.utils.translation import gettext_lazy as _

class RelocationPlanNotFoundError(NotFoundError):
    default_message = _("Ko'chirish rejasi (relocation plan) topilmadi")
    error_code = "relocation_plan_not_found"

    def __init__(self, plan_id=None, **extra):
        super().__init__(plan_id=plan_id, **extra)


class TaskNotFoundError(NotFoundError):
    default_message = _("Vazifa (task) topilmadi")
    error_code = "task_not_found"

    def __init__(self, task_id=None, **extra):
        super().__init__(task_id=task_id, **extra)


class TaskAlreadyAssignedError(ConflictError):
    default_message = _("Vazifa allaqachon boshqa xodimga biriktirilgan")
    error_code = "task_already_assigned"

    def __init__(self, task_id=None, assigned_to=None, **extra):
        super().__init__(task_id=task_id, assigned_to=assigned_to, **extra)


class TaskInvalidStateError(ConflictError):
    default_message = _("Vazifa hozirgi holatda bu amalni bajarish mumkin emas")
    error_code = "task_invalid_state"

    def __init__(self, task_id=None, current_status=None, **extra):
        super().__init__(task_id=task_id, current_status=current_status, **extra)


class RelocationPlanConflictError(ConflictError):
    default_message = _("Mashina boshqa ko'chirish rejasida band")
    error_code = "relocation_plan_conflict"

    def __init__(self, plan_id=None, car_id=None, **extra):
        super().__init__(plan_id=plan_id, car_id=car_id, **extra)
