from pathlib import Path

path = Path("services/local-core/src/book_os_core/app.py")
text = path.read_text()
old = '''    @app.get("/api/provider-lane/readiness")
    def provider_readiness(_: None = Depends(require_token)) -> dict[str, object]:
        roles: dict[str, dict[str, object]] = {}
        for role in ("WRITER", "EDITOR", "EVALUATOR"):
            decision = (
                provider_lane.route(role)
                if provider_lane
                else RussiaPolicy().route(seed_capabilities(), role=role)
            )
            roles[role] = {
                "available": decision.available,
                "reason": decision.reason,
                "provider": decision.capability.provider if decision.capability else None,
                "model": decision.capability.model if decision.capability else None,
            }
        return {
            "region": "RU",
            "ready": all(bool(value["available"]) for value in roles.values()),
            "implementation_ready": True,
            "live_promotion_required": True,
            "credentials": credential_availability(provider_secrets),
            "roles": roles,
        }
'''
new = '''    @app.get("/api/provider-lane/readiness")
    def provider_readiness(_: None = Depends(require_token)) -> dict[str, object]:
        required_launch_roles = ("WRITER", "EDITOR")
        roles: dict[str, dict[str, object]] = {}
        for role in (*required_launch_roles, "EVALUATOR"):
            decision = (
                provider_lane.route(role)
                if provider_lane
                else RussiaPolicy().route(seed_capabilities(), role=role)
            )
            roles[role] = {
                "available": decision.available,
                "reason": decision.reason,
                "provider": decision.capability.provider if decision.capability else None,
                "model": decision.capability.model if decision.capability else None,
            }
        routes_ready = all(bool(roles[role]["available"]) for role in required_launch_roles)
        credentials = credential_availability(provider_secrets)
        selected_providers = {
            str(roles[role]["provider"])
            for role in required_launch_roles
            if roles[role]["available"] and roles[role]["provider"] is not None
        }
        credentials_ready = routes_ready and all(
            credentials.get(provider) == "AVAILABLE" for provider in selected_providers
        )
        return {
            "region": "RU",
            "ready": routes_ready,
            "routes_ready": routes_ready,
            "production_ready": routes_ready and credentials_ready,
            "implementation_ready": True,
            "live_promotion_required": not routes_ready,
            "credentials_ready": credentials_ready,
            "credentials": credentials,
            "required_launch_roles": list(required_launch_roles),
            "evaluation_role": roles["EVALUATOR"],
            "roles": roles,
        }
'''
if old not in text:
    raise SystemExit("provider readiness target not found")
path.write_text(text.replace(old, new, 1))
