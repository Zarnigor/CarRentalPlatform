from rest_framework.permissions import AllowAny


class ActionSerializerMixin:

    serializer_action_map: dict = {}
    default_serializer_class = None

    def get_serializer_class(self):
        return self.serializer_action_map.get(self.action, self.default_serializer_class)


class ActionPermissionMixin:
    public_actions: set = set()

    def get_permissions(self):
        if self.action in self.public_actions:
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]