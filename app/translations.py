# translations.py — CZ / EN UI strings for K8s AI Analyzer

TEXTS = {
    # ── App ────────────────────────────────────────────────────────────────────
    'app_subtitle':         {'CZ': "Nástroj AI-analýzy Kubernetes pro L2/L3 support týmy",
                             'EN': "AI-powered Kubernetes analysis tool for L2/L3 support teams"},

    # ── Sidebar ────────────────────────────────────────────────────────────────
    'sidebar_config':       {'CZ': "Konfigurace",               'EN': "Configuration"},
    'connection_mode':      {'CZ': "Režim připojení",           'EN': "Connection mode"},
    'mode_kubeconfig':      {'CZ': "Nahrát kubeconfig soubory", 'EN': "Upload kubeconfig files"},
    'mode_rancher':         {'CZ': "Rancher Gateway",           'EN': "Rancher Gateway"},
    'mode_help':            {'CZ': "Vyberte způsob připojení ke Kubernetes clusterům",
                             'EN': "Select the method for connecting to Kubernetes clusters"},
    'upload_kubeconfig':    {'CZ': "Nahrát kubeconfig soubory", 'EN': "Upload kubeconfig files"},
    'kubeconfig_loaded':    {'CZ': "✅ Načteno {n} kubeconfig(s)", 'EN': "✅ Loaded {n} kubeconfig(s)"},

    'rancher_section':      {'CZ': "🐄 Rancher Připojení",     'EN': "🐄 Rancher Connection"},
    'rancher_gw_label':     {'CZ': "Rancher Gateway",           'EN': "Rancher Gateway"},
    'rancher_gw_help':      {'CZ': "Vyberte Rancher instanci nebo zadejte vlastní URL",
                             'EN': "Select a Rancher instance or enter a custom URL"},
    'rancher_custom_url':   {'CZ': "✏️ Zadat vlastní URL...",  'EN': "✏️ Custom URL..."},
    'rancher_url_label':    {'CZ': "Vlastní Rancher URL",       'EN': "Custom Rancher URL"},
    'rancher_url_ph':       {'CZ': "https://rancher.example.com", 'EN': "https://rancher.example.com"},
    'rancher_url_help':     {'CZ': "URL vašeho Rancher serveru", 'EN': "Your Rancher server URL"},
    'username':             {'CZ': "Uživatelské jméno",         'EN': "Username"},
    'username_help':        {'CZ': "Rancher uživatelské jméno", 'EN': "Rancher username"},
    'password':             {'CZ': "Heslo",                     'EN': "Password"},
    'password_help':        {'CZ': "Rancher heslo",             'EN': "Rancher password"},
    'verify_ssl':           {'CZ': "Ověřovat SSL certifikáty",  'EN': "Verify SSL certificates"},
    'verify_ssl_help':      {'CZ': "Vypněte pro self-signed certifikáty",
                             'EN': "Disable for self-signed certificates"},
    'btn_connect_rancher':  {'CZ': "🔌 Připojit k Rancher",    'EN': "🔌 Connect to Rancher"},
    'err_enter_url':        {'CZ': "⚠️ Zadejte URL Rancher serveru", 'EN': "⚠️ Enter Rancher server URL"},
    'err_enter_creds':      {'CZ': "⚠️ Vyplňte uživatelské jméno a heslo",
                             'EN': "⚠️ Enter username and password"},
    'spinner_connecting':   {'CZ': "Připojuji se k Rancher...", 'EN': "Connecting to Rancher..."},
    'clusters_found':       {'CZ': "📋 Nalezeno {n} clusterů", 'EN': "📋 Found {n} clusters"},
    'no_clusters':          {'CZ': "⚠️ Žádné clustery nenalezeny", 'EN': "⚠️ No clusters found"},
    'err_generic':          {'CZ': "❌ Chyba: {e}",             'EN': "❌ Error: {e}"},
    'available_clusters':   {'CZ': "📋 Dostupné clustery",      'EN': "📋 Available clusters"},
    'select_cluster':       {'CZ': "Vyberte cluster",           'EN': "Select cluster"},
    'select_cluster_help':  {'CZ': "Vyberte cluster pro analýzu", 'EN': "Select cluster for analysis"},
    'btn_load_kubeconfig':  {'CZ': "🔄 Načíst kubeconfig",      'EN': "🔄 Load kubeconfig"},
    'spinner_kubeconfig':   {'CZ': "Načítám kubeconfig...",     'EN': "Loading kubeconfig..."},
    'kubeconfig_ok':        {'CZ': "✅ Kubeconfig načten úspěšně ({m})",
                             'EN': "✅ Kubeconfig loaded successfully ({m})"},
    'kubeconfig_fail':      {'CZ': "❌ Nepodařilo se získat kubeconfig ani jedním způsobem.",
                             'EN': "❌ Failed to obtain kubeconfig by any method."},
    'kubeconfig_preview':   {'CZ': "🔍 Debug: Kubeconfig náhled", 'EN': "🔍 Debug: Kubeconfig preview"},
    'warn_exec_creds':      {'CZ': "⚠️ generateKubeconfig vrátil exec: credentials (vyžaduje rancher CLI). Přepínám na Basic Auth proxy...",
                             'EN': "⚠️ generateKubeconfig returned exec: credentials (requires rancher CLI). Switching to Basic Auth proxy..."},
    'warn_gen_failed':      {'CZ': "⚠️ generateKubeconfig selhalo: {e}", 'EN': "⚠️ generateKubeconfig failed: {e}"},
    'info_403_key':         {'CZ': "🔑 API klíč nemá oprávnění volat generateKubeconfig. Zkuste klíč s **No Scope** nebo rolí **Cluster Owner**. Přepínám na Basic Auth proxy...",
                             'EN': "🔑 API key lacks permission to call generateKubeconfig. Try a key with **No Scope** or **Cluster Owner** role. Switching to Basic Auth proxy..."},
    'err_proxy_kube':       {'CZ': "❌ Nelze vygenerovat proxy kubeconfig: {e}",
                             'EN': "❌ Cannot generate proxy kubeconfig: {e}"},

    'ai_model':             {'CZ': "AI Model",                  'EN': "AI Model"},
    'ollama_ok':            {'CZ': "✅ Ollama běží ({url})",     'EN': "✅ Ollama running ({url})"},
    'ollama_err':           {'CZ': "❌ Ollama nedostupná na {url}: {e}",
                             'EN': "❌ Ollama unavailable at {url}: {e}"},

    # ── Tabs ───────────────────────────────────────────────────────────────────
    'tab_overview':         {'CZ': "Přehled clusteru",          'EN': "Cluster Overview"},
    'tab_pods':             {'CZ': "Analýza podů",              'EN': "Pod Analysis"},
    'tab_events':           {'CZ': "Eventy & Alerty",           'EN': "Events & Alerts"},
    'tab_insights':         {'CZ': "AI Insights",               'EN': "AI Insights"},
    'tab_chat':             {'CZ': "AI Chat",                   'EN': "AI Chat"},
    'tab_k8sgpt':           {'CZ': "K8sGPT Analýza",            'EN': "K8sGPT Analysis"},
    'tab_logs':             {'CZ': "Logy",                      'EN': "Logs"},
    'tab_egress':           {'CZ': "Egress / Network Test",     'EN': "Egress / Network Test"},

    # ── Tab 1: Cluster Overview ────────────────────────────────────────────────
    'h_cluster_overview':   {'CZ': "Přehled clusteru",          'EN': "Cluster Overview"},
    'metric_nodes':         {'CZ': "Nody",                      'EN': "Nodes"},
    'metric_total_pods':    {'CZ': "Celkem podů",               'EN': "Total Pods"},
    'metric_namespaces':    {'CZ': "Namespacy",                 'EN': "Namespaces"},
    'h_node_status':        {'CZ': "Stav nodů",                 'EN': "Node Status"},
    'connect_prompt':       {'CZ': "Připojte se ke clusteru pomocí kubeconfig nebo Rancher.",
                             'EN': "Please connect to a cluster via kubeconfig or Rancher."},
    'err_init':             {'CZ': "❌ Chyba inicializace: {e}", 'EN': "❌ Initialization error: {e}"},

    # ── Tab 2: Pod Analysis ────────────────────────────────────────────────────
    'h_pod_analysis':       {'CZ': "Analýza podů",              'EN': "Pod Analysis"},
    'pod_running':          {'CZ': "Běžící",                    'EN': "Running"},
    'pod_pending':          {'CZ': "Čekající",                  'EN': "Pending"},
    'pod_failed':           {'CZ': "Selhané",                   'EN': "Failed"},
    'pod_succeeded':        {'CZ': "Dokončené",                 'EN': "Succeeded"},
    'h_problematic_pods':   {'CZ': "Problematické pody",        'EN': "Problematic Pods"},

    # ── Tab 3: Events ──────────────────────────────────────────────────────────
    'h_events':             {'CZ': "Eventy & Alerty",           'EN': "Events & Alerts"},
    'h_recent_events':      {'CZ': "Nedávné eventy (poslední hodina)", 'EN': "Recent Events (Last Hour)"},
    'no_recent_events':     {'CZ': "Žádné nedávné eventy",      'EN': "No recent events found"},
    'h_resource_util':      {'CZ': "Využití prostředků",        'EN': "Resource Utilization"},
    'cpu_usage':            {'CZ': "Využití CPU",               'EN': "CPU Usage"},
    'mem_usage':            {'CZ': "Využití paměti",            'EN': "Memory Usage"},

    # ── Tab 4: AI Insights ─────────────────────────────────────────────────────
    'h_ai_insights':        {'CZ': "AI Insights",               'EN': "AI Insights"},
    'not_connected':        {'CZ': "Nejste připojeni ke clusteru.", 'EN': "Not connected to cluster."},
    'analysis_type':        {'CZ': "Typ analýzy",               'EN': "Analysis Type"},
    'btn_generate':         {'CZ': "🚀 Spustit AI analýzu",     'EN': "🚀 Generate AI Analysis"},
    'spinner_loading_data': {'CZ': "⏳ Načítám data z clusteru...", 'EN': "⏳ Loading cluster data..."},
    'model_starting':       {'CZ': "⚙️ Model **{m}** startuje… (CPU inference, první tokeny za ~15-30s)",
                             'EN': "⚙️ Model **{m}** starting… (CPU inference, first tokens in ~15-30s)"},
    'model_thinking':       {'CZ': "⚙️ Model přemýšlí… ({n} interních tokenů)",
                             'EN': "⚙️ Model thinking… ({n} internal tokens)"},
    'thinking_done':        {'CZ': "⚙️ Thinking hotovo, generuji odpověď…",
                             'EN': "⚙️ Thinking done, generating response…"},
    'model_generating':     {'CZ': "⚙️ Generuji odpověď…",     'EN': "⚙️ Generating response…"},
    'analysis_done':        {'CZ': "✅ Model: {m} | {n} slov",  'EN': "✅ Model: {m} | {n} words"},
    'analysis_error':       {'CZ': "Analýza selhala: {e}",      'EN': "AI analysis failed: {e}"},

    # ── Tab 5: AI Chat ─────────────────────────────────────────────────────────
    'h_ai_chat':            {'CZ': "🤖 AI Chat Asistent",       'EN': "🤖 AI Chat Assistant"},
    'spinner_ctx_loading':  {'CZ': "⏳ Načítám data z clusteru (jednorázově)...",
                             'EN': "⏳ Loading cluster data (once)..."},
    'grafana_offline':      {'CZ': "⚠️ Grafana offline",        'EN': "⚠️ Grafana offline"},
    'prometheus_ok_cluster':{'CZ': "✅ +Prometheus ({c})",      'EN': "✅ +Prometheus ({c})"},
    'prometheus_ok':        {'CZ': "✅ +Prometheus",             'EN': "✅ +Prometheus"},
    'ctx_status':           {'CZ': "📊 Data clusteru: {t} | {s}", 'EN': "📊 Cluster data: {t} | {s}"},
    'btn_refresh_ctx':      {'CZ': "Obnovit data z clusteru",   'EN': "Refresh cluster data"},
    'expander_examples':    {'CZ': "💡 Příklady dotazů",        'EN': "💡 Example prompts"},
    'chat_placeholder':     {'CZ': "Zeptejte se na cluster...", 'EN': "Ask about your cluster..."},
    'btn_send':             {'CZ': "Odeslat",                   'EN': "Send"},
    'btn_clear_chat':       {'CZ': "🗑️ Vymazat chat",           'EN': "🗑️ Clear Chat"},
    'chat_error':           {'CZ': "Omlouvám se, nastala chyba: {e}",
                             'EN': "Sorry, I encountered an error: {e}"},
    'ctx_unavailable':      {'CZ': "(data clusteru nedostupná)", 'EN': "(cluster data unavailable)"},
    'ctx_not_connected':    {'CZ': "(nepřipojeno ke clusteru)", 'EN': "(not connected to cluster)"},

    # ── Tab 6: K8sGPT ─────────────────────────────────────────────────────────
    'h_k8sgpt':             {'CZ': "🔍 K8sGPT AI Analýza",      'EN': "🔍 K8sGPT AI Analysis"},
    'k8sgpt_desc':          {'CZ': "**K8sGPT Operátor** průběžně analyzuje cluster a výsledky ukládá jako `Result` objekty v Kubernetes.\nTato stránka zobrazuje výsledky přímo z Kubernetes API — bez nutnosti CLI binárky.",
                             'EN': "**K8sGPT Operator** continuously analyzes the cluster and stores results as `Result` objects in Kubernetes.\nThis page displays results directly from the Kubernetes API — no CLI binary needed."},
    'filter_by_kind':       {'CZ': "Filtrovat dle Kind",         'EN': "Filter by Kind"},
    'btn_load_results':     {'CZ': "🔄 Načíst výsledky",        'EN': "🔄 Load results"},
    'spinner_k8sgpt':       {'CZ': "Načítám K8sGPT Results z Kubernetes API...",
                             'EN': "Loading K8sGPT Results from Kubernetes API..."},
    'k8sgpt_no_issues':     {'CZ': "✅ Žádné problémy nenalezeny (nebo K8sGPT CR ještě neprovedl analýzu)",
                             'EN': "✅ No issues found (or K8sGPT CR has not yet run analysis)"},
    'k8sgpt_hint':          {'CZ': "💡 Pokud vidíte tuto zprávu poprvé, K8sGPT CR možná ještě nebyl vytvořen. Proveďte `helm upgrade` pro aplikaci nové konfigurace.",
                             'EN': "💡 If you see this for the first time, the K8sGPT CR may not have been created yet. Run `helm upgrade` to apply the new configuration."},
    'k8sgpt_issues_found':  {'CZ': "🔍 Nalezeno **{n}** problémů", 'EN': "🔍 Found **{n}** issues"},
    'k8sgpt_ai_analysis':   {'CZ': "**AI analýza:**",            'EN': "**AI analysis:**"},
    'k8sgpt_errors':        {'CZ': "**Chyby:**",                 'EN': "**Errors:**"},
    'k8sgpt_cr_status':     {'CZ': "⚙️ Status K8sGPT CR (operátor)", 'EN': "⚙️ K8sGPT CR Status (operator)"},
    'btn_load_cr':          {'CZ': "🔄 Načíst status K8sGPT CR", 'EN': "🔄 Load K8sGPT CR status"},
    'k8sgpt_not_connected': {'CZ': "Nepřipojeno",               'EN': "Not connected"},
    'k8sgpt_403':           {'CZ': "❌ **403 Forbidden** — service account webui nemá přístup k `results.core.k8sgpt.ai`.\n\nSpusťte `helm upgrade` pro aplikaci nových RBAC pravidel.",
                             'EN': "❌ **403 Forbidden** — webui service account has no access to `results.core.k8sgpt.ai`.\n\nRun `helm upgrade` to apply new RBAC rules."},
    'k8sgpt_no_crd':        {'CZ': "❌ **CRD results.core.k8sgpt.ai nenalezeno** — k8sgpt operator není nainstalován v clusteru.",
                             'EN': "❌ **CRD results.core.k8sgpt.ai not found** — k8sgpt operator is not installed in the cluster."},
    'k8sgpt_api_err':       {'CZ': "❌ Kubernetes API chyba: {e}", 'EN': "❌ Kubernetes API error: {e}"},
    'k8sgpt_cr_none':       {'CZ': "⚠️ Žádný K8sGPT CR nenalezen — operátor neanalyzuje. Spusťte `helm upgrade`.",
                             'EN': "⚠️ No K8sGPT CR found — operator is not analyzing. Run `helm upgrade`."},
    'k8sgpt_cr_no_crd':     {'CZ': "⚠️ CRD `k8sgpts.core.k8sgpt.ai` nenalezeno — k8sgpt operator ještě nenainstaloval CRD, nebo restartuje. Zkuste za chvíli znovu.",
                             'EN': "⚠️ CRD `k8sgpts.core.k8sgpt.ai` not found — k8sgpt operator has not installed the CRD yet, or is restarting. Try again shortly."},
    'k8sgpt_cr_403':        {'CZ': "❌ **403 Forbidden** — service account nemá přístup k `k8sgpts.core.k8sgpt.ai`.",
                             'EN': "❌ **403 Forbidden** — service account has no access to `k8sgpts.core.k8sgpt.ai`."},
    'k8sgpt_cr_api_err':    {'CZ': "❌ Kubernetes API chyba ({s}): {r}", 'EN': "❌ Kubernetes API error ({s}): {r}"},
    'k8sgpt_cr_warn':       {'CZ': "Nelze načíst K8sGPT CR: {e}", 'EN': "Cannot load K8sGPT CR: {e}"},

    # ── Tab 7: Logs ────────────────────────────────────────────────────────────
    'h_logs':               {'CZ': "Logy podů",                 'EN': "Pod Logs"},
    'log_namespace':        {'CZ': "Namespace",                 'EN': "Namespace"},
    'log_pod':              {'CZ': "Pod",                       'EN': "Pod"},
    'log_container':        {'CZ': "Kontejner",                 'EN': "Container"},
    'log_container_help':   {'CZ': "Prázdné = první kontejner", 'EN': "Empty = first container"},
    'log_lines':            {'CZ': "Počet řádků",               'EN': "Lines"},
    'log_hours':            {'CZ': "Hodin zpět",                'EN': "Hours back"},
    'btn_reset_cache':      {'CZ': "🔄 Reset cache",            'EN': "🔄 Reset cache"},
    'btn_reset_cache_help': {'CZ': "Obnoví seznam namespaců a podů", 'EN': "Reload namespace and pod lists"},
    'btn_load_logs':        {'CZ': "🔍 Načíst logy",            'EN': "🔍 Load logs"},
    'spinner_logs':         {'CZ': "Načítám logy...",           'EN': "Loading logs..."},
    'spinner_namespaces':   {'CZ': "Načítám namespacy...",      'EN': "Loading namespaces..."},
    'spinner_pods':         {'CZ': "Načítám pody v {ns}...",    'EN': "Loading pods in {ns}..."},
    'loki_info':            {'CZ': "ℹ️ Loki nedostupný — logy se načtou přes Kubernetes API",
                             'EN': "ℹ️ Loki unavailable — logs will be loaded via Kubernetes API"},
    'loki_ok':              {'CZ': "📊 Loki: `{url}`{cinfo} — pokrývá {n} namespaců",
                             'EN': "📊 Loki: `{url}`{cinfo} — covers {n} namespaces"},
    'loki_diag':            {'CZ': "🔍 Loki diagnostika",       'EN': "🔍 Loki diagnostics"},
    'loki_show_labels':     {'CZ': "Zobrazit dostupné labely v Loki", 'EN': "Show available Loki labels"},
    'loki_show_ns':         {'CZ': "Zobrazit namespacy v Loki", 'EN': "Show namespaces in Loki"},
    'loki_labels_title':    {'CZ': "**Dostupné labely:**",       'EN': "**Available labels:**"},
    'loki_ns_title':        {'CZ': "**Namespacy pokryté Loki:**", 'EN': "**Namespaces covered by Loki:**"},
    'loki_show_pods':       {'CZ': "Zobrazit pody v namespace `{ns}` (Loki)",
                             'EN': "Show pods in namespace `{ns}` (Loki)"},
    'loki_ns_not_covered':  {'CZ': "ℹ️ Namespace `{ns}` není v Loki (Loki sbírá jen: {covered}...) — načítám přes K8s API",
                             'EN': "ℹ️ Namespace `{ns}` not in Loki (Loki covers: {covered}...) — loading via K8s API"},
    'loki_fallback_err':    {'CZ': "Loki query selhalo, fallback na K8s API: {e}",
                             'EN': "Loki query failed, falling back to K8s API: {e}"},
    'loki_empty_fallback':  {'CZ': "ℹ️ Loki nevrátil logy za posledních {h} h — zkouším K8s API…",
                             'EN': "ℹ️ Loki returned no logs for the last {h} h — trying K8s API…"},
    'log_no_logs':          {'CZ': "(žádné logy)",              'EN': "(no logs)"},
    'log_empty_info':       {'CZ': "ℹ️ Žádné logy nenalezeny — pod neloguje nebo byl restartován.",
                             'EN': "ℹ️ No logs found — pod is not logging or was restarted."},

    # ── Footer ─────────────────────────────────────────────────────────────────
    'footer':               {'CZ': "Vytvořeno pro L2 Support týmy | Lokální AI analýza Kubernetes",
                             'EN': "Built for L2 Support Teams | Local AI-powered Kubernetes Analysis"},

    # ── Tab 8: Egress / Network Test ───────────────────────────────────────────
    'h_egress':             {'CZ': "🔌 Egress / Network Test",  'EN': "🔌 Egress / Network Test"},
    'egress_desc':          {'CZ': "Zjistí egress VIP namespacu (CiliumEgressGatewayPolicy) a otestuje konektivitu k zadanému cíli přímo z podu.",
                             'EN': "Discovers the namespace egress VIP (CiliumEgressGatewayPolicy) and tests connectivity to a user-supplied target directly from a pod."},
    'egress_pod_ips_title': {'CZ': "🖥️ Pody v namespace ({n})", 'EN': "🖥️ Pods in namespace ({n})"},
    'egress_loading_policies': {'CZ': "Načítám CiliumEgressGatewayPolicy...", 'EN': "Loading CiliumEgressGatewayPolicy..."},
    'egress_policy_err':    {'CZ': "⚠️ Chyba při načítání Cilium policies: {e}",
                             'EN': "⚠️ Error loading Cilium policies: {e}"},
    'egress_policies_found': {'CZ': "✅ Nalezeno {n} CiliumEgressGatewayPolicy pro tento namespace",
                              'EN': "✅ Found {n} CiliumEgressGatewayPolicy for this namespace"},
    'egress_no_policies':   {'CZ': "ℹ️ Žádná CiliumEgressGatewayPolicy pro tento namespace (nebo Cilium CRD není nainstalováno).",
                             'EN': "ℹ️ No CiliumEgressGatewayPolicy found for this namespace (or Cilium CRD not installed)."},
    'egress_commands_title': {'CZ': "🛠️ Manuální ověřovací příkazy (skill)",
                              'EN': "🛠️ Manual verification commands (skill)"},
    'egress_test_title':    {'CZ': "🧪 Test konektivity",        'EN': "🧪 Connectivity Test"},
    'egress_target_label':  {'CZ': "Cíl (IP nebo hostname:port)", 'EN': "Target (IP or hostname:port)"},
    'egress_target_help':   {'CZ': "Např. 10.20.30.40:443 nebo db.corp:5432",
                             'EN': "E.g. 10.20.30.40:443 or db.corp:5432"},
    'egress_btn_test':      {'CZ': "▶ Testovat",                 'EN': "▶ Test"},
    'egress_err_target':    {'CZ': "⚠️ Zadejte cíl ve formátu host:port",
                             'EN': "⚠️ Enter target in host:port format"},
    'egress_err_no_pods':   {'CZ': "❌ Žádné Running pody v namespace {ns}",
                             'EN': "❌ No Running pods in namespace {ns}"},
    'egress_spinner':       {'CZ': "Testuji {host}:{port} z podu {pod}...",
                             'EN': "Testing {host}:{port} from pod {pod}..."},
    'egress_result_open':   {'CZ': "✅ **{host}:{port}** — port OTEVŘEN (komunikace povolena)",
                             'EN': "✅ **{host}:{port}** — port OPEN (communication allowed)"},
    'egress_result_closed': {'CZ': "❌ **{host}:{port}** — port UZAVŘEN / nedosažitelný",
                             'EN': "❌ **{host}:{port}** — port CLOSED / unreachable"},
    'egress_result_unknown': {'CZ': "⚠️ Výsledek neurčitý — zkontrolujte detail výstupu níže",
                              'EN': "⚠️ Result inconclusive — check the output detail below"},
    'egress_result_detail': {'CZ': "🔍 Výstup z podu {pod}",    'EN': "🔍 Output from pod {pod}"},
    'egress_result_from':   {'CZ': "Spuštěno v podu `{pod}` ({ns}) | Pod IP: `{ip}`",
                             'EN': "Executed in pod `{pod}` ({ns}) | Pod IP: `{ip}`"},
    'egress_vip_hint':      {'CZ': "ℹ️ Provoz z tohoto namespacu by měl odcházet se src IP: **{vips}** (egress VIP). Ověřte přes tcpdump nebo FW logy.",
                             'EN': "ℹ️ Traffic from this namespace should leave with src IP: **{vips}** (egress VIP). Verify via tcpdump or FW logs."},
    'egress_actual_ip_match':   {'CZ': "✅ Skutečná odchozí IP: **{ip}** — shoduje se s egress VIP",
                              'EN': "✅ Actual outbound IP: **{ip}** — matches egress VIP"},
    'egress_actual_ip_mismatch': {'CZ': "⚠️ Skutečná odchozí IP: **{ip}** — liší se od očekávané egress VIP ({vip})",
                                  'EN': "⚠️ Actual outbound IP: **{ip}** — differs from expected egress VIP ({vip})"},
    'egress_actual_ip_info':     {'CZ': "ℹ️ Skutečná odchozí IP: **{ip}**",
                                  'EN': "ℹ️ Actual outbound IP: **{ip}**"},
    'egress_actual_ip_unknown':  {'CZ': "ℹ️ Skutečnou odchozí IP se nepodařilo zjistit (echo služba nedostupná)",
                                  'EN': "ℹ️ Actual outbound IP could not be determined (echo service unreachable)"},
    'egress_fw_title':      {'CZ': "📋 Generovat FW ticket (XLS)",
                             'EN': "📋 Generate FW ticket (XLS)"},
    'egress_fw_desc':       {'CZ': "Port je uzavřen. Vygenerujte XLS šablonu pro security tým pro otevření firewallu.",
                             'EN': "Port is closed. Generate XLS template for the security team to open the firewall."},
    'egress_fw_justification': {'CZ': "Odůvodnění pravidla (Justification)",
                                'EN': "Rule justification"},
    'egress_fw_justification_help': {'CZ': "Popište proč je potřeba tato komunikace (např. 'Záloha dat do Azure Blob storage')",
                                     'EN': "Describe why this communication is needed (e.g. 'Backup data to Azure Blob storage')"},
    'egress_fw_btn':        {'CZ': "⬇️ Stáhnout XLS šablonu",  'EN': "⬇️ Download XLS template"},
    'egress_fw_warn_justification': {'CZ': "⚠️ Zadejte odůvodnění pravidla",
                                     'EN': "⚠️ Enter rule justification"},

    # ── Egress: XLS bulk test ──────────────────────────────────────────────────
    'egress_xls_title':     {'CZ': "📊 Batch test z FW šablony (XLS)",
                             'EN': "📊 Batch test from FW template (XLS)"},
    'egress_xls_upload_label': {'CZ': "Nahrát FW šablonu (.xlsx)",
                                'EN': "Upload FW template (.xlsx)"},
    'egress_xls_upload_help':  {'CZ': "Nahrajte XLS šablonu FW žádosti. Otestuje všechny cíle kde zdrojový VLAN = 54 (egress OT) nebo 59 (egress IT).",
                                'EN': "Upload FW request XLS template. Tests all targets where source VLAN = 54 (egress OT) or 59 (egress IT)."},
    'egress_xls_parse_err': {'CZ': "❌ Chyba při čtení XLS souboru: {e}",
                             'EN': "❌ Error reading XLS file: {e}"},
    'egress_xls_no_rows':   {'CZ': "⚠️ V souboru nebyla nalezena žádná pravidla se zdrojovým VLAN 54 (OT) nebo 59 (IT).",
                             'EN': "⚠️ No rules with source VLAN 54 (OT) or 59 (IT) found in the file."},
    'egress_xls_parsed':    {'CZ': "📋 Nalezeno **{total}** pravidel → **{unique}** unikátních cílů (OT/VLAN 54: {ot}, IT/VLAN 59: {it})",
                             'EN': "📋 Found **{total}** rules → **{unique}** unique targets (OT/VLAN 54: {ot}, IT/VLAN 59: {it})"},
    'egress_xls_targets_expander': {'CZ': "📋 Cíle k testování ({n})",
                                    'EN': "📋 Targets to test ({n})"},
    'egress_xls_run_btn':   {'CZ': "▶ Spustit batch test všech cílů",
                             'EN': "▶ Run batch test for all targets"},
    'egress_xls_spinner':   {'CZ': "Spouštím batch test ({n} cílů) v namespace {ns}...",
                             'EN': "Running batch test ({n} targets) in namespace {ns}..."},
    'egress_xls_open_count':  {'CZ': "✅ Otevřeno", 'EN': "✅ Open"},
    'egress_xls_closed_count': {'CZ': "❌ Uzavřeno", 'EN': "❌ Closed"},
    'egress_xls_unknown_count': {'CZ': "⚠️ Neznámé", 'EN': "⚠️ Unknown"},
    'egress_xls_open_table': {'CZ': "✅ Otevřené porty (provoz povolen):",
                              'EN': "✅ Open ports (traffic allowed):"},
    'egress_xls_closed_table': {'CZ': "❌ Uzavřené / nedosažitelné porty:",
                                'EN': "❌ Closed / unreachable ports:"},
    'egress_xls_raw_output': {'CZ': "🔍 Raw výstup z testovacího podu",
                              'EN': "🔍 Raw output from test pod"},
    'egress_xls_clear_btn': {'CZ': "🗑 Vymazat výsledky", 'EN': "🗑 Clear results"},

    # ── Login tabs ─────────────────────────────────────────────────────────────
    'login_tab_up':         {'CZ': "👤 Username / Password",    'EN': "👤 Username / Password"},
    'login_tab_ping':       {'CZ': "🔐 PingID Browser Login",   'EN': "🔐 PingID Browser Login"},
    'spinner_logging_in':   {'CZ': "🔐 Přihlašování...",        'EN': "🔐 Logging in..."},
    'mfa_required_warn':    {'CZ': "🔐 PingID MFA vyžadováno — zadejte OTP kód",
                             'EN': "🔐 PingID MFA required — enter OTP code"},

    # ── PingID Browser Login tab ───────────────────────────────────────────────
    'pingid_tab_info':      {'CZ': "**PingID Browser Login** — použijte pokud máte zapnuté MFA (push notifikace).\n\n"
                                   "1. Klikněte **Otevřít Rancher login** → přihlaste se normálně (username/password + PingID push na mobilu)\n"
                                   "2. Po přihlášení do Rancher UI: **☰ → Account & API Keys → API Keys → Create Key**\n"
                                   "3. Zkopírujte vygenerovaný Bearer token a vložte níže",
                             'EN': "**PingID Browser Login** — use this if MFA (push notification) is enabled.\n\n"
                                   "1. Click **Open Rancher Login** → sign in normally (username/password + PingID push on mobile)\n"
                                   "2. After logging in to Rancher UI: **☰ → Account & API Keys → API Keys → Create Key**\n"
                                   "3. Copy the generated Bearer token and paste it below"},
    'btn_open_rancher':     {'CZ': "🌐 Otevřít Rancher login (PingID)",
                             'EN': "🌐 Open Rancher Login (PingID)"},
    'pingid_opens':         {'CZ': "Otevře: `{url}`",           'EN': "Opens: `{url}`"},
    'pingid_no_url':        {'CZ': "Nejdřív vyberte Rancher URL výše",
                             'EN': "Please select a Rancher URL above first"},
    'pingid_after_login':   {'CZ': "**Po přihlášení:** Rancher UI → vpravo nahoře ☰ → *Account & API Keys* → *API Keys* → **Add Key** → zkopírujte *Bearer Token*",
                             'EN': "**After login:** Rancher UI → top right ☰ → *Account & API Keys* → *API Keys* → **Add Key** → copy the *Bearer Token*"},
    'bearer_token_label':   {'CZ': "Bearer Token",              'EN': "Bearer Token"},
    'bearer_token_help':    {'CZ': "Bearer token z Rancher API Keys (formát: token-xxxxx:yyy...)",
                             'EN': "Bearer token from Rancher API Keys (format: token-xxxxx:yyy...)"},
    'btn_login_token':      {'CZ': "✅ Přihlásit s tokenem",    'EN': "✅ Login with token"},
    'err_enter_token':      {'CZ': "Vložte Bearer token",       'EN': "Please enter a Bearer token"},
    'spinner_verify_token': {'CZ': "Ověřuji token...",          'EN': "Verifying token..."},

    # ── Push pending UI ────────────────────────────────────────────────────────
    'push_sent_ok':         {'CZ': "📱 **Push notifikace odeslána na váš telefon!**",
                             'EN': "📱 **Push notification sent to your phone!**"},
    'push_sent_info':       {'CZ': "Otevřete **PingID aplikaci** na telefonu a schvalte notifikaci.\n\nPoté klikněte **Schválil jsem**.",
                             'EN': "Open the **PingID app** on your phone and approve the notification.\n\nThen click **I approved it**."},
    'push_failed_err':      {'CZ': "❌ **Push notifikaci se nepodařilo odeslat.**\n\n"
                                   "Kubernetes pod nemůže dosáhnout `authenticator.pingone.eu` "
                                   "(síť/firewall blokuje odchozí připojení).\n\n"
                                   "**Řešení:** Použijte záložku **🔐 PingID Browser Login** — "
                                   "přihlaste se v prohlížeči a vložte Bearer token.",
                             'EN': "❌ **Push notification could not be sent.**\n\n"
                                   "The Kubernetes pod cannot reach `authenticator.pingone.eu` "
                                   "(network/firewall blocking outbound connections).\n\n"
                                   "**Solution:** Use the **🔐 PingID Browser Login** tab — "
                                   "log in via browser and paste the Bearer token."},
    'push_failed_caption':  {'CZ': "Chyba: {e}",                'EN': "Error: {e}"},
    'btn_push_approved':    {'CZ': "✅ Schválil jsem — dokončit přihlášení",
                             'EN': "✅ I approved it — complete login"},
    'spinner_verifying':    {'CZ': "Ověřuji...",                 'EN': "Verifying..."},
    'btn_push_retry':       {'CZ': "🔄 Push nepřišel — zkusit znovu",
                             'EN': "🔄 No push — try again"},
    'push_retry_info':      {'CZ': "Zadejte heslo znovu a klikněte Připojit — bude odeslán nový push.",
                             'EN': "Re-enter your password and click Connect — a new push will be sent."},
    'btn_cancel':           {'CZ': "✖ Zrušit",                  'EN': "✖ Cancel"},
    'push_debug_expander':  {'CZ': "🔍 Debug: obsah stránky PingFederate",
                             'EN': "🔍 Debug: PingFederate page content"},
    'push_debug_pending_url': {'CZ': "Pending URL: {url}",      'EN': "Pending URL: {url}"},
    'push_debug_js_urls':   {'CZ': "**JS URL endpoints nalezené na stránce:**",
                             'EN': "**JS URL endpoints found on page:**"},
    'push_debug_html':      {'CZ': "**Začátek HTML stránky:**",  'EN': "**Beginning of HTML page:**"},

    # ── MFA OTP UI ─────────────────────────────────────────────────────────────
    'mfa_warning':          {'CZ': "🔐 **PingID MFA** — zadejte OTP kód z aplikace PingID / autentifikátoru",
                             'EN': "🔐 **PingID MFA** — enter OTP code from PingID app / authenticator"},
    'otp_label':            {'CZ': "OTP kód",                   'EN': "OTP Code"},
    'otp_help':             {'CZ': "Kód z PingID mobilní aplikace, TOTP nebo SMS",
                             'EN': "Code from PingID mobile app, TOTP or SMS"},
    'btn_verify_otp':       {'CZ': "✅ Ověřit OTP",             'EN': "✅ Verify OTP"},
    'spinner_verify_otp':   {'CZ': "Ověřuji OTP...",            'EN': "Verifying OTP..."},
    'err_enter_otp':        {'CZ': "Zadejte OTP kód",           'EN': "Please enter OTP code"},
}


