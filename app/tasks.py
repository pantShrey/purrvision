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

# We keep v1 for deleting namespaces, but we don't need it for pod waiting anymore
v1 = client.CoreV1Api()

def log_audit(db: Session, store_id: str, event: str, details: dict = None):
    details_str = json.dumps(details) if details else ""
    # Print to console for immediate debugging
    if details:
        print(f"[{store_id}] {event} - {details_str}")
    else:
        print(f"[{store_id}] {event}")
        
    log = AuditLog(store_id=store_id, event=event, details=details_str)
    db.add(log)
    db.commit()

def run_command(cmd_list, timeout=300):
    """
    Runs a shell command and returns the output.
    Raises Exception with stderr if it fails.
    """
    try:
        result = subprocess.run(
            cmd_list, 
            capture_output=True, 
            text=True, 
            timeout=timeout, 
            check=True
        )
        # Return stdout so we can log it
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise Exception(f"Command timed out after {timeout}s")
    except subprocess.CalledProcessError as e:
        # Capture the actual error message from stderr
        error_msg = e.stderr.strip() or e.stdout.strip()
        raise Exception(f"Command failed: {error_msg}")

def provision_store_task(store_id: str):
    db: Session = SessionLocal()
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store: return

    try:
        store.status = StoreStatus.PROVISIONING
        log_audit(db, store_id, "Provisioning Started")
        
        env = os.getenv("URUMI_ENV", "local") 
        values_file = f"./charts/woocommerce/values-{env}.yaml"
        if not os.path.exists(values_file):
            raise Exception(f"Values file missing: {values_file}")
            
        log_audit(db, store_id, f"Using Environment: {env}")
        release_name = f"store-{store.name}"
        namespace = release_name
        
        if env == "local":
            host_url = f"{store.name}.127.0.0.1.nip.io"
            protocol = "http"
        else:
            host_url = f"{store.name}.urumi.store"
            protocol = "https"

        # HELM UPGRADE
        # Note: We rely on --wait to ensure pods are ready before this command finishes
        helm_cmd = [
            "helm", "upgrade", "--install", release_name, "./charts/woocommerce",
            "--create-namespace", "--namespace", namespace,
            "-f", values_file,
            
            # Network & Ingress
            "--set", f"ingress.host={host_url}",
            "--set", f"ingress.protocol={protocol}",

            # Credentials (Injected safely)
            "--set", f"mariadb.auth.password={store.admin_password}",
            "--set", f"mariadb.auth.rootPassword={store.admin_password}",
            "--set", f"wordpress.db.password={store.admin_password}",
            
            # Sidecar Configuration
            "--set", f"wordpress.title={store.name}",
            "--set", f"wordpress.admin.user={store.admin_user}",
            "--set", f"wordpress.admin.password={store.admin_password}",
            "--set", "wordpress.admin.email=admin@example.com",
            
            "--atomic", "--wait", "--timeout", "8m"
        ]
        
        # LOGGING IMPROVEMENT: Capture and log the Helm output
        log_audit(db, store_id, "Running Helm", {"release": release_name})
        helm_output = run_command(helm_cmd)
        
        # If we get here, Helm finished successfully implies Pods are Ready.
        store.status = StoreStatus.READY
        store.url = f"{protocol}://{host_url}"
        
        # Save the Helm output to the audit log (Great for debugging/demos)
        log_audit(db, store_id, "Provisioning Complete", {
            "url": store.url, 
            "helm_output": helm_output[:500] + "..." if len(helm_output) > 500 else helm_output
        })
        db.commit()

    except Exception as e:
        store.status = StoreStatus.FAILED
        log_audit(db, store_id, "Provisioning Failed", {"error": str(e)})
        db.commit()
    finally:
        db.close()

def delete_store_task(store_id: str):
    db: Session = SessionLocal()
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store: return

    try:
        log_audit(db, store_id, "Deletion Started")
        
        original_name = store.name 
        release_name = f"store-{original_name}"
        namespace = release_name

        # Capture uninstall logs too
        log_audit(db, store_id, "Uninstalling Helm Chart")
        helm_out = run_command(["helm", "uninstall", release_name, "-n", namespace, "--wait"], timeout=120)

        log_audit(db, store_id, "Deleting Namespace")
        run_command(["kubectl", "delete", "ns", namespace], timeout=120)
        
        new_name = f"{original_name}-deleted-{int(time.time())}"
        store.name = new_name
        store.status = StoreStatus.DELETED
        store.url = None 
        
        log_audit(db, store_id, "Deletion Complete", {
            "renamed_to": new_name,
            "helm_cleanup": helm_out
        })
        db.commit()

    except Exception as e:
        log_audit(db, store_id, "Deletion Failed", {"error": str(e)})
        store.status = StoreStatus.FAILED 
        db.commit()
    finally:
        db.close()