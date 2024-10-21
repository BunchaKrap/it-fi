from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from datetime import datetime
from pymongo import MongoClient
from pymongo.mongo_client import MongoClient  # noqa: F811
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import os
from werkzeug.utils import secure_filename
from bson import ObjectId

# import requests

load_dotenv()

uri = "mongodb+srv://vukijee:Y6HSTeyKvjeO77oh@it-fi.jsi9p.mongodb.net/?retryWrites=true&w=majority&appName=IT-fi"

app = Flask(__name__)
curr_yr = datetime.now().year
client = MongoClient(uri, server_api=ServerApi("1"))
bcrypt = Bcrypt(app)
app.secret_key = "madre_mia"
new_db = client["donations"]
don_coll = new_db["donations"]


try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


cloudinary.config(
    cloud_name="doi7brn37",
    api_key="397221829232896",
    api_secret="uvdoBL5SzfsLgdCInDA4jMl0El4",
    secure=True,
)


def open_don_data():
    try:
        lahjotukset = list(don_coll.find({}))

        for item in lahjotukset:
            item["_id"] = str(item["_id"])
        return don_coll, lahjotukset

    except Exception as e:
        print(f"Error: {e}")


def open_data(collection_name):
    try:
        db = client["ToriScrape"]
        collection = db[collection_name]

        tiedostot = list(collection.find({}))

        for document in tiedostot:
            document["_id"] = str(document["_id"])

        return tiedostot

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def open_user_data():
    try:
        db = client["users"]
        collection = db["user_data"]

        all_users = list(collection.find({}))

        for item in all_users:
            item["_id"] = str(item["_id"])

        return all_users

    except Exception as e:
        print(f"Error: {e}")
        return []


category_ids = {
    "Antiikki ja taide": "006",
    "Auto-, vene- ja moottoripyörätarvikkeet": "010",
    "Elektroniikka ja kodinkoneet": "001",
    "Eläimet ja eläintarvikkeet": "007",
    "Huonekalut ja sisustus": "004",
    "Koti, puutarha ja rakentaminen": "009",
    "Lapset ja vanhemmat": "005",
    "Liiketoiminta ja palvelut": "008",
    "Urheilu ja ulkoilu": "003",
    "Vaatteet, kosmetiikka ja asusteet": "011",
    "Viihde ja harrastukset": "002",
}


def find_item_loc(category_name=None):
    tiedostot = open_data("MainColl")
    unique_locations = set()

    for details in tiedostot:
        try:
            extra_data = details.get("extra_data", {})
            item_category = extra_data.get("item_category")

            if category_name and item_category != category_name:
                continue

            location = details.get("location")
            if location:
                location_parts = location.split(", ")

                if len(location_parts) > 0:
                    unique_locations.add(location_parts[0])

        except Exception as e:
            print(f"Error processing item: {e}")
            continue

    return unique_locations


def is_logged_in():
    return "logged_in" in session and session["logged_in"]


def is_admin():
    return is_logged_in() and session.get("user_role").lower() == "admin"


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", cat_ids=category_ids), 404


# session["user_id"] = str(user["_id"])
@app.context_processor
def inject_user():
    if "logged_in" in session and session["logged_in"]:
        return {
            "user_id": session.get("user_id"),
            "user_fname": session.get("user_fname", ""),
            "user_lname": session.get("user_lname", ""),
            "user_email": session.get("user_email", ""),
            "user_role": session.get("user_role", "reg"),
            "logged_in": True,
        }
    return {
        "user_fname": "",
        "user_email": "",
        "user_role": "guest",
        "logged_in": False,
    }


@app.context_processor
def inject_all_items():
    tiedostot = open_data("MainColl")
    return dict(all_items=tiedostot)


@app.context_processor
def inject_curr_yr():
    return {"curr_yr": curr_yr}


