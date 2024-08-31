from dora import Node
import pyarrow as pa

node = Node()


def get_number_in_text(text: str) -> int:
    if "1" in text or "one" in text:
        return 1
    elif "2" in text or "two" in text:
        return 2
    elif "3" in text or "three" in text:
        return 3
    elif "4" in text or "four" in text:
        return 4
    elif "5" in text or "five" in text:
        return 5
    elif "6" in text or "six" in text:
        return 6
    elif "7" in text or "seven" in text:
        return 7
    elif "8" in text or "eight" in text:
        return 8
    elif "9" in text or "nine" in text:
        return 9
    elif "10" in text or "ten" in text:
        return 10
    else:
        return 1


for event in node:
    if event["type"] == "INPUT":
        if event["id"] == "keyboard":
            char = event["value"][0].as_py()

            if char == "w":
                node.send_output("movec", pa.array([-0.02, 0, 0, 0, 0, 0, 0.1]))
            elif char == "s":
                node.send_output("movec", pa.array([0.02, 0, 0, 0, 0, 0, 0.1]))
            elif char == "c":
                node.send_output("go_to", pa.array([" home"]))
            elif char == "a":
                node.send_output("movec", pa.array([0, -0.02, 0, 0, 0, 0, 0.1]))
            elif char == "d":
                node.send_output("movec", pa.array([0, 0.02, 0, 0, 0, 0, 0.1]))
            elif char == "e":
                node.send_output("movec", pa.array([0, 0, 0.02, 0, 0, 0, 0.1]))
            elif char == "q":
                node.send_output("movec", pa.array([0, 0, -0.02, 0, 0, 0, 0.1]))
            elif char == "t":
                node.send_output("claw", pa.array([0]))
            elif char == "r":
                node.send_output("claw", pa.array([100]))
            elif char == "6":
                node.send_output("movej", pa.array([0, 0, 0, 0, -0.1, 0, 0.1]))
            elif char == "4":
                node.send_output("movej", pa.array([0, 0, 0, 0, 0.1, 0, 0.1]))
            elif char == "3":
                node.send_output("movej", pa.array([-0.1, 0, 0, 0, 0, 0, 0.1]))
            elif char == "1":
                node.send_output("movej", pa.array([0.1, 0, 0, 0, 0, 0, 0.1]))
            elif char == "8":
                node.send_output("movej", pa.array([0, 0, 0, -0.1, 0, 0, 0.1]))
            elif char == "2":
                node.send_output("movej", pa.array([0, 0, 0, 0.1, 0, 0, 0.1]))
            elif char == "7":
                node.send_output("movej", pa.array([0, 0, 0, 0, 0, 0.1, 0.1]))
            elif char == "9":
                node.send_output("movej", pa.array([0, 0, 0, 0, 0, -0.1, 0.1]))
            elif char == "x":
                node.send_output("stop", pa.array([]))
        elif event["id"] == "text" or event["id"] == "key_interpolation":
            text = event["value"][0].as_py().lower()
            text = text.replace(".", "")
            number = get_number_in_text(text)
            distance = 0.03 * number
            rotation = 0.2 * number
            t = 0.1 * number
            turning = "turning" in text

            if "forward" in text and not turning:
                node.send_output("movec", pa.array([-distance, 0, 0, 0, 0, 0, t]))
            elif "back" in text and not turning:
                node.send_output("movec", pa.array([distance, 0, 0, 0, 0, 0, t]))
            elif "right" in text and not turning:
                node.send_output("movec", pa.array([0, -distance, 0, 0, 0, 0, t]))
            elif "left" in text and not turning:
                node.send_output("movec", pa.array([0, distance, 0, 0, 0, 0, t]))
            elif "up" in text and not turning:
                node.send_output("movec", pa.array([0, 0, distance, 0, 0, 0, t]))
            elif "down" in text and not turning:
                node.send_output("movec", pa.array([0, 0, -distance, 0, 0, 0, t]))
            elif "close" in text:
                node.send_output("claw", pa.array([0]))
            elif "open" in text:
                node.send_output("claw", pa.array([100]))
            elif "right" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, 0, -rotation, 0, t]))
            elif "left" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, 0, rotation, 0, t]))
            elif "up" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, -rotation, 0, 0, t]))
            elif "down" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, rotation, 0, 0, t]))
            elif "backward" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, 0, 0, rotation, t]))
            elif "forward" in text and turning:
                node.send_output("movej", pa.array([0, 0, 0, 0, 0, -rotation, t]))
            elif "stop" in text:
                node.send_output("stop", pa.array([]))
            elif "saving" in text:
                node.send_output("save", pa.array([text.replace("saving ", "")]))
            elif "recording" in text:
                node.send_output("record", pa.array([text.replace("recording ", "")]))
            elif "cut" in text:
                node.send_output("cut", pa.array([text]))
            elif "playing" in text:
                node.send_output("play", pa.array([text.replace("playing ", "")]))
            elif "go " in text:
                node.send_output("go_to", pa.array([text.replace("go ", "")]))
            elif "end of teaching" in text:
                node.send_output("end_teach", pa.array([text]))
            elif "teaching" in text:
                node.send_output("teach", pa.array([text]))
