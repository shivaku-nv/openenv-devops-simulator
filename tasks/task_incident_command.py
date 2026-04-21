def get_incident_command_task():
    return {
        "logs": (
            "Out of memory: Killed process 2145 (python3)\n"
            "checkout-api latency p95 exceeded 4.2s\n"
            "Deployment completed for checkout-api 18 minutes ago\n"
            "Customer support reports failed payments in us-east-1"
        ),
        "metrics": {
            "memory": 96,
            "cpu": 82,
            "latency_p95_ms": 4200,
            "error_rate": 0.18,
            "queue_depth": 240,
        },
        "label": "memory_leak",
        "solution": "restart_service",
        "reward_profile": "incident_command",
        "alerts": [
            "checkout-api high latency",
            "payment retries above threshold",
            "container memory saturation warning",
        ],
        "deployment_history": [
            "checkout-api v2026.04.21 deployed 18 minutes ago",
            "feature flag payment-retry enabled 23 minutes ago",
        ],
        "stakeholder_updates": [
            "Support: users cannot complete checkout in us-east-1",
            "Business: partner traffic is dropping after the latest deploy",
        ],
        "requires_communication": True,
        "requires_postmortem": True,
        "recommended_roles": [
            "incident_commander",
            "sre_agent",
            "app_logs_agent",
        ],
        "playbook_hint": "Investigate memory pressure before attempting rollback.",
    }
