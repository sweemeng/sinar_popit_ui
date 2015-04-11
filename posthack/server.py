__author__ = 'sweemeng'
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
import requests

"""
This is a hack for adding post. This will be replace with a proper frontend
"""

app = Flask(__name__)
POPIT_ENDPOINT = "https://sinar-malaysia.popit.mysociety.org/api/v0.1"
#POPIT_ENDPOINT = "http://localhost:3000/api"
API_KEY = "06b50c66ad47e99728b2b527de9db0429668da12"
headers = {"Apikey":API_KEY}

@app.route("/")
def glue():
    return render_template("glue.html")

@app.route("/addpost/<organization_id>", methods=["GET", "POST"])
def add_post(organization_id):
    if request.method=="POST":
        data = {}
        data["label"] = request.form["name"]
        data["role"] = request.form["role"]

        if request.form["start_date"]:
            data["start_date"] = request.form["start_date"]
        if request.form["end_date"]:
            data["end_date"] = request.form["end_date"]
        data["organization_id"] = organization_id

        url = "%s/%s" % (POPIT_ENDPOINT, "posts")

        r = requests.post(url, data=data, headers=headers)

        return str((r.status_code, r.content))

    return render_template("addpost.html", organization_id=organization_id)


@app.route("/listorgs/")
def list_organizations():
    params = {}
    if request.args.get("page"):
        params["page"] = request.args.get("page")

    url =  "%s/%s" % (POPIT_ENDPOINT, "organizations")
    r = requests.get(url, params=params)
    data = r.json()
    page =  data["page"]
    url = "/create/"
    next_page = ""
    prev_page = ""
    has_more = data["has_more"]
    if data["has_more"]:
        next_page = "/listorgs/?page=%d" % (page + 1)
    if page > 1:
        prev_page = "/listorgs/?page=%d" % (page - 1)
    organizations = data["result"]
    return render_template("list_organizations.html",
                           organizations=organizations,
                           url=url,
                           next_page=next_page,
                           prev_page=prev_page,
                           has_more=has_more)

@app.route("/addmembers/<organizations_id>", methods=["GET", "POST"])
def create_membership(organizations_id):
    if request.method == "POST":
        data = {
            "label": request.form["name"],
            "role": request.form["role"],
            "person_id": request.form["person_id"],
            "post_id": request.form["post_id"],
            "organization_id": organizations_id,
            "start_date": request.form["start_date"],
        }
        if request.form["end_date"]:
            data["end_date"]  = request.form["end_date"]
        return "Done"
    persons = fetch_entity("persons")

    posts = get_entity("posts", "organization_id", organizations_id)
    return render_template("post_memberships.html",
                           persons=persons,
                           posts=posts,
                           organizations_id=organizations_id)

@app.route("/addmembers/", methods=["GET", "POST"])
def go_to_membership():
    if request.method == "POST":
        url = "/addmembers/%s" % request.form["organization"]
        return redirect(url)
    organizations = fetch_entity("organizations")
    return render_template("redirect_membership.html",
                           organizations=organizations)

@app.route("/mergeperson/", methods=["GET", "POST"])
def merge_person():
    if request.method == "POST":
        primary_person = request.form["primary_person"]
        secondary_person = request.form["secondary_person"]
        merge_url = "%s/persons/%s/merge/%s" % (POPIT_ENDPOINT, primary_person, secondary_person)
        print merge_url
        r =  requests.post(merge_url, headers=headers)
        if r.status_code == 200:
            return "ok"
        return str((r.status_code, r.content, r.reason))
    persons = fetch_entity("persons")
    return render_template("mergeperson.html", persons=persons)

@app.route("/selectperson/", methods=["GET", "POST"])
def select_person_merge():
    params = {}
    if request.method.get("page",""):
        params["page"] = request.method.get("page")

    url = "%s/%s" % (POPIT_ENDPOINT, "persons")
    r = requests.get(url, params=params)
    data = r.json()
    persons =  data["result"]
    return data["result"]

@app.route("/deletemembership/<person_id>", methods=["POST", "GET"])
def delete_post(person_id):
    if request.method == "POST":
        requests.delete(request.form["membership"])
        return "Done"

    person = fetch_one_entity("persons", person_id)
    return render_template("person_membership.html", person=person)

@app.route("/deletepostmembership/<post_id>", methods=["POST", "GET"])
def delete_post_membership(post_id):
    if request.method ==  "POST":
        requests.delete(request.form["membership"])
        print request.form["membership"]
        return "Done"
    post = fetch_one_entity("posts", post_id)
    memberships = {}
    for membership in post["memberships"]:
        person = fetch_one_entity("persons", membership["person_id"])
        print "processing name"
        membership["person_name"] =  person["name"]
        organization = fetch_one_entity("organizations", membership["organization_id"])

        print "processing org"
        membership["organization_name"] = organization["name"]

    return render_template("post_membership.html", post=post)

@app.route("/listpost/")
def list_post():
    params = {}
    if request.args.get("page"):
        params["page"] = request.args.get("page")
    post_url = "%s/%s" % (POPIT_ENDPOINT, "posts")
    r = requests.get(post_url, params=params)

    data = r.json()
    page = data["page"]
    next_url = ""
    prev_url = ""
    if page >= 1:
        next_url = "/listpost/?page=%d" % (page+1)
    if page > 1:
        prev_url = "/listpost/?page=%d" % (page-1)

    posts = data["result"]
    has_more = data.get("has_more")
    url = "/deletepostmembership"
    return render_template("list_post.html",
                           posts=posts,
                           url=url,
                           prev_url=prev_url,
                           next_url=next_url,
                           has_more=has_more)

@app.route("/listperson/delete/")
def list_person():
    params = {}
    if request.args.get("page"):
        params["page"] = request.args.get("page")
    person_url = "%s/%s" % (POPIT_ENDPOINT, "persons")
    r = requests.get(person_url, params=params)
    data = r.json()
    persons = data["result"]
    page =  data["total"] / data["per_page"]
    if (page * data["per_page"]) < data["total"]:
        page = page + 1
    pages = range(1, page+1)
    url = "/deletemembership"
    return render_template("list_person.html", persons=persons, url=url, pages=pages)


def fetch_one_entity(entity_type, entity_id):
    url = "%s/%s/%s" % (POPIT_ENDPOINT, entity_type, entity_id)
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        return data["result"]

    return []

def fetch_entity(entity_type):
    url = "%s/%s" % (POPIT_ENDPOINT, entity_type)
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        data = r.json()
        return data["result"]
    return []

def search_entity(entity, key, value):
    url = "%s/search/%s?q=%s:%s" % (POPIT_ENDPOINT, entity, key, value)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        return data["result"]
    return []

def get_entity(entity, key, value):
    url = "%s/%s" % (POPIT_ENDPOINT, entity)
    r = requests.get(url)
    data = r.json()
    result_list = []
    for entry in data["result"]:
        if entry.get(key) == value:
            result_list.append(entry)

    return result_list

if __name__ == "__main__":
    app.run(debug=True)