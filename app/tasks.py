import subprocess
import time
import json
import os
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
    # FIX: Print the details so you can see the error in the terminal!
    details_str = json.dumps(details) if details else ""
    if details:
        print(f"[{store_id}] {event} - {details_str}")
    else:
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
        # Capture both stdout and stderr for debugging
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
        store.status = StoreStatus.PROVISIONING
        log_audit(db, store_id, "Provisioning Started")
        
        # 1. Determine Environment (Local vs Prod)
        env = os.getenv("URUMI_ENV", "local") 
        values_file = f"./charts/woocommerce/values-{env}.yaml"
        
        # FIX: Check if the file actually exists!
        if not os.path.exists(values_file):
            raise Exception(f"Values file not found at: {values_file}. Did you create charts/woocommerce/values-local.yaml?")

        log_audit(db, store_id, f"Using Environment: {env}")

        release_name = f"store-{store.name}"
        namespace = release_name
        
        # 2. Dynamic Host Logic
        if env == "local":
            host_url = f"{store.name}.127.0.0.1.nip.io"
        else:
            host_url = f"{store.name}.urumi.store" # Prod domain

        # 3. HELM INSTALL
        log_audit(db, store_id, "Running Helm", {"release": release_name})
        helm_cmd = [
            "helm", "upgrade", "--install", release_name, "./charts/woocommerce",
            "--create-namespace", "--namespace", namespace,
            "-f", values_file,
            "--set", f"ingress.host={host_url}",
            "--set", f"mariadb.auth.password={store.admin_password}",
            "--set", f"mariadb.auth.rootPassword={store.admin_password}",
            "--set", f"wordpress.db.password={store.admin_password}",
            "--atomic",
            "--wait",
            "--timeout", "5m"
        ]
        run_command(helm_cmd)

        # 4. WAIT FOR POD
        pod_name = wait_for_pod_ready(namespace, "app.kubernetes.io/name=woocommerce")

        # 5. CONFIGURE WORDPRESS (Using Sidecar)
        log_audit(db, store_id, "Configuring WordPress", {"pod": pod_name, "container": "wp-cli"})
        
        for attempt in range(5):
            try:
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
                
                run_command([
                    "kubectl", "exec", "-n", namespace, pod_name, "-c", "wp-cli", "--",
                    "wp", "plugin", "activate", "woocommerce"
                ], timeout=60)
                
                break
            except Exception as e:
                if attempt == 4: raise e
                print(f"WP-CLI retry {attempt}: {e}")
                time.sleep(5)

        # 6. SUCCESS
        store.status = StoreStatus.READY
        store.url = f"http://{host_url}"
        log_audit(db, store_id, "Provisioning Complete", {"url": store.url})
        db.commit()

    except Exception as e:
        store.status = StoreStatus.FAILED
        # The error will now print to your terminal!
        log_audit(db, store_id, "Provisioning Failed", {"error": str(e)})
        db.commit()
    finally:
        db.close()

def delete_store_task(store_id: str):
    db: Session = SessionLocal()
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store:
        return

    try:
        log_audit(db, store_id, "Deletion Started")
        
        original_name = store.name
        release_name = f"store-{original_name}"
        namespace = release_name

        # 1. HELM UNINSTALL
        log_audit(db, store_id, "Uninstalling Helm Chart")
        run_command(["helm", "uninstall", release_name, "-n", namespace, "--wait"], timeout=120)

        # 2. DELETE NAMESPACE
        log_audit(db, store_id, "Deleting Namespace")
        run_command(["kubectl", "delete", "ns", namespace], timeout=120)
        
        # 3. RENAME STORE
        new_name = f"{original_name}-deleted-{int(time.time())}"
        store.name = new_name
        store.status = StoreStatus.DELETED
        store.url = None 
        
        log_audit(db, store_id, "Deletion Complete", {"renamed_to": new_name})
        db.commit()

    except Exception as e:
        log_audit(db, store_id, "Deletion Failed", {"error": str(e)})
        store.status = StoreStatus.FAILED 
        db.commit()
    finally:
        db.close()