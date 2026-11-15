import os

from tofastapi.django_conv import convert_project

URLS = 'from django.urls import path\nfrom . import views\n\nurlpatterns = [\n    path("about/", views.About.as_view()),\n    path("p/<int:pk>/", views.Page.as_view()),\n]\n'
VIEWS = '''from django.views.generic import TemplateView


class About(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "About"
        return context


class Page(TemplateView):
    template_name = "page.html"
'''


def test_template_view(tmp_path):
    proj = tmp_path / "proj"
    (proj / "config").mkdir(parents=True)
    (proj / "config" / "__init__.py").write_text("")
    (proj / "config" / "urls.py").write_text('from django.urls import path, include\nurlpatterns = [path("", include("blog.urls"))]\n')
    (proj / "blog").mkdir()
    (proj / "blog" / "__init__.py").write_text("")
    (proj / "blog" / "urls.py").write_text(URLS)
    (proj / "blog" / "views.py").write_text(VIEWS)
    (proj / "manage.py").write_text("")
    (proj / "config" / "settings.py").write_text("ROOT_URLCONF = 'config.urls'\n")
    out = tmp_path / "out"
    res = convert_project(str(proj), str(out))
    assert res.routes == 2
    src = ""
    for root, _, files in os.walk(out):
        for f in files:
            if f.endswith(".py"):
                src += open(os.path.join(root, f), encoding="utf-8").read()
    assert "Jinja2Templates" in src
    assert "templates.TemplateResponse(request, 'about.html', _About_context())" in src
    assert 'def Page_get(request: Request, pk: int)' in src
    assert "dict(kwargs)" in src
    compile(src, "converted", "exec")
