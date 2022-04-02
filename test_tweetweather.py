import unittest
from tweetweather import *


class TestMethods(unittest.TestCase):
    # @unittest.skip("this test hits an external endpoint w/ rate limiting")
    def test_get_weather_when_valid_returns_weather_object(self):

        # ARRANGE
        lat, long = 48.8567, 2.3508
        # Note location for this test is inconsistently returning as paris OR st merri
        expected_location = "Saint-Merri" 
        expected_country = "France"

        # ACT
        test = Integrations()
        result = test.get_weather(lat=lat, long=long)

        # ASSERT
        self.assertEqual(expected_country, result.country)
        self.assertEqual(expected_location, result.location)

        # check that weather is in a reasonable range
        self.assertTrue(-100 < result.temperature_f < 200)

        # verify that weather was last updated in the past
        self.assertLess(result.last_updated, datetime.now())




