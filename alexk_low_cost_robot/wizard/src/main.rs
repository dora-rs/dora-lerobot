use clap::Parser;
use rustypot::device::{xl330, xl430};
use std::time::Duration;

use rustypot::DynamixelSerialIO;

use serialport::{SerialPort, SerialPortBuilder};

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

        pos.iter()
            .map(|&x| read_i32_angle(x))
            .collect::<Vec<_>>()
    } else {
        // x430 for 2 first and xl330 for the rest

        let mut pos = xl430::sync_read_present_position(&io, serial_port, &[0, 1])
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
    if puppet {
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
    mode: &[u8; 6],
) {
    if puppet {
        xl330::sync_write_drive_mode(&io, serial_port, &[0, 1, 2, 3, 4, 5], mode)
            .expect("Communication error");
    } else {
        xl430::sync_write_drive_mode(&io, serial_port, &[0, 1], &mode[0..2])
            .expect("Communication error");

        xl330::sync_write_drive_mode(&io, serial_port, &[2, 3, 4, 5], &mode[2..6])
            .expect("Communication error");
    }
}

fn get_correction(rounded_position: &Vec<i32>, inverted: &[bool; 6]) -> Vec<i32> {
    let suited = suited();

    return vec![0; 6];
}

fn suited() -> Vec<i32> {
    return vec![0; 6];
}

fn prepare_configuration(io: &DynamixelSerialIO, serial_port: &mut dyn SerialPort, puppet: bool) {
    xl330::sync_write_torque_enable(&io, serial_port, &[2, 3, 4, 5], &[0; 4])
        .expect("Communication error");

    // Now we enable all modes to "position extended"

    xl330::sync_write_operating_mode(&io, serial_port, &[2, 3, 4, 5], &[4; 4])
        .expect("Communication error");

    if !puppet {
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
}

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

fn invert(pos: &Vec<i32>, inverted: &[bool; 6]) -> Vec<i32> {
    pos.iter()
        .enumerate()
        .map(|(i, &x)| if inverted[i] { x } else { -x })
        .collect::<Vec<_>>()
}

fn configure_homing(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    inverted: &[bool; 6],
    puppet: bool,
) {
    println!("------Configuring homing");

    prepare_configuration(io, serial_port, puppet);

    // set homing position to 0 for all servos (if puppet, 0-5 with xl330, if master, 0-1 with xl430 and 2-5 with xl330)
    set_homing(io, serial_port, puppet, &vec![0; 6]);

    // get current positions
    let pos = get_positions(io, serial_port, puppet);

    // get nearest rounded positions

    let nearest_rounded = get_nearest_rounded_positions(&pos);

    // get correction

    let correction = get_correction(&nearest_rounded, inverted);

    // set homing position to nearest rounded positions

    set_homing(io, serial_port, puppet, &correction);
}

fn configure_drive_mode(
    io: &DynamixelSerialIO,
    serial_port: &mut dyn SerialPort,
    puppet: bool,
) -> [bool; 6] {
    println!("------Configuring drive mode");

    prepare_configuration(io, serial_port, puppet);

    return [false; 6];
}

fn main() {
    let cli = Cli::parse();

    let mut serial_port = serialport::new(cli.port, 1_000_000)
        .timeout(Duration::from_millis(200))
        .open()
        .expect("Failed to open port");

    let io = DynamixelSerialIO::v2();

    let puppet = cli.puppet || !cli.master;

    println!(
        "Starting configuring {} arm!",
        if puppet { "puppet" } else { "master" }
    );

    println!("Place the arm in position 1, as shown in the README image");
    pause();

    configure_homing(
        &io,
        serial_port.as_mut(),
        &[false, false, false, false, false, false],
        puppet,
    );

    set_drive_mode(&io, serial_port.as_mut(), puppet, &[0; 6]);

    println!("Place the arm in position 2, as shown in the README image");
    pause();

    let invert = configure_drive_mode(&io, serial_port.as_mut(), puppet);

    println!("Place the arm back in position 1, as shown in the README image");
    pause();

    configure_homing(&io, serial_port.as_mut(), &invert, puppet);

    println!("Configuration done!");
}
