use clap::Parser;
use rustypot::device::{xl330, xl430};
use std::time::Duration;

use rustypot::DynamixelSerialIO;

use serialport::SerialPort;

use std::io::{stdin, stdout, Read, Write};

// Import necessary traits and macros for command line parsing and debugging
#[derive(Parser, Debug)]
// Define the structure for command line arguments with meta information
#[clap(author, version, about, long_about = None)]
pub struct Cli {
    // Define a command line argument for 'port'
    // This argument is specified using '--port' and expects a String value representing the serial port on which the Dynamixel servos are connected
    #[clap(long)]
    pub port: String,

    // Define a command line flag for 'puppet'
    // This flag is specified using '--puppet' and is a boolean (true if present). Add this flag if you're configuring the puppet arm
    #[clap(long, action)]
    pub puppet: bool,

    // Define a command line flag for 'master'
    // This flag is specified using '--master' and is a boolean (true if present). Add this flag if you're configuring the master arm
    #[clap(long, action)]
    pub master: bool,
    // You can not configure both arms at the same time, you must choose one, configure it and then run the program again to configure the other arm
}

// The pause function is used to pause the program and wait for the user to press Enter before continuing
// This way the user can take the time to place the arm in the correct position before continuing
fn pause() {
    let mut stdout = stdout();
    stdout.write(b"Press Enter to continue...").unwrap();
    stdout.flush().unwrap();
    stdin().read(&mut [0]).unwrap();
}

// The angle retrieved from "ReadPosition' is a 32-bit unsigned integer, but we need to convert it to a 32-bit signed integer to represent positive and negative angle values
fn read_i32_angle(angle: u32) -> i32 {
    if angle < i32::MAX as u32 {
        angle as i32
    } else {
        -((u32::MAX - angle) as i32)
    }
}

// The get_positions function is used to retrieve the current position of the servos in the arm, we
// check if the arm is a puppet or master arm and then read the present position of the servos with appropriate API (XL330 or XL430)
fn get_positions(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    puppet: bool,
) -> Vec<i32> {
    let pos = if !puppet {
        let pos = xl330::sync_read_present_position(&io, serial_port, &[0, 1, 2, 3, 4, 5])
            .expect("Read Communication error");

        pos.iter().map(|&x| read_i32_angle(x)).collect::<Vec<_>>()
    } else {
        // x430 for 2 first and xl330 for the rest

        let pos = xl430::sync_read_present_position(&io, serial_port, &[0, 1])
            .expect("Read Communication error");

        let pos2 = xl330::sync_read_present_position(&io, serial_port, &[2, 3, 4, 5])
            .expect("Read Communication error");

        pos.iter()
            .chain(pos2.iter())
            .map(|&x| read_i32_angle(x))
            .collect::<Vec<_>>()
    };

    pos
}

// This function is used to set an offset value that lets you manipulate more friendly angles (e.g. 0 to 360 degrees) instead of the raw values
fn set_homing(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    puppet: bool,
    pos: &Vec<i32>,
) {
    if !puppet {
        xl330::sync_write_homing_offset(&io, serial_port, &[0, 1, 2, 3, 4, 5], &pos)
            .expect("Communication error");
    } else {
        xl430::sync_write_homing_offset(&io, serial_port, &[0, 1], &pos[0..2])
            .expect("Communication error");

        xl330::sync_write_homing_offset(&io, serial_port, &[2, 3, 4, 5], &pos[2..6])
            .expect("Communication error");
    }
}

// This function is used to set the drive mode of the servos, which determines how the servos "count" the position values.
// It is important to set the drive mode correctly to ensure that the servos move correctly and in the desired direction.
fn set_drive_mode(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    puppet: bool,
    mode: &Vec<bool>,
) {
    let mode = mode
        .iter()
        .map(|&x| if x { 1 } else { 0 })
        .collect::<Vec<_>>();

    if !puppet {
        xl330::sync_write_drive_mode(&io, serial_port, &[0, 1, 2, 3, 4, 5], &mode)
            .expect("Communication error");
    } else {
        xl430::sync_write_drive_mode(&io, serial_port, &[0, 1], &mode[0..2])
            .expect("Communication error");

        xl330::sync_write_drive_mode(&io, serial_port, &[2, 3, 4, 5], &mode[2..6])
            .expect("Communication error");
    }
}

// The correction function calculates the correction needed to adjust the homing position of the servos regarding wanted positions
fn get_correction(pos: &Vec<i32>, inverted: &Vec<bool>) -> Vec<i32> {
    let wanted = wanted_pos1();

    let mut correction = invert(pos, inverted);

    for i in 0..6 {
        if inverted[i] {
            correction[i] -= wanted[i];
        } else {
            correction[i] += wanted[i];
        }
    }

    return correction;
}

// The present position wanted in position 1 for the arm
fn wanted_pos1() -> Vec<i32> {
    return vec![0, 0, 1024, 0, -1024, 0];
}

// The present position wanted in position 2 for the arm
fn wanted_pos2() -> Vec<i32> {
    return vec![1024, 1024, 0, -1024, 0, 1024];
}

