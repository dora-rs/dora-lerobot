from reachy_sdk import ReachySDK

reachy = ReachySDK("10.42.0.24")  # , with_mobile_base=True)


reachy.turn_on("reachy")

# reachy.mobile_base.goto(0.1, 0, 0)

reachy.turn_off_smoothly("reachy")
