"""
Extended tests for apps/usuarios/middleware.py covering missing lines/branches.

Missing targets:
  Line 33:   REMOTE_ADDR fallback branch (no HTTP_X_FORWARDED_FOR header)
  49->51:    process_response when thread has no current_empleado attr
  51->54:    process_response when thread has no current_ip attr
"""

from threading import current_thread

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.usuarios.middleware import AuditContextMiddleware


class AuditContextMiddlewareRemoteAddrTest(TestCase):
    """Cover line 33: REMOTE_ADDR path when no HTTP_X_FORWARDED_FOR."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditContextMiddleware(lambda req: HttpResponse("OK"))

    def tearDown(self):
        thread = current_thread()
        for attr in ("current_empleado", "current_ip"):
            if hasattr(thread, attr):
                delattr(thread, attr)

    def test_process_request_uses_remote_addr_when_no_x_forwarded_for(self):
        """Line 33: when X-Forwarded-For is absent, REMOTE_ADDR is used."""
        request = self.factory.get("/")
        # Ensure HTTP_X_FORWARDED_FOR is NOT set
        request.META.pop("HTTP_X_FORWARDED_FOR", None)
        request.META["REMOTE_ADDR"] = "10.0.0.42"

        self.middleware.process_request(request)

        thread = current_thread()
        self.assertEqual(thread.current_ip, "10.0.0.42")

    def test_process_request_prefers_x_forwarded_for(self):
        """When X-Forwarded-For IS present, the first IP is used."""
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        self.middleware.process_request(request)
        thread = current_thread()
        self.assertEqual(thread.current_ip, "1.2.3.4")


class AuditContextMiddlewareProcessResponseTest(TestCase):
    """Cover branches 49->51, 51->54, and line 52: process_response attr paths."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditContextMiddleware(lambda req: HttpResponse("OK"))

    def test_process_response_without_any_thread_attrs(self):
        """Branches 49->51 and 51->54: response when thread has neither attr."""
        request = self.factory.get("/")
        response = HttpResponse("OK")
        thread = current_thread()

        # Guarantee the attrs are NOT on the thread
        for attr in ("current_empleado", "current_ip"):
            if hasattr(thread, attr):
                delattr(thread, attr)

        result = self.middleware.process_response(request, response)
        self.assertIs(result, response)

    def test_process_response_with_both_thread_attrs(self):
        """Line 52: delattr(thread, 'current_ip') executes when both attrs are set."""
        request = self.factory.get("/")
        response = HttpResponse("OK")
        thread = current_thread()

        thread.current_empleado = None
        thread.current_ip = "192.168.0.1"

        try:
            result = self.middleware.process_response(request, response)
            self.assertIs(result, response)
            self.assertFalse(hasattr(thread, "current_empleado"))
            self.assertFalse(hasattr(thread, "current_ip"))
        finally:
            for attr in ("current_empleado", "current_ip"):
                if hasattr(thread, attr):
                    delattr(thread, attr)

    def test_process_response_without_current_ip_only(self):
        """Branch 51->54: thread has current_empleado but not current_ip."""
        request = self.factory.get("/")
        response = HttpResponse("OK")
        thread = current_thread()

        thread.current_empleado = None  # set empleado
        if hasattr(thread, "current_ip"):
            delattr(thread, "current_ip")  # ensure ip is NOT set

        try:
            result = self.middleware.process_response(request, response)
            self.assertIs(result, response)
            self.assertFalse(hasattr(thread, "current_empleado"))
        finally:
            for attr in ("current_empleado", "current_ip"):
                if hasattr(thread, attr):
                    delattr(thread, attr)


class AuditContextMiddlewareAuthenticatedUserTest(TestCase):
    """Lines 23-28: authenticated user path in process_request (try/except Empleados.get)."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditContextMiddleware(lambda req: HttpResponse("OK"))

    def tearDown(self):
        thread = current_thread()
        for attr in ("current_empleado", "current_ip"):
            if hasattr(thread, attr):
                delattr(thread, attr)

    def test_process_request_with_authenticated_user_no_empleado_row(self):
        """Lines 23-28: authenticated user, Empleados.get raises DoesNotExist → except caught."""
        from django.contrib.auth.models import User

        user = User.objects.create_user(username="mwtest_auth", password="pass123")
        request = self.factory.get("/")
        request.user = user  # is_authenticated=True for real User objects

        # Empleados.objects.get(id=user.id) will raise DoesNotExist (no Empleados row)
        # → except: catches it → empleado = None
        self.middleware.process_request(request)

        thread = current_thread()
        self.assertIsNone(thread.current_empleado)
