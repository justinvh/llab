from .commit import urlpatterns as commit_urlpatterns
from .project import urlpatterns as project_urlpatterns

urlpatterns = commit_urlpatterns + project_urlpatterns
