
# TODO use the more straightforward has:geo tag in when upgraded from Sandbox developer level- link to code
# {"value": "twitter data has:geo"}


from datetime import datetime
import json
import requests as requests

# bearer_token = os.environ.get("BEARER_TOKEN")

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAIxcawEAAAAA9gyCYhkWb2BQ2Mp5tVQltjIpneU%3DbfnRngdlgXK8vzn79NKQopvVoqWJ3NsbwM5MKVV3V7V7Z2POYi"
WEATHER_API_KEY = "991db1f58950453daea225235222803"
TWITTER_BASE_URL = "https://api.twitter.com"
TWITTER_SAMPLE_PATH = "/2/tweets/sample/stream?expansions=geo.place_id"
TWITTER_LOCATION_PATH = "/2/tweets/"



class Weather:
    def __init__(self, location: str, country: str, temperature_f: float, last_updated: datetime):
        self.location = location
        self.country = country
        self.temperature_f = temperature_f
        self.last_updated = last_updated


class TweetLatLong:
    def __init__(self, timestamp: datetime, lat: float, long: float):
        self.timestamp = timestamp
        self.lat = lat
        self.long = long


class Integrations:

    def get_weather(self, lat, long) -> Weather:
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

    def twitter_bearer_oauth(self, r):
        """
        Method required by bearer token authentication.
        """

        r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
        r.headers["User-Agent"] = "v2FilteredStreamPython"
        return r

    def twitter_bearer_oauth_tweet(self, r):
        """
        Method required by bearer token authentication.
        """

        r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
        r.headers["User-Agent"] = "v2TweetLookupPython"
        return r

    def stream_twitter_locations(self):

        # open to tweet sample stream
        response = requests.get(
            TWITTER_BASE_URL + TWITTER_SAMPLE_PATH,
            # auth=self.twitter_bearer_oauth(auth_type="v2FilteredStreamPython", r = None),
            auth=self.twitter_bearer_oauth,
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
                    # print(json.dumps(json_response, indent=4, sort_keys=True))
                    tweet_id = json_response['data']['id']

                    enrichment_request_url = f"https://api.twitter.com/2/tweets/{tweet_id}?expansions=geo.place_id&place.fields=full_name,geo,id,place_type"

                    # enrichment_request_url = TWITTER_BASE_URL + TWITTER_LOCATION_PATH + f':{place_id}.json'
                    enrichment_response = requests.get(
                        enrichment_request_url,
                        auth=self.twitter_bearer_oauth_tweet,
                    )

                    print(json.loads(enrichment_response.text))


def main():

    k = 5 # TODO move this to user input

    # start the stream of sample tweets
    integrations = Integrations()
    integrations.stream_twitter_locations()

if __name__ == "__main__":
    main()