@app.route("/")
def kotisivut():
    tiedostot = open_data("MainColl")
    unique_locations = find_item_loc()
    return render_template(
        "index.html",
        tiedostot=tiedostot,
        curr_yr=curr_yr,
        show_ad=True,
        page_title="Etusivu",
        cat_ids=category_ids,
        unique_locations=sorted(unique_locations),
    )


@app.route("/kategoriat")
def categories_view():
    tiedostot = open_data("MainColl")
    unique_locations = find_item_loc()
    return render_template(
        "categories.html",
        tiedostot=tiedostot,
        show_ad=False,
        page_title="Kategoriat",
        cat_ids=category_ids,
        unique_locations=sorted(unique_locations),
        category=None,
    )


@app.route("/kategoria/<id>")
def categories(id):
    category_name = None

    for name, cat_id in category_ids.items():
        if cat_id == id:
            category_name = name
            break

    if category_name:
        unique_locations = find_item_loc(category_name)
        tiedostot = open_data("MainColl")

        filtered_items = [
            item
            for item in tiedostot
            if item.get("extra_data", {}).get("item_category") == category_name
        ]

        return render_template(
            "category.html",
            category=category_name.capitalize(),
            tiedostot=filtered_items,
            page_title=f"{category_name.capitalize()}",
            cat_ids=category_ids,
            unique_locations=sorted(unique_locations),
        )
    else:
        tiedostot = open_data("MainColl")
        return render_template(
            "error.html",
            tiedostot=tiedostot,
            category=category_name,
            cat_ids=category_ids,
        ), 404


@app.route("/meista")
def about():
    tiedostot = open_data("MainColl")
    return render_template(
        "about.html",
        curr_yr=curr_yr,
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Meistä",
        cat_ids=category_ids,
    )


@app.route("/lahjoita")
def donaa():
    tiedostot = open_data("MainColl")
    mapbox_token = os.getenv("MAPBOX_TOKEN")
    return render_template(
        "donaaaa.html",
        cats=category_ids,
        curr_yr=curr_yr,
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Lahjoita",
        cat_ids=category_ids,
        MAPBOX_TOKEN=mapbox_token,
    )


@app.route("/submit_donation", methods=["POST"])
def submit_donation():
    try:
        category_id = request.form.get("category")
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        category_name = None
        for name, cat_id in category_ids.items():
            if cat_id == category_id:
                category_name = name
                break
        product = request.form.get("product")
        condition = request.form.get("condition")
        age = request.form.get("age")
        more_details = request.form.get("don_item_deets")
        animals_yes = request.form.get("animals_yes")
        email = request.form.get("email")
        first_name = request.form.get("first-name")
        surname = request.form.get("surname")
        address = request.form.get("address")
        postal_code = request.form.get("postal-code")
        city = request.form.get("city")
        area = request.form.get("area")
        region = request.form.get("region")
        newsletter = "newsletter" in request.form

        image_file = request.files.get("image")
        image_url = None

        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext not in [".jpg", ".jpeg", ".png"]:
                return "Invalid file type. Please upload a JPG or PNG image.", 400

            try:
                upload_result = cloudinary.uploader.upload(
                    image_file, folder="IT-fi/donations"
                )
                image_url = upload_result["url"]
            except Exception as e:
                return f"An error occurred while uploading the image: {str(e)}"
        timestamp = datetime.now()
        donation_data = {
            "product": product,
            "category": category_name,
            "condition": condition,
            "age": age,
            "more_details": more_details,
            "animals_yes": bool(animals_yes),
            "email": email,
            "first_name": first_name,
            "surname": surname,
            "address": address,
            "postal_code": postal_code,
            "city": city,
            "area": area,
            "region": region,
            "newsletter": newsletter,
            "image_url": image_url,
            "submitted_time": timestamp,
            "user_ip": user_ip,
        }

        don_coll.insert_one(donation_data)

        return redirect(url_for("thank_you"))

    except Exception as e:
        print(e)
        return "An error occurred while processing your donation. Please try again."