# ── Chat example prompts ────────────────────────────────────────────────────────
CHAT_EXAMPLES = {
    'CZ': [
        ("📊 Přehled clusteru",      "Kolik podů aktuálně běží v clusteru a které jsou problémové?"),
        ("🔴 CrashLoop / Pending",   "Které pody jsou ve stavu CrashLoopBackOff nebo Pending a proč?"),
        ("💾 Top pody RAM",          "Který pod aktuálně spotřebovává nejvíce paměti?"),
        ("⚡ Top pody CPU",           "Jaké jsou top 5 podů podle spotřeby CPU?"),
        ("🖥️ Vytíženost nodů",       "Jaká je vytíženost CPU a paměti na jednotlivých nodech?"),
        ("📦 Kapacita nodů",         "Kolik volné kapacity pro pody zbývá na každém nodu?"),
        ("📄 Eventy",                "Jsou v clusteru nějaké varovné eventy za poslední hodinu?"),
        ("🔔 Grafana alerty",        "Jsou aktivní nějaké Grafana alerty?"),
    ],
    'EN': [
        ("📊 Cluster overview",      "How many pods are running and which ones are problematic?"),
        ("🔴 CrashLoop / Pending",   "Which pods are in CrashLoopBackOff or Pending state and why?"),
        ("💾 Top pods RAM",          "Which pod is currently consuming the most memory?"),
        ("⚡ Top pods CPU",           "What are the top 5 pods by CPU usage?"),
        ("🖥️ Node utilization",      "What is the CPU and memory utilization on each node?"),
        ("📦 Node capacity",         "How much remaining pod capacity is available on each node?"),
        ("📄 Events",                "Are there any warning events in the cluster in the last hour?"),
        ("🔔 Grafana alerts",        "Are there any active Grafana alerts?"),
    ],
}


