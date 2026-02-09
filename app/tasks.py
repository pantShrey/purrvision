import subprocess
import time
import json
from sqlalchemy.orm import Session
from kubernetes import client, config
from .database import SessionLocal, Store, AuditLog, StoreStatus

# Load Kube Config
try:
    config.load_kube_config()
except:
    config.load_incluster_config()

v1 = client.CoreV1Api()

def log_audit(db: Session, store_id: str, event: str, details: dict = None):
    details_str = json.dumps(details) if details else ""
    print(f"[{store_id}] {event}")
    log = AuditLog(store_id=store_id, event=event, details=details_str)
    db.add(log)
    db.commit()

def run_command(cmd_list, timeout=300):
    try:
        result = subprocess.run(
            cmd_list, 
            capture_output=True, 
            text=True, 
            timeout=timeout, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise Exception(f"Command timed out after {timeout}s: {' '.join(cmd_list)}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip()
        raise Exception(f"Command failed: {error_msg}")

def wait_for_pod_ready(namespace, label_selector, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)
        if len(pods.items) > 0:
            pod = pods.items[0]
            # Wait for Running phase AND all containers (WP + Sidecar) to be ready
            if pod.status.phase == "Running" and all(c.ready for c in pod.status.container_statuses):
                return pod.metadata.name
        time.sleep(5)
    raise Exception("Timeout waiting for Pod to be ready")

def provision_store_task(store_id: str):
    db: Session = SessionLocal()
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store:
        return

    try:
        # 1. Update Status
        store.status = StoreStatus.PROVISIONING
        log_audit(db, store_id, "Provisioning Started")
        
        release_name = f"store-{store.name}"
        namespace = release_name
        host_url = f"{store.name}.local"

        # 2. HELM INSTALL
        log_audit(db, store_id, "Running Helm", {"release": release_name})
        helm_cmd = [
            "helm", "upgrade", "--install", release_name, "./charts/woocommerce",
            "--create-namespace", "--namespace", namespace,
            "--set", f"ingress.host={host_url}",
            "--set", "mariadb.primary.persistence.enabled=false",
            "--atomic",
            "--wait",
            "--timeout", "5m"
        ]
        run_command(helm_cmd)

        # 3. WAIT FOR POD
        pod_name = wait_for_pod_ready(namespace, "app.kubernetes.io/name=woocommerce")

        # 4. CONFIGURE WORDPRESS (Using Sidecar)
        log_audit(db, store_id, "Configuring WordPress", {"pod": pod_name, "container": "wp-cli"})
        
        # Retry loop for WP-CLI (Database might be warming up)
        for attempt in range(5):
            try:
                # Install Core
                # Note: We target '-c wp-cli' explicitly!
                run_command([
                    "kubectl", "exec", "-n", namespace, pod_name, "-c", "wp-cli", "--",
                    "wp", "core", "install",
                    "--url=http://" + host_url,
                    "--title=" + store.name,
                    "--admin_user=" + store.admin_user,
                    "--admin_password=" + store.admin_password,
                    "--admin_email=admin@example.com",
                    "--skip-email"
                ], timeout=60)
                
                # Activate WooCommerce
                run_command([
                    "kubectl", "exec", "-n", namespace, pod_name, "-c", "wp-cli", "--",
                    "wp", "plugin", "activate", "woocommerce"
                ], timeout=60)
                
                # OPTIONAL: Set Rewrite Structure (Good for permalinks)
                run_command([
                    "kubectl", "exec", "-n", namespace, pod_name, "-c", "wp-cli", "--",
                    "wp", "rewrite", "structure", "/%postname%/"
                ], timeout=60)
                
                break # Success!
            except Exception as e:
                if attempt == 4: raise e
                print(f"WP-CLI retry {attempt}: {e}")
                time.sleep(5)

        # 5. SUCCESS
        store.status = StoreStatus.READY
        store.url = f"http://{host_url}"
        log_audit(db, store_id, "Provisioning Complete", {"url": store.url})
        db.commit()

    except Exception as e:
        store.status = StoreStatus.FAILED
        log_audit(db, store_id, "Provisioning Failed", {"error": str(e)})
        db.commit()
    finally:
        db.close()