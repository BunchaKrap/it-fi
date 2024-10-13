from flask import Flask, render_template
from datetime import datetime
from pymongo import MongoClient
from pymongo.mongo_client import MongoClient  # noqa: F811
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
# import os

# import requests

load_dotenv()

uri = "mongodb+srv://vukijee:Y6HSTeyKvjeO77oh@it-fi.jsi9p.mongodb.net/?retryWrites=true&w=majority&appName=IT-fi"

app = Flask(__name__)
curr_yr = datetime.now().year
client = MongoClient(uri, server_api=ServerApi("1"))

try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


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


# print(open_data("MainColl"))


@app.context_processor
def inject_all_items():
    tiedostot = open_data("MainColl")
    return dict(all_items=tiedostot)


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
    return render_template(
        "donaaaa.html",
        curr_yr=curr_yr,
        show_ad=False,
        tiedostot=tiedostot,
        page_title="Lahjoita",
        cat_ids=category_ids,
    )


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


# if __name__ == "__main__":  # for dev
#     app.run(debug=True)