# ── AI Insights descriptions ────────────────────────────────────────────────────
INSIGHTS_DESCRIPTIONS = {
    'CZ': {
        "General Cluster Health": (
            "📋 **Co bude analyzováno:** stav nodů (Ready/NotReady) · počty podů podle stavu "
            "(Running, Pending, Failed) · varování z event logu za poslední 2h · doporučení pro L2/L3 support"
        ),
        "Problematic Pods Analysis": (
            "🔴 **Co bude analyzováno:** pody ve stavu Pending, Failed, CrashLoopBackOff · "
            "eventy spojené s problémy · root cause analýza · kubectl příkazy pro diagnostiku a opravu"
        ),
        "Resource Optimization": (
            "⚡ **Co bude analyzováno:** využití CPU a paměti · distribuce podů · "
            "over/under-provisioned deploymenty · doporučení pro škálování"
        ),
        "Security Check": (
            "🔒 **Co bude analyzováno:** bezpečnostní zranitelnosti · RBAC konfigurace · "
            "síťová bezpečnost · best practices pro zabezpečení clusteru"
        ),
    },
    'EN': {
        "General Cluster Health": (
            "📋 **What will be analyzed:** node status (Ready/NotReady) · pod counts by state "
            "(Running, Pending, Failed) · warning events in the last 2h · recommendations for L2/L3 support"
        ),
        "Problematic Pods Analysis": (
            "🔴 **What will be analyzed:** pods in Pending, Failed, CrashLoopBackOff · "
            "related events · root cause analysis · kubectl commands for diagnosis and remediation"
        ),
        "Resource Optimization": (
            "⚡ **What will be analyzed:** CPU and memory utilization · pod distribution · "
            "over/under-provisioned deployments · scaling recommendations"
        ),
        "Security Check": (
            "🔒 **What will be analyzed:** security vulnerabilities · RBAC configuration · "
            "network security · cluster security best practices"
        ),
    },
}


def get_t(lang: str):
    """Returns a translation helper t(key, **kwargs) bound to the given language."""
    def t(key: str, **kw):
        entry = TEXTS.get(key, {})
        s = entry.get(lang) or entry.get('CZ') or key
        return s.format(**kw) if kw else s
    return t
