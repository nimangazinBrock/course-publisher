#!/usr/bin/env python
# encoding: utf-8
import json
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, request
from flask_cors import CORS

API_VERSION = '1.36'
AUTH_SERVICE = 'https://auth.brightspace.com/'
CONFIG_LOCATION = 'config.json'

def get_config():
    with open(CONFIG_LOCATION, 'r') as f:
        return json.load(f)


def put_config(config):
    with open(CONFIG_LOCATION, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)


def trade_in_refresh_token(config):
    response = requests.post(
        '{}/core/connect/token'.format(AUTH_SERVICE),
        # Content-Type 'application/x-www-form-urlencoded'
        data={
            'grant_type': 'refresh_token',
            'refresh_token': config['refresh_token'],
            'scope': 'orgunits:*:*'
        },
        auth=HTTPBasicAuth(config['client_id'], config['client_secret'])
    )
    return response.json()


def get_orgunit_details(org_unit_id, config, access_token):
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    endpoint = '{bspace_url}d2l/api/lp/{lp_version}/courses/{org_unit_id}'.format(
        bspace_url=config['bspace_url'],
        lp_version=API_VERSION,
        org_unit_id=org_unit_id
    )
    response = requests.get(endpoint, headers=headers)

    if response.status_code != 200:
        print(f"{endpoint} request did not succeed")

    return response


def put_orgunit_details(org_unit_id, body, config, access_token):
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    endpoint = '{bspace_url}/d2l/api/lp/{lp_version}/courses/{org_unit_id}'.format(
        bspace_url=config['bspace_url'],
        lp_version=API_VERSION,
        org_unit_id=org_unit_id
    )

    response = requests.put(endpoint, headers=headers, json=body)

    if response.status_code != 200:
        print(f"{endpoint} request did not succeed")
        response.raise_for_status()

    return response


app = Flask(__name__)
CORS(app)


@app.route('/publish', methods=['POST'])
def update_record():
    try:
        try:
            org_unit_id = request.json['id']
        except:
            raise ValueError
    except ValueError:
        return "Incorrect Ogr Unit Id", 400

    #get config parameters
    #call refresh token
    #update config parameters
    config = get_config()
    token_response = trade_in_refresh_token(config)
    config['refresh_token'] = token_response['refresh_token']
    print(token_response)
    put_config(config)

    # call get org unit details
    org_unit_details = get_orgunit_details(org_unit_id, config, token_response['access_token'])

    course_offering_info = {
        "Name": org_unit_details.json()["Name"],
        "Code": org_unit_details.json()["Code"],
        "StartDate": org_unit_details.json()["StartDate"],
        "EndDate": org_unit_details.json()["EndDate"],
        "IsActive": True,
        "Description": {
            "Content": org_unit_details.json()["Description"]["Html"],
            "Type": "Html"
        },
        "CanSelfRegister": org_unit_details.json()["CanSelfRegister"],
    }

    print(course_offering_info)

    #call update org unit details
    put_response = put_orgunit_details(org_unit_id, course_offering_info, config, token_response['access_token'])

    if put_response.status_code != 200:
        result = "error"
    else:
        result = "success"

    return result

#app.run()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