@app.route("/kiitos")
def thank_you():
    don_items, lahjotukset = open_don_data()

    last_donation_cursor = don_items.find().sort([("_id", -1)]).limit(1)
    last_donation = list(last_donation_cursor)

    if last_donation:
        last_donation = last_donation[0]
        last_donation["_id"] = str(last_donation["_id"])

        if is_logged_in():
            user_email = session.get("user_email")
            donation_email = last_donation.get("email")
            if user_email != donation_email:
                flash("Sorppa kamut!", "error")
                return redirect(url_for("show_dash"))
        else:
            flash("You must be logged in to view this page.", "error")
            return redirect(url_for("kirjaudu"))
    else:
        last_donation = None

    return render_template(
        "kiitos.html",
        cat_ids=category_ids,
        show_ad=False,
        don_items=lahjotukset,
        last_don=last_donation,
        page_title="Kiitos!",
    )


@app.route("/kaikkidonot")
def kaikki_donot():
    tiedostot = open_data("MainColl")
    don_coll_ref, don_items = open_don_data()

    last_donation = don_items[-1] if don_items else None
    if is_admin():
        return render_template(
            "all_dons.html",
            last_don=last_donation,
            don_items=don_items,
            cat_ids=category_ids,
            tiedostot=tiedostot,
            show_ad=False,
        )
    else:
        flash("No authorization.", "error")
        return redirect(request.referrer or url_for("show_dash"))


@app.route("/kaikkayt")
def all_uzers():
    tiedostot = open_data("MainColl")
    all_users = open_user_data()
    don_coll_ref, don_items = open_don_data()

    all_users.sort(key=lambda x: x["user_created"], reverse=True)

    last_donation = don_items[-1] if don_items else None

    if is_admin():
        return render_template(
            "all_uzers.html",
            all_users=all_users,
            last_don=last_donation,
            don_items=don_items,
            cat_ids=category_ids,
            tiedostot=tiedostot,
            show_ad=False,
        )
    else:
        flash("No authorization.", "error")
        return redirect(request.referrer or url_for("show_dash"))


@app.route("/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id):
    user_collection = get_usr_details()
    try:
        result = user_collection.delete_one({"_id": ObjectId(user_id)})

        if result.deleted_count == 1:
            flash("User successfully deleted.", "success")
        else:
            flash("User not found.", "warning")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for("all_uzers"))


@app.route("/accept_donation/<donation_id>", methods=["POST"])
def accept_donation(donation_id):
    try:
        tiedostot = open_data("MainColl")
        donation_id = ObjectId(donation_id)

        donation = don_coll.find_one({"_id": donation_id})
        print(f"Received donation_id: {donation_id}")

        if donation:
            tiedostot.insert_one(donation)
            don_coll.delete_one({"_id": donation_id})

            flash("Donation accepted successfully!", "success")
        else:
            flash("Donation not found.", "error")
    except Exception as e:
        print(f"Error accepting donation: {e}")
        flash("An error occurred while accepting the donation: " + str(e), "error")

    return redirect(url_for("kaikki_donot"))


@app.route("/delete_donation/<donation_id>", methods=["POST"])
def delete_donation(donation_id):
    try:
        result = don_coll.delete_one({"_id": ObjectId(donation_id)})

        if result.deleted_count == 1:
            flash("Donation successfully deleted.", "success")
        else:
            flash("Donation not found.", "warning")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for("kaikki_donot"))


@app.route("/tietosuoja")
def tietosuoja():
    tiedostot = open_data("MainColl")
    return render_template(
        "privacy.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Tietosuoja",
        cat_ids=category_ids,
    )


@app.route("/evasteet")
def cookies():
    tiedostot = open_data("MainColl")
    return render_template(
        "cookies.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Evästeet",
        cat_ids=category_ids,
    )


@app.route("/otayhteytta")
def contact():
    tiedostot = open_data("MainColl")
    return render_template(
        "contact.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Ota Yhteyttä",
        cat_ids=category_ids,
    )


