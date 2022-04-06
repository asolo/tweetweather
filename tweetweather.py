from datetime import datetime
import json
import os
import requests as requests
import sys

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")


TWITTER_BASE_URL = "https://api.twitter.com"
TWITTER_SAMPLE_PATH = "/2/tweets/sample/stream?expansions=geo.place_id"
TWITTER_TWEET_PATH = "/2/tweets/"
TWITTER_EXPANSIONS = "?expansions=geo.place_id&place.fields=full_name,geo,id,place_type"
STREAM_OUTPUT_FILE = "data/tweet_weather_stream.txt"
AVERAGE_OUTPUT_FILE = "data/tweet_weather_average.txt"

# todo implement a real cache like redis, or persist to DB to avoid memory exceptions
CACHE_OF_TEMPS = {}


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

    @staticmethod
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

    @staticmethod
    def twitter_bearer_oauth(r):
        """
        Method required by bearer token authentication.
        """

        r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
        r.headers["User-Agent"] = "v2FilteredStreamPython"
        return r

    # todo combine repeated code
    @staticmethod
    def twitter_bearer_oauth_tweet( r):
        """
        Method required by bearer token authentication.
        """

        r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
        r.headers["User-Agent"] = "v2TweetLookupPython"
        return r

    def stream_twitter_locations(self, k: int) -> None:

        # clean up an existing files
        if os.path.exists(STREAM_OUTPUT_FILE):
            os.remove(STREAM_OUTPUT_FILE)

        if os.path.exists(AVERAGE_OUTPUT_FILE):
            os.remove(AVERAGE_OUTPUT_FILE)

        # Open two files in write mode
        with open(STREAM_OUTPUT_FILE, "w") as writer_stream:
            with open(AVERAGE_OUTPUT_FILE, "w") as writer_avg:
                # write the headers for the output files

                # Todo: for twitter connections add an exponential back off to handle errors like code 429
                # open to tweet sample stream
                response = requests.get(
                    TWITTER_BASE_URL + TWITTER_SAMPLE_PATH,
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

                line_count = 0
                # iterate over stream of results from twitter feed to filter those with a location only
                for response_line in response.iter_lines():
                    if response_line:
                        json_response = json.loads(response_line)

                        # verify that returned data has a geotag location
                        if json_response['data']['geo'] != {}:
                            tweet_id = json_response['data']['id']

                            # todo: future improvement: can we batch our enrichment requests
                            enrichment_request_url = TWITTER_BASE_URL + TWITTER_TWEET_PATH \
                                                     + str(tweet_id) + TWITTER_EXPANSIONS

                            enrichment_response = requests.get(
                                enrichment_request_url,
                                auth=self.twitter_bearer_oauth_tweet,
                            )

                            # todo future improvement: gracefully handle some failures, and continue with new requests.
                            if enrichment_response.status_code != 200:
                                raise Exception(
                                    "Request returned an error: {} {}".format(
                                        response.status_code, response.text
                                    )
                                )

                            enriched_tweet = json.loads(enrichment_response.text)
                            tweet_geo = enriched_tweet["includes"]["places"][0]["geo"]

                            # does this tweet have point or a bbox
                            if tweet_geo["type"] == "Feature":
                                bbox_coords = tweet_geo["bbox"]

                                # get the centroid
                                long = round((bbox_coords[0]+bbox_coords[2])/2,7)
                                lat = round((bbox_coords[1]+bbox_coords[3])/2,7)

                            elif tweet_geo["type"] == "Point":

                                # format for return is [Longigtude, Latitude]
                                [long, lat] = tweet_geo["Coordinates"]

                            # todo future work support a polygon object or V1 BBOX
                            else:
                                raise Exception(
                                    "Request geo type is not supported"
                                    )

                            # call the weather API
                            weather = self.get_weather(lat=lat, long=long)

                            # create result line for streaming file
                            line_weather_stream = f"Tweet Location: {weather.location} - {weather.country},"\
                                    + f"temp_f: {weather.temperature_f}, last_updated: {weather.last_updated}\n"

                            # Write a line at the end of the file.
                            writer_stream.write(line_weather_stream)

                            # update the cache
                            if weather.location in CACHE_OF_TEMPS:
                                temps_array = CACHE_OF_TEMPS[weather.location]

                                # bump a temp if we are at the max
                                if len(temps_array) == k:
                                    print("pop off")
                                    temps_array.pop(0)

                                # add the newest temp to the other end
                                temps_array.append(weather.temperature_f)

                                # update the cache
                                CACHE_OF_TEMPS[weather.location] = temps_array
                            else:
                                # if location not already in the cahce, initialize it with a new array
                                temps_array = [weather.temperature_f]
                                CACHE_OF_TEMPS[weather.location] = temps_array

                            number_of_data_points = len(temps_array)
                            average_temp = sum(temps_array)/len(temps_array)

                            line_weather_average = f"Tweet Location: {weather.location} - {weather.country},"\
                                    + f"rolling_avg_temp_f: {average_temp}, last_updated: {weather.last_updated}, "\
                                    + f"number_of_data_points: {number_of_data_points}\n"

                            # write rolling average value cache to streaming file 2
                            writer_avg.write(line_weather_average)

                            # print a status every 10 lines
                            if line_count % 10 == 0:
                                print(f"{line_count} lines streamed so far. use ctrl+c to stop stream")

                            line_count +=1


def main():

    # check if k has been configured from command line
    if len(sys.argv) == 1:
        # set a default value of k if not set
        k = 5
        print("k is set to default", k)
    else:
        k = sys.argv[1]
        print("k is configured:", k)

    # start the stream of sample tweets
    integrations = Integrations()
    integrations.stream_twitter_locations(k=k)


if __name__ == "__main__":
    main()