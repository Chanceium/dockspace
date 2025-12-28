"""
Django views for Dockspace.

This file contains minimal views since the frontend is now handled by Vue.js.
All UI routing is managed by Vue Router on the client side.
"""
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse


@login_required(login_url="/login")
def protected_media(request, path):
	"""
	Serve media files only to authenticated users.
	Prevents unauthorized access to uploaded files.
	"""
	media_path = os.path.join(settings.MEDIA_ROOT, path)

	# Security: prevent path traversal attacks
	media_path = os.path.abspath(media_path)
	if not media_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
		raise Http404("Invalid file path")

	if not os.path.exists(media_path) or not os.path.isfile(media_path):
		raise Http404("File not found")

	return FileResponse(open(media_path, 'rb'))


def vue_spa_view(request, exception=None):
	"""
	Serve the Vue.js SPA for all non-API routes.
	This allows Vue Router to handle client-side routing.

	The Vue app is built to dockspace/static/dist/ by running:
	    cd frontend && npm run build
	"""
	# Path to the Vue.js build
	vue_index_path = Path(settings.BASE_DIR) / 'backend' / 'dockspace' / 'static' / 'dist' / 'index.html'

	if not vue_index_path.exists():
		raise Http404(
			"Vue.js app not built. "
			"Run 'cd frontend && npm run build' to build the frontend."
		)

	# Read and serve the index.html
	with open(vue_index_path, 'r', encoding='utf-8') as f:
		html_content = f.read()

	return HttpResponse(html_content, content_type='text/html')