@app.route("/saannot")
def rules():
    tiedostot = open_data("MainColl")
    return render_template(
        "rules.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Säännöt & Käyttöehdot",
        cat_ids=category_ids,
    )


@app.route("/affiliates")
def affiliates():
    tiedostot = open_data("MainColl")
    return render_template(
        "affiliates.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Affiliates",
        cat_ids=category_ids,
    )


@app.route("/palkrangok")
def admin_logi():
    tiedostot = open_data("MainColl")
    return render_template(
        "palkrangok.html",
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Admin Login",
        cat_ids=category_ids,
    )


def get_usr_details():
    db = client["users"]
    collection = db["user_data"]
    return collection


@app.route("/dash")
def show_dash():
    try:
        if is_logged_in():
            user_role = session.get("user_role")

            if user_role == "admin":
                return render_template(
                    "/admin_dash.html",
                    show_ad=False,
                    page_title="Admin Dashboard",
                    cat_ids=category_ids,
                )
            else:
                return render_template(
                    "/dashboard.html",
                    show_ad=False,
                    page_title="User Dashboard",
                    cat_ids=category_ids,
                )
        else:
            return redirect(url_for("kirjaudu"))

    except Exception as e:
        print(f"Unexpected error: {e}")
        return redirect(url_for("kirjaudu"))


@app.route("/register")
def register():
    return render_template("/uusi_kayt.html")


@app.route("/kirjaudu", methods=["POST", "GET"])
def kirjaudu():
    return render_template("login.html")


@app.route("/create_new_user", methods=["POST"])
def create_user():
    user_db = client["users"]
    user_coll = user_db["user_data"]
    timestamp = datetime.now()
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    crypted_pw = bcrypt.generate_password_hash(request.form.get("login-pw")).decode(
        "utf-8"
    )
    user_details = {
        "etunimi": request.form.get("usr-etunimi"),
        "sukunimi": request.form.get("usr-sukunimi"),
        "sähköposti": request.form.get("login-email"),
        "salasana": crypted_pw,
        "role": "regular",
        "user_created": timestamp,
        "user_ip": user_ip,
    }
    try:
        existing_user = user_coll.find_one(
            {"sähköposti": user_details["sähköposti"].lower()}
        )

        if existing_user:
            flash("Tällä sähköpostilla on jo rekisteröity käyttäjä!", "error")
            print("Email already in use.")
            return redirect(url_for("register"))

        user_coll.insert_one(user_details)
        # print(f"Data saved: {user_details}")
        flash("Käyttäjä onnistuneesti rekisteröity.", "success")
        return redirect(url_for("kirjaudu"))

    except Exception as e:
        print(f"Exception error: {e}")
        flash("An error occurred during registration.", "error")
        return redirect(url_for("register"))


@app.route("/check_login", methods=["POST"])
def check_login():
    login_email = request.form.get("login-name-usr")
    login_pw = request.form.get("login-pw-usr")
    user_collection = get_usr_details()

    try:
        user = user_collection.find_one({"sähköposti": login_email.lower()})
        if user and bcrypt.check_password_hash(user["salasana"], login_pw):
            session["logged_in"] = True
            session["user_id"] = str(user["_id"])
            session["user_fname"] = user.get("etunimi", "")
            session["user_lname"] = user.get("sukunimi", "")
            session["user_email"] = user["sähköposti"]
            session["user_role"] = user.get("role", "reg")
            return redirect(url_for("show_dash"))
        else:
            flash("Väärä sähköposti tai salasana.", "error")
            return redirect(url_for("kirjaudu"))
    except Exception as e:
        print(f"Another error buddy... {e}")
        flash("An unexpected error occurred.", "error")
        return redirect(url_for("kirjaudu"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("kirjaudu"))


# if __name__ == "__main__":  # for dev
#     app.run(debug=True)
