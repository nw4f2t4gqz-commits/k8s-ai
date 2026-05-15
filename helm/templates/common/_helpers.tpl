{{/*
Expand the name of the chart.
*/}}
{{- define "k8sgpt-ai-analyzer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "k8sgpt-ai-analyzer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "k8sgpt-ai-analyzer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "k8sgpt-ai-analyzer.labels" -}}
helm.sh/chart: {{ include "k8sgpt-ai-analyzer.chart" . }}
{{ include "k8sgpt-ai-analyzer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "k8sgpt-ai-analyzer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "k8sgpt-ai-analyzer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "k8sgpt-ai-analyzer.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "k8sgpt-ai-analyzer.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
App.py content
*/}}
{{- define "k8sgpt-ai-analyzer.app" -}}
import streamlit as st
from k8s_analyzer import K8sAnalyzer
import ollama
import time

st.set_page_config(page_title="K8s AI Analyzer", page_icon="🚀", layout="wide")

st.title("🚀 Kubernetes AI Cluster Analyzer")
st.markdown("AI-powered analysis tool for L2 support teams")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")

    # Multi-cluster support
    kubeconfigs = st.file_uploader("Upload kubeconfig files", type=["yaml", "yml"], accept_multiple_files=True)

    if kubeconfigs:
        st.success(f"Loaded {len(kubeconfigs)} kubeconfig(s)")

    # AI Model selection
    model_options = ["mistral:7b", "llama2:7b", "codellama:7b"]
    selected_model = st.selectbox("AI Model", model_options, index=0)

    # Check if Ollama is running
    try:
        ollama.list()
        st.success("Ollama is running")
    except:
        st.error("Ollama not running. Please start Ollama first.")

# Main content
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Cluster Overview", "Pod Analysis", "Events & Alerts", "AI Insights", "AI Chat", "K8sGPT Analysis"])

with tab1:
    st.header("Cluster Overview")

    if kubeconfigs:
        analyzer = K8sAnalyzer(kubeconfigs[0])  # For now, use first config

        # Test connection
        connected, message = analyzer.test_connection()
        if connected:
            st.success(message)
        else:
            st.error(message)
            st.stop()  # Stop execution if connection fails

        col1, col2, col3 = st.columns(3)

        with col1:
            nodes = analyzer.get_nodes()
            st.metric("Nodes", len(nodes))

        with col2:
            pods = analyzer.get_pods()
            st.metric("Total Pods", len(pods))

        with col3:
            namespaces = analyzer.get_namespaces()
            st.metric("Namespaces", len(namespaces))

        # Node status
        st.subheader("Node Status")
        node_data = []
        for node in nodes:
            node_data.append({
                'Name': node.metadata.name,
                'Status': node.status.conditions[-1].type if node.status.conditions else 'Unknown',
                'CPU': node.status.capacity.get('cpu', 'N/A'),
                'Memory': node.status.capacity.get('memory', 'N/A')
            })
        st.table(node_data)

    else:
        st.info("Please upload kubeconfig files to get started")

with tab2:
    st.header("Pod Analysis")

    if kubeconfigs:
        analyzer = K8sAnalyzer(kubeconfigs[0])

        # Pod status overview
        pods = analyzer.get_pods()
        status_counts = {}
        for pod in pods:
            status = pod.status.phase
            status_counts[status] = status_counts.get(status, 0) + 1

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Running", status_counts.get('Running', 0))
        with col2:
            st.metric("Pending", status_counts.get('Pending', 0))
        with col3:
            st.metric("Failed", status_counts.get('Failed', 0))
        with col4:
            st.metric("Succeeded", status_counts.get('Succeeded', 0))

        # Problematic pods
        problematic_pods = [pod for pod in pods if pod.status.phase in ['Pending', 'Failed', 'CrashLoopBackOff']]
        if problematic_pods:
            st.subheader("Problematic Pods")
            prob_data = []
            for pod in problematic_pods:
                restarts = 0
                if pod.status.container_statuses:
                    restarts = pod.status.container_statuses[0].restart_count
                prob_data.append({
                    'Name': pod.metadata.name,
                    'Namespace': pod.metadata.namespace,
                    'Status': pod.status.phase,
                    'Restarts': restarts
                })
            st.table(prob_data)

with tab3:
    st.header("Events & Alerts")

    if kubeconfigs:
        analyzer = K8sAnalyzer(kubeconfigs[0])

        # Recent events
        st.subheader("Recent Events (Last Hour)")
        events = analyzer.get_recent_events(hours=1)

        if events:
            event_data = []
            for event in events[:20]:  # Show last 20 events
                event_data.append({
                    'Time': event['time'].strftime('%H:%M:%S') if hasattr(event['time'], 'strftime') else str(event['time']),
                    'Type': event['type'],
                    'Reason': event['reason'],
                    'Message': event['message'][:100] + '...' if len(event['message']) > 100 else event['message'],
                    'Source': event['source'],
                    'Object': event['object']
                })
            st.table(event_data)
        else:
            st.info("No recent events found")

        # Resource utilization
        st.subheader("Resource Utilization")
        nodes = analyzer.get_nodes()
        pods = analyzer.get_pods()

        total_cpu = 0
        total_memory = 0
        used_cpu = 0
        used_memory = 0

        for node in nodes:
            if node.status.capacity:
                cpu = node.status.capacity.get('cpu', '0')
                memory = node.status.capacity.get('memory', '0')

                # Parse CPU (can be in cores or millicores)
                if cpu.endswith('m'):
                    total_cpu += float(cpu[:-1]) / 1000
                else:
                    total_cpu += float(cpu) if cpu.isdigit() else 0

                # Parse memory (convert to Mi)
                if memory.endswith('Ki'):
                    total_memory += float(memory[:-2]) / 1024
                elif memory.endswith('Mi'):
                    total_memory += float(memory[:-2])
                elif memory.endswith('Gi'):
                    total_memory += float(memory[:-2]) * 1024

        # Calculate used resources from pods
        for pod in pods:
            if pod.spec.containers and pod.status.phase == 'Running':
                for container in pod.spec.containers:
                    if container.resources.requests:
                        cpu_req = container.resources.requests.get('cpu', '0')
                        mem_req = container.resources.requests.get('memory', '0')

                        if cpu_req.endswith('m'):
                            used_cpu += float(cpu_req[:-1]) / 1000
                        else:
                            used_cpu += float(cpu_req) if cpu_req.isdigit() else 0

                        if mem_req.endswith('Mi'):
                            used_memory += float(mem_req[:-2])
                        elif mem_req.endswith('Gi'):
                            used_memory += float(mem_req[:-2]) * 1024

        col1, col2 = st.columns(2)
        with col1:
            cpu_usage = (used_cpu / total_cpu * 100) if total_cpu > 0 else 0
            st.metric("CPU Usage", f"{cpu_usage:.1f}%", f"{used_cpu:.2f}/{total_cpu:.2f} cores")
            st.progress(min(cpu_usage / 100, 1.0))

        with col2:
            mem_usage = (used_memory / total_memory * 100) if total_memory > 0 else 0
            st.metric("Memory Usage", f"{mem_usage:.1f}%", f"{used_memory:.0f}/{total_memory:.0f} Mi")
            st.progress(min(mem_usage / 100, 1.0))

with tab4:
    st.header("AI Insights")

    if kubeconfigs:
        analyzer = K8sAnalyzer(kubeconfigs[0])

        # Quick analysis options
        analysis_type = st.selectbox(
            "Analysis Type",
            ["General Cluster Health", "Problematic Pods Analysis", "Resource Optimization", "Security Check"]
        )

        if st.button("Generate AI Analysis"):
            with st.spinner("Analyzing cluster with AI..."):
                cluster_info = analyzer.get_cluster_summary()
                events = analyzer.get_recent_events(hours=2)
                problematic_pods = [pod for pod in analyzer.get_pods() if pod.status.phase in ['Pending', 'Failed', 'CrashLoopBackOff']]

                # Create specific prompts based on analysis type
                if analysis_type == "General Cluster Health":
                    prompt = f"""
                    Analyze this Kubernetes cluster health for L2 support:

                    Cluster Summary:
                    - Nodes: {cluster_info['nodes']}
                    - Total Pods: {cluster_info['pods']}
                    - Namespaces: {cluster_info['namespaces']}
                    - Problematic Pods: {cluster_info['problematic_pods']}

                    Recent Events: {len(events)} events in last 2 hours

                    Please provide:
                    1. Overall cluster health assessment
                    2. Critical issues requiring immediate attention
                    3. Recommendations for L2 support team
                    """

                elif analysis_type == "Problematic Pods Analysis":
                    prompt = f"""
                    Analyze problematic pods in this Kubernetes cluster:

                    Problematic Pods: {len(problematic_pods)}
                    {chr(10).join([f"- {pod.metadata.name} in {pod.metadata.namespace}: {pod.status.phase}" for pod in problematic_pods[:5]])}

                    Recent Events: {len([e for e in events if 'pod' in e['object'].lower()])}

                    Please provide:
                    1. Root cause analysis for each problematic pod
                    2. Step-by-step troubleshooting guide
                    3. Commands to run for diagnosis
                    4. Potential solutions and fixes
                    """

                elif analysis_type == "Resource Optimization":
                    prompt = f"""
                    Analyze resource utilization in this Kubernetes cluster:

                    Cluster Resources:
                    - Nodes: {cluster_info['nodes']}
                    - Total Pods: {cluster_info['pods']}
                    - Pod Status Distribution: {cluster_info['pod_status_distribution']}

                    Please provide:
                    1. Resource utilization assessment
                    2. Over/under-provisioned resources
                    3. Optimization recommendations
                    4. Scaling suggestions
                    """

                else:  # Security Check
                    prompt = f"""
                    Perform security analysis of this Kubernetes cluster:

                    Cluster Info:
                    - Namespaces: {cluster_info['namespaces']}
                    - Total Pods: {cluster_info['pods']}
                    - Recent Events: {len(events)}

                    Please provide:
                    1. Security vulnerabilities assessment
                    2. RBAC and permissions analysis
                    3. Network security recommendations
                    4. Best practices compliance check
                    """

                try:
                    response = ollama.generate(model=selected_model, prompt=prompt)
                    st.markdown(response['response'])
                except Exception as e:
                    st.error(f"AI analysis failed: {str(e)}")

with tab5:
    st.header("🤖 AI Chat Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat interface
    st.markdown("Ask me anything about your Kubernetes cluster! I have access to real-time cluster data.")

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    col1, col2 = st.columns([4, 1])
    with col1:
        prompt = st.text_input("Ask about your cluster...", key="chat_input", label_visibility="collapsed")
    with col2:
        send_button = st.button("Send", use_container_width=True)

    if send_button and prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Generate AI response
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Get cluster context if kubeconfig is available
                        cluster_context = ""
                        if kubeconfigs:
                            analyzer = K8sAnalyzer(kubeconfigs[0])
                            cluster_info = analyzer.get_cluster_summary()
                            events = analyzer.get_recent_events(hours=1)
                            problematic_pods = [pod for pod in analyzer.get_pods() if pod.status.phase in ['Pending', 'Failed', 'CrashLoopBackOff']]

                            cluster_context = f"""
                            Current Cluster Status:
                            - Nodes: {cluster_info['nodes']}
                            - Total Pods: {cluster_info['pods']}
                            - Namespaces: {cluster_info['namespaces']}
                            - Problematic Pods: {cluster_info['problematic_pods']}
                            - Recent Events: {len(events)} in last hour

                            Problematic Pods:
                            {chr(10).join([f"- {pod.metadata.name} in {pod.metadata.namespace}: {pod.status.phase}" for pod in problematic_pods[:3]])}
                            """

                        # Create enhanced prompt with cluster context
                        full_prompt = f"""
                        You are an expert Kubernetes support assistant helping L2/L3 engineers troubleshoot cluster issues.

                        {cluster_context}

                        User Question: {prompt}

                        Please provide helpful, actionable advice. Include specific kubectl commands when relevant.
                        Focus on practical solutions and best practices.
                        """

                        response = ollama.generate(model=selected_model, prompt=full_prompt)
                        ai_response = response['response']

                        st.markdown(ai_response)

                        # Add AI response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})

                    except Exception as e:
                        error_msg = f"Sorry, I encountered an error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

        # Clear input
        st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

with tab6:
    st.header("🔍 K8sGPT AI Analysis")

    st.markdown("""
    **K8sGPT** je specializovaný AI nástroj pro Kubernetes troubleshooting.
    Poskytuje detailní analýzu problémů s praktickými řešeními.
    """)

    if kubeconfigs:
        analyzer = K8sAnalyzer(kubeconfigs[0])

        # K8sGPT analysis options
        col1, col2 = st.columns([1, 1])

        with col1:
            analyze_with_explain = st.checkbox("Include AI explanations", value=True)
            analyze_namespace = st.selectbox(
                "Namespace (optional)",
                ["all"] + [ns.metadata.name for ns in analyzer.get_namespaces()],
                index=0
            )

        with col2:
            analyze_filters = st.multiselect(
                "Filter analyzers",
                ["Pod", "Service", "ConfigMap", "Secret", "PersistentVolume", "Deployment", "StatefulSet", "DaemonSet"],
                default=[]
            )

        if st.button("🚀 Run K8sGPT Analysis", type="primary"):
            with st.spinner("Running K8sGPT analysis... This may take a few minutes"):
                try:
                    # Prepare command
                    cmd = ["k8sgpt", "analyze"]

                    if analyze_with_explain:
                        cmd.append("--explain")

                    if analyze_namespace != "all":
                        cmd.extend(["--namespace", analyze_namespace])

                    if analyze_filters:
                        cmd.extend(["--filter", ",".join(analyze_filters)])

                    # Use the uploaded kubeconfig
                    kubeconfig_path = None
                    if kubeconfigs:
                        # Save uploaded kubeconfig temporarily
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                            content = kubeconfigs[0].getvalue().decode('utf-8')
                            f.write(content)
                            kubeconfig_path = f.name

                        cmd.extend(["--kubeconfig", kubeconfig_path])

                    # Run K8sGPT
                    import subprocess
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                    # Clean up temp file
                    if kubeconfig_path and os.path.exists(kubeconfig_path):
                        os.unlink(kubeconfig_path)

                    if result.returncode == 0:
                        st.success("K8sGPT analysis completed!")

                        # Display results
                        st.code(result.stdout, language="bash")

                        # Parse and display issues count
                        lines = result.stdout.strip().split('\n')
                        issue_count = 0
                        for line in lines:
                            if line.strip().startswith(tuple(str(i) + ':' for i in range(10))):
                                issue_count += 1

                        if issue_count > 0:
                            st.warning(f"🔍 Found {issue_count} potential issues")
                        else:
                            st.success("✅ No issues found!")

                    else:
                        st.error(f"K8sGPT analysis failed: {result.stderr}")

                except subprocess.TimeoutExpired:
                    st.error("K8sGPT analysis timed out. Try with fewer filters or smaller namespace.")
                except Exception as e:
                    st.error(f"Error running K8sGPT: {str(e)}")

        # Info about K8sGPT
        with st.expander("ℹ️ About K8sGPT"):
            st.markdown("""
            **K8sGPT** analyzuje váš Kubernetes cluster a identifikuje:

            - **ConfigMap/Secret issues**: Nepoužívané nebo špatně nakonfigurované objekty
            - **Pod problems**: CrashLoopBackOff, Pending stavy, resource issues
            - **Service issues**: Nesprávné konfigurace služeb
            - **Security concerns**: RBAC problémy, nebezpečné konfigurace
            - **Resource optimization**: Nadměrné nebo nedostatečné alokace

            **Výhody oproti základní AI analýze:**
            - Specializované Kubernetes znalosti
            - Automatická detekce konkrétních problémů
            - Připravené řešení s kubectl příkazy
            - Rychlejší troubleshooting
            """)

# Footer
st.markdown("---")
st.markdown("Built for L2 Support Teams | Local AI-powered Kubernetes Analysis")
{{- end }}

{{/*
K8s analyzer content
*/}}
{{- define "k8sgpt-ai-analyzer.analyzer" -}}
import os
import tempfile
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

class K8sAnalyzer:
    def __init__(self, kubeconfig_file=None):
        self.kubeconfig_file = kubeconfig_file
        self.v1 = None
        self.v1_core = None
        self._load_config()

    def _load_config(self):
        """Load Kubernetes configuration from uploaded file or default"""
        try:
            if self.kubeconfig_file:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    content = self.kubeconfig_file.getvalue().decode('utf-8')
                    f.write(content)
                    temp_path = f.name

                config.load_kube_config(temp_path)
                os.unlink(temp_path)  # Clean up temp file
            else:
                config.load_kube_config()

            self.v1 = client.CoreV1Api()
            self.v1_apps = client.AppsV1Api()
            self.v1_batch = client.BatchV1Api()

        except Exception as e:
            raise Exception(f"Failed to load Kubernetes config: {str(e)}")

    def get_nodes(self):
        """Get all nodes in the cluster"""
        try:
            if not self.v1:
                return []
            return self.v1.list_node().items
        except Exception as e:
            print(f"Error getting nodes: {e}")
            return []

    def get_pods(self, namespace=None):
        """Get all pods, optionally filtered by namespace"""
        try:
            if not self.v1:
                return []
            if namespace:
                return self.v1.list_namespaced_pod(namespace).items
            else:
                return self.v1.list_pod_for_all_namespaces().items
        except Exception as e:
            print(f"Error getting pods: {e}")
            return []

    def get_namespaces(self):
        """Get all namespaces"""
        try:
            if not self.v1:
                return []
            return self.v1.list_namespace().items
        except Exception as e:
            print(f"Error getting namespaces: {e}")
            return []

    def test_connection(self):
        """Test connection to the cluster"""
        try:
            if not self.v1:
                return False, "Kubernetes client not initialized"
            # Try to get cluster version as a simple connectivity test
            self.v1.api_client.call_api('/version', 'GET')
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_services(self, namespace=None):
        """Get all services"""
        try:
            if namespace:
                return self.v1.list_namespaced_service(namespace).items
            else:
                return self.v1.list_service_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting services: {e}")
            return []

    def get_deployments(self, namespace=None):
        """Get all deployments"""
        try:
            if namespace:
                return self.v1_apps.list_namespaced_deployment(namespace).items
            else:
                return self.v1_apps.list_deployment_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting deployments: {e}")
            return []

    def get_events(self, namespace=None):
        """Get recent events"""
        try:
            if namespace:
                return self.v1.list_namespaced_event(namespace).items
            else:
                return self.v1.list_event_for_all_namespaces().items
        except ApiException as e:
            print(f"Error getting events: {e}")
            return []

    def get_pod_logs(self, pod_name, namespace, container=None, tail_lines=100):
        """Get logs from a specific pod"""
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return logs
        except ApiException as e:
            return f"Error getting logs: {e}"

    def get_cluster_summary(self):
        """Get basic cluster summary for AI analysis"""
        nodes = self.get_nodes()
        pods = self.get_pods()
        namespaces = self.get_namespaces()

        problematic_pods = [
            pod for pod in pods
            if pod.status.phase in ['Pending', 'Failed', 'CrashLoopBackOff']
        ]

        return {
            'nodes': len(nodes),
            'pods': len(pods),
            'namespaces': len(namespaces),
            'problematic_pods': len(problematic_pods),
            'node_status': [node.status.conditions[-1].type for node in nodes if node.status.conditions],
            'pod_status_distribution': {
                status: len([p for p in pods if p.status.phase == status])
                for status in set(p.status.phase for p in pods)
            }
        }

    def analyze_pod_health(self, pod):
        """Analyze individual pod health"""
        analysis = {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'status': pod.status.phase,
            'issues': []
        }

        # Check for restarts
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.restart_count > 0:
                    analysis['issues'].append(f"Container {container.name} restarted {container.restart_count} times")

        # Check status
        if pod.status.phase == 'Pending':
            analysis['issues'].append("Pod is in Pending state")
        elif pod.status.phase == 'Failed':
            analysis['issues'].append("Pod has Failed")
        elif pod.status.phase == 'CrashLoopBackOff':
            analysis['issues'].append("Pod is in CrashLoopBackOff")

        return analysis

    def get_recent_events(self, hours=1):
        """Get events from the last N hours"""
        import datetime
        now = datetime.datetime.utcnow()
        cutoff = now - datetime.timedelta(hours=hours)

        events = self.get_events()
        recent_events = []

        for event in events:
            if event.last_timestamp:
                event_time = event.last_timestamp.replace(tzinfo=None)
                if event_time > cutoff:
                    recent_events.append({
                        'time': event.last_timestamp,
                        'type': event.type,
                        'reason': event.reason,
                        'message': event.message,
                        'source': event.source.component if event.source else 'Unknown',
                        'namespace': event.metadata.namespace,
                        'object': f"{event.involved_object.kind}/{event.involved_object.name}"
                    })

        return sorted(recent_events, key=lambda x: x['time'], reverse=True)
{{- end }}
