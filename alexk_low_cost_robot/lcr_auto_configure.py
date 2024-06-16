"""
LCR Auto Configure: This program is used to automatically configure the Low Cost Robot (LCR) for the user.

The program will:
1. Disable all torque motors of provided LCR.
2. Ask the user to move the LCR to the position 1 (see CONFIGURING.md for more details).
3. Record the position of the LCR.
4. Ask the user to move the LCR to the position 2 (see CONFIGURING.md for more details).
5. Record the position of the LCR.
6. Ask the user to move back the LCR to the position 1.
7. Record the position of the LCR.
8. Calculate the offset of the LCR and save it to the configuration file.

It will also enable all appropriate operating modes for the LCR according if the LCR is a puppet or a master.
"""