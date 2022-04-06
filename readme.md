# TwitterWeather
### introduction
This is a learning project for creating a stream of tweet data and accompanying temperatures from the tweet locations.
A running average is also calculated for each tweet location based on a configurable integer of the last "k" tweets

# functionality
Starting the program from the command line and inputting a configuration will connect to the Twitter 1% sample rate 
stream, and for each tweet that has a location included, will use weatherapi.com to determine the last known temperature
for that location. 

Two streaming results files are persisted to the local environment. The first "tweet_weather_stream" has the location
and weather for each tweet. The second, "tweet_weather_average" contains the rolling average of the last "k" measurements
of that location. If there are less than k tweets for a location, then all current measurements for that location are used
for the rolling average. 

# prerequisites:
python 3.x

# Set Environment Variables
Auth tokens need to be obtained by registering for the twitter developer API and the weatherapi.com API. Once those auth
tokens are known, those variables van be set in your terminal by running the following:
```bash
$ export 'BEARER_TOKEN'='<your_bearer_token>'
$ export 'WEATHER_API_TOKEN'='<your_weather_token>'
```

# how to configure and launch application
Navigate to the root directory of `tweetweather` and create a virtual environment with
```bash
$ python3 -m venv venv
```

Then activate the venv:
```bash
$ . venv/bin/activate
```

Install requirements to your venv:
```bash
$ pip install -r requirements.txt
```

Start the application by running:
```bash
$ python3 tweetweather.py <k>
```
where k is an integer representing the number of measurements to use in a rolling average temperature. If this is not 
included, k will default to 5.

# Assumptions
1. The human readable location name of the tweet and corresponding name from the weather api often differ. 
The results will defer to the weather api's location.
2. No tweet data was returning from the stream with polygons, bboxs, coordinates. Thus all tweets are sent to the 
get tweets end point which means that all tweets will come back as a bbox or a point. Polygon has been ignored for now.

### future work:
- Break up api calls into separate functions and stream data to queues for each of these api calls, such that each api call
can be reactive and scaled horizontally if needed.
- Deploy service with an encrypted config file (Sealed secrets eg) containing auth tokens for APIs
- Add fault tolerance for API calls - backoff tolerance
- Use the more straightforward has:geo tag in streaming call in when upgraded from Sandbox developer level instead of
pulling back all tweets and programmatically filtering for tweets with locations.
- The lookup by tweet endpoint supports multiple tweetids, so we could batch our enrichment requests to make less calls. 
