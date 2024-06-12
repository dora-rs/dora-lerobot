from reachy_sdk import ReachySDK

reachy = ReachySDK("10.42.0.124")

reachy.turn_on("reachy")


reachy.turn_off_smoothly("reachy")
