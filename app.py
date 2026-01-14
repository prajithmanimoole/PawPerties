"""
Main Flask Application
Property Registration Blockchain System
"""

from dotenv import load_dotenv

# Load environment variables from .env file FIRST (before importing blockchain)
load_dotenv()

import atexit
import copy
import glob
import os
import shutil
import signal
import sys
import warnings
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from google import genai

from auth import (
    AuthService,
    admin_required,
    login_required,
    officer_or_admin_required,
    user_required,
)
from blockchain import PropertyBlockchain
from chatbot_service import ChatbotService
from cid_manager import cid_manager
from config import Config
from models import (
    Appointment,
    BlockchainBackup,
    Message,
    Property,
    User,
    db,
    init_db,
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db(app)

# Initialize blockchain (singleton instance with auto-save after operations and auto-restore)
blockchain = PropertyBlockchain(verbose=False, auto_restore=True)
print(f"✓ Blockchain initialized with {len(blockchain.chain)} blocks")

# Restore from database if blockchain only has genesis block
with app.app_context():
    if len(blockchain.chain) == 1:  # Only genesis block
        try:
            latest_backup = BlockchainBackup.query.order_by(
                BlockchainBackup.created_at.desc()
            ).first()
            if latest_backup:
                blockchain.load_from_encrypted_data(latest_backup.backup_data)
                print(f"✓ Blockchain restored from database: {latest_backup.name}")
                print(f"✓ Restored {len(blockchain.chain)} blocks from backup")
            else:
                print("ℹ No database backup found - starting fresh")
        except Exception as e:
            print(f"⚠ Could not restore from database: {str(e)}")

# Initialize Gemini AI
gemini_client = None
try:
    if (
        app.config["GEMINI_API_KEY"]
        and app.config["GEMINI_API_KEY"] != "YOUR_API_KEY_HERE"
    ):
        gemini_client = genai.Client(api_key=app.config["GEMINI_API_KEY"])
        print("✓ Gemini AI connected")
    else:
        gemini_client = None
        print("⚠ Using offline chatbot mode (no API key)")
except Exception as e:
    gemini_client = None
    print("⚠ Using offline chatbot mode")

# Initialize Chatbot Service
chatbot_service = ChatbotService(blockchain, gemini_client)


# ============================================================================
# AUTO BACKUP ON SHUTDOWN
# ============================================================================


def auto_backup_on_shutdown():
    """Automatically backup blockchain to database and IPFS when server shuts down"""
    # Suppress socket errors during Flask shutdown on Windows
    original_stderr = sys.stderr
    try:
        # Redirect stderr temporarily to suppress threading errors
        import io

        sys.stderr = io.StringIO()

        # Restore stderr for our messages
        sys.stderr = original_stderr

        print("\n🔄 Auto-backing up blockchain...")

        # Use app context for database operations
        with app.app_context():
            # Get encrypted blockchain data
            encrypted_data = blockchain.get_encrypted_data()

            # Create auto-backup record
            timestamp = datetime.now()
            display_name = f"Auto-backup - {timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
            filename = f"auto_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.encrypted"

            backup = BlockchainBackup(
                name=display_name,
                filename=filename,
                backup_data=encrypted_data,
                created_by=1,  # System user (admin)
            )

            db.session.add(backup)
            db.session.commit()
            print(f"✅ Database backup completed: {display_name}")

            # Clean up old backups (keep only last 10)
            cleanup_old_backups()

            # Save to file for IPFS backup
            os.makedirs("blocks", exist_ok=True)
            with open("blocks/blockchain_data.encrypted", "w") as f:
                f.write(encrypted_data)
            print(f"✅ File backup saved to blocks/blockchain_data.encrypted")

            # Backup to IPFS and save CID using CID manager
            print("\n🌐 Backing up blockchain to IPFS...")
            ipfs_cid = blockchain.backup_to_ipfs()
            if ipfs_cid:
                print(f"✅ IPFS backup completed!")
                print(f"   CID: {ipfs_cid}")
                print(f"   View at: https://gateway.pinata.cloud/ipfs/{ipfs_cid}")

                # Save IPFS CID using CID manager for auto-restore on restart
                metadata = {
                    "blocks_count": len(blockchain.chain),
                    "file_size": os.path.getsize("blocks/blockchain_data.encrypted")
                    if os.path.exists("blocks/blockchain_data.encrypted")
                    else 0,
                    "timestamp": datetime.now().isoformat(),
                    "source": "auto_backup_on_shutdown",
                }

                if cid_manager.save_cid(ipfs_cid, metadata):
                    print(f"✅ IPFS CID saved for automatic restoration")
                else:
                    print(f"⚠️ Could not save IPFS CID via CID manager")
            else:
                print(
                    "⚠️ IPFS backup skipped (API keys not configured or error occurred)"
                )

    except Exception as e:
        sys.stderr = original_stderr
        print(f"❌ Auto-backup failed: {str(e)}")
        try:
            with app.app_context():
                db.session.rollback()
        except:
            pass  # Ignore rollback errors if no session
    finally:
        # Always restore stderr
        sys.stderr = original_stderr


def cleanup_old_backups():
    """Keep only the last 10 backups in database"""
    try:
        # Get all backups ordered by creation date (newest first)
        all_backups = BlockchainBackup.query.order_by(
            BlockchainBackup.created_at.desc()
        ).all()

        if len(all_backups) > 10:
            # Keep first 10, delete the rest
            backups_to_delete = all_backups[10:]

            for backup in backups_to_delete:
                db.session.delete(backup)

            db.session.commit()
            print(f"🧹 Cleaned up {len(backups_to_delete)} old backups (kept last 10)")

    except Exception as e:
        print(f"❌ Backup cleanup failed: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass  # Ignore rollback errors


# Register auto-backup function to run on shutdown
atexit.register(auto_backup_on_shutdown)

# Register signal handlers for graceful shutdown (SIGTERM from Render pause/stop)
def signal_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT) from Render or user"""
    print(f"\n⚠️ Received shutdown signal ({signum})")
    auto_backup_on_shutdown()
    sys.exit(0)

# Register signal handlers for different shutdown scenarios
signal.signal(signal.SIGTERM, signal_handler)  # Render pause/stop sends SIGTERM
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C sends SIGINT


# ============================================================================
# JINJA2 FILTERS
# ============================================================================


@app.template_filter("mask_aadhar")
def mask_aadhar_filter(aadhar):
    """Mask Aadhar number showing only last 4 digits (e.g., XXXX-XXXX-1234)"""
    if not aadhar:
        return "N/A"
    # Remove any existing formatting
    aadhar_clean = str(aadhar).replace(" ", "").replace("-", "")
    if len(aadhar_clean) != 12:
        return aadhar  # Return as-is if invalid format
    # Mask first 8 digits, show last 4
    return f"XXXX-XXXX-{aadhar_clean[-4:]}"


@app.template_filter("mask_pan")
def mask_pan_filter(pan):
    """Mask PAN number showing only last 4 characters (e.g., XXXXX1234X)"""
    if not pan:
        return "N/A"
    # Remove any existing formatting
    pan_clean = str(pan).replace(" ", "").replace("-", "").upper()
    if len(pan_clean) != 10:
        return pan  # Return as-is if invalid format
    # Mask first 6 characters, show last 4
    return f"XXXXX{pan_clean[-5:]}"


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================


@app.route("/")
def index():
    """Redirect to the appropriate dashboard if logged in, else to login"""
    if not AuthService.is_authenticated():
        return redirect(url_for("login"))

    user = AuthService.get_current_user()
    if user["role"] == "user":
        return redirect(url_for("user_dashboard"))
    else:
        return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page with role-based redirection"""
    if AuthService.is_authenticated():
        user_role = session.get("role")
        if user_role == "user":
            return redirect(url_for("user_dashboard"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("login.html")

        success, user, message = AuthService.login_user(username, password)

        if success:
            flash(f"Welcome, {user.full_name}!", "success")
            if user.role == "user":
                return redirect(url_for("user_dashboard"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration page with automatic property linking"""
    if AuthService.is_authenticated():
        return redirect(url_for("index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        customer_key = request.form.get("customer_key", "").strip()
        pan = request.form.get("pan", "").strip()
        aadhar = request.form.get("aadhar", "").strip()
        password = request.form.get("password", "")

        if not all([full_name, customer_key, pan, aadhar, password]):
            flash("Please fill all required fields.", "danger")
            return render_template("register.html")

        success, new_user, message = AuthService.register_user(
            full_name, customer_key, pan, aadhar, password
        )

        if success:
            # Search blockchain for matching properties
            matching_properties = blockchain.search_by_owner_details(
                customer_key, pan, aadhar
            )

            if matching_properties:
                for prop_data in matching_properties:
                    # Check if property already linked
                    if not Property.query.filter_by(
                        property_key=prop_data["property_key"]
                    ).first():
                        new_property = Property(
                            property_key=prop_data["property_key"],
                            user_id=new_user.id,
                            address=prop_data["address"],
                            pincode=prop_data["pincode"],
                            value=prop_data["value"],
                            survey_no=prop_data["survey_no"],
                        )
                        db.session.add(new_property)
                db.session.commit()
                flash(
                    f"{len(matching_properties)} properties linked to your account.",
                    "info",
                )

            flash(message, "success")
            return redirect(url_for("login"))
        else:
            flash(message, "danger")

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    """User logout"""
    AuthService.logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# ============================================================================
# DASHBOARD
# ============================================================================


@app.route("/appointments")
@officer_or_admin_required
def manage_appointments():
    """Display all appointments for officers and admins."""
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template("manage_appointments.html", appointments=appointments)


@app.route("/appointment/<int:appointment_id>/update_status", methods=["POST"])
@officer_or_admin_required
def update_appointment_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get("status")
    if new_status in ["confirmed", "rejected", "completed"]:
        appointment.status = new_status
        db.session.commit()
        flash(
            f"Appointment #{appointment_id} status updated to {new_status}.", "success"
        )
    else:
        flash("Invalid status.", "danger")
    return redirect(url_for("manage_appointments"))


@app.route("/chat/<int:appointment_id>")
@login_required
def view_chat(appointment_id):
    current_user = AuthService.get_current_user()
    appointment = Appointment.query.get_or_404(appointment_id)

    # Security check: only user or official/admin can view
    if not (
        current_user["id"] == appointment.user_id
        or current_user["role"] in ["officer", "admin"]
    ):
        flash("You are not authorized to view this chat.", "danger")
        return redirect(url_for("user_dashboard"))

    # Check if appointment is rejected
    if appointment.status == "rejected":
        flash("This appointment has been rejected and cannot be accessed.", "warning")
        if current_user["role"] == "user":
            return redirect(url_for("user_dashboard"))
        else:
            return redirect(url_for("manage_appointments"))

    return render_template("chat.html", appointment=appointment)


@app.route("/chat/<int:appointment_id>/messages")
@login_required
def get_messages(appointment_id):
    messages = (
        Message.query.filter_by(appointment_id=appointment_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return jsonify(
        {
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "sender_name": msg.sender.full_name,
                    "content": msg.content,
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for msg in messages
            ]
        }
    )


@app.route("/chat/<int:appointment_id>/send", methods=["POST"])
@login_required
def send_message(appointment_id):
    current_user = AuthService.get_current_user()
    data = request.get_json()
    new_message = Message(
        appointment_id=appointment_id,
        sender_id=current_user["id"],
        content=data["content"],
    )
    db.session.add(new_message)
    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/dashboard")
@officer_or_admin_required
def dashboard():
    """Admin and Officer dashboard"""
    user = AuthService.get_current_user()
    blockchain_info = blockchain.get_chain_info()

    all_properties = blockchain.get_all_properties()
    recent_properties = sorted(
        all_properties, key=lambda x: x.get("last_updated", ""), reverse=True
    )[:5]

    return render_template(
        "dashboard.html",
        user=user,
        blockchain_info=blockchain_info,
        recent_properties=recent_properties,
    )


# ============================================================================
# PROPERTY OPERATIONS
# ============================================================================


@app.route("/property/add", methods=["GET", "POST"])
@officer_or_admin_required
def add_property():
    """Add new property to blockchain with Indian standards"""
    user = AuthService.get_current_user()

    if request.method == "POST":
        # Extract all form fields
        property_key = request.form.get("property_key", "").strip()
        owner = request.form.get("owner", "").strip()
        address = request.form.get("address", "").strip()
        pincode = request.form.get("pincode", "").strip()
        value = request.form.get("value", "").strip()
        aadhar_no = request.form.get("aadhar_no", "").strip()
        pan_no = request.form.get("pan_no", "").strip()
        survey_no = request.form.get("survey_no", "").strip()
        rtc_no = request.form.get("rtc_no", "").strip()
        village = request.form.get("village", "").strip()
        taluk = request.form.get("taluk", "").strip()
        district = request.form.get("district", "").strip()
        state = request.form.get("state", "").strip()
        land_area = request.form.get("land_area", "").strip()
        land_type = request.form.get("land_type", "").strip()
        description = request.form.get("description", "").strip()

        # Validation - required fields
        if not all(
            [property_key, owner, address, pincode, value, aadhar_no, pan_no, survey_no]
        ):
            flash("All required fields must be filled.", "danger")
            return render_template("add_property.html", user=user)

        # Validate value
        try:
            value = float(value)
            if value <= 0:
                raise ValueError("Property value must be positive")
        except ValueError:
            flash("Invalid property value.", "danger")
            return render_template("add_property.html", user=user)

        # Add to blockchain with Indian standards
        try:
            block = blockchain.add_property(
                property_key=property_key,
                owner=owner,
                address=address,
                pincode=pincode,
                value=value,
                aadhar_no=aadhar_no,
                pan_no=pan_no,
                survey_no=survey_no,
                rtc_no=rtc_no,
                village=village,
                taluk=taluk,
                district=district,
                state=state,
                land_area=land_area,
                land_type=land_type,
                description=description,
            )
            blockchain.save_and_exit()
            flash(
                f"Property {property_key} registered successfully! Block #{block.index}",
                "success",
            )
            return redirect(url_for("view_property", property_key=property_key))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("add_property.html", user=user)


@app.route("/property/transfer", methods=["GET", "POST"])
@officer_or_admin_required
def transfer_property():
    """Transfer property ownership with identity validation"""
    user = AuthService.get_current_user()

    if request.method == "POST":
        property_key = request.form.get("property_key", "").strip()
        new_owner = request.form.get("new_owner", "").strip()
        new_owner_aadhar = request.form.get("new_owner_aadhar", "").strip()
        new_owner_pan = request.form.get("new_owner_pan", "").strip()
        transfer_value = request.form.get("transfer_value", "").strip()
        stamp_duty_paid = request.form.get("stamp_duty_paid", "").strip()
        registration_fee = request.form.get("registration_fee", "").strip()

        # Validation - required fields
        if not all([property_key, new_owner, new_owner_aadhar, new_owner_pan]):
            flash(
                "Property key, new owner name, Aadhar, and PAN are required.", "danger"
            )
            return render_template("transfer_property.html", user=user)

        # Parse optional numeric fields
        try:
            transfer_value = float(transfer_value) if transfer_value else None
            stamp_duty_paid = float(stamp_duty_paid) if stamp_duty_paid else None
            registration_fee = float(registration_fee) if registration_fee else None
        except ValueError:
            flash("Invalid numeric value entered.", "danger")
            return render_template("transfer_property.html", user=user)

        try:
            block = blockchain.transfer_property(
                property_key=property_key,
                new_owner=new_owner,
                new_owner_aadhar=new_owner_aadhar,
                new_owner_pan=new_owner_pan,
                transfer_value=transfer_value,
                transfer_reason="sale",
                stamp_duty_paid=stamp_duty_paid,
                registration_fee=registration_fee,
            )
            blockchain.save_and_exit()
            flash(
                f"Property {property_key} transferred successfully! Block #{block.index}",
                "success",
            )
            return redirect(url_for("view_property", property_key=property_key))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("transfer_property.html", user=user)


@app.route("/property/inherit", methods=["GET", "POST"])
@officer_or_admin_required
def inherit_property():
    """Record property inheritance with legal validation"""
    user = AuthService.get_current_user()

    if request.method == "POST":
        property_key = request.form.get("property_key", "").strip()
        from_owner = request.form.get("from_owner", "").strip()
        heir = request.form.get("heir", "").strip()
        heir_aadhar = request.form.get("heir_aadhar", "").strip()
        heir_pan = request.form.get("heir_pan", "").strip()
        relationship = request.form.get("relationship", "").strip()
        legal_heir_certificate_no = request.form.get(
            "legal_heir_certificate_no", ""
        ).strip()

        # Validation - required fields
        if not all([property_key, from_owner, heir, heir_aadhar, heir_pan]):
            flash(
                "Property key, deceased owner name, heir name, Aadhar, and PAN are required.",
                "danger",
            )
            return render_template("inherit_property.html", user=user)

        try:
            block = blockchain.inherit_property(
                property_key=property_key,
                deceased_owner=from_owner,
                heir=heir,
                heir_aadhar=heir_aadhar,
                heir_pan=heir_pan,
                relationship=relationship,
                legal_heir_certificate_no=legal_heir_certificate_no,
            )
            blockchain.save_and_exit()
            flash(
                f"Property {property_key} inheritance recorded! Block #{block.index}",
                "success",
            )
            return redirect(url_for("view_property", property_key=property_key))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return render_template("inherit_property.html", user=user)


@app.route("/property/view/<property_key>")
@login_required
def view_property(property_key):
    """View current state of a property"""
    user = AuthService.get_current_user()
    property_data = blockchain.get_property(property_key)

    if not property_data:
        flash(f"Property {property_key} not found.", "warning")
        return redirect(url_for("dashboard"))

    return render_template("view_property.html", user=user, property=property_data)


@app.route("/property/history/<property_key>")
@login_required
def property_history(property_key):
    """View complete transaction history of a property"""
    user = AuthService.get_current_user()

    try:
        history = blockchain.get_property_history(property_key)
        current_state = blockchain.get_property_current_state(property_key)
        current_owner_aadhar = current_state.get("aadhar_no")
    except ValueError:
        flash(f"Property {property_key} not found.", "warning")
        return redirect(url_for("dashboard"))

    # Process history to remove/mask sensitive data
    # IMPORTANT: Use deep copy to avoid mutating the original blockchain data
    processed_history = []
    for block in history:
        # Create a deep copy to ensure we never mutate the original blockchain
        block_copy = copy.deepcopy(block)

        # 1. Remove hash information
        block_copy.pop("hash", None)
        block_copy.pop("previous_hash", None)

        data = block_copy.get("data", {})

        # 2. Mask Aadhaar numbers that do not belong to the current owner
        if data.get("type") == "registration":
            if data.get("aadhar_no") and data["aadhar_no"] != current_owner_aadhar:
                data["aadhar_no"] = f"********{data['aadhar_no'][-4:]}"

        elif data.get("type") == "transfer":
            if data.get("previous_owner_aadhar"):
                data["previous_owner_aadhar"] = (
                    f"********{data['previous_owner_aadhar'][-4:]}"
                )
            if (
                data.get("new_owner_aadhar")
                and data["new_owner_aadhar"] != current_owner_aadhar
            ):
                data["new_owner_aadhar"] = f"********{data['new_owner_aadhar'][-4:]}"

        processed_history.append(block_copy)

    return render_template(
        "property_history.html",
        user=user,
        property_key=property_key,
        history=processed_history,
    )


@app.route("/property/search", methods=["GET", "POST"])
@login_required
def search_owner():
    """Unified property search for admins and officers"""
    user = AuthService.get_current_user()
    if user["role"] == "user":
        flash("You do not have permission to search all properties.", "danger")
        return redirect(url_for("user_dashboard"))

    properties = []
    search_query = ""
    if request.method == "POST":
        search_query = request.form.get("query", "").strip()
        if search_query:
            properties = blockchain.unified_search(search_query)

    return render_template(
        "search_owner.html", user=user, properties=properties, search_query=search_query
    )


# Keep comprehensive_search route for backward compatibility but redirect
@app.route("/property/comprehensive-search", methods=["GET", "POST"])
@login_required
def comprehensive_search():
    """Redirect to unified search"""
    return redirect(url_for("search_owner"))


@app.route("/property/all")
@officer_or_admin_required
def all_properties():
    """View all properties in the system (for admins and officers)"""
    user = AuthService.get_current_user()
    properties = blockchain.get_all_properties()

    properties = sorted(
        properties, key=lambda x: x.get("last_updated", ""), reverse=True
    )

    return render_template("all_properties.html", user=user, properties=properties)


# ============================================================================
# CHATBOT ROUTES
# ============================================================================


@app.route("/chatbot")
@login_required
def chatbot():
    """Render the chatbot interface."""
    return render_template("chatbot.html")


@app.route("/chatbot/message", methods=["POST"])
@login_required
def chatbot_message():
    """Handle chatbot messages and return responses."""
    data = request.get_json()
    message = data.get("message", "")
    user_id = session.get("user_id")

    response = chatbot_service.handle_message(user_id, message)
    return jsonify({"response": response})


# ============================================================================
# USER DASHBOARD AND PROFILE
# ============================================================================


@app.route("/user/dashboard")
@user_required
def user_dashboard():
    """User dashboard to view owned properties and appointments"""
    user_id = session.get("user_id")
    user = User.query.get_or_404(user_id)
    user_properties = Property.query.filter_by(user_id=user.id).all()
    user_appointments = (
        Appointment.query.filter_by(user_id=user.id)
        .order_by(Appointment.created_at.desc())
        .all()
    )
    return render_template(
        "user_dashboard.html",
        user=user,
        properties=user_properties,
        appointments=user_appointments,
    )


@app.route("/user/profile", methods=["GET", "POST"])
@user_required
def user_profile():
    """User profile page to view and update details"""
    user_id = session.get("user_id")
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user_profile"))

    return render_template("user_profile.html", user=user)


@app.route(
    "/appointment/schedule/<property_key>/<appointment_type>", methods=["GET", "POST"]
)
@user_required
def schedule_appointment(property_key, appointment_type):
    """Schedule an appointment for property transfer or inheritance."""
    if appointment_type not in ["transfer", "inheritance"]:
        flash("Invalid appointment type.", "danger")
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        user_id = session.get("user_id")
        full_name = request.form.get("full_name")
        phone_number = request.form.get("phone_number")
        email = request.form.get("email")
        preferred_date_str = request.form.get("preferred_date")
        preferred_time_str = request.form.get("preferred_time")
        notes = request.form.get("notes")

        preferred_date = datetime.strptime(preferred_date_str, "%Y-%m-%d").date()
        preferred_time = datetime.strptime(preferred_time_str, "%H:%M").time()

        # Server-side validation for date and time
        if preferred_date.weekday() == 6:  # 6 corresponds to Sunday
            flash(
                "Appointments cannot be scheduled on Sundays. Please choose a different day.",
                "danger",
            )
            return render_template(
                "schedule_appointment.html",
                property_key=property_key,
                appointment_type=appointment_type,
            )

        if not (
            datetime.strptime("08:00", "%H:%M").time()
            <= preferred_time
            <= datetime.strptime("18:00", "%H:%M").time()
        ):
            flash(
                "Appointments can only be scheduled between 8:00 AM and 6:00 PM.",
                "danger",
            )
            return render_template(
                "schedule_appointment.html",
                property_key=property_key,
                appointment_type=appointment_type,
            )

        new_appointment = Appointment(
            user_id=user_id,
            property_key=property_key,
            appointment_type=appointment_type,
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            notes=notes,
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash(
            "Appointment requested successfully. An officer will contact you to confirm.",
            "success",
        )
        return redirect(url_for("user_dashboard"))

    return render_template(
        "schedule_appointment.html",
        property_key=property_key,
        appointment_type=appointment_type,
    )


# ============================================================================
# BLOCKCHAIN ADMINISTRATION (ADMIN ONLY)
# ============================================================================


@app.route("/admin/blockchain")
@admin_required
def blockchain_admin():
    """Blockchain administration dashboard"""
    user = AuthService.get_current_user()
    blockchain_info = blockchain.get_chain_info()
    is_valid, validation_message, validation_logs = blockchain.validate_with_details()

    return render_template(
        "blockchain_admin.html",
        user=user,
        blockchain_info=blockchain_info,
        is_valid=is_valid,
        validation_message=validation_message,
        validation_logs=validation_logs,
    )


@app.route("/admin/blockchain/validate")
@admin_required
def validate_blockchain():
    """Validate blockchain integrity"""
    is_valid, message = blockchain.is_valid()

    if is_valid:
        flash(f"Blockchain validation successful: {message}", "success")
    else:
        flash(f"Blockchain validation failed: {message}", "danger")

    return redirect(url_for("blockchain_admin"))


@app.route("/admin/blockchain/view")
@admin_required
def view_blockchain():
    """View complete blockchain"""
    user = AuthService.get_current_user()
    blockchain_data = blockchain.to_dict()

    return render_template(
        "view_blockchain.html", user=user, blockchain=blockchain_data
    )


@app.route("/admin/blockchain/backup", methods=["POST"])
@admin_required
def backup_blockchain():
    """Create blockchain backup and save to database"""
    user = AuthService.get_current_user()

    try:
        # Get encrypted blockchain data
        encrypted_data = blockchain.get_encrypted_data()

        # Create backup record
        timestamp = datetime.now()
        display_name = f"Save - {timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
        filename = f"blockchain_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.encrypted"

        backup = BlockchainBackup(
            name=display_name,
            filename=filename,
            backup_data=encrypted_data,
            created_by=user["id"],
        )

        db.session.add(backup)
        db.session.commit()

        flash(f"✅ Blockchain backup saved to database: {display_name}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Backup failed: {str(e)}", "danger")

    return redirect(url_for("blockchain_admin"))


@app.route("/admin/blockchain/restore", methods=["POST"])
@admin_required
def restore_blockchain():
    """Restore blockchain from database backup"""
    global blockchain

    backup_id_str = request.form.get("backup_file", "").strip()

    if not backup_id_str:
        flash("No backup specified", "danger")
        return redirect(url_for("blockchain_admin"))

    try:
        backup_id = int(backup_id_str.replace("db_backup_", ""))
    except ValueError:
        flash("Invalid backup ID", "danger")
        return redirect(url_for("blockchain_admin"))

    # Get the backup from database
    backup = BlockchainBackup.query.get(backup_id)
    if not backup:
        flash("Backup not found", "danger")
        return redirect(url_for("blockchain_admin"))

    try:
        # Backup current blockchain before restoring
        current_data = blockchain.get_encrypted_data()
        pre_restore_backup = BlockchainBackup(
            name=f"Pre-restore backup - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            filename="auto_backup_pre_restore.encrypted",
            backup_data=current_data,
            created_by=AuthService.get_current_user()["id"],
        )
        db.session.add(pre_restore_backup)
        db.session.commit()
        flash(
            f"Current blockchain backed up to database as: {pre_restore_backup.name}",
            "info",
        )

        # Create new blockchain instance and load from backup data
        new_blockchain = PropertyBlockchain(verbose=True)
        success = new_blockchain.load_from_encrypted_data(backup.backup_data)

        if success:
            blockchain = new_blockchain
            # Save to local storage for persistence
            blockchain._save_blockchain()
            flash(
                f'✅ Blockchain restored from database backup "{backup.name}"! Loaded {len(blockchain.chain)} blocks.',
                "success",
            )
        else:
            # Try recovery as fallback
            recovery_success, recovery_message = (
                new_blockchain.attempt_recovery_from_encrypted_data(backup.backup_data)
            )

            if recovery_success:
                blockchain = new_blockchain
                # Save to local storage for persistence
                blockchain._save_blockchain()
                flash(f"⚠️ Partial recovery successful: {recovery_message}", "warning")
                flash(
                    f'Restored {len(blockchain.chain)} blocks from backup "{backup.name}"',
                    "info",
                )
            else:
                # Provide detailed error information
                error_details = []
                if hasattr(new_blockchain, "logs") and new_blockchain.logs:
                    # Show last 5 error logs
                    error_logs = [
                        log
                        for log in new_blockchain.logs[-10:]
                        if "error" in log.lower()
                        or "failed" in log.lower()
                        or "invalid" in log.lower()
                    ]
                    if error_logs:
                        error_details = error_logs[-5:]  # Last 5 relevant logs

                error_msg = "❌ Blockchain restore failed! Backup data is corrupted."
                if error_details:
                    error_msg += " Details: " + " | ".join(error_details)
                else:
                    error_msg += (
                        " The backup data appears to be corrupted or incompatible."
                    )

                flash(error_msg, "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Restore failed: {str(e)}", "danger")

    return redirect(url_for("blockchain_admin"))


@app.route("/admin/blockchain/list-backups")
@admin_required
def list_backups():
    """Get list of available database backups as JSON with friendly names"""
    backups = BlockchainBackup.query.order_by(BlockchainBackup.created_at.desc()).all()

    backup_list = []
    for i, backup in enumerate(backups, 1):
        backup_list.append(
            {
                "id": backup.id,
                "path": f"db_backup_{backup.id}",  # Use ID for restore
                "name": backup.name,
            }
        )

    return jsonify({"backups": backup_list})


@app.route("/admin/backup-ipfs", methods=["POST"])
@admin_required
def backup_to_ipfs():
    """Backup blockchain to IPFS (Admin only)"""
    # Clear logs before backup
    blockchain.logs = []

    cid = blockchain.backup_to_ipfs()

    if cid:
        # Save IPFS CID using CID manager for auto-restore
        metadata = {
            "blocks_count": len(blockchain.chain),
            "file_size": os.path.getsize(blockchain.STORAGE_FILE)
            if os.path.exists(blockchain.STORAGE_FILE)
            else 0,
            "created_by": session.get("user_id", 1),  # Current user or system
            "timestamp": datetime.now().isoformat(),
            "source": "manual_backup",
        }

        if cid_manager.save_cid(cid, metadata):
            flash(f"✅ Backup successful! IPFS CID: {cid}", "success")
            flash(f"View at: https://gateway.pinata.cloud/ipfs/{cid}", "info")
            flash(
                f"✅ CID saved for automatic restoration on server restart",
                "success",
            )
        else:
            flash(f"✅ Backup successful! IPFS CID: {cid}", "success")
            flash(f"⚠️ Could not save CID for auto-restore", "warning")
    else:
        flash("❌ Backup failed. Check the details below.", "danger")
        # Show logs from the backup attempt
        if hasattr(blockchain, "logs") and blockchain.logs:
            for log in blockchain.logs[-10:]:
                if "error" in str(log).lower():
                    flash(f"❌ {log}", "danger")
                else:
                    flash(f"ℹ️ {log}", "info")

    return redirect(url_for("blockchain_admin"))


@app.route("/admin/restore-ipfs", methods=["POST"])
@admin_required
def restore_from_ipfs():
    """Restore blockchain from IPFS using CID (Admin only)"""
    global blockchain

    cid = request.form.get("ipfs_cid", "").strip()

    if not cid:
        flash("❌ No IPFS CID provided", "danger")
        return redirect(url_for("blockchain_admin"))

    # Basic CID validation (Qm... for CIDv0 or baf... for CIDv1)
    # CIDv0: starts with Qm, 46 chars
    # CIDv1: starts with baf, variable length (typically 59+ chars)
    cid = cid.strip()  # Remove any whitespace
    is_valid_cid = (
        (cid.startswith("Qm") and len(cid) >= 46)  # CIDv0
        or (cid.startswith("baf") and len(cid) >= 50)  # CIDv1
    )
    if not is_valid_cid:
        flash(
            f'❌ Invalid IPFS CID format. CID should start with "Qm" (v0) or "baf" (v1)',
            "danger",
        )
        return redirect(url_for("blockchain_admin"))

    try:
        # Backup current blockchain before restoring
        if os.path.exists(blockchain.STORAGE_FILE):
            pre_restore_backup = f"blocks/blockchain_pre_ipfs_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.encrypted"
            shutil.copy(blockchain.STORAGE_FILE, pre_restore_backup)
            flash(f"Current blockchain backed up to: {pre_restore_backup}", "info")

        # Clear logs before restore attempt
        blockchain.logs = []

        # Restore from IPFS
        result = blockchain.restore_from_ipfs(cid)

        if result:
            # Reload the blockchain instance
            blockchain = PropertyBlockchain(verbose=True)
            flash(f"✅ Blockchain restored from IPFS! CID: {cid}", "success")
            flash(f"Loaded {len(blockchain.chain)} blocks", "info")
        else:
            # Show ALL logs for debugging
            if hasattr(blockchain, "logs") and blockchain.logs:
                for log in blockchain.logs[-10:]:
                    if "error" in str(log).lower() or "failed" in str(log).lower():
                        flash(f"❌ {log}", "danger")
                    else:
                        flash(f"ℹ️ {log}", "info")
            else:
                flash("❌ Failed to restore from IPFS. No logs available.", "danger")

    except Exception as e:
        flash(f"❌ IPFS restore error: {str(e)}", "danger")

    return redirect(url_for("blockchain_admin"))


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template("500.html"), 500


# ============================================================================
# CONTEXT PROCESSOR
# ============================================================================


@app.context_processor
def inject_user():
    """Make current user available in all templates"""
    return dict(current_user=AuthService.get_current_user())


# ============================================================================
# CHATBOT ROUTE
# ============================================================================


@app.route("/chatbot/ask", methods=["POST"])
def chatbot_ask():
    """AI Chatbot powered by Gemini for property-related queries"""
    try:
        data = request.get_json()
        user_question = data.get("question", "").strip()

        if not user_question:
            return jsonify({"answer": "Please ask a question!", "success": True})

        # Get current user role for context-aware responses
        current_user = AuthService.get_current_user()
        user_role = current_user.get("role", "user") if current_user else "user"

        # System context for the chatbot
        system_context = f"""You are PawParties AI Assistant, a helpful chatbot for a Property Registration Blockchain System in India.

SYSTEM INFORMATION:
- Property Registration Fee: ₹5,000 (fixed, one-time)
- Property Transfer Fee: ₹3,000 (per transfer)
- Stamp Duty on Transfers: 2% of property transaction value
- Registration Fee on Transfers: 5% of property transaction value
- System uses blockchain technology for permanent, tamper-proof property records
- All properties require valid Aadhar card (12 digits) and PAN card (format: ABCDE1234F)
- Users can: register properties, transfer ownership, inherit properties, view complete history
- Officers & Admins: manage the system, validate records, handle appointments
- Appointments: can be scheduled with officials through the appointment system
- All transactions are cryptographically secured and permanently recorded

CURRENT USER ROLE: {user_role}

IMPORTANT INSTRUCTION FOR USER ROLE:
- If user_role is "user" and they ask about transfers, inheritance, or any official processes, tell them to schedule an appointment with officials through the "My Appointments" section in their dashboard.
- Regular users cannot directly perform transfers - they need official approval through the appointment system.
- Only officers and admins can process transfers directly.

CAPABILITIES:
- Property registration and transfer process guidance
- Fee calculations and explanations
- Document requirements
- Appointment booking help
- Blockchain technology explanations
- Property search and history viewing

Keep answers concise (2-3 sentences), helpful, friendly, and accurate. Use emojis occasionally.
If asked about something outside property/blockchain, politely redirect to property-related topics.

User Question: """

        # Try Gemini API first, fallback to rule-based if unavailable
        if gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash", contents=system_context + user_question
                )
                answer = response.text.strip()
            except Exception:
                answer = get_fallback_answer(user_question, user_role)
        else:
            answer = get_fallback_answer(user_question, user_role)

        return jsonify({"answer": answer, "success": True})

    except Exception:
        return jsonify(
            {
                "answer": "Sorry, I encountered an error. Please try again or contact support.",
                "success": False,
            }
        )


def get_fallback_answer(question, user_role="user"):
    """Rule-based fallback answers when Gemini is unavailable"""
    q = question.lower()

    # Check if user is asking about transfer, inheritance, or appointment-related actions
    is_transfer_query = any(
        word in q for word in ["transfer", "ownership", "sell", "buy"]
    )
    is_inheritance_query = any(
        word in q for word in ["inherit", "inheritance", "heir", "succession"]
    )
    is_appointment_query = any(
        word in q for word in ["appointment", "official", "meeting", "schedule", "book"]
    )

    # For regular users asking about transfers or inheritance, direct them to appointments
    if user_role == "user" and (
        is_transfer_query or is_inheritance_query or is_appointment_query
    ):
        if is_transfer_query:
            return "📅 To transfer property ownership, please schedule an appointment with an official. Go to your Dashboard → 'My Appointments' section → 'Request New Appointment' → Select 'Transfer' as the type. An officer will guide you through the process and handle the transfer."
        elif is_inheritance_query:
            return "📅 To record inheritance, please schedule an appointment with an official. Go to your Dashboard → 'My Appointments' section → 'Request New Appointment' → Select 'Inheritance' as the type. An officer will help you complete the inheritance process."
        else:
            return "📅 To schedule an appointment: Go to your Dashboard → 'My Appointments' section → 'Request New Appointment' → Select date, time, and purpose (Transfer/Inheritance) → Submit. Officials will accept/reschedule and chat with you to complete the process."

    # Registration queries
    if any(
        word in q
        for word in ["register", "registration", "add property", "new property"]
    ):
        return "📝 To register a property: Click 'Add Property' → Fill in owner details (Name, Aadhar, PAN) → Enter property details (address, survey number, land info) → Submit. Registration fee is ₹5,000."

    # Fee queries
    elif any(
        word in q for word in ["fee", "cost", "charge", "price", "payment", "how much"]
    ):
        return "💰 **Fees:** Registration = ₹5,000 | Transfer = ₹3,000 + Stamp Duty (2%) + Registration Fee (5% of property value). Example: For ₹50 lakh property → ₹1 lakh stamp + ₹2.5 lakh reg fee."

    # Transfer queries (for officers/admins)
    elif is_transfer_query and user_role in ["admin", "officer"]:
        return "🔄 To transfer property: Go to 'Transfer Property' → Enter property key → New owner's details (Aadhar, PAN) → Transaction value → Submit. Stamp duty & reg fee calculated automatically."

    # Inheritance queries (for officers/admins)
    elif is_inheritance_query and user_role in ["admin", "officer"]:
        return "👨‍👩‍👦 To record inheritance: Click 'Inherit Property' → Property key → Heir's details (Aadhar, PAN) → Relationship → Submit. Usually lower/no stamp duty for inheritance."

    # Document queries
    elif any(
        word in q for word in ["document", "documents", "required", "need", "papers"]
    ):
        return "📄 **Required documents:** Valid Aadhar card (12 digits), PAN card (ABCDE1234F format), property ownership proof, survey number, address details, and land measurement documents."

    # Blockchain/Security queries
    elif any(
        word in q for word in ["blockchain", "security", "safe", "tamper", "hack"]
    ):
        return "🔐 Our blockchain uses SHA-256 cryptography + proof-of-work mining. Every record is permanent, tamper-proof, and publicly verifiable. No one can alter past transactions without detection."

    # History/View queries
    elif any(word in q for word in ["history", "view", "check", "see", "track"]):
        return "🔍 To view property history: Search property → 'View Property' → 'View Transaction History'. You'll see complete ownership chain, all transfers, values, and dates - fully transparent!"

    # Search queries
    elif any(word in q for word in ["search", "find", "locate", "look"]):
        return "🔎 **Search options:** 'Search by Owner' (find all properties of a person) | 'All Properties' (browse complete registry) | Enter property key for specific property details."

    # Aadhar/PAN queries
    elif any(word in q for word in ["aadhar", "pan", "id", "identification"]):
        return "🆔 Aadhar must be exactly 12 digits. PAN must follow format: ABCDE1234F (5 letters, 4 numbers, 1 letter). Both are mandatory for all property transactions."

    # Chat/Support queries
    elif any(word in q for word in ["chat", "message", "contact", "talk", "speak"]):
        return "💬 Book an appointment to chat with officials! They can answer specific questions about your property, guide you through processes, and handle special cases."

    # Greeting
    elif any(
        word in q for word in ["hello", "hi", "hey", "good morning", "good afternoon"]
    ):
        return "👋 Hello! I'm PawParties AI Assistant. I can help you with property registration, transfers, fees, appointments, and more. What would you like to know?"

    # Thanks
    elif any(word in q for word in ["thank", "thanks", "appreciate"]):
        return "😊 You're welcome! Feel free to ask if you have more questions. Happy to help!"

    # Default response
    else:
        return "🤖 I can help you with: **Property Registration, Transfers, Inheritance, Fees & Costs, Documents, Appointments, Blockchain Security, Search & History**. What would you like to know about?"


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PROPERTY REGISTRATION BLOCKCHAIN SYSTEM")
    print("=" * 60)
    print("\nDefault Login Credentials:")
    print("  Admin    - Username: admin     Password: admin123")
    print("  Officer  - Username: officer1  Password: officer123")
    print("\nIMPORTANT: Change default passwords in production!")
    print("=" * 60 + "\n")

    app.run(debug=True, host="127.0.0.1", port=5000)
