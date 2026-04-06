INCIDENT_SCENARIOS = [
    {
        "incident_id": "INC-EASY-001",
        "task_level": "easy",
        "title": "Database connection pool exhausted",
        "true_root_cause": "API Gateway exceeded max connections to Postgres database.",
        "true_affected_service": "postgres-db",
        "required_runbook_keywords": ["increase", "max_connections", "pgbouncer", "restart", "pool"],
        "required_postmortem_sections": {
            "summary": ["exhausted", "database", "connections"],
            "root_cause": ["pool size", "max_connections", "limit"],
            "timeline": ["began", "alert", "resolved"],
            "impact": ["api", "downtime", "auth failed"],
            "action_items": ["pgbouncer", "pool size limit"]
        },
        "alert": {
            "alert_id": "ALT-001",
            "title": "High API Error Rate",
            "severity": "P1",
            "triggered_at": "2024-03-15T09:05:00Z",
            "affected_services": ["api-gateway", "postgres-db"],
            "description": "The api-gateway is experiencing a 500 error rate of over 15% in the last 2 minutes."
        },
        "metrics": [
            {
                "service_name": "postgres-db",
                "metric_name": "active_connections",
                "value": 100.0,
                "unit": "count",
                "threshold": 95.0,
                "is_anomalous": True
            },
            {
                "service_name": "api-gateway",
                "metric_name": "error_rate_5xx",
                "value": 18.5,
                "unit": "%",
                "threshold": 5.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-15T09:04:01Z", "level": "INFO", "service": "api-gateway", "message": "Request incoming for /api/v1/users", "trace_id": "tr-1a"},
            {"timestamp": "2024-03-15T09:04:02Z", "level": "INFO", "service": "postgres-db", "message": "Connection authenticated from 10.0.1.15", "trace_id": None},
            {"timestamp": "2024-03-15T09:04:05Z", "level": "ERROR", "service": "api-gateway", "message": "Failed to connect to database: FATAL: sorry, too many clients already", "trace_id": "tr-1b"},
            {"timestamp": "2024-03-15T09:04:10Z", "level": "ERROR", "service": "api-gateway", "message": "psycopg2.OperationalError: FATAL: sorry, too many clients already", "trace_id": "tr-1c"},
            {"timestamp": "2024-03-15T09:04:15Z", "level": "CRITICAL", "service": "postgres-db", "message": "remaining connection slots are reserved for non-replication superuser connections", "trace_id": None},
            {"timestamp": "2024-03-15T09:04:20Z", "level": "ERROR", "service": "api-gateway", "message": "Database connection timeout", "trace_id": "tr-1d"},
            {"timestamp": "2024-03-15T09:04:25Z", "level": "ERROR", "service": "api-gateway", "message": "Failed to query users table", "trace_id": "tr-1e"},
            {"timestamp": "2024-03-15T09:05:00Z", "level": "ERROR", "service": "api-gateway", "message": "Healthcheck failed. DB unreachable.", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-DB-101",
                "title": "Postgres Max Connections Reached",
                "tags": ["database", "postgres", "connections"],
                "content": "If Postgres logs 'too many clients already', check pg_stat_activity. You may need to increase max_connections in postgresql.conf or restart PgBouncer."
            },
            {
                "article_id": "KB-API-202",
                "title": "API Gateway Troubleshooting",
                "tags": ["api-gateway", "500-errors"],
                "content": "API Gateway 500s are usually caused by downstream timeouts. Check the specific error message to identify the failing downstream service."
            }
        ]
    },
    {
        "incident_id": "INC-EASY-002",
        "task_level": "easy",
        "title": "Nginx returning 502",
        "true_root_cause": "The backend payment-service process crashed, causing Nginx to return bad gateway.",
        "true_affected_service": "payment-service",
        "required_runbook_keywords": ["restart", "payment-service", "systemctl", "crash"],
        "required_postmortem_sections": {
            "summary": ["502", "nginx", "payment-service", "crashed"],
            "root_cause": ["service crash", "backend", "connection refused"],
            "timeline": ["alert", "troubleshoot", "restart"],
            "impact": ["payments failed", "checkout broken"],
            "action_items": ["investigate crash", "auto-restart"]
        },
        "alert": {
            "alert_id": "ALT-002",
            "title": "Nginx Elevated 502 Bad Gateway",
            "severity": "P2",
            "triggered_at": "2024-03-16T14:20:00Z",
            "affected_services": ["nginx-ingress", "payment-service"],
            "description": "Nginx ingress controller is reporting 502 responses for requests to /payments."
        },
        "metrics": [
            {
                "service_name": "nginx-ingress",
                "metric_name": "http_502_rate",
                "value": 45.0,
                "unit": "%",
                "threshold": 2.0,
                "is_anomalous": True
            },
            {
                "service_name": "payment-service",
                "metric_name": "cpu_usage",
                "value": 0.0,
                "unit": "%",
                "threshold": 80.0,
                "is_anomalous": False
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-16T14:18:00Z", "level": "INFO", "service": "payment-service", "message": "Processing payment transaction tx-992", "trace_id": "tx-992"},
            {"timestamp": "2024-03-16T14:18:22Z", "level": "CRITICAL", "service": "payment-service", "message": "Segmentation fault (core dumped)", "trace_id": None},
            {"timestamp": "2024-03-16T14:18:23Z", "level": "INFO", "service": "payment-service", "message": "Exiting with code 139", "trace_id": None},
            {"timestamp": "2024-03-16T14:18:45Z", "level": "ERROR", "service": "nginx-ingress", "message": "connect() failed (111: Connection refused) while connecting to upstream", "trace_id": "tx-993"},
            {"timestamp": "2024-03-16T14:19:00Z", "level": "ERROR", "service": "nginx-ingress", "message": "upstream prematurely closed connection", "trace_id": "tx-994"},
            {"timestamp": "2024-03-16T14:19:15Z", "level": "ERROR", "service": "nginx-ingress", "message": "connect() failed (111: Connection refused) while connecting to upstream", "trace_id": "tx-995"},
            {"timestamp": "2024-03-16T14:19:30Z", "level": "ERROR", "service": "nginx-ingress", "message": "connect() failed (111: Connection refused) while connecting to upstream", "trace_id": "tx-996"},
            {"timestamp": "2024-03-16T14:20:00Z", "level": "ERROR", "service": "nginx-ingress", "message": "connect() failed (111: Connection refused) while connecting to upstream", "trace_id": "tx-997"}
        ],
        "kb_articles": [
            {
                "article_id": "KB-NGX-001",
                "title": "Fixing Nginx 502 Bad Gateway",
                "tags": ["nginx", "502", "networking"],
                "content": "A 502 Bad Gateway typically implies the backend service that Nginx proxies to is down or not accepting connections. Check if the backend process is running."
            },
            {
                "article_id": "KB-PAY-005",
                "title": "Payment Service Restart Runbook",
                "tags": ["payment", "service"],
                "content": "To restart the payment service: run `systemctl restart payment-service`. Check logs in /var/log/payments/."
            }
        ]
    },
    {
        "incident_id": "INC-EASY-003",
        "task_level": "easy",
        "title": "Redis OOM",
        "true_root_cause": "Redis ran out of memory, rejecting new writes from the caching layer.",
        "true_affected_service": "redis-cache",
        "required_runbook_keywords": ["flush", "eviction", "memory", "maxmemory"],
        "required_postmortem_sections": {
            "summary": ["redis", "oom", "memory limit"],
            "root_cause": ["maxmemory", "eviction policy", "cache full"],
            "timeline": ["memory plateau", "write failures"],
            "impact": ["cache misses", "latency spike"],
            "action_items": ["change eviction policy", "increase ram"]
        },
        "alert": {
            "alert_id": "ALT-003",
            "title": "Redis Memory Critical / Write Failures",
            "severity": "P2",
            "triggered_at": "2024-03-18T06:10:00Z",
            "affected_services": ["redis-cache", "worker-service"],
            "description": "Redis memory usage is at 100%. Worker service is reporting cache write failures."
        },
        "metrics": [
            {
                "service_name": "redis-cache",
                "metric_name": "memory_usage",
                "value": 99.9,
                "unit": "%",
                "threshold": 90.0,
                "is_anomalous": True
            },
            {
                "service_name": "worker-service",
                "metric_name": "cache_error_rate",
                "value": 30.5,
                "unit": "%",
                "threshold": 5.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-18T06:08:00Z", "level": "WARN", "service": "redis-cache", "message": "Memory warning: 95% utilized.", "trace_id": None},
            {"timestamp": "2024-03-18T06:09:00Z", "level": "ERROR", "service": "worker-service", "message": "Failed to SET key user:session:123 - OOM command not allowed when used memory > 'maxmemory'.", "trace_id": "tsk-1"},
            {"timestamp": "2024-03-18T06:09:15Z", "level": "ERROR", "service": "worker-service", "message": "Failed to SET key product:details:500 - OOM command not allowed when used memory > 'maxmemory'.", "trace_id": "tsk-2"},
            {"timestamp": "2024-03-18T06:09:30Z", "level": "CRITICAL", "service": "redis-cache", "message": "OOM command not allowed when used memory > 'maxmemory'.", "trace_id": None},
            {"timestamp": "2024-03-18T06:09:40Z", "level": "ERROR", "service": "worker-service", "message": "Failed to SET key analytics:daily - OOM command not allowed when used memory > 'maxmemory'.", "trace_id": "tsk-3"},
            {"timestamp": "2024-03-18T06:09:50Z", "level": "ERROR", "service": "worker-service", "message": "Exception in caching layer: RedisError: OOM", "trace_id": None},
            {"timestamp": "2024-03-18T06:10:00Z", "level": "ERROR", "service": "worker-service", "message": "Redis is read-only. Retrying...", "trace_id": None},
            {"timestamp": "2024-03-18T06:10:10Z", "level": "CRITICAL", "service": "redis-cache", "message": "Out of memory. No keys to evict. Policy: noeviction.", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-REDIS-301",
                "title": "Redis Out of Memory (OOM)",
                "tags": ["redis", "oom", "cache"],
                "content": "If Redis logs 'OOM command not allowed check maxmemory-policy. If it is 'noeviction', you must manually flush unused keys or change policy to 'allkeys-lru'."
            },
            {
                "article_id": "KB-WORKER-002",
                "title": "Worker Service Cache Fallback",
                "tags": ["worker", "caching"],
                "content": "The worker service defaults to writing to Redis. If Redis is down, it skips cache and queries DB directly, which may increase DB load."
            }
        ]
    },
    {
        "incident_id": "INC-MED-001",
        "task_level": "medium",
        "title": "Upstream timeout causing downstream queue backup",
        "true_root_cause": "An external API dependency timed out, causing the worker-service to exhaust its thread pool and pile up the message queue.",
        "true_affected_service": "worker-service",
        "required_runbook_keywords": ["timeout", "concurrency", "restart", "queue", "flush"],
        "required_postmortem_sections": {
            "summary": ["upstream", "timeout", "queue", "backlog"],
            "root_cause": ["external api", "thread exhaustion", "infinite hang"],
            "timeline": ["api degraded", "queue grew", "workers locked"],
            "impact": ["background jobs stalled", "data delayed"],
            "action_items": ["add request timeout", "circuit breaker"]
        },
        "alert": {
            "alert_id": "ALT-101",
            "title": "High Kafka Queue Lag",
            "severity": "P1",
            "triggered_at": "2024-03-20T11:00:00Z",
            "affected_services": ["kafka", "worker-service"],
            "description": "Consumer lag for 'job-queue' topic has exceeded 50,000 messages."
        },
        "metrics": [
            {
                "service_name": "kafka",
                "metric_name": "consumer_lag",
                "value": 52000.0,
                "unit": "messages",
                "threshold": 10000.0,
                "is_anomalous": True
            },
            {
                "service_name": "worker-service",
                "metric_name": "active_threads",
                "value": 100.0,
                "unit": "%",
                "threshold": 95.0,
                "is_anomalous": True
            },
            {
                "service_name": "worker-service",
                "metric_name": "external_api_latency",
                "value": 30000.0,
                "unit": "ms",
                "threshold": 5000.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-20T10:55:00Z", "level": "INFO", "service": "worker-service", "message": "Calling 3rd party shipping API...", "trace_id": "job-1001"},
            {"timestamp": "2024-03-20T10:55:05Z", "level": "INFO", "service": "worker-service", "message": "Calling 3rd party shipping API...", "trace_id": "job-1002"},
            {"timestamp": "2024-03-20T10:55:30Z", "level": "WARN", "service": "worker-service", "message": "Timeout matching downstream. API request to shipping provider hung.", "trace_id": "job-1001"},
            {"timestamp": "2024-03-20T10:56:00Z", "level": "WARN", "service": "worker-service", "message": "Worker pool saturated. No available threads.", "trace_id": None},
            {"timestamp": "2024-03-20T10:57:00Z", "level": "ERROR", "service": "worker-service", "message": "Failed to poll Kafka: consumer thread locked.", "trace_id": None},
            {"timestamp": "2024-03-20T10:58:00Z", "level": "WARN", "service": "kafka", "message": "Consumer group 'worker-group' is lagging.", "trace_id": None},
            {"timestamp": "2024-03-20T10:59:00Z", "level": "ERROR", "service": "worker-service", "message": "Queue capacity exceeded internally. Rejecting messages.", "trace_id": None},
            {"timestamp": "2024-03-20T11:00:00Z", "level": "CRITICAL", "service": "kafka", "message": "Lag alert threshold breached for topic job-queue", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-KAFKA-100",
                "title": "Kafka Consumer Lag Troubleshoot",
                "tags": ["kafka", "lag", "consumers"],
                "content": "Lag happens when consumers die or process too slowly. Check the consumer service logs for thread deadlocks, high CPU, or infinite blocking calls."
            },
            {
                "article_id": "KB-WORKER-003",
                "title": "Worker Service Integrations",
                "tags": ["worker", "shipping-api"],
                "content": "The worker service relies on external REST APIs. If an external API is down, we must temporarily disable the integration flag or hard restart consumers."
            }
        ]
    },
    {
        "incident_id": "INC-MED-002",
        "task_level": "medium",
        "title": "Memory leak causing CPU spike",
        "true_root_cause": "A memory leak in the elasticsearch indexer caused GC thrashing, resulting in 100% CPU usage.",
        "true_affected_service": "elasticsearch",
        "required_runbook_keywords": ["memory leak", "heap", "gc", "restart", "jvm"],
        "required_postmortem_sections": {
            "summary": ["cpu spike", "memory leak", "elasticsearch"],
            "root_cause": ["garbage collection", "heap exhaustion", "gc thrashing"],
            "timeline": ["memory grew", "cpu spiked", "unresponsive"],
            "impact": ["search failed", "api latency"],
            "action_items": ["heap dump", "fix leak", "increase heap"]
        },
        "alert": {
            "alert_id": "ALT-102",
            "title": "Elasticsearch Unresponsive",
            "severity": "P2",
            "triggered_at": "2024-03-21T02:30:00Z",
            "affected_services": ["elasticsearch", "api-gateway"],
            "description": "Elasticsearch node health is RED. API search requests are timing out."
        },
        "metrics": [
            {
                "service_name": "elasticsearch",
                "metric_name": "cpu_usage",
                "value": 100.0,
                "unit": "%",
                "threshold": 80.0,
                "is_anomalous": True
            },
            {
                "service_name": "elasticsearch",
                "metric_name": "jvm_heap_usage",
                "value": 99.5,
                "unit": "%",
                "threshold": 85.0,
                "is_anomalous": True
            },
            {
                "service_name": "api-gateway",
                "metric_name": "search_latency",
                "value": 9000.0,
                "unit": "ms",
                "threshold": 500.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-21T02:25:00Z", "level": "WARN", "service": "elasticsearch", "message": "[gc][old] [14562] duration [900ms], collections [1]/[1.5s], total [900ms]/[2h], memory [15.9gb]->[15.8gb]/[16gb]", "trace_id": None},
            {"timestamp": "2024-03-21T02:26:00Z", "level": "WARN", "service": "elasticsearch", "message": "[gc][old] [14603] duration [1.2s], collections [1]/[1.3s], memory [15.9gb]->[15.9gb]/[16gb]", "trace_id": None},
            {"timestamp": "2024-03-21T02:27:00Z", "level": "ERROR", "service": "elasticsearch", "message": "System.OutOfMemoryException: Java heap space", "trace_id": None},
            {"timestamp": "2024-03-21T02:28:00Z", "level": "ERROR", "service": "api-gateway", "message": "Search request to ES failed: Read timeout", "trace_id": "req-991"},
            {"timestamp": "2024-03-21T02:29:00Z", "level": "CRITICAL", "service": "elasticsearch", "message": "Node is running out of memory. GC pause 2500ms.", "trace_id": None},
            {"timestamp": "2024-03-21T02:29:30Z", "level": "ERROR", "service": "api-gateway", "message": "Search request to ES failed: Read timeout", "trace_id": "req-992"},
            {"timestamp": "2024-03-21T02:29:45Z", "level": "ERROR", "service": "api-gateway", "message": "Search request to ES failed: Read timeout", "trace_id": "req-993"},
            {"timestamp": "2024-03-21T02:30:00Z", "level": "CRITICAL", "service": "elasticsearch", "message": "Node left cluster due to unresponsiveness.", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-ES-101",
                "title": "Elasticsearch High CPU",
                "tags": ["elasticsearch", "cpu", "jvm"],
                "content": "High CPU in ES is often a symptom of JVM heap exhaustion causing GC thrashing. Check JVM heap usage metrics. If near 100%, restart the node and capture a heap dump to find the memory leak."
            },
            {
                "article_id": "KB-API-205",
                "title": "Handling Search Failures",
                "tags": ["api-gateway", "search"],
                "content": "API Gateway relies on Elasticsearch for the /search endpoint. If ES is down, the API falls back to degraded mode (no results)."
            }
        ]
    },
    {
        "incident_id": "INC-MED-003",
        "task_level": "medium",
        "title": "Slow database queries freezing auth service",
        "true_root_cause": "A missing database index on the users table caused full table scans, overwhelming the DB CPU and freezing the auth-service.",
        "true_affected_service": "postgres-db",
        "required_runbook_keywords": ["index", "slow query", "auth-service", "database", "cpu"],
        "required_postmortem_sections": {
            "summary": ["auth", "slow queries", "database cpu"],
            "root_cause": ["missing index", "table scan", "high cpu"],
            "timeline": ["query deployed", "db load spiked", "auth timeout"],
            "impact": ["users cannot login", "auth timeouts"],
            "action_items": ["create index", "query review"]
        },
        "alert": {
            "alert_id": "ALT-103",
            "title": "Auth Service Latency Critical",
            "severity": "P1",
            "triggered_at": "2024-03-22T08:15:00Z",
            "affected_services": ["auth-service", "postgres-db"],
            "description": "Auth-service p99 latency exceeded 10 seconds. Logins are failing."
        },
        "metrics": [
            {
                "service_name": "postgres-db",
                "metric_name": "cpu_usage",
                "value": 98.5,
                "unit": "%",
                "threshold": 80.0,
                "is_anomalous": True
            },
            {
                "service_name": "auth-service",
                "metric_name": "latency_p99",
                "value": 12000.0,
                "unit": "ms",
                "threshold": 1000.0,
                "is_anomalous": True
            },
            {
                "service_name": "postgres-db",
                "metric_name": "slow_queries_per_sec",
                "value": 45.0,
                "unit": "count",
                "threshold": 5.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-22T08:10:00Z", "level": "INFO", "service": "auth-service", "message": "Received login request for user_id=8831", "trace_id": "lgn-1"},
            {"timestamp": "2024-03-22T08:11:00Z", "level": "WARN", "service": "postgres-db", "message": "SLOW QUERY (5050ms): SELECT * FROM users WHERE last_login_ip = '10.0.x.x';", "trace_id": None},
            {"timestamp": "2024-03-22T08:12:00Z", "level": "WARN", "service": "postgres-db", "message": "SLOW QUERY (8100ms): SELECT * FROM users WHERE last_login_ip = '10.0.x.x';", "trace_id": None},
            {"timestamp": "2024-03-22T08:13:00Z", "level": "ERROR", "service": "auth-service", "message": "Login request timed out after 10000ms", "trace_id": "lgn-1"},
            {"timestamp": "2024-03-22T08:14:00Z", "level": "ERROR", "service": "auth-service", "message": "Database query timeout for table 'users'", "trace_id": "lgn-2"},
            {"timestamp": "2024-03-22T08:14:30Z", "level": "WARN", "service": "postgres-db", "message": "CPU threshold exceeded due to high i/o wait on sequential scan", "trace_id": None},
            {"timestamp": "2024-03-22T08:15:00Z", "level": "ERROR", "service": "auth-service", "message": "Circuit breaker OPEN for auth-db-pool", "trace_id": None},
            {"timestamp": "2024-03-22T08:15:10Z", "level": "CRITICAL", "service": "auth-service", "message": "Login requests completely failing", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-DB-008",
                "title": "Postgres CPU Spikes",
                "tags": ["postgres", "cpu", "performance"],
                "content": "If Postgres CPU is near 100%, it is usually caused by unoptimized queries doing sequential scans. Check for 'SLOW QUERY' in logs. Creating missing indexes usually resolves this."
            },
            {
                "article_id": "KB-AUTH-200",
                "title": "Auth Service DB Timeouts",
                "tags": ["auth-service", "database"],
                "content": "Auth service requires sub-200ms DB responses. If queries take too long, the connection pool locks up, and the circuit breaker opens."
            }
        ]
    },
    {
        "incident_id": "INC-HARD-001",
        "task_level": "hard",
        "title": "Network partition looks like an app bug",
        "true_root_cause": "A network partition between AZ1 and AZ2 caused auth-service and payment-service to lose connection to the central Redis cluster.",
        "true_affected_service": "network-infrastructure",
        "required_runbook_keywords": ["network", "partition", "az", "failover", "connectivity"],
        "required_postmortem_sections": {
            "summary": ["network partition", "multiple services", "connection resets"],
            "root_cause": ["aws az failure", "network drop", "switch failure"],
            "timeline": ["errors started", "services isolated", "failover triggered"],
            "impact": ["cross-az traffic dropped", "payments failed", "auth failed"],
            "action_items": ["az failover runbook", "multi-az redis"]
        },
        "alert": {
            "alert_id": "ALT-201",
            "title": "Massive Multi-Service Error Spike",
            "severity": "P1",
            "triggered_at": "2024-03-25T16:00:00Z",
            "affected_services": ["auth-service", "payment-service", "redis-cache"],
            "description": "Critical spike in errors across multiple independent microservices simultaneously."
        },
        "metrics": [
            {
                "service_name": "auth-service",
                "metric_name": "error_rate_5xx",
                "value": 45.0,
                "unit": "%",
                "threshold": 5.0,
                "is_anomalous": True
            },
            {
                "service_name": "payment-service",
                "metric_name": "error_rate_5xx",
                "value": 38.0,
                "unit": "%",
                "threshold": 5.0,
                "is_anomalous": True
            },
            {
                "service_name": "redis-cache",
                "metric_name": "cpu_usage",
                "value": 15.0,
                "unit": "%",
                "threshold": 80.0,
                "is_anomalous": False
            },
            {
                "service_name": "network-infrastructure",
                "metric_name": "cross_az_packet_loss",
                "value": 100.0,
                "unit": "%",
                "threshold": 1.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-25T15:58:00Z", "level": "INFO", "service": "auth-service", "message": "Authenticating user", "trace_id": "auth-1"},
            {"timestamp": "2024-03-25T15:58:05Z", "level": "ERROR", "service": "auth-service", "message": "Connection reset by peer while reading from redis-cache.az2.internal", "trace_id": "auth-1"},
            {"timestamp": "2024-03-25T15:58:10Z", "level": "ERROR", "service": "payment-service", "message": "Timeout while discovering peers: No route to host 10.0.5.15", "trace_id": "pay-2"},
            {"timestamp": "2024-03-25T15:58:30Z", "level": "ERROR", "service": "auth-service", "message": "Failed to connect to redis-cache. AZ networking unreachable.", "trace_id": "auth-2"},
            {"timestamp": "2024-03-25T15:59:00Z", "level": "ERROR", "service": "payment-service", "message": "Connection reset by peer: cannot connect to payment-processor", "trace_id": "pay-3"},
            {"timestamp": "2024-03-25T15:59:30Z", "level": "WARN", "service": "redis-cache", "message": "Lost connection to 150 clients abruptly.", "trace_id": None},
            {"timestamp": "2024-03-25T16:00:00Z", "level": "CRITICAL", "service": "auth-service", "message": "Multiple dependencies unreachable. Entering survival mode.", "trace_id": None},
            {"timestamp": "2024-03-25T16:00:10Z", "level": "CRITICAL", "service": "nginx-ingress", "message": "Upstreams auth-service and payment-service highly unstable.", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-NET-900",
                "title": "AZ Failover Runbook",
                "tags": ["network", "az failover", "aws"],
                "content": "If multiple unrelated services log 'Connection reset by peer' or 'No route to host' to specific subnets, suspect a network partition or AZ failure. Do not restart apps. Initiate emergency traffic routing to the healthy AZ."
            },
            {
                "article_id": "KB-APP-404",
                "title": "Debugging App Connection Refused",
                "tags": ["app", "connection issues"],
                "content": "If an app throws connection refused, it's usually because the target app crashed. Check the target app's CPU/Memory."
            }
        ]
    },
    {
        "incident_id": "INC-HARD-002",
        "task_level": "hard",
        "title": "Bad deploy causing DB deadlocks looking like traffic spike",
        "true_root_cause": "A recent deployment of the order-service introduced a bulk-update query that locks tables in an inconsistent order, causing Postgres deadlocks. This creates a backlog that looks like a DDoS/traffic spike.",
        "true_affected_service": "order-service",
        "required_runbook_keywords": ["rollback", "deploy", "deadlock", "order-service", "transaction"],
        "required_postmortem_sections": {
            "summary": ["deadlocks", "order-service", "deployment", "false traffic spike"],
            "root_cause": ["bad transaction logic", "table locking", "new release"],
            "timeline": ["deploy finished", "locks accumulated", "api degraded"],
            "impact": ["orders failed", "database locked"],
            "action_items": ["revert deployment", "fix lock ordering", "db testing"]
        },
        "alert": {
            "alert_id": "ALT-202",
            "title": "Order Service Degradation / Suspected Traffic Spike",
            "severity": "P1",
            "triggered_at": "2024-03-28T10:15:00Z",
            "affected_services": ["order-service", "postgres-db", "api-gateway"],
            "description": "High latency and errors on order creation. API gateway queuing requests. Suspicion of DDoS."
        },
        "metrics": [
            {
                "service_name": "api-gateway",
                "metric_name": "request_in_flight",
                "value": 5000.0,
                "unit": "count",
                "threshold": 1000.0,
                "is_anomalous": True
            },
            {
                "service_name": "order-service",
                "metric_name": "response_time",
                "value": 15000.0,
                "unit": "ms",
                "threshold": 2000.0,
                "is_anomalous": True
            },
            {
                "service_name": "postgres-db",
                "metric_name": "db_locked_transactions",
                "value": 120.0,
                "unit": "count",
                "threshold": 5.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-28T10:05:00Z", "level": "INFO", "service": "order-service", "message": "Application started. Version v2.4.1 deployed successfully.", "trace_id": None},
            {"timestamp": "2024-03-28T10:08:00Z", "level": "INFO", "service": "order-service", "message": "Processing bulk order update for merchant 88", "trace_id": "ord-1"},
            {"timestamp": "2024-03-28T10:10:00Z", "level": "ERROR", "service": "postgres-db", "message": "ERROR: deadlock detected. Detail: Process 124 waits for ShareLock on transaction 99; blocked by process 125.", "trace_id": None},
            {"timestamp": "2024-03-28T10:11:00Z", "level": "ERROR", "service": "postgres-db", "message": "ERROR: deadlock detected. Deadlock found when trying to get lock; try restarting transaction", "trace_id": None},
            {"timestamp": "2024-03-28T10:12:00Z", "level": "ERROR", "service": "order-service", "message": "User action failed: SQLAlchemy.exc.OperationalError: deadlock detected", "trace_id": "ord-2"},
            {"timestamp": "2024-03-28T10:13:00Z", "level": "WARN", "service": "api-gateway", "message": "Upstream order-service taking too long. Queuing request.", "trace_id": "req-999"},
            {"timestamp": "2024-03-28T10:14:00Z", "level": "CRITICAL", "service": "api-gateway", "message": "Max concurrent requests exceeded. Rejecting incoming traffic.", "trace_id": None},
            {"timestamp": "2024-03-28T10:15:00Z", "level": "ERROR", "service": "order-service", "message": "Transaction rollback failed due to connection timeout", "trace_id": "ord-3"}
        ],
        "kb_articles": [
            {
                "article_id": "KB-DB-401",
                "title": "Resolving DB Deadlocks",
                "tags": ["database", "deadlock", "postgres"],
                "content": "Deadlocks occur when two transactions hold locks and wait for each other. If this suddenly appears, it's almost always a code bug. Roll back the latest deployment."
            },
            {
                "article_id": "KB-API-101",
                "title": "Handling DDoS and High Traffic",
                "tags": ["api-gateway", "ddos", "traffic"],
                "content": "If requests_in_flight spikes, enable standard rate limiting at the WAF level. Note: Ensure downstream isn't just responding slowly, causing requests to pile up."
            }
        ]
    },
    {
        "incident_id": "INC-HARD-003",
        "task_level": "hard",
        "title": "Infinite retry loop in microservice DDOSing API gateway",
        "true_root_cause": "A misconfigured retry loop in worker-service (no exponential backoff) is infinitely retrying a broken endpoint, causing a self-inflicted DDoS on the api-gateway.",
        "true_affected_service": "worker-service",
        "required_runbook_keywords": ["retry", "backoff", "worker-service", "infinite loop", "ddos"],
        "required_postmortem_sections": {
            "summary": ["self-ddos", "retry storm", "worker-service"],
            "root_cause": ["missing backoff", "infinite retries", "code bug"],
            "timeline": ["endpoint failed", "retries triggered", "api overwhelmed"],
            "impact": ["gateway crashed", "platform down"],
            "action_items": ["implement backoff", "circuit breaker", "fix worker loop"]
        },
        "alert": {
            "alert_id": "ALT-203",
            "title": "API Gateway Traffic Spike / Rate Limits",
            "severity": "P1",
            "triggered_at": "2024-03-30T22:00:00Z",
            "affected_services": ["api-gateway", "worker-service"],
            "description": "API Gateway is receiving 100x normal traffic volume and throwing 429 Too Many Requests."
        },
        "metrics": [
            {
                "service_name": "api-gateway",
                "metric_name": "request_rate",
                "value": 50000.0,
                "unit": "req/sec",
                "threshold": 5000.0,
                "is_anomalous": True
            },
            {
                "service_name": "worker-service",
                "metric_name": "cpu_usage",
                "value": 95.0,
                "unit": "%",
                "threshold": 80.0,
                "is_anomalous": True
            },
            {
                "service_name": "api-gateway",
                "metric_name": "http_429_rate",
                "value": 60.0,
                "unit": "%",
                "threshold": 1.0,
                "is_anomalous": True
            }
        ],
        "recent_logs": [
            {"timestamp": "2024-03-30T21:55:00Z", "level": "WARN", "service": "api-gateway", "message": "Upstream service 'inventory' returned 503 Service Unavailable", "trace_id": "req-1"},
            {"timestamp": "2024-03-30T21:55:01Z", "level": "INFO", "service": "worker-service", "message": "Failed to update inventory. Retrying failed request...", "trace_id": "req-1"},
            {"timestamp": "2024-03-30T21:55:01Z", "level": "INFO", "service": "worker-service", "message": "Failed to update inventory. Retrying failed request...", "trace_id": "req-1"},
            {"timestamp": "2024-03-30T21:56:00Z", "level": "WARN", "service": "api-gateway", "message": "Rate limit exceeded for internal IP 10.0.1.55 (worker-service)", "trace_id": None},
            {"timestamp": "2024-03-30T21:57:00Z", "level": "ERROR", "service": "worker-service", "message": "API Gateway returned 429 Too Many Requests. Retrying in 0ms...", "trace_id": "req-1"},
            {"timestamp": "2024-03-30T21:58:00Z", "level": "CRITICAL", "service": "api-gateway", "message": "Max connection pool reached. CPU at 100%. Dropping packets.", "trace_id": None},
            {"timestamp": "2024-03-30T21:59:00Z", "level": "ERROR", "service": "worker-service", "message": "Upstream request timeout. Retrying failed request...", "trace_id": "req-2"},
            {"timestamp": "2024-03-30T22:00:00Z", "level": "CRITICAL", "service": "worker-service", "message": "Thread pool exhausted executing retry loop.", "trace_id": None}
        ],
        "kb_articles": [
            {
                "article_id": "KB-API-999",
                "title": "Mitigating DDoS Attacks",
                "tags": ["ddos", "security", "api-gateway"],
                "content": "If traffic spikes 100x naturally, enable Cloudflare Under Attack mode. However, if the source IP is internal, look for a rogue script or retry storm."
            },
            {
                "article_id": "KB-DEV-101",
                "title": "Safe Retry Patterns",
                "tags": ["development", "retries"],
                "content": "All inter-service communications must implement exponential backoff and jitter. A missing backoff can cause a retry storm that acts like a self-inflicted DDoS."
            }
        ]
    }
]