fn prepare_configuration(io: &DynamixelSerialIO, serial_port: &mut dyn SerialPort, puppet: bool) {
    // To be configured, all servos must be in "torque disable" mode
    xl330::sync_write_torque_enable(&io, serial_port, &[2, 3, 4, 5], &[0; 4])
        .expect("Communication error");

    // We need to work with 'extended position mode' (4) for all servos, because in joint mode (1) the servos can't rotate more than 360 degrees (from 0 to 4095)
    // And some mistake can happen while assembling the arm, you could end up with a servo with a position 0 or 4095 at a crucial point
    // See [https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/#operating-mode11]
    xl330::sync_write_operating_mode(&io, serial_port, &[2, 3, 4, 5], &[4; 4])
        .expect("Communication error");

    if puppet {
        xl330::sync_write_torque_enable(&io, serial_port, &[0, 1], &[0; 2])
            .expect("Communication error");

        xl330::sync_write_operating_mode(&io, serial_port, &[0, 1], &[4; 2])
            .expect("Communication error");
    } else {
        xl430::sync_write_torque_enable(&io, serial_port, &[0, 1], &[0; 2])
            .expect("Communication error");

        xl430::sync_write_operating_mode(&io, serial_port, &[0, 1], &[4; 2])
            .expect("Communication error");
    }

    set_drive_mode(io, serial_port, puppet, &vec![false; 6]);
    set_homing(io, serial_port, puppet, &vec![0; 6]);
}

// To register position during the process we need to know approximately in which position the arm is
fn get_nearest_rounded_positions(pos: &Vec<i32>) -> Vec<i32> {
    pos.iter()
        .map(|&x| {
            if x >= 0 {
                let k = x / 1024;
                if x % 1024 > 512 {
                    (k + 1) * 1024
                } else {
                    k * 1024
                }
            } else {
                let k = (-x) / 1024;
                if (-x) % 1024 > 512 {
                    -(k + 1) * 1024
                } else {
                    -k * 1024
                }
            }
        })
        .collect::<Vec<_>>()
}

// useful function to invert the mode of the servos
fn invert(pos: &Vec<i32>, inverted: &Vec<bool>) -> Vec<i32> {
    pos.iter()
        .enumerate()
        .map(|(i, &x)| if inverted[i] { x } else { -x })
        .collect::<Vec<_>>()
}

fn configure_homing(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    inverted: &Vec<bool>,
    puppet: bool,
) {
    println!("------Configuring homing");

    // set homing position to 0 for all servos
    set_homing(io, serial_port, puppet, &vec![0; 6]);

    // get current positions
    let pos = get_positions(io, serial_port, puppet);

    // get nearest rounded positions
    let nearest_rounded = get_nearest_rounded_positions(&pos);

    // get correction
    let correction = get_correction(&nearest_rounded, inverted);

    // set homing position
    set_homing(io, serial_port, puppet, &correction);

    let pos = get_positions(io, serial_port, puppet);
}

fn configure_drive_mode(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    puppet: bool,
) -> Vec<bool> {
    println!("------Configuring drive mode");

    // get current positions
    let pos = get_positions(io, serial_port, puppet);

    // get nearest rounded positions
    let nearest_rounded = get_nearest_rounded_positions(&pos);

    // if a position of a servo is not exactly the one wanted for position2, we need to invert the mode of this servo by setting the drive mode to 1
    let inverted = nearest_rounded
        .iter()
        .zip(wanted_pos2().iter())
        .map(|(x, y)| x != y)
        .collect::<Vec<_>>();

    set_drive_mode(io, serial_port, puppet, &inverted);

    return inverted;
}

fn main() {
    let cli = Cli::parse();

    let mut serial_port = serialport::new(cli.port, 1_000_000)
        .timeout(Duration::from_secs(5))
        .open()
        .expect("Failed to open port");

    let io = DynamixelSerialIO::v2();

    let puppet = cli.puppet || !cli.master;

    println!(
        "Starting configuring {} arm!",
        if puppet { "puppet" } else { "master" }
    );

    // Reset all parameters to default values
    prepare_configuration(&io, serial_port.as_mut(), puppet);

    println!("Place the arm in position 1, as shown in the README image");
    pause();

    // Configure a first homing try, assuming all servos are in the right direction
    configure_homing(
        &io,
        serial_port.as_mut(),
        &vec![false, false, false, false, false, false],
        puppet,
    );

    println!("Place the arm in position 2, as shown in the README image");
    pause();

    // Check what servos need to be inverted in this configuration
    let inverted = configure_drive_mode(&io, serial_port.as_mut(), puppet);

    println!("Place the arm back in position 1, as shown in the README image");
    pause();

    // Reconfigure homing with the correct inverted servos
    configure_homing(&io, serial_port.as_mut(), &inverted, puppet);

    println!("Configuration done!");
    println!("Make sure everything is working as expected by moving the arm and checking the position values :");
    pause();

    loop {
        let pos = get_positions(&io, serial_port.as_mut(), puppet);

        println!("{:?}", pos);

        std::thread::sleep(Duration::from_secs(2));
    }
}
