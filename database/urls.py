from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("prognose", views.prognose, name="prognose"),
    path("betm_prognose", views.betm_prognose, name="betm_prognose"),
    path(
        "urteil/erstellen", views.UrteilErstellenView.as_view(), name="urteil_erstellen"
    ),
    path(
        "urteil/update/<int:pk>/",
        views.UrteilUpdateView.as_view(),
        name="urteil_update",
    ),
    path("ws_evaluation", views.ws_evaluation, name="ws_evaluation"),
    path("betm_evaluation", views.betm_evaluation, name="betm_evaluation"),
    path("database", views.database, name="database"),
    # alte Methode
    # path('model/reset', views.kimodel_reset, name='kimodel_reset'),
    path("dev", views.dev, name="dev"),
    path("betm_dev", views.betm_dev, name="betm_dev"),
    path(
        "betm_kimodelle_neu_generieren",
        views.betm_kimodelle_neu_generieren,
        name="betm_kimodelle_neu_generieren",
    ),
    path(
        "betm_evaluations_kimodelle_neu_generieren",
        views.betm_evaluations_kimodelle_neu_generieren,
        name="betm_evaluations_kimodelle_neu_generieren",
    ),
    path(
        "ws_kimodelle_neu_generieren",
        views.ws_kimodelle_neu_generieren,
        name="ws_kimodelle_neu_generieren",
    ),
    path(
        "ws_db_scatterplots_aktualisieren",
        views.ws_db_scatterplots_aktualisieren,
        name="ws_db_scatterplots_aktualisieren",
    ),
    path("csv_neu_speichern", views.csv_erstellen, name="csv_neu_speichern"),
    path("text_funktionsweise", views.text_funktionsweise, name="text_funktionsweise"),
    path(
        "text_strafzumessung_mit_hilfe_von_ki",
        views.text_strafzumessung_mit_hilfe_von_ki,
        name="text_warum",
    ),
    path("betmdatabase", views.BetmUrteilListView.as_view(), name="betmdatabase"),
    path(
        "betmurteil/<int:pk>",
        views.BetmUrteilDetailView.as_view(),
        name="betmurteil_detail",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
