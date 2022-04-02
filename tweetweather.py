# import requests
# # This is a sample Python script.
#
# # Press ⌃R to execute it or replace it with your code.
# # Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
# import requests
# import requests_oauthlib
# # def get_tweet(name):
# #     # Use a breakpoint in the code line below to debug your script.
# #     print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.
#
#
# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#
#     get_endpoint = "https://api.twitter.com/2/tweets/440322224407314432?expansions=attachments.media_keys,author_id"
#
#
#
#     # TODO: abstract to config file, remove from repo
#     my_headers = {f'Authorization': f'Bearer {bearer_token}'}
#     response = requests.get(get_endpoint, headers=my_headers)
#
#     print(response)
#     print(response.content)

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
# bearer_token = os.environ.get("BEARER_TOKEN")
from datetime import datetime

import requests
import os
import json

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
# bearer_token = os.environ.get("BEARER_TOKEN")
bearer_token = "AAAAAAAAAAAAAAAAAAAAAIxcawEAAAAA9gyCYhkWb2BQ2Mp5tVQltjIpneU%3DbfnRngdlgXK8vzn79NKQopvVoqWJ3NsbwM5MKVV3V7V7Z2POYi"
WEATHER_API_KEY = "991db1f58950453daea225235222803"
# has:geo
url = "https://api.twitter.com/2/tweets/sample/stream?expansions=geo.place_id"

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_rules():

    # determine if any rules currently exists
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):

    # if rules have not been found, move on
    if rules is None or "data" not in rules:
        return None

    # else, delete any rules that already exist before we set new ones
    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(delete):
    # set the filtering rules on which tweets to be pulled into the stream
    rules = [
        # TODO use the more straightforward has:geo tag in when upgraded from Sandbox developer level
        # {"value": "twitter data has:geo"}
    ]
    # post the rules to the endpoint
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream(set):

    # open to tweet sample stream
    response = requests.get(
        url,
        auth=bearer_oauth,
        stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )

    # iterate over stream of results from twitter feed to filter those with a location only
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)

            # verify that returned data has a geotag location
            if json_response['data']['geo'] != {}:
                print(json.dumps(json_response, indent=4, sort_keys=True))


class Weather:
    def __init__(self, location: str, country: str, temperature_f: float, last_updated: datetime):
        self.location = location
        self.country = country
        self.temperature_f = temperature_f
        self.last_updated = last_updated


def get_weather(lat, long) -> Weather:
    request_url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{long}"
    response = requests.get(request_url)
    if response.status_code != 200:
        raise Exception(
            "Cannot get weather from weatherapi.com (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )

    # convert string response to a dict
    resource = json.loads(response.text)

    # unpack the important parts of the json resource (note: can limit the amount of fields returned at
    # https://www.weatherapi.com/my/ )
    location = resource['location']['name']
    country = resource['location']['country']
    temperatue_f = resource['current']['temp_f']
    last_updated_epoch = resource['current']['last_updated_epoch']
    last_updated = datetime.fromtimestamp(last_updated_epoch)

    return Weather(location, country, temperatue_f, last_updated)



def main():
    # get, clear existing, and set any new rules
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)

    # start the stream of sample tweets
    get_stream(set)

if __name__ == "__main__":
    main()