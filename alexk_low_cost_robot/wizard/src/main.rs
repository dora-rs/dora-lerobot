use std::time::Duration;
use clap::Parser;
use rustypot::device::{xl330, xl430};
use rustypot::DynamixelSerialIO;
use serialport::SerialPort; // 4.2.7

#[derive(Parser, Debug)]
#[clap(author, version, about, long_about = None)]
pub struct Cli {
    #[clap(
        long, value_delimiter = ' ', num_args = 1.., default_value = "false false false false false false"
    )]
    pub inverted: Vec<bool>,

    #[clap(long, action)]
    pub homing: bool,

    #[clap(long, action)]
    pub drive: bool,

    #[clap(long)]
    pub port: String,

    #[clap(long, action)]
    pub puppet: bool,
}


fn convert_to_extended_mode(angle: u32) -> i32 {
    if angle < i32::MAX as u32 {
        angle as i32
    } else {
        -((u32::MAX - angle) as i32)
    }
}

fn get_positions(io: &DynamixelSerialIO, serial_port: &mut dyn SerialPort, puppet: bool) -> Vec<i32> {
    let pos = if !puppet {
        let pos = xl330::sync_read_present_position(
            &io,
            serial_port,
            &[0, 1, 2, 3, 4, 5],
        ).expect("Read Communication error");

        pos.iter().map(|&x| convert_to_extended_mode(x)).collect::<Vec<_>>()
    } else {
        // x430 for 2 first and xl330 for the rest

        let mut pos = xl430::sync_read_present_position(
            &io,
            serial_port,
            &[0, 1],
        ).expect("Read Communication error");

        let pos2 = xl330::sync_read_present_position(
            &io,
            serial_port,
            &[2, 3, 4, 5],
        ).expect("Read Communication error");

        pos.iter().chain(pos2.iter()).map(|&x| convert_to_extended_mode(x)).collect::<Vec<_>>()
    };

    pos
}

fn prepare_configuration(io: &DynamixelSerialIO, serial_port: &mut dyn SerialPort, puppet: bool) {
    xl330::sync_write_torque_enable(
        &io,
        serial_port,
        &[2, 3, 4, 5],
        &[0; 4],
    ).expect("Communication error");

    // Now we enable all modes to "position extended"

    xl330::sync_write_operating_mode(
        &io,
        serial_port,
        &[2, 3, 4, 5],
        &[4; 4],
    ).expect("Communication error");

    if !puppet {
        xl330::sync_write_torque_enable(
            &io,
            serial_port,
            &[0, 1],
            &[0; 2],
        ).expect("Communication error");

        xl330::sync_write_operating_mode(
            &io,
            serial_port,
            &[0, 1],
            &[4; 2],
        ).expect("Communication error");
    } else {
        xl430::sync_write_torque_enable(
            &io,
            serial_port,
            &[0, 1],
            &[0; 2],
        ).expect("Communication error");

        xl430::sync_write_operating_mode(
            &io,
            serial_port,
            &[0, 1],
            &[4; 2],
        ).expect("Communication error");
    }
}

fn get_nearest_rounded_positions (pos: &Vec<i32>) -> Vec<i32> {
    pos.iter().map(|&x| {
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
    }).collect::<Vec<_>>()
}

fn invert(pos: &Vec<i32>, inverted: &[bool; 6]) -> Vec<i32> {
    pos.iter().enumerate().map(|(i, &x)| {
        if inverted[i] {
            -x
        } else {
            x
        }
    }).collect::<Vec<_>>()
}

fn configure_homing(io: &DynamixelSerialIO, serial_port: &mut dyn SerialPort, inverted: &[bool; 6], puppet: bool) {
    println!("------Configuring homing");

    prepare_configuration(io, serial_port, puppet);
}

fn main() {
    let cli = Cli::parse();
    println!("CLI is {:#?}", cli);

    // Configure the serial port
    let mut serial_port = serialport::new(cli.port, 1_000_000).timeout(Duration::from_millis(200)).open().expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
}