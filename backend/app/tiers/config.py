from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TierConfig:
    id: str
    name: str
    description: str
    max_iterations: int
    task_timeout_seconds: int
    max_concurrent_tasks: int
    runner_mode: str
    persistence: str
    deployment_targets: tuple[str, ...]
    allow_android_release_build: bool
    allow_google_play_publish: bool
    web_search_enabled: bool
    image_generation_enabled: bool
    max_web_search_results: int
    max_images_per_request: int
    health_checks_enabled: bool
    rollback_enabled: bool


TIERS: dict[str, TierConfig] = {
    "assane_moyen": TierConfig(
        id="assane_moyen",
        name="Assane Moyen",
        description="Pour les tests guidés et les tâches simples dans un environnement de développement.",
        max_iterations=12,
        task_timeout_seconds=600,
        max_concurrent_tasks=1,
        runner_mode="local",
        persistence="sqlite",
        deployment_targets=("vercel",),
        allow_android_release_build=False,
        allow_google_play_publish=False,
        web_search_enabled=False,
        image_generation_enabled=False,
        max_web_search_results=0,
        max_images_per_request=0,
        health_checks_enabled=False,
        rollback_enabled=False,
    ),
    "assane_fiable": TierConfig(
        id="assane_fiable",
        name="Assane Fiable",
        description="Pour un usage renforcé avec runner Docker, PostgreSQL et vérifications de publication configurables.",
        max_iterations=24,
        task_timeout_seconds=1200,
        max_concurrent_tasks=3,
        runner_mode="docker",
        persistence="postgres",
        deployment_targets=("vercel", "github", "cloudflare_pages", "cloudflare_workers"),
        allow_android_release_build=True,
        allow_google_play_publish=False,
        web_search_enabled=True,
        image_generation_enabled=True,
        max_web_search_results=5,
        max_images_per_request=1,
        health_checks_enabled=True,
        rollback_enabled=False,
    ),
    "assane_eleve": TierConfig(
        id="assane_eleve",
        name="Assane Élevé",
        description="Pour les environnements configurés avec quotas élargis, contrôles de santé et publication Android sous conditions.",
        max_iterations=48,
        task_timeout_seconds=2400,
        max_concurrent_tasks=10,
        runner_mode="docker",
        persistence="postgres",
        deployment_targets=("vercel", "github", "cloudflare_pages", "cloudflare_workers", "google_play"),
        allow_android_release_build=True,
        allow_google_play_publish=True,
        web_search_enabled=True,
        image_generation_enabled=True,
        max_web_search_results=10,
        max_images_per_request=4,
        health_checks_enabled=True,
        rollback_enabled=True,
    ),
}

UNIVERSAL_LIMITATIONS = (
    "Les niveaux autorisent des capacités ; ils ne fournissent aucune clé API, aucun compte de publication ni infrastructure externe.",
    "Un backend Python/Node arbitraire, un GPU ou une base privée nécessitent une cible d’hébergement et un adaptateur réellement configurés.",
    "La publication Google Play exige un AAB signé, un compte développeur et un compte de service autorisé.",
    "Le navigateur, l’inspection et la génération d’images restent soumis aux limites de sécurité et de réseau du backend.",
)


def get_tier(tier_id: str) -> TierConfig:
    try:
        return TIERS[tier_id]
    except KeyError as exc:
        raise ValueError(f"Niveau Assane inconnu : {tier_id}") from exc


def list_tiers() -> list[TierConfig]:
    return list(TIERS.values())
