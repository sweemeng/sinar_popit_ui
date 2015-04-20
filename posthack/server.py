__author__ = 'sweemeng'
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import make_response
from flask import Response
import json
import requests

"""
This is a hack for adding post. This will be replace with a proper frontend
"""

app = Flask(__name__)
POPIT_ENDPOINT = "https://sinar-malaysia.popit.mysociety.org/api/v0.1"
#POPIT_ENDPOINT = "http://localhost:3000/api"
API_KEY = "06b50c66ad47e99728b2b527de9db0429668da12"
headers = {"Apikey":API_KEY}

cache = {}


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

        r = requests.post(url, data=data, headers=headers,verify=False)

        del_list = []
        for key in cache:
            if url in key:
                del_list.append(key)

        for key in del_list:
            del cache[key]

        return str((r.status_code, r.content))

    return render_template("addpost.html", organization_id=organization_id)

@app.route("/search/<entity>")
def search(entity):
    key = "name"
    name = request.args.get("name")

    if not name:
        key = "label"
        name = request.args.get("label")
    if not name:
        return Response(json.dumps([]), mimetype="application/json")
    value = search_entity(entity, key, name)
    print value
    return Response(json.dumps(value), mimetype="application/json")

@app.route("/listorgs/")
def list_organizations():
    params = {}
    if request.args.get("page"):
        params["page"] = request.args.get("page")

    url =  "%s/%s" % (POPIT_ENDPOINT, "organizations")
    cache_key = str((url, params))
    if cache_key in cache:
        r = cache[cache_key]
    else:
        r = requests.get(url, params=params, verify=False)
        cache[cache_key] = r

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
            "role": request.form["role"],
            "person_id": request.form["person_id"],
            "post_id": request.form["post_id"],
            "organization_id": organizations_id,
            "start_date": request.form["start_date"],
        }
        if request.form["end_date"]:
            data["end_date"]  = request.form["end_date"]
        url = "%s/%s/" % (POPIT_ENDPOINT, "memberships")
        r = requests.post(url, headers=headers, data=data, verify=False)
        if r.status_code != 200:
            return r.content

        return r.content

    return render_template("post_memberships.html",
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
        primary_person = request.form["target_id"]
        secondary_person = request.form["source_id"]
        person_one = fetch_one_entity("persons", primary_person)
        person_two = fetch_one_entity("persons", secondary_person)

        for membership in person_two["memberships"]:
            data = {}

            data["role"] = membership["role"]
            data["person_id"] = primary_person
            data["organization_id"] = membership["organization_id"]
            data["post_id"] = membership["post_id"]
            data["start_date"] = membership["start_date"]
            if "end_data" in membership:
                data["end_date"] = membership["end_date"]
            url = "%s/%s" % (POPIT_ENDPOINT, "memberships")
            r = requests.post(url, headers=headers, data=data, verify=False)
            if r.status_code != 200:
                print r.content


        merge_url = "%s/persons/%s/merge/%s" % (POPIT_ENDPOINT, primary_person, secondary_person)
        print merge_url
        r =  requests.post(merge_url, headers=headers, verify=False)
        if r.status_code == 200:
            return "ok"
        person_url = "%s/%s" % (POPIT_ENDPOINT, "persons")
        if person_url in cache:
            del cache[person_url]
        first_person_url = "%s/%s" % (person_url, primary_person)
        if first_person_url in cache:
            del cache[first_person_url]
        second_person_url = "%s/%s" % (person_url, secondary_person)
        if second_person_url in cache:
            del cache[second_person_url]
        return str((r.status_code, r.content, r.reason))
        #return "OK"

    return render_template("mergeperson.html")

@app.route("/selectperson/", methods=["GET", "POST"])
def select_person_merge():
    params = {}
    if request.method.get("page",""):
        params["page"] = request.method.get("page")

    url = "%s/%s" % (POPIT_ENDPOINT, "persons")
    cache_key = str((url, params))
    if cache_key in cache:
        r = cache[cache_key]
    else:
        r = requests.get(url, params=params, verify=False)
        cache[cache_key] = r
    data = r.json()
    persons =  data["result"]
    return data["result"]

@app.route("/deletemembership/<person_id>", methods=["POST", "GET"])
def delete_post(person_id):
    if request.method == "POST":
        requests.delete(request.form["membership"], verify=False)
        return "Done"

    person = fetch_one_entity("persons", person_id)
    return render_template("person_membership.html", person=person)

@app.route("/deletepostmembership/<post_id>", methods=["POST", "GET"])
def delete_post_membership(post_id):
    if request.method ==  "POST":
        requests.delete(request.form["membership"], verify=False)
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
    cache_key = str((post_url, params))
    if cache_key in cache:
        r = cache[cache_key]
    else:
        r = requests.get(post_url, params=params, verify=False)
        cache[cache_key] = r

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
    cache_key = str((person_url, params))
    if cache_key in cache:
        r = cache[cache_key]
    else:
        r = requests.get(person_url, params=params, verify=False)
        cache[cache_key] = r
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
    if url in cache:
        r = cache[url]
    else:
        r = requests.get(url, verify=False)
        cache[url] = r
    if r.status_code == 200:
        data = r.json()
        return data["result"]

    return []

def fetch_entity(entity_type):
    url = "%s/%s" % (POPIT_ENDPOINT, entity_type)
    if url in cache:
        r = cache[url]
    else:
        r = requests.get(url, headers=headers, verify=False)
        cache[url] = r

    if r.status_code == 200:
        data = r.json()
        return data["result"]
    return []

# This is only used in merging user, don't cache as the result will change
def search_entity(entity, key, value):
    url = "%s/search/%s?q=%s:%s" % (POPIT_ENDPOINT, entity, key, value)
    r = requests.get(url, headers=headers, verify=False)
    if r.status_code == 200:
        data = r.json()
        return data["result"]
    return []

def get_entity(entity, key, value):
    url = "%s/%s" % (POPIT_ENDPOINT, entity)
    if url in cache:
        r = cache[url]
    else:
        r = requests.get(url, verify=False)
        cache[url] = r
    data = r.json()
    result_list = []
    for entry in data["result"]:
        if entry.get(key) == value:
            result_list.append(entry)

    return result_list

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
