"""Run the requests against the ORIGINAL DRF project in a fresh interpreter (module names clash with the Django sample)."""
import json
import os
import sys

proj, req_file = sys.argv[1], sys.argv[2]
sys.path.insert(0, proj)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django  # noqa: E402

django.setup()
from rest_framework.test import APIClient  # noqa: E402

c = APIClient()
out = []
for method, url, kw in json.load(open(req_file)):
    r = c.generic(method, url, json.dumps(kw["json"]) if "json" in kw else "", content_type="application/json")
    ct = r.headers.get("Content-Type", "")
    body = json.loads(r.content) if "json" in ct and r.content else (r.content.decode() if r.content else "")
    out.append([r.status_code, body])
print(json.dumps(out))